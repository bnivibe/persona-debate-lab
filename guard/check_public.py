#!/usr/bin/env python3
"""Privacy guard for the public persona-debate-lab repo.

Fails when a tracked file contains Hangul, an email address, a phone number,
a money amount, a URL outside the allowlist, or a deny-listed term; when a file
cannot be read as text; when a path is outside the expected layout; or when a
path itself matches a rule. Reports the file, line and rule only. The matched
text is never printed, and a path that is itself a finding is withheld, so CI
logs cannot leak what the guard caught.

Modes: the tracked files as they are on disk (default), the staged changes
(--staged, pre-commit), a commit message (--message FILE, commit-msg), every
commit and its message in a range (--history BASE..HEAD, CI), and the commits
a push would publish (--pre-push, reads the pre-push hook's stdin).
"""
import argparse
import fnmatch
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

RULES = [
    ("hangul", re.compile(
        r"[\u1100-\u11FF\u3130-\u318F\u3200-\u321E\u3260-\u327E\uA960-\uA97F"
        r"\uAC00-\uD7AF\uD7B0-\uD7FF\uFFA0-\uFFDC]")),
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")),
    ("phone", re.compile(
        # North American with separators: (NXX) NXX-XXXX, NXX.NXX.XXXX, +1 NXX NXX XXXX, also glued to words.
        r"(?<![\d-])(?:\+?1[ .-]?)?(?:\([2-9]\d{2}\)\s?|[2-9]\d{2}[ .-])[2-9]\d{2}[ .-]\d{4}(?![\d-])"
        # North American without separators; date-like runs (2026101412) are left alone.
        r"|(?<![\w-])(?:\+1)?(?!20\d{2}(?:0[1-9]|1[0-2]))[2-9]\d{2}[2-9]\d{6}(?![\w-])"
        # Korean mobiles, with or without +82 or 82 and an optional (0).
        r"|(?<![\w-])(?:\+?82[ .-]?(?:\(0\))?1[016789]|01[016789])[ .-]?\d{3,4}[ .-]?\d{4}(?![\w-])"
        # Korean landlines: 0X-XXX-XXXX and 0XX.XXX.XXXX, with a dash, dot, space or closing paren.
        r"|(?<![\d-])0\d{1,2}[ .)-]\d{3,4}[ .-]\d{4}(?![\d-])")),
    # A lone $1 or $2 is a shell or awk positional, so a single-digit dollar counts only with a
    # magnitude, a rate or a sentence end after it. "won" needs a real amount and is never "won't".
    ("money", re.compile(
        r"\$(?:\s\d|\d[\d,]*\d|\d[.,]\d)"
        r"|\$\d\s?(?:k|m|mm|b|bn|million|billion|thousand|grand)\b"
        r"|\$\d(?=\s?(?:per\b|an?\s|/\s?(?:mo|month|yr|year|wk|week|day|hr|hour)\b)|\.(?:\s|$))"
        r"|\b[a-z]{1,2}\$\s?\d"
        r"|[\u20A9\u20AC\u00A3]\s?\d"
        r"|(?<![\w.])\d[\d,.]*[\$\u20A9\u20AC\u00A3](?![\w{(])"
        r"|\b(?:CAD|USD|KRW|EUR|GBP)\s?\d"
        r"|\d[\d,.]*\s?(?:k|m|mm|bn|million|billion|thousand)?\s?(?:CAD|USD|KRW|EUR|GBP|dollars?|bucks)\b"
        r"|\d[\d,.]*\s?(?:k|m|mm|bn|million|billion|thousand)\s?won\b(?!['\u2019])"
        r"|(?:\d{1,3}(?:,\d{3})+|\d{5,})\s?won\b(?!['\u2019])", re.IGNORECASE)),
]
# Any scheme, and protocol-relative links (two slashes, then a dotted host).
URL = re.compile(
    r"\b[a-z][a-z0-9+.-]*://[^\s)>\]\"'`]+"
    r"|(?<![\w:/])//[a-z0-9-]+(?:\.[a-z0-9-]+)+[^\s)>\]\"'`]*", re.IGNORECASE)
# A link written without a scheme (a domain followed by a path, query, fragment or port) is
# still a link, whatever its TLD. Endings this repo uses for file names are not TLDs here.
FILE_ENDINGS = r"py|md|sh|csv|yml|yaml|json|txt|toml|app|lock|cfg|ini|html|css|js|ts|png|jpg|svg|pdf"
BARE_DOMAIN = re.compile(
    r"(?<![\w@./-])(?:[a-z0-9-]+\.)+(?!(?:" + FILE_ENDINGS + r")\b)[a-z]{2,24}(?:[/?#]|:\d)[^\s)>\]\"'`]*",
    re.IGNORECASE)
