import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bin"))
import discord_debate as dd  # noqa: E402


class FakeResponse:
    def __init__(self, body=b""):
        self.body = body

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class PostRound(unittest.TestCase):
    def test_counts_successes_and_keeps_going(self):
        calls = []

        def urlopen(req, timeout=None):
            calls.append(req)
            if len(calls) == 2:
                raise OSError("boom")
            return FakeResponse()

        msgs = [{"persona": "A", "content": "x"}, {"persona": "B", "content": "y"}, {"content": "z"}]
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            sent = dd.post_round("https" + "://hook.invalid/abc", msgs, sleep=lambda s: None, urlopen=urlopen)
        self.assertEqual(sent, 2)
        self.assertEqual(len(calls), 3)
        self.assertNotIn("hook.invalid", err.getvalue())
        self.assertIn("OSError", err.getvalue())


class FetchMessages(unittest.TestCase):
    def test_bookmark_is_latest_of_any_author(self):
        raw = [{"id": "30", "author": {"id": "bot"}, "content": "mirror"},
               {"id": "10", "author": {"id": "me"}, "content": "note one"},
               {"id": "20", "author": {"id": "me"}, "content": "note two"}]

        def urlopen(req, timeout=None):
            return FakeResponse(json.dumps(raw).encode())

        out, latest = dd.fetch_user_messages("t", "c", user_id="me", urlopen=urlopen)
        self.assertEqual([m["id"] for m in out], ["10", "20"])
        self.assertEqual(latest, "30")

    def test_bad_body_returns_empty(self):
        def urlopen(req, timeout=None):
            return FakeResponse(b'{"not": "a list"}')

        self.assertEqual(dd.fetch_user_messages("t", "c", urlopen=urlopen), ([], None))


class Secrets(unittest.TestCase):
    def test_export_and_quotes(self):
        with tempfile.NamedTemporaryFile("w", suffix=".env", delete=False) as fh:
            fh.write("# comment\nexport NAME_A='value-a'\nNAME_B=\"value-b\"\n")
        self.assertEqual(dd.load_secret("NAME_A", fh.name), "value-a")
        self.assertEqual(dd.load_secret("NAME_B", fh.name), "value-b")
        self.assertIsNone(dd.load_secret("NAME_C", fh.name))

    def test_missing_file_is_feature_off(self):
        self.assertIsNone(dd.load_secret("ANY", "/nonexistent/secrets.env"))


class Minors(unittest.TestCase):
    """Final-review minor M9: malformed input never raises, env secrets are read first."""

    def test_odd_items_do_not_raise(self):
        posted = []

        def urlopen(req, timeout=None):
            posted.append(json.loads(req.data.decode("utf-8")))
            return FakeResponse()

        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            sent = dd.post_round("https" + "://hook.invalid/abc",
                                 [{"persona": "A", "content": "x"}, "junk", {"persona": "B", "content": 5}],
                                 sleep=lambda s: None, urlopen=urlopen)
        self.assertEqual(sent, 2)
        self.assertEqual(posted[1]["content"], "5")

    def test_top_level_object_is_skipped(self):
        os.environ[dd.WEBHOOK_SECRET] = "https" + "://hook.invalid/abc"
        saved = sys.stdin
        sys.stdin = io.StringIO('{"persona": "A", "content": "x"}')
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                self.assertEqual(dd.main(["post"]), 0)
        finally:
            sys.stdin = saved
            del os.environ[dd.WEBHOOK_SECRET]
        self.assertIn("invalid input", out.getvalue())

    def test_environment_is_read_before_the_file(self):
        os.environ["DEBATE_TEST_SECRET"] = "from-env"
        try:
            self.assertEqual(dd.load_secret("DEBATE_TEST_SECRET", "/nonexistent/secrets.env"), "from-env")
        finally:
            del os.environ["DEBATE_TEST_SECRET"]


class Review2(unittest.TestCase):
    """Second review, F16: odd stdin and null fields never raise."""

    def run_post(self, stdin):
        os.environ[dd.WEBHOOK_SECRET] = "https" + "://hook.invalid/abc"
        saved = sys.stdin
        sys.stdin = stdin
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                code = dd.main(["post"])
        finally:
            sys.stdin = saved
            del os.environ[dd.WEBHOOK_SECRET]
        return code, out.getvalue()

    def test_non_utf8_stdin_is_skipped(self):
        code, out = self.run_post(io.TextIOWrapper(io.BytesIO(b"\xff\xfe["), encoding="utf-8"))
        self.assertEqual(code, 0)
        self.assertIn("invalid input", out)

    def test_deep_nesting_is_skipped(self):
        code, out = self.run_post(io.StringIO("[" * 200000))
        self.assertEqual(code, 0)
        self.assertIn("invalid input", out)

    def test_null_fields_become_placeholders(self):
        posted = []

        def urlopen(req, timeout=None):
            posted.append(json.loads(req.data.decode("utf-8")))
            return FakeResponse()

        dd.post_round("https" + "://hook.invalid/abc", [{"persona": None, "content": None}],
                      sleep=lambda s: None, urlopen=urlopen)
        self.assertEqual((posted[0]["username"], posted[0]["content"]), ("?", ""))


class Prepublish(unittest.TestCase):
    """Pre-publish review, D6: a webhook without a scheme never raises or prints its token."""

    def test_schemeless_webhook_is_refused_quietly(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            ok = dd.post_message("discord" + ".com/api/webhooks/1/" + "SECRETTOKEN", "A", "x",
                                 urlopen=lambda req, timeout=None: FakeResponse())
        self.assertFalse(ok)
        self.assertNotIn("SECRETTOKEN", err.getvalue())


class Followups(unittest.TestCase):
    """Deferred review, D9: one odd item never drops the rest of the page."""

    def fetch(self, raw):
        def urlopen(req, timeout=None):
            return FakeResponse(json.dumps(raw).encode())

        return dd.fetch_user_messages("t", "c", user_id="me", urlopen=urlopen)

    def test_null_author_and_non_object_items_are_skipped(self):
        raw = [{"id": "10", "author": {"id": "me"}, "content": "note one"},
               {"id": "40", "author": None, "content": "system notice"},
               "junk", None, 7,
               {"id": "20", "author": "not-an-object", "content": "odd"},
               {"id": "30", "author": {"id": "me"}, "content": "note two"}]
        out, latest = self.fetch(raw)
        self.assertEqual([m["content"] for m in out], ["note one", "note two"])
        self.assertEqual(latest, "40")


if __name__ == "__main__":
    unittest.main()
