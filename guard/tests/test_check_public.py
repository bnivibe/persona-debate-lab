import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_public as cp  # noqa: E402

# Every fixture in this file is synthetic: NANP fiction numbers (555-0100 to 555-0199),
# reserved example domains, made-up amounts and names. Never use a value from anyone's records.
# Fixtures are assembled at runtime so this file itself passes the guard.
HANGUL = chr(0xD55C) + chr(0xAE00)
EMAIL = "someone" + "@" + "example.org"
SHORT_EMAIL = "a" + "@" + "b.co"
NA_PHONE = "-".join(["604", "555", "0123"])
KR_PHONE = "-".join(["010", "1234", "5678"])
HTTPS = "https" + "://"


class ScanText(unittest.TestCase):
    def rules(self, text, deny=()):
        return [rule for (_p, _l, rule) in cp.scan_text("x.md", text, list(deny))]

    def test_clean_text_passes(self):
        self.assertEqual(self.rules("A plain English line.\nAnother one."), [])

    def test_hangul_fails(self):
        self.assertEqual(self.rules("hello " + HANGUL), ["hangul"])

    def test_email_fails(self):
        self.assertEqual(self.rules("write to " + EMAIL + " today"), ["email"])

    def test_phone_formats_fail(self):
        for text in ["call " + NA_PHONE, "call (604) 555 " + "0123", "call +1 604.555." + "0123", "call " + KR_PHONE]:
            self.assertEqual(self.rules(text), ["phone"], text)

    def test_dates_and_versions_are_not_phones(self):
        self.assertEqual(self.rules("on 2026-10-14 we used v1.2.3"), [])

    def test_money_fails(self):
        for text in ["rent is " + "$" + "4,321", "CAD" + " 100 per day", "about 100 " + "CAD", "KRW" + " 50000", "1,000 " + "won"]:
            self.assertEqual(self.rules(text), ["money"], text)

    def test_shell_dollar_is_not_money(self):
        self.assertEqual(self.rules("cd $HOME and echo ${VAR}"), [])

    def test_url_allowlist(self):
        self.assertEqual(self.rules("see https://github.com/bnivibe/persona-debate-lab/blob/main/METHOD.md"), [])
        self.assertEqual(self.rules("see " + HTTPS + "github" + ".com/bnivibe/other-repo"), ["url"])
        self.assertEqual(self.rules("see " + HTTPS + "example" + ".com/page"), ["url"])

    def test_denylist_case_and_possessive(self):
        self.assertEqual(self.rules("ACME called", ["Acme"]), ["denylist"])
        self.assertEqual(self.rules("Acme's team", ["Acme"]), ["denylist"])

    def test_denylist_needs_word_boundary(self):
        self.assertEqual(self.rules("a Zetaform demo", ["Zeta"]), [])

    def test_denylist_multiword_spacing(self):
        self.assertEqual(self.rules("met Jane   Doe there", ["Jane Doe"]), ["denylist"])

    def test_line_numbers(self):
        found = cp.scan_text("x.md", "ok\nok\nmail " + SHORT_EMAIL, [])
        self.assertEqual(found, [("x.md", 3, "email")])


class Reporting(unittest.TestCase):
    def test_report_never_prints_the_match(self):
        lines = cp.format_findings(cp.scan_text("x.md", "hi " + EMAIL, []))
        self.assertTrue(lines)
        self.assertNotIn(EMAIL, "\n".join(lines))
        self.assertNotIn("example", "\n".join(lines))


class Files(unittest.TestCase):
    def test_binary_is_skipped(self):
        text, skipped = cp.decode(b"\x89PNG\r\n\x1a\n\x00\xff\xfe")
        self.assertIsNone(text)
        self.assertTrue(skipped)


class Denylist(unittest.TestCase):
    def test_env_list_is_used_first(self):
        os.environ["DENYLIST"] = "Alpha Corp\n\n# comment\nBeta"
        try:
            self.assertEqual(cp.load_denylist(), ["Alpha Corp", "Beta"])
        finally:
            del os.environ["DENYLIST"]

    def test_missing_list_exits(self):
        saved = os.environ.pop("DENYLIST", None)
        os.environ["DEBATE_DENYLIST"] = "/nonexistent/denylist.txt"
        try:
            with self.assertRaises(SystemExit) as ctx:
                cp.load_denylist()
            self.assertEqual(ctx.exception.code, 2)
        finally:
            del os.environ["DEBATE_DENYLIST"]
            if saved is not None:
                os.environ["DENYLIST"] = saved


