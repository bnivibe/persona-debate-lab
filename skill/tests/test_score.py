import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bin"))
import score  # noqa: E402

HEADER = "date,thread,category,round,persona,proposals,survived,attacked,fact_errors,adopted,outcome"
OUT_HEADER = "date,thread,category,round,ideas_total,ideas_used,rating"


def rows(*lines):
    return score.parse_rows("\n".join([HEADER, *lines]))


def outcomes(*lines):
    return score.parse_rows("\n".join([OUT_HEADER, *lines]))


class Summarize(unittest.TestCase):
    def test_counts_and_rates(self):
        r = rows("2026-10-13,T001,career,1,a,2,1,3,0,,pending",
                 "2026-10-20,T002,tech,1,a,2,2,0,1,1,hit")
        s = score.summarize(r, ["a", "b"])
        self.assertEqual(s["a"]["rounds"], 2)
        self.assertEqual(s["a"]["proposals"], 4)
        self.assertEqual(s["a"]["survived"], 3)
        self.assertEqual(s["a"]["fact_errors"], 1)
        self.assertEqual(score.rate(s["a"], "survival"), "75%")
        self.assertEqual(score.rate(s["a"], "hit"), "100%")

    def test_no_outcomes_and_no_rounds_are_na(self):
        s = score.summarize(rows("2026-10-13,T001,career,1,a,2,1,0,0,,pending"), ["a", "b"])
        self.assertEqual(score.rate(s["a"], "hit"), "n/a")
        self.assertEqual(s["b"]["rounds"], 0)
        self.assertEqual(score.rate(s["b"], "survival"), "n/a")

    def test_unknown_persona_names_the_row(self):
        with self.assertRaises(ValueError) as ctx:
            score.summarize(rows("2026-10-13,T001,career,1,ghost,1,1,0,0,,pending"), ["a"])
        self.assertIn("row 2", str(ctx.exception))

    def test_bad_outcome_and_bad_category(self):
        with self.assertRaises(ValueError):
            score.summarize(rows("2026-10-13,T001,career,1,a,1,1,0,0,,maybe"), ["a"])
        with self.assertRaises(ValueError):
            score.summarize(rows("2026-10-13,T001,hobby,1,a,1,1,0,0,,pending"), ["a"])

    def test_non_integer_count(self):
        with self.assertRaises(ValueError) as ctx:
            score.summarize(rows("2026-10-13,T001,career,1,a,two,1,0,0,,pending"), ["a"])
        self.assertIn("row 2", str(ctx.exception))


class MethodTrend(unittest.TestCase):
    def test_average_rating_and_adoption(self):
        t = score.method_trend(outcomes("2026-10-13,T001,career,1,8,3,4",
                                        "2026-10-20,T002,tech,1,6,0,2",
                                        "2026-10-27,T003,life,1,5,,"))
        self.assertEqual(t["rated"], 2)
        self.assertEqual(t["pending"], 1)
        self.assertEqual(t["avg_rating"], "3.0")
        self.assertEqual(t["adoption"], "21%")

    def test_nothing_rated_is_na(self):
        t = score.method_trend(outcomes("2026-10-13,T001,career,1,8,,"))
        self.assertEqual(t["avg_rating"], "n/a")
        self.assertEqual(t["adoption"], "n/a")

    def test_rating_out_of_range_names_the_row(self):
        with self.assertRaises(ValueError) as ctx:
            score.method_trend(outcomes("2026-10-13,T001,career,1,8,3,6"))
        self.assertIn("row 2", str(ctx.exception))

    def test_used_more_than_total(self):
        with self.assertRaises(ValueError):
            score.method_trend(outcomes("2026-10-13,T001,career,1,2,3,4"))


class Roster(unittest.TestCase):
    def test_reads_backticked_ids(self):
        text = "| id | label |\n|---|---|\n| `alpha` | Alpha |\n| `beta-two` | Beta |\n"
        self.assertEqual(score.roster_ids(text), ["alpha", "beta-two"])


class Markers(unittest.TestCase):
    def test_replace_between_markers(self):
        doc = "top\n<!-- scoreboard:start -->\nold\n<!-- scoreboard:end -->\nbottom\n"
        out = score.replace_block(doc, "NEW")
        self.assertIn("<!-- scoreboard:start -->\nNEW\n<!-- scoreboard:end -->", out)
        self.assertTrue(out.startswith("top") and out.endswith("bottom\n"))

    def test_missing_markers_raise(self):
        with self.assertRaises(ValueError):
            score.replace_block("no markers here", "NEW")


class PublicIds(unittest.TestCase):
    """I7: thread must be a public id, date ISO, round a positive integer, in both CSVs."""

    def assert_row_error(self, fn, *args):
        with self.assertRaises(ValueError) as ctx:
            fn(*args)
        self.assertIn("row 2", str(ctx.exception))

    def test_private_slug_in_rounds_fails(self):
        self.assert_row_error(score.summarize, rows("2026-10-13,my-private-slug,career,1,a,2,1,0,0,,pending"), ["a"])

    def test_bad_date_and_round_in_rounds_fail(self):
        self.assert_row_error(score.summarize, rows("Oct 13,T001,career,1,a,2,1,0,0,,pending"), ["a"])
        self.assert_row_error(score.summarize, rows("2026-10-13,T001,career,0,a,2,1,0,0,,pending"), ["a"])

    def test_private_slug_in_outcomes_fails(self):
        self.assert_row_error(score.method_trend, outcomes("2026-10-13,my-private-slug,career,1,8,,"))

    def test_bad_round_in_outcomes_fails(self):
        self.assert_row_error(score.method_trend, outcomes("2026-10-13,T001,career,x,8,,"))