WWW_HOST = re.compile(r"(?<![\w@./-])www\.[a-z0-9-]+(?:\.[a-z0-9-]+)+", re.IGNORECASE)
# (exact host, path prefix). A prefix matches whole path segments only.
ALLOWED_URLS = (
    ("github.com", "/bnivibe/persona-debate-lab"),
    ("docs.claude.com", ""),
    ("www.anthropic.com", ""),
    ("discord.com", "/api"),
)
# A Discord webhook URL is a credential: anyone holding it can post to the channel.
DISCORD_HOSTS = {"discord.com", "discordapp.com", "ptb.discord.com", "canary.discord.com"}
# Every tracked path must match one of these. A transcript saved into the clone by
# mistake is then an unexpected path, whatever its words are.
# Matched segment by segment, so a pattern never reaches into a deeper folder.
EXPECTED_PATHS = (
    "README.md", "METHOD.md", "LICENSE", ".gitignore",
    "personas/roster.md", "lessons/LESSONS.md",
    "scorecards/rounds.csv", "scorecards/outcomes.csv",
    "skill/SKILL.md", "skill/bin/*.py", "skill/templates/*.md", "skill/tests/test_*.py",
    "guard/check_public.py", "guard/install-hooks.sh", "guard/tests/test_*.py",
    ".github/workflows/*.yml",
)
DEFAULT_DENYLIST = Path.home() / ".claude" / "debate-denylist.txt"
ZERO = "0" * 40


def deny_pattern(term):
    # Words may be split by a line wrap or markdown emphasis (**Jane** Doe).
    words = [re.escape(w) for w in term.split()]
    return re.compile(r"(?<![A-Za-z0-9])" + r"[\s*_]+".join(words) + r"(?![A-Za-z0-9])", re.IGNORECASE)


def url_allowed(url):
    try:
        parts = urlsplit(url)
        host = (parts.hostname or "").lower()
    except ValueError:
        return False
    path = parts.path
    if host in DISCORD_HOSTS and "/webhooks/" in path + "/":
        return False
    for allowed_host, prefix in ALLOWED_URLS:
        if host == allowed_host and (not prefix or path == prefix or path.startswith(prefix + "/")):
            return True
    return False


def scan_text(path, text, deny):
    found = []
    for no, line in enumerate(text.splitlines(), start=1):
        for name, rx in RULES:
            if rx.search(line):
                found.append((path, no, name))
        urls = URL.findall(line) + ["https://" + bare for bare in BARE_DOMAIN.findall(line) + WWW_HOST.findall(line)]
        # Trailing punctuation belongs to the sentence, not the link.
        if any(not url_allowed(url.rstrip(".,;:!?")) for url in urls):
            found.append((path, no, "url"))
    # Deny terms run over the whole text so a term split across lines is still caught.
    hit_lines = set()
    for rx in (deny_pattern(t) for t in deny):
        for m in rx.finditer(text):
            hit_lines.add(text.count("\n", 0, m.start()) + 1)
    found.extend((path, no, "denylist") for no in sorted(hit_lines))
    found.sort(key=lambda f: f[1])
    return found


TRAILER = re.compile(r"^[A-Za-z][A-Za-z-]*-by:\s", re.IGNORECASE)
TRAILER_ADDRESS = re.compile(r"<[^<>\s]+@[^<>\s]+>")
# Git's own scissors block, exactly as `git commit -v` writes it into the editor file.
SCISSORS = re.compile(r"^(.) -{24} >8 -{24}\n\1 Do not modify or remove the line above\.$", re.MULTILINE)


def scan_message(label, text, deny, cut_scissors=False):
    """Commit messages are public too, so every line is scanned, comment lines included.

    Only the address inside a trailer (an author identity, out of scope) is masked; the rest of a
    trailer line is scanned. Only the commit-msg hook cuts at git's own scissors block (the
    `git commit -v` diff below it is not the message); a stored message is scanned whole.
    """
    cut = SCISSORS.search(text) if cut_scissors else None
    if cut:
        text = text[:cut.start()]
    lines = [TRAILER_ADDRESS.sub("<>", line) if TRAILER.match(line) else line for line in text.splitlines()]
    return scan_text(label, "\n".join(lines), deny)


def message_findings(label, raw, deny, cut_scissors=False):
    text, undecodable = decode(raw)
    if undecodable:
        return [(label, 0, "undecodable")]
    return scan_message(label, text, deny, cut_scissors)


def expected_path(path, pattern):
    parts, wanted = path.split("/"), pattern.split("/")
    return len(parts) == len(wanted) and all(fnmatch.fnmatchcase(a, b) for a, b in zip(parts, wanted))


def path_rules(path, deny):
    rules = [name for name, rx in RULES if rx.search(path)]
    words = re.sub(r"[-_./]+", " ", path)
    if any(deny_pattern(t).search(path) or deny_pattern(t).search(words) for t in deny):
        rules.append("denylist")
    if not any(expected_path(path, pattern) for pattern in EXPECTED_PATHS):
        rules.append("unexpected-path")
    return rules


def decode(raw):
    """Return (text, undecodable). UTF-16 with a byte-order mark is read; anything else must be UTF-8.
    Text that still holds a NUL after decoding (UTF-32 read as UTF-16, for one) is undecodable."""
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        try:
            text = raw.decode("utf-16")
        except UnicodeDecodeError:
            return None, True
        return (None, True) if "\x00" in text else (text, False)
    if b"\x00" in raw:
        return None, True
    try:
        return raw.decode("utf-8"), False
    except UnicodeDecodeError:
        return None, True