class Fixes(unittest.TestCase):
    """Final-review findings I1 to I8: every gap must fail closed."""

    def rules(self, text, deny=()):
        return [rule for (_p, _l, rule) in cp.scan_text("x.md", text, list(deny))]

    def blob_rules(self, items, deny=()):
        return [rule for (_p, _l, rule) in cp.scan_blobs(items, list(deny))]

    # I1: undecodable content is a finding, UTF-16 with a BOM is read
    def test_utf16_with_bom_is_decoded(self):
        self.assertEqual(cp.decode(b"\xff\xfe" + "hi there".encode("utf-16-le")), ("hi there", False))

    def test_legacy_korean_encoding_is_a_finding(self):
        self.assertEqual(self.blob_rules([("README.md", HANGUL.encode("cp949"))]), ["undecodable"])

    def test_binary_is_a_finding(self):
        self.assertEqual(self.blob_rules([("README.md", b"\x89PNG\r\n\x1a\n\x00\xff")]), ["undecodable"])

    # I3: paths are scanned and never printed when they hit
    def test_path_is_scanned_and_withheld(self):
        found = cp.scan_blobs([("lessons/acme-offer.md", b"clean")], ["Acme"])
        self.assertIn("denylist", [r for (_p, _l, r) in found])
        self.assertNotIn("acme", "\n".join(cp.format_findings(found)).lower())

    # I8: only known paths may be tracked
    def test_unexpected_path_is_a_finding_and_withheld(self):
        found = cp.scan_blobs([("notes/private-slug/thread.md", b"clean")], [])
        self.assertEqual([r for (_p, _l, r) in found], ["unexpected-path"])
        self.assertNotIn("private-slug", "\n".join(cp.format_findings(found)))

    def test_expected_paths_pass(self):
        paths = ["README.md", "METHOD.md", "LICENSE", ".gitignore", "personas/roster.md",
                 "scorecards/rounds.csv", "lessons/LESSONS.md", "skill/bin/score.py",
                 "skill/templates/thread.md", "guard/check_public.py", ".github/workflows/guard.yml"]
        self.assertEqual(self.blob_rules([(p, b"clean") for p in paths]), [])

    # I4: a deny term split by a line wrap or markdown emphasis
    def test_denylist_across_wrap_and_emphasis(self):
        self.assertEqual(self.rules("we met Jane\nDoe there", ["Jane Doe"]), ["denylist"])
        self.assertEqual(self.rules("met **Jane** Doe", ["Jane Doe"]), ["denylist"])

    def test_wrapped_hit_reports_its_first_line(self):
        self.assertEqual(cp.scan_text("x.md", "ok\nJane\nDoe", ["Jane Doe"]), [("x.md", 2, "denylist")])

    # I5: exact hosts, segment-bounded paths, no webhook URLs
    def test_url_lookalikes_and_webhooks_fail(self):
        for url in [HTTPS + "discord" + ".com/api/webhooks/123/abc",
                    HTTPS + "discord" + ".com/api/v10/webhooks/123/abc",
                    HTTPS + "docs.claude.com.evil" + ".example/x",
                    HTTPS + "github" + ".com/bnivibe/persona-debate-lab-private"]:
            self.assertEqual(self.rules("see " + url), ["url"], url)

    def test_allowed_urls_pass(self):
        for url in [HTTPS + "discord.com/api/v10/channels/1/messages",
                    HTTPS + "docs.claude.com/en/docs",
                    HTTPS + "github.com/bnivibe/persona-debate-lab"]:
            self.assertEqual(self.rules("see " + url), [], url)

    def test_trailing_punctuation_is_not_part_of_the_link(self):
        self.assertEqual(self.rules("(" + HTTPS + "github.com/bnivibe/persona-debate-lab, 1.0)"), [])
        self.assertEqual(self.rules("see " + HTTPS + "docs.claude.com/en/docs."), [])

    # I6: an empty deny-list cannot switch layer 3 off
    def test_empty_denylist_exits(self):
        os.environ["DENYLIST"] = "# only a comment\n   \n"
        try:
            with self.assertRaises(SystemExit) as ctx:
                cp.load_denylist()
            self.assertEqual(ctx.exception.code, 2)
        finally:
            del os.environ["DENYLIST"]

    # I2: pre-push ranges
    def test_pre_push_ranges(self):
        zero = "0" * 40
        a, b = "a" * 40, "b" * 40
        self.assertEqual(cp.pre_push_revs(f"refs/heads/x {a} refs/heads/x {b}\n"), [[f"{b}..{a}"]])
        self.assertEqual(cp.pre_push_revs(f"refs/heads/x {a} refs/heads/x {zero}\n", "origin"),
                         [[a, "--not", "--remotes=origin"]])
        self.assertEqual(cp.pre_push_revs(f"(delete) {zero} refs/heads/x {b}\n"), [])