class Minors(unittest.TestCase):
    """Final-review minors M5, M6, M7, M15."""

    def error(self, fn, *args):
        with self.assertRaises(ValueError) as ctx:
            fn(*args)
        return str(ctx.exception)

    # M5
    def test_row_number_survives_a_blank_line(self):
        text = "\n".join([HEADER, "", "2026-10-13,T001,career,1,ghost,1,1,0,0,,pending"])
        self.assertIn("row 3", self.error(score.summarize, score.parse_rows(text), ["a"]))

    # M6
    def test_impossible_counts_fail(self):
        for line in ["2026-10-13,T001,career,1,a,1,2,0,0,,pending",
                     "2026-10-13,T001,career,1,a,2,1,-1,0,,pending",
                     "2026-10-13,T001,career,1,a,1,1,0,0,2,hit"]:
            self.assertIn("row 2", self.error(score.summarize, rows(line), ["a"]), line)

    def test_duplicate_rows_fail(self):
        line = "2026-10-13,T001,career,1,a,2,1,0,0,,pending"
        self.assertIn("row 3", self.error(score.summarize, rows(line, line), ["a"]))
        out = "2026-10-13,T001,career,1,8,,"
        self.assertIn("row 3", self.error(score.method_trend, outcomes(out, out)))

    # M7
    def test_markers_must_appear_once_and_in_order(self):
        twice = "<!-- scoreboard:start -->\n<!-- scoreboard:start -->\nx\n<!-- scoreboard:end -->\n"
        swapped = "<!-- scoreboard:end -->\nx\n<!-- scoreboard:start -->\n"
        for doc in (twice, swapped):
            with self.assertRaises(ValueError):
                score.replace_block(doc, "NEW")

    def test_write_changes_nothing_when_one_file_is_broken(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "personas").mkdir()
            (root / "scorecards").mkdir()
            readme = "top\n<!-- scoreboard:start -->\nold\n<!-- scoreboard:end -->\n"
            (root / "README.md").write_text(readme)
            (root / "personas" / "roster.md").write_text("| `a` | A |\nno markers\n")
            (root / "scorecards" / "rounds.csv").write_text(HEADER + "\n2026-10-13,T001,career,1,a,2,1,0,0,,pending\n")
            (root / "scorecards" / "outcomes.csv").write_text(OUT_HEADER + "\n2026-10-13,T001,career,1,2,,\n")
            saved = score.ROOT
            score.ROOT = root
            try:
                with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(score.main(["--write"]), 1)
            finally:
                score.ROOT = saved
            self.assertEqual((root / "README.md").read_text(), readme)

    # M15
    def test_brief_shows_last_round_date(self):
        s = score.summarize(rows("2026-10-13,T001,career,1,a,2,1,0,0,,pending",
                                 "2026-10-20,T002,tech,1,a,2,1,0,0,,pending"), ["a", "b"])
        text = score.brief(s)
        self.assertIn("a: rounds 2, last 2026-10-20", text)
        self.assertIn("b: rounds 0, last never", text)


class Review2(unittest.TestCase):
    """Second review, F13 to F15."""

    def test_negative_idea_counts_fail(self):
        for line in ["2026-10-13,T001,career,1,8,-3,4", "2026-10-13,T001,career,1,-8,-9,4"]:
            with self.assertRaises(ValueError) as ctx:
                score.method_trend(outcomes(line))
            self.assertIn("row 2", str(ctx.exception))

    def test_dates_must_be_plain_iso(self):
        for date in ["20260101", "2026-W53-4"]:
            with self.assertRaises(ValueError):
                score.summarize(rows(f"{date},T001,career,1,a,2,1,0,0,,pending"), ["a"])

    def test_write_leaves_no_temp_files(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "personas").mkdir()
            (root / "scorecards").mkdir()
            marks = "<!-- scoreboard:start -->\nold\n<!-- scoreboard:end -->\n"
            (root / "README.md").write_text("top\n" + marks)
            (root / "personas" / "roster.md").write_text("| `a` | A |\n" + marks)
            (root / "scorecards" / "rounds.csv").write_text(HEADER + "\n2026-10-13,T001,career,1,a,2,1,0,0,,pending\n")
            (root / "scorecards" / "outcomes.csv").write_text(OUT_HEADER + "\n2026-10-13,T001,career,1,2,,\n")
            saved = score.ROOT
            score.ROOT = root
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(score.main(["--write"]), 0)
            finally:
                score.ROOT = saved
            self.assertIn("| `a` | 1 |", (root / "README.md").read_text())
            self.assertEqual(sorted(p.name for p in root.iterdir()), ["README.md", "personas", "scorecards"])
            self.assertEqual(sorted(p.name for p in (root / "personas").iterdir()), ["roster.md"])


class Prepublish(unittest.TestCase):
    """Pre-publish review, D7: the CSVs hold counts only, so no column can carry free text."""

    def test_extra_field_in_a_row_fails(self):
        with self.assertRaises(ValueError) as ctx:
            score.summarize(rows("2026-10-13,T001,career,1,a,2,1,0,0,,pending,free text"), ["a"])
        self.assertIn("row 2", str(ctx.exception))

    def test_missing_field_in_a_row_fails(self):
        with self.assertRaises(ValueError):
            score.method_trend(outcomes("2026-10-13,T001,career,1,8"))

    def test_extra_header_column_fails(self):
        with self.assertRaises(ValueError):
            score.parse_rows(HEADER + ",notes\n2026-10-13,T001,career,1,a,2,1,0,0,,pending,x\n", score.ROUNDS_HEADER)


if __name__ == "__main__":
    unittest.main()