def scan_blobs(items, deny, prefix=""):
    """Scan (path, raw bytes) pairs. A file that cannot be read as text is a finding, not a skip."""
    found = []
    for n, (path, raw) in enumerate(items, start=1):
        hits = path_rules(path, deny)
        label = f"{prefix}path #{n} (withheld)" if hits else f"{prefix}{path}"
        found.extend((label, 0, rule) for rule in hits)
        if raw is None:
            found.append((label, 0, "unreadable"))
            continue
        text, undecodable = decode(raw)
        if undecodable:
            found.append((label, 0, "undecodable"))
            continue
        found.extend((label, no, rule) for (_p, no, rule) in scan_text(path, text, deny))
    return found


def format_findings(found):
    return [f"{path}: {rule}" if no == 0 else f"{path}:{no}: {rule}" for (path, no, rule) in found]


def load_denylist():
    env = os.environ.get("DENYLIST")
    if env:
        source = env
    else:
        path = Path(os.environ.get("DEBATE_DENYLIST", DEFAULT_DENYLIST)).expanduser()
        if not path.is_file():
            print(f"guard: deny-list missing ({path}). Create it or set DENYLIST.", file=sys.stderr)
            raise SystemExit(2)
        source = path.read_text(encoding="utf-8")
    terms = []
    for line in source.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            terms.append(line)
    if not terms:
        print("guard: deny-list has no terms. Refusing to run with the name check switched off.", file=sys.stderr)
        raise SystemExit(2)
    return terms


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True).stdout


def split_z(out):
    return [p for p in out.decode("utf-8", "surrogateescape").split("\0") if p]


def tracked_files(staged):
    out = git("diff", "--cached", "--name-only", "-z", "--diff-filter=d") if staged else git("ls-files", "-z")
    return list(dict.fromkeys(split_z(out)))  # an unmerged path is listed once per stage


def read(path, staged):
    """Staged mode reads the index. Otherwise the working tree, so an edit is scanned before it is
    staged; a symlink is read as its target text, never followed, and a tracked file missing on
    disk falls back to the index. Returns None when git cannot produce the content (unmerged)."""
    try:
        if not staged:
            p = Path(path)
            if p.is_symlink():
                return os.readlink(p).encode("utf-8", "surrogateescape")
            if p.is_file():
                return p.read_bytes()
        return git("show", f":{path}")
    except subprocess.CalledProcessError:
        return None


def history_findings(rev_args, deny):
    """Scan every file each commit in the range adds or changes, so a leak removed later still fails."""
    found = []
    for sha in git("rev-list", *rev_args).decode().split():
        out = git("diff-tree", "-r", "--root", "-m", "--no-commit-id", "--name-only", "-z", "--diff-filter=d", sha)
        paths = list(dict.fromkeys(split_z(out)))
        found.extend(scan_blobs([(p, git("show", f"{sha}:{p}")) for p in paths], deny, prefix=f"{sha[:7]} "))
        found.extend(message_findings(f"{sha[:7]} commit message", git("log", "-1", "--format=%B", sha), deny))
    return found


def pre_push_revs(text, remote="origin"):
    """Rev-list arguments for each ref in the pre-push hook's stdin.

    A new branch is scanned back to what THIS remote already has. Excluding every remote would
    skip commits that only another remote knows, such as a private repo's history being ported.
    """
    revs = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) != 4:
            continue
        _local_ref, local_sha, _remote_ref, remote_sha = parts
        if local_sha == ZERO:
            continue  # a branch deletion publishes nothing
        revs.append([local_sha, "--not", f"--remotes={remote}"] if remote_sha == ZERO
                    else [f"{remote_sha}..{local_sha}"])
    return revs


def main(argv=None):
    ap = argparse.ArgumentParser(description="Privacy guard for the public repo")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--staged", action="store_true", help="scan the staged snapshot (pre-commit)")
    mode.add_argument("--history", metavar="REVS", help="scan every commit in a range, e.g. BASE..HEAD")
    mode.add_argument("--pre-push", nargs="?", const="origin", metavar="REMOTE",
                      help="scan the commits a push to REMOTE would publish (pre-push hook)")
    mode.add_argument("--message", metavar="FILE", help="scan a commit message file (commit-msg hook)")
    args = ap.parse_args(argv)
    deny = load_denylist()
    if args.message:
        found = message_findings("commit message", Path(args.message).read_bytes(), deny, cut_scissors=True)
    elif args.history or args.pre_push:
        ranges = [args.history.split()] if args.history else pre_push_revs(sys.stdin.read(), args.pre_push)
        found = []
        for rev_args in ranges:
            found.extend(history_findings(rev_args, deny))
    else:
        found = scan_blobs([(p, read(p, args.staged)) for p in tracked_files(args.staged)], deny)
    for line in format_findings(found):
        print(line)
    print(f"guard: {len(found)} finding(s), {len(deny)} deny-list term(s)")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