class History(unittest.TestCase):
    """I2: a leak added and later removed must still fail the history scan."""

    def test_removed_leak_in_history_is_caught(self):
        with tempfile.TemporaryDirectory() as d:
            git = make_repo(d)
            readme = Path(d) / "README.md"
            readme.write_text("clean\n")
            git("add", "README.md")
            git("commit", "-q", "-m", "one")
            first = git("rev-parse", "HEAD")
            readme.write_text("mail " + EMAIL + "\n")
            git("commit", "-q", "-am", "two")
            readme.write_text("clean\n")
            git("commit", "-q", "-am", "three")
            saved = os.getcwd()
            os.environ["DENYLIST"] = "Zeta"
            try:
                os.chdir(d)
                found = cp.history_findings([f"{first}..HEAD"], ["Zeta"])
                self.assertEqual([r for (_p, _l, r) in found], ["email"])
                self.assertEqual(cp.main(["--history", f"{first}..HEAD"]), 1)
                self.assertEqual(cp.main([]), 0)
            finally:
                os.chdir(saved)
                del os.environ["DENYLIST"]


INSTALLER = Path(__file__).resolve().parents[1] / "install-hooks.sh"


# Git subprocesses in these tests never read the developer's global or system config, so a
# global core.hooksPath or template dir cannot leak in or be written to.
ISOLATED = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


def make_repo(d):
    def git(*args, check=True):
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t" + "@" + "t.invalid",
                               "-c", "commit.gpgsign=false", *args],
                              cwd=d, check=check, capture_output=True, text=True, env=ISOLATED).stdout.strip()
    git("init", "-q", "-b", "main")
    return git


class InRepo:
    """Run the guard inside a temporary repo with a made-up deny-list, output silenced."""

    def __init__(self, d, deny="Zeta"):
        self.d, self.deny = d, deny

    def __enter__(self):
        self.saved = os.getcwd()
        self.env = os.environ.get("DENYLIST")
        os.environ["DENYLIST"] = self.deny
        os.chdir(self.d)
        return self

    def __exit__(self, *exc):
        os.chdir(self.saved)
        if self.env is None:
            os.environ.pop("DENYLIST", None)
        else:
            os.environ["DENYLIST"] = self.env
        return False

    def main(self, *argv):
        with contextlib.redirect_stdout(io.StringIO()):
            return cp.main(list(argv))


