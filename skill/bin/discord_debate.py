#!/usr/bin/env python3
"""Discord bridge for persona debates: webhook writes, bot reads.

Without secrets it skips quietly (feature off). A Discord failure never blocks
a round. Git holds the record; Discord is a disposable view.

Each secret is read from the environment first, then from the secrets file.
Secret names are configurable so any user can wire their own:
  DEBATE_WEBHOOK_ENV    name of the webhook secret   (default IDEA_DEBATE_DISCORD_WEBHOOK)
  DEBATE_BOT_TOKEN_ENV  name of the bot token secret (default IDEA_DEBATE_DISCORD_BOT_TOKEN)
  DEBATE_SECRETS_FILE   path of the secrets file     (default ~/.claude/secrets.env)
"""
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

SECRETS_PATH = Path(os.environ.get("DEBATE_SECRETS_FILE", Path.home() / ".claude" / "secrets.env")).expanduser()
WEBHOOK_SECRET = os.environ.get("DEBATE_WEBHOOK_ENV", "IDEA_DEBATE_DISCORD_WEBHOOK")
BOT_TOKEN_SECRET = os.environ.get("DEBATE_BOT_TOKEN_ENV", "IDEA_DEBATE_DISCORD_BOT_TOKEN")
MAX_CONTENT = 2000       # Discord message body limit
POST_DELAY = 0.5         # headroom under the webhook rate limit (about 5 requests per 2s)
TIMEOUT = 10

# The Discord API sits behind Cloudflare, which rejects urllib's default
# User-Agent (Python-urllib/3.x) with 403 error code 1010. Without this header
# not a single message reaches a real server, and fake-response tests cannot
# catch that.
USER_AGENT = "DiscordBot (https://github.com/bnivibe/persona-debate-lab, 1.0)"
API_BASE = "https://discord.com/api/v10"


def load_secret(name, path=None):
    """Read a secret from the environment, then the secrets file. Missing everywhere returns None (feature off)."""
    if os.environ.get(name):
        return os.environ[name]
    path = Path(path) if path else SECRETS_PATH
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        key, sep, value = line.partition("=")
        if sep and key.strip() == name:
            return value.strip().strip("'\"")
    return None


def post_message(webhook, username, content, urlopen=None):
    """Send one persona's turn through the webhook. Never raises."""
    urlopen = urlopen or urllib.request.urlopen
    if not webhook.startswith("https://"):
        # A malformed value would otherwise surface in an exception message, token included.
        print("discord: post failed (webhook is not an https URL)", file=sys.stderr)
        return False
    payload = json.dumps(
        {"username": username, "content": content[:MAX_CONTENT]}
    ).encode("utf-8")
    try:
        req = urllib.request.Request(
            webhook,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
            method="POST",
        )
        with urlopen(req, timeout=TIMEOUT):
            return True
    except Exception as exc:
        # Log and swallow, printing the class name only: neither the URL nor
        # the exception message, so the webhook and payload never reach stderr.
        print(f"discord: post failed ({type(exc).__name__})", file=sys.stderr)
        return False


def post_round(webhook, messages, sleep=None, urlopen=None):
    """Send a list of {"persona", "content"} in order. Returns how many succeeded.

    One failure does not stop the rest: the mirror is not a gate.
    """
    sleep = sleep if sleep is not None else time.sleep
    sent = 0
    for i, msg in enumerate(messages):
        # A malformed item must not raise either: dying here would stop the
        # round halfway with the earlier personas already mirrored.
        if isinstance(msg, dict):
            persona = msg.get("persona")
            content = msg.get("content")
            persona = "?" if persona is None else str(persona)
            content = "" if content is None else str(content)
            if post_message(webhook, persona, content, urlopen=urlopen):
                sent += 1
        else:
            print("discord: skipped an item that is not an object", file=sys.stderr)
        if i < len(messages) - 1:
            sleep(POST_DELAY)
    return sent


def fetch_user_messages(token, channel_id, after=None, user_id=None, urlopen=None):
    """Read the channel once at round start to collect the user's interjections.

    Returns (my messages, bookmark). The bookmark is the newest message id on
    this page **regardless of author**. Advancing it only on the user's own
    messages would let the mirror bot's posts widen the unread window every
    round, until a real note falls off the 100-message page and silently
    disappears.

    No standing listener: one poll at the round boundary is enough.
    On any failure it returns ([], None); a dead Discord never stops a round.
    """
    urlopen = urlopen or urllib.request.urlopen
    url = f"{API_BASE}/channels/{channel_id}/messages?limit=100"
    if after:
        url += f"&after={after}"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bot {token}", "User-Agent": USER_AGENT},
        method="GET",
    )
    try:
        with urlopen(req, timeout=TIMEOUT) as resp:
            raw = json.loads(resp.read().decode("utf-8"))

        # Parsing and normalising stay inside the same try: a body that is not
        # a list (AttributeError) or a non-numeric id (ValueError) fails here.
        # This runs at round start, before any commit, so it must never raise.
        out = []
        latest = None
        for m in raw:
            # One odd item (not an object, or "author": null on a system message) is skipped;
            # it must not throw away the user's notes on the rest of the page.
            if not isinstance(m, dict):
                continue
            mid = m.get("id")
            if not mid:
                continue  # an item without an id can be neither bookmarked nor sorted
            if latest is None or int(mid) > int(latest):
                latest = mid
            author = m.get("author")
            if user_id and (author.get("id") if isinstance(author, dict) else None) != user_id:
                continue
            out.append(
                {
                    "id": mid,
                    "content": m.get("content", ""),
                    "timestamp": m.get("timestamp", ""),
                }
            )
        # Do not rely on API order. Snowflake ids are time-ordered, so sort by them.
        out.sort(key=lambda m: int(m["id"]))
        return out, latest
    except Exception:
        return [], None


def main(argv=None):
    """CLI. Without secrets it exits 0 quietly, so callers never need to branch."""
    import argparse

    ap = argparse.ArgumentParser(description="Discord bridge for persona debates")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("post", help="mirror a JSON list of turns from stdin to the channel")

    fp = sub.add_parser("fetch", help="collect the user's interjections once")
    fp.add_argument("--channel", required=True)
    fp.add_argument("--after")
    fp.add_argument("--user")

    args = ap.parse_args(argv)

    if args.cmd == "post":
        webhook = load_secret(WEBHOOK_SECRET)
        if not webhook:
            # Leave before reading stdin: run by hand on a machine without the
            # webhook it would otherwise hang waiting for input, or die with a
            # traceback on broken JSON.
            print(f"discord: skipped ({WEBHOOK_SECRET} unset)")
            return 0
        try:
            messages = json.load(sys.stdin)
        except (ValueError, RecursionError):
            # ValueError covers broken JSON and stdin that is not UTF-8; RecursionError, absurd nesting.
            # The model writes this JSON by hand every round; quotes and
            # newlines breaking it is a common authoring slip, not a hypothetical.
            print("discord: skipped (invalid input)")
            return 0
        if not isinstance(messages, list):
            print("discord: skipped (invalid input)")
            return 0
        sent = post_round(webhook, messages)
        print(f"posted {sent}/{len(messages)}")
        return 0

    token = load_secret(BOT_TOKEN_SECRET)
    if not token:
        print(json.dumps({"messages": [], "latest_id": None}))
        return 0
    rows, latest = fetch_user_messages(
        token, args.channel, after=args.after, user_id=args.user
    )
    print(json.dumps({"messages": rows, "latest_id": latest}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