class Minors(unittest.TestCase):
    """Final-review minors M1 to M4, M10, M14, M16."""

    def rules(self, text, deny=()):
        return [rule for (_p, _l, rule) in cp.scan_text("x.md", text, list(deny))]

    # M1
    def test_more_phone_formats_fail(self):
        for text in ["call +82 10 1234 " + "5678", "call +82-10-1234-" + "5678", "call 010 1234 " + "5678",
                     "call 0101234" + "5678", "call (604)555-" + "0123", "call 604555" + "0123"]:
            self.assertEqual(self.rules(text), ["phone"], text)

    def test_long_ids_timestamps_and_hashes_are_not_phones(self):
        for text in ["channel 98765432109876" + "54321", "epoch 17000" + "00000", "commit a60455" + "50123b"]:
            self.assertEqual(self.rules(text), [], text)

    # M2
    def test_more_money_fails(self):
        for text in ["about 4,321 " + "dollars", "paid 4,321" + "$", "costs " + chr(0x20AC) + "40",
                     "costs " + chr(0xA3) + "40", "costs $" + "12", "costs $" + "1.50", "costs $ " + "5"]:
            self.assertEqual(self.rules(text), ["money"], text)

    def test_positional_dollars_and_won_as_a_verb_pass(self):
        for text in ["awk '{print $1, $2}'", "echo $1 $2", "sed 's/x/$1/'", "persona 2 won the clash"]:
            self.assertEqual(self.rules(text), [], text)

    # M3
    def test_uppercase_scheme_and_bare_domains_fail(self):
        for text in ["see HTTPS" + "://example.org/page", "see linkedin" + ".com/in/jane-doe",
                     "see drive.google" + ".com/file/d/x"]:
            self.assertEqual(self.rules(text), ["url"], text)

    def test_bare_allowed_domain_and_file_names_pass(self):
        for text in ["see github" + ".com/bnivibe/persona-debate-lab", "run skill/bin/score.py and guard/check_public.py",
                     "re.compile(x)", "see docs.claude" + ".com/en/docs"]:
            self.assertEqual(self.rules(text), [], text)

    # M4
    def test_halfwidth_and_enclosed_hangul_fail(self):
        for code in (0xFFA1, 0x3200, 0x3260):
            self.assertEqual(self.rules("x " + chr(code)), ["hangul"], hex(code))

    # M14
    def test_commit_message_scans_comment_and_trailer_lines(self):
        msg = ("fix: tidy\n\n# Zeta called from " + NA_PHONE + "\nSuggested-by: Zeta\n"
               "Co-Authored-By: X <" + EMAIL + ">\n")
        found = sorted(r for (_p, _l, r) in cp.scan_message("msg", msg, ["Zeta"]))
        self.assertEqual(found, ["denylist", "denylist", "phone"])

    def test_message_mode_exits_1(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "COMMIT_EDITMSG"
            path.write_text("fix: mention Zeta\n")
            with InRepo(d) as repo:
                self.assertEqual(repo.main("--message", str(path)), 1)

    def test_history_scans_commit_messages(self):
        with tempfile.TemporaryDirectory() as d:
            git = make_repo(d)
            (Path(d) / "README.md").write_text("clean\n")
            git("add", "README.md")
            git("commit", "-q", "-m", "one")
            first = git("rev-parse", "HEAD")
            (Path(d) / "README.md").write_text("still clean\n")
            git("commit", "-q", "-am", "two: talk about Zeta")
            with InRepo(d):
                found = cp.history_findings([f"{first}..HEAD"], ["Zeta"])
            self.assertEqual([r for (_p, _l, r) in found], ["denylist"])
            self.assertTrue(found[0][0].endswith("commit message"))

    # M10, M16
    def test_main_exit_codes_on_the_tree(self):
        with tempfile.TemporaryDirectory() as d:
            git = make_repo(d)
            (Path(d) / "README.md").write_text("mail " + EMAIL + "\n")
            git("add", "README.md")
            git("commit", "-q", "-m", "one")
            with InRepo(d) as repo:
                self.assertEqual(repo.main(), 1)
                (Path(d) / "README.md").write_text("clean\n")
                git("commit", "-q", "-am", "two")
                self.assertEqual(repo.main(), 0)

    def test_deleted_working_file_does_not_crash(self):
        with tempfile.TemporaryDirectory() as d:
            git = make_repo(d)
            (Path(d) / "README.md").write_text("clean\n")
            git("add", "README.md")
            git("commit", "-q", "-m", "one")
            (Path(d) / "README.md").unlink()
            with InRepo(d) as repo:
                self.assertEqual(repo.main(), 0)

    def test_staged_type_change_is_scanned(self):
        with tempfile.TemporaryDirectory() as d:
            git = make_repo(d)
            (Path(d) / "LICENSE").write_text("clean\n")
            (Path(d) / "README.md").symlink_to("LICENSE")
            git("add", "LICENSE", "README.md")
            git("commit", "-q", "-m", "one")
            (Path(d) / "README.md").unlink()
            (Path(d) / "README.md").write_text("mail " + EMAIL + "\n")
            git("add", "README.md")
            with InRepo(d) as repo:
                self.assertEqual(repo.main("--staged"), 1)

    def test_missing_denylist_exits_2_from_main(self):
        saved = os.environ.pop("DENYLIST", None)
        os.environ["DEBATE_DENYLIST"] = "/nonexistent/denylist.txt"
        try:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as ctx:
                cp.main([])
            self.assertEqual(ctx.exception.code, 2)
        finally:
            del os.environ["DEBATE_DENYLIST"]
            if saved is not None:
                os.environ["DENYLIST"] = saved


class Installer(unittest.TestCase):
    """M11: hooks land where git looks for them, and a foreign hook is never overwritten."""

    def run_installer(self, cwd, env=ISOLATED):
        return subprocess.run(["sh", str(INSTALLER)], cwd=cwd, capture_output=True, text=True, env=env)

    def test_installs_all_three_hooks_in_a_linked_worktree(self):
        with tempfile.TemporaryDirectory() as d:
            main = Path(d) / "main"
            main.mkdir()
            git = make_repo(main)
            (main / "README.md").write_text("clean\n")
            git("add", "README.md")
            git("commit", "-q", "-m", "one")
            git("worktree", "add", "-q", str(Path(d) / "wt"), "-b", "wt")
            result = self.run_installer(Path(d) / "wt")
            self.assertEqual(result.returncode, 0, result.stderr)
            hooks = main / ".git" / "hooks"
            for name in ("pre-commit", "commit-msg", "pre-push"):
                self.assertIn("guard/check_public.py", (hooks / name).read_text(), name)

    def test_refuses_to_replace_a_foreign_hook(self):
        with tempfile.TemporaryDirectory() as d:
            make_repo(d)
            hook = Path(d) / ".git" / "hooks" / "pre-commit"
            hook.parent.mkdir(parents=True, exist_ok=True)
            hook.write_text("#!/bin/sh\necho mine\n")
            result = self.run_installer(d)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(hook.read_text(), "#!/bin/sh\necho mine\n")


class Review2(unittest.TestCase):
    """Second review, F1 to F17."""

    def rules(self, text, deny=()):
        return [rule for (_p, _l, rule) in cp.scan_text("x.md", text, list(deny))]

    # F2: amounts the earlier rule caught, plus magnitudes and units
    def test_money_with_magnitudes_and_units_fails(self):
        for text in ["a $" + "5k signing bonus", "valued at $" + "1M", "raised $" + "2 million",
                     "I pay $" + "9 a month", "$" + "9/mo", "it was $" + "5.", "US$" + "5",
                     "offer 43k " + "CAD", "43K " + "USD", "salary was 12 million " + "won",
                     "1.5M " + "won", "5 million " + "dollars", "43k " + "dollars", "1,000" + chr(0x20A9)]:
            self.assertEqual(self.rules(text), ["money"], text)

    # F7: ordinary prose and code that is not money
    def test_money_false_positives_pass(self):
        for text in ["by 2027 won" + "'t matter", "In 2026 won the vote", "var x2" + "$ = 1", "echo 1 $",
                     "sed 's/x/$" + "1/'"]:
            self.assertEqual(self.rules(text), [], text)

    # F6: formats the earlier rule caught, and more Korean shapes
    def test_phone_regressions_fail(self):
        for text in ["_604-555-" + "0123_", "Tel604-555-" + "0123", "604-555-" + "0123x12", "604-555-" + "0123ext 12",
                     chr(0x4E2D) + "604-555-" + "0123", "031.123." + "4567", "031 123 " + "4567", "02 123 " + "4567",
                     "02)123-" + "4567", "82-10-1234-" + "5678", "+82 (0)10-1234-" + "5678"]:
            self.assertEqual(self.rules(text), ["phone"], text)

    # F7: ids and stamps that are not phones
    def test_run_ids_and_stamps_are_not_phones(self):
        for text in ["CI run 18234" + "567890 passed", "stamp 20261" + "01412"]:
            self.assertEqual(self.rules(text), [], text)

    # F8: links with any TLD, query or port, protocol-relative, any scheme, bare www hosts
    def test_more_link_shapes_fail(self):
        for text in ["vid" + ".be/x", "maps.goo" + ".gl/abc", "meet" + ".us/j/1", "news.example.co" + ".uk/x",
                     "cs.uni" + ".edu/x", "forms" + ".gle/abc", "www.jane-doe" + ".com", "Profile:jane" + ".example/in/x",
                     "see /" + "/evil.example" + ".com/x", "ftp:" + "//evil" + ".com/x", "example" + ".com?id=1",
                     "example" + ".com:8080/x"]:
            self.assertEqual(self.rules(text), ["url"], text)

    # F7: file names, app bundles and code are not links
    def test_file_names_and_code_are_not_links(self):
        for text in ["open Tool.app/Contents/MacOS/x", "x = a//b", "see os.path: and guard/check_public.py:12",
                     "README.md#privacy", "skill/templates/thread.md"]:
            self.assertEqual(self.rules(text), [], text)

    # F9: the git commit -v diff below the scissors line is not part of the message
    def test_message_mode_cuts_the_verbose_diff(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "COMMIT_EDITMSG"
            path.write_text("fix: clean the lessons\n# " + "-" * 24 + " >8 " + "-" * 24 +
                            "\n# Do not modify or remove the line above.\n-Zeta was here\n")
            with InRepo(d) as repo:
                self.assertEqual(repo.main("--message", str(path)), 0)

    # F10: a message that is not UTF-8 fails closed
    def test_undecodable_message_is_a_finding(self):
        found = cp.message_findings("msg", ("fix: " + HANGUL).encode("cp949"), [])
        self.assertEqual([r for (_p, _l, r) in found], ["undecodable"])

    # F3: the default mode scans what is on disk, staged or not
    def test_unstaged_edit_is_scanned(self):
        with tempfile.TemporaryDirectory() as d:
            git = make_repo(d)
            (Path(d) / "README.md").write_text("clean\n")
            git("add", "README.md")
            git("commit", "-q", "-m", "one")
            (Path(d) / "README.md").write_text("call " + NA_PHONE + "\n")
            with InRepo(d) as repo:
                self.assertEqual(repo.main(), 1)

    def test_intent_to_add_file_is_scanned(self):
        with tempfile.TemporaryDirectory() as d:
            git = make_repo(d)
            (Path(d) / "README.md").write_text("clean\n")
            git("add", "README.md")
            git("commit", "-q", "-m", "one")
            (Path(d) / "METHOD.md").write_text("call " + NA_PHONE + "\n")
            git("add", "-N", "METHOD.md")
            with InRepo(d) as repo:
                self.assertEqual(repo.main(), 1)

    # F17: an unmerged path is a finding, not a traceback
    def test_unmerged_path_is_a_finding(self):
        with tempfile.TemporaryDirectory() as d:
            git = make_repo(d)
            readme = Path(d) / "README.md"
            readme.write_text("base\n")
            git("add", "README.md")
            git("commit", "-q", "-m", "one")
            git("switch", "-q", "-c", "side")
            readme.write_text("side\n")
            git("commit", "-q", "-am", "side")
            git("switch", "-q", "main")
            readme.write_text("main\n")
            git("commit", "-q", "-am", "main")
            git("merge", "-q", "side", check=False)
            with InRepo(d) as repo:
                self.assertEqual(repo.main("--staged"), 1)


class Installer2(unittest.TestCase):
    """Second review, F4 and F11."""

    def run_installer(self, cwd, env=ISOLATED):
        return subprocess.run(["sh", str(INSTALLER)], cwd=cwd, capture_output=True, text=True, env=env)

    def test_refuses_a_global_hooks_path(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d) / "repo"
            repo.mkdir()
            make_repo(repo)
            shared = Path(d) / "shared-hooks"
            shared.mkdir()
            config = Path(d) / "gitconfig"
            config.write_text(f"[core]\n\thooksPath = {shared}\n")
            result = self.run_installer(repo, env={**ISOLATED, "GIT_CONFIG_GLOBAL": str(config)})
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(shared.iterdir()), [])

    def test_no_partial_install(self):
        with tempfile.TemporaryDirectory() as d:
            make_repo(d)
            hooks = Path(d) / ".git" / "hooks"
            hooks.mkdir(parents=True, exist_ok=True)
            (hooks / "commit-msg").write_text("#!/bin/sh\necho mine\n")
            result = self.run_installer(d)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((hooks / "pre-commit").exists())
            self.assertFalse((hooks / "pre-push").exists())

    def test_hook_that_only_mentions_the_guard_is_foreign(self):
        with tempfile.TemporaryDirectory() as d:
            make_repo(d)
            hook = Path(d) / ".git" / "hooks" / "pre-commit"
            hook.parent.mkdir(parents=True, exist_ok=True)
            mine = "#!/bin/sh\npython3 guard/check_public.py --staged || exit 1\nnpm run lint\n"
            hook.write_text(mine)
            self.assertNotEqual(self.run_installer(d).returncode, 0)
            self.assertEqual(hook.read_text(), mine)

    def test_rerun_over_own_hooks_succeeds(self):
        with tempfile.TemporaryDirectory() as d:
            make_repo(d)
            self.assertEqual(self.run_installer(d).returncode, 0)
            self.assertEqual(self.run_installer(d).returncode, 0)


class Prepublish(unittest.TestCase):
    """Pre-publish review, D1 to D4."""

    # D1: commits known only to another remote are still scanned before a push
    def test_pre_push_scans_commits_known_only_to_another_remote(self):
        with tempfile.TemporaryDirectory() as d:
            git = make_repo(d)
            (Path(d) / "README.md").write_text("mail " + EMAIL + "\n")
            git("add", "README.md")
            git("commit", "-q", "-m", "one")
            sha = git("rev-parse", "HEAD")
            git("update-ref", "refs/remotes/old/main", sha)
            revs = cp.pre_push_revs(f"refs/remotes/old/main {sha} refs/heads/port {'0' * 40}\n", "origin")
            with InRepo(d):
                found = [r for rev in revs for (_p, _l, r) in cp.history_findings(rev, ["Zeta"])]
            self.assertEqual(found, ["email"])

    # D2: the layout is matched per path segment, not with a slash-crossing glob
    def test_deep_paths_under_known_folders_are_unexpected(self):
        for path in ["skill/threads/job-offer/thread.md", "skill/rounds/round-01.md",
                     "guard/notes/private.txt", "scorecards/private/notes.csv"]:
            self.assertEqual([r for (_p, _l, r) in cp.scan_blobs([(path, b"clean")], [])], ["unexpected-path"], path)

    # D3: a scissors-shaped line in a stored message hides nothing
    def test_history_never_cuts_at_scissors(self):
        with tempfile.TemporaryDirectory() as d:
            git = make_repo(d)
            (Path(d) / "README.md").write_text("clean\n")
            git("add", "README.md")
            git("commit", "-q", "-m", "one")
            first = git("rev-parse", "HEAD")
            git("commit", "-q", "--allow-empty", "-m", "fix: tidy",
                "-m", "# " + "-" * 24 + " >8 " + "-" * 24 + "\ncall Zeta")
            with InRepo(d):
                found = cp.history_findings([f"{first}..HEAD"], ["Zeta"])
            self.assertEqual([r for (_p, _l, r) in found], ["denylist"])

    def test_message_mode_cuts_only_at_gits_own_scissors(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "COMMIT_EDITMSG"
            path.write_text("fix: tidy\n# " + "-" * 24 + " >8 " + "-" * 24 + "\ncall Zeta\n")
            with InRepo(d) as repo:
                self.assertEqual(repo.main("--message", str(path)), 1)

    # D4: UTF-32 is not read as UTF-16 full of NULs
    def test_utf32_is_undecodable(self):
        raw = ("call " + NA_PHONE + " or mail " + EMAIL).encode("utf-32")
        self.assertEqual([r for (_p, _l, r) in cp.scan_blobs([("README.md", raw)], ["Zeta"])], ["undecodable"])


class Followups(unittest.TestCase):
    """Deferred review, D5, D8 and D10."""

    def rules(self, text, deny=()):
        return [rule for (_p, _l, rule) in cp.scan_text("x.md", text, list(deny))]

    # D8: a phone typed with a Unicode dash or space is still a phone
    def test_phones_with_unicode_separators_fail(self):
        for sep in (chr(0x2013), chr(0x2011), chr(0x2212), chr(0x2010), chr(0x2014), chr(0xFF0D)):
            self.assertEqual(self.rules("call " + NA_PHONE.replace("-", sep)), ["phone"], hex(ord(sep)))
            self.assertEqual(self.rules("call " + KR_PHONE.replace("-", sep)), ["phone"], hex(ord(sep)))
        for sep in (chr(0xA0), chr(0x202F), chr(0x2009), chr(0x3000)):
            self.assertEqual(self.rules("call (604)" + sep + "555" + sep + "0123"), ["phone"], hex(ord(sep)))
            self.assertEqual(self.rules("call +1" + sep + NA_PHONE.replace("-", sep)), ["phone"], hex(ord(sep)))

    def test_unicode_separators_keep_line_numbers(self):
        text = "ok\n" + NA_PHONE.replace("-", chr(0x2013)) + "\nok"
        self.assertEqual(cp.scan_text("x.md", text, []), [("x.md", 2, "phone")])

    def test_unicode_separator_in_a_path_is_still_a_phone(self):
        path = "skill/bin/" + NA_PHONE.replace("-", chr(0x2011)) + ".py"
        self.assertEqual([r for (_p, _l, r) in cp.scan_blobs([(path, b"clean")], [])], ["phone"])

    def test_en_dash_ranges_are_not_phones(self):
        self.assertEqual(self.rules("rounds 1" + chr(0x2013) + "3, years 2026" + chr(0x2013) + "2027"), [])

    # D10: the identity lines git writes into the editor buffer, exactly as git writes them
    TEMPLATE = ("\n# Please enter the commit message for your changes. Lines starting\n"
                "# with '#' will be ignored, and an empty message aborts the commit.\n#\n"
                "# Author:    A Person <" + EMAIL + ">\n"
                "# Committer: A Person <" + "a" + "@" + "host.example.local>\n#\n# On branch main\n")

    def message_exit(self, text):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "COMMIT_EDITMSG"
            path.write_text(text)
            with InRepo(d) as repo:
                return repo.main("--message", str(path))

    def test_editor_identity_lines_are_masked_in_message_mode(self):
        self.assertEqual(self.message_exit("fix: tidy\n" + self.TEMPLATE), 0)

    def test_editor_identity_names_are_still_scanned(self):
        self.assertEqual(self.message_exit("fix: tidy\n" + self.TEMPLATE.replace("A Person <", "Zeta <", 1)), 1)

    def test_identity_lines_not_in_gits_exact_shape_are_scanned(self):
        for line in ["# Author: A Person <" + EMAIL + ">", "Author:    A Person <" + EMAIL + ">",
                     "# Author:    A Person <" + EMAIL + "> and more", "# Reviewer:  A Person <" + EMAIL + ">"]:
            self.assertEqual(self.message_exit("fix: tidy\n\n" + line + "\n"), 1, line)

    def test_stored_messages_never_mask_identity_lines(self):
        found = cp.message_findings("msg", ("fix: tidy\n" + self.TEMPLATE).encode(), [])
        self.assertEqual([r for (_p, _l, r) in found], ["email", "email"])

    # D10: a regex end anchor after a digit is not a trailing dollar sign
    def test_regex_end_anchors_are_not_money(self):
        for text in ['re.compile(r"^0$")', "pat = '\\d+0$'", "x = `^[a-z]+1$`", 'r"\\d{3}0$"', 'r"(a)0$"']:
            self.assertEqual(self.rules(text), [], text)

    def test_trailing_dollar_amounts_in_quotes_still_fail(self):
        for text in ['{"rent": "4,321' + '$"}', 'say "4,321' + '$"', "paid 4,321" + "$ total", "'rent 4,321" + "$'"]:
            self.assertEqual(self.rules(text), ["money"], text)

    # D10: 32-bit integer limits are not phones; a phone without separators still is
    def test_integer_limits_are_not_phones(self):
        for text in ["INT_MAX = 2147483647", "UINT32_MAX = 4294967295", "if n >= 2147483648:", "mask(4294967296)"]:
            self.assertEqual(self.rules(text), [], text)
        self.assertEqual(self.rules("call 604555" + "0123"), ["phone"])
        self.assertEqual(self.rules("id 21474836470"), [])


ZERO = "0" * 40


class PushedRefs(unittest.TestCase):
    """Deferred review, D5: a push publishes ref names and tag messages, not only commits."""

    def repo(self, d):
        git = make_repo(d)
        (Path(d) / "README.md").write_text("clean\n")
        git("add", "README.md")
        git("commit", "-q", "-m", "one")
        return git, git("rev-parse", "HEAD")

    def push(self, d, stdin, deny="Zeta"):
        with InRepo(d, deny):
            found = cp.pre_push_findings(stdin, [deny])
        return sorted(r for (_p, _l, r) in found), found

    def test_annotated_tag_message_is_scanned(self):
        with tempfile.TemporaryDirectory() as d:
            git, _head = self.repo(d)
            git("tag", "-a", "v1", "-m", "release for Zeta", "-m", "call " + NA_PHONE)
            rules, _ = self.push(d, f"refs/tags/v1 {git('rev-parse', 'v1')} refs/tags/v1 {ZERO}\n")
            self.assertEqual(rules, ["denylist", "phone"])

    def test_clean_tag_and_its_tagger_line_pass(self):
        with tempfile.TemporaryDirectory() as d:
            git, _head = self.repo(d)
            git("tag", "-a", "v1", "-m", "release one")
            rules, _ = self.push(d, f"refs/tags/v1 {git('rev-parse', 'v1')} refs/tags/v1 {ZERO}\n")
            self.assertEqual(rules, [])

    def test_tag_name_inside_the_tag_object_is_scanned(self):
        with tempfile.TemporaryDirectory() as d:
            git, _head = self.repo(d)
            git("tag", "-a", "zeta-release", "-m", "clean")
            rules, found = self.push(d, f"refs/tags/zeta-release {git('rev-parse', 'zeta-release')} refs/tags/v9 {ZERO}\n")
            self.assertEqual(rules, ["denylist"])
            self.assertNotIn("zeta", "\n".join(cp.format_findings(found)).lower())

    def test_tag_of_a_tag_is_followed(self):
        with tempfile.TemporaryDirectory() as d:
            git, _head = self.repo(d)
            git("tag", "-a", "v1", "-m", "inner note for Zeta")
            git("tag", "-a", "v2", "v1", "-m", "outer")
            rules, _ = self.push(d, f"refs/tags/v2 {git('rev-parse', 'v2')} refs/tags/v2 {ZERO}\n")
            self.assertEqual(rules, ["denylist"])

    def test_lightweight_tag_has_no_message(self):
        with tempfile.TemporaryDirectory() as d:
            _git, head = self.repo(d)
            rules, _ = self.push(d, f"refs/tags/v0 {head} refs/tags/v0 {ZERO}\n")
            self.assertEqual(rules, [])

    def test_pushed_ref_names_are_scanned_and_withheld(self):
        with tempfile.TemporaryDirectory() as d:
            _git, head = self.repo(d)
            for ref, want in [("refs/heads/notes-for-zeta", ["denylist"]), ("refs/heads/call-" + NA_PHONE, ["phone"]),
                              ("refs/tags/" + NA_PHONE.replace("-", "."), ["phone"]),
                              ("refs/heads/persona-debate-lab/claude/guard-followups", [])]:
                rules, found = self.push(d, f"refs/heads/main {head} {ref} {ZERO}\n")
                self.assertEqual(rules, want, ref)
                self.assertNotIn(ref.split("/")[-1], "\n".join(cp.format_findings(found)), ref)

    def test_deleting_a_ref_scans_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            _git, head = self.repo(d)
            rules, _ = self.push(d, f"(delete) {ZERO} refs/heads/notes-for-zeta {head}\n")
            self.assertEqual(rules, [])

    def test_pre_push_main_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            git, head = self.repo(d)
            git("tag", "-a", "v1", "-m", "release for Zeta")
            saved = sys.stdin
            try:
                with InRepo(d) as repo:
                    sys.stdin = io.StringIO(f"refs/tags/v1 {git('rev-parse', 'v1')} refs/tags/v1 {ZERO}\n")
                    self.assertEqual(repo.main("--pre-push", "origin"), 1)
                    sys.stdin = io.StringIO(f"refs/heads/main {head} refs/heads/main {ZERO}\n")
                    self.assertEqual(repo.main("--pre-push", "origin"), 0)
            finally:
                sys.stdin = saved

    # CI: the tag a tag push published
    def test_tag_mode(self):
        with tempfile.TemporaryDirectory() as d:
            git, _head = self.repo(d)
            git("tag", "-a", "v1", "-m", "release for Zeta")
            git("tag", "-a", "v2", "-m", "release two")
            git("tag", "v3")
            with InRepo(d) as repo:
                self.assertEqual(repo.main("--tag", "refs/tags/v1"), 1)
                self.assertEqual(repo.main("--tag", "refs/tags/v2"), 0)
                self.assertEqual(repo.main("--tag", "refs/tags/v3"), 0)
                self.assertEqual(repo.main("--tag", "refs/tags/missing"), 1)


if __name__ == "__main__":
    unittest.main()
