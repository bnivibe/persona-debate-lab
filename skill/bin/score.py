#!/usr/bin/env python3
"""Summarize the scorecards into a per-persona track record and a method trend.

Persona track record (scorecards/rounds.csv):
  survival rate = survived / proposals
  hit rate      = hits / decided outcomes (hit, miss, mixed; pending is not decided)
Method trend (scorecards/outcomes.csv, one row per round):
  average rating of rated rounds (1-5), adoption = ideas used / ideas proposed.
Every rate prints n/a when its denominator is zero.
"""
import argparse
import csv
import io
import os
import re
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATEGORIES = {"career", "tech", "learning", "life", "tooling"}
OUTCOMES = {"hit", "miss", "mixed", "pending"}
COUNTS = ("proposals", "survived", "attacked", "fact_errors")
ROUNDS_HEADER = ["date", "thread", "category", "round", "persona", *COUNTS, "adopted", "outcome"]
OUTCOMES_HEADER = ["date", "thread", "category", "round", "ideas_total", "ideas_used", "rating"]
START, END = "<!-- scoreboard:start -->", "<!-- scoreboard:end -->"
THREAD_ID = re.compile(r"T\d{3,}")
ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def parse_rows(text, header=None):
    """Rows as dicts, each with `_line`: its physical line, so errors stay right after a blank line."""
    reader = csv.DictReader(io.StringIO(text))
    if header is not None and reader.fieldnames != header:
        raise ValueError(f"header must be exactly: {','.join(header)}")
    rows = []
    for row in reader:
        row["_line"] = reader.line_num
        rows.append(row)
    return rows


def _where(name, row, n):
    return f"{name} row {row.get('_line', n)}"


def roster_ids(text):
    return re.findall(r"^\|\s*`([a-z0-9-]+)`\s*\|", text, flags=re.MULTILINE)


def _check_shape(row, where):
    # Counts only: an extra field could carry free text, a missing one shifts every column.
    if None in row or any(v is None for v in row.values()):
        raise ValueError(f"{where}: wrong number of fields")


def _check_category(row, where):
    if row.get("category") not in CATEGORIES:
        raise ValueError(f"{where}: category must be one of {sorted(CATEGORIES)}")


def _check_ids(row, where):
    # Public files never name a topic: a private slug in `thread` would publish it.
    if not THREAD_ID.fullmatch(row.get("thread") or ""):
        raise ValueError(f"{where}: thread must be a public id like T001")
    try:
        # fromisoformat alone also takes 20260101 and week dates; the public CSVs stay uniform.
        if not ISO_DATE.fullmatch(row.get("date") or ""):
            raise ValueError
        date.fromisoformat(row["date"])
        round_no = int(row.get("round") or "")
    except ValueError:
        raise ValueError(f"{where}: date must be YYYY-MM-DD and round a whole number") from None
    if round_no < 1:
        raise ValueError(f"{where}: round must be 1 or more")


def summarize(rows, ids):
    out = {i: {"rounds": 0, "proposals": 0, "survived": 0, "attacked": 0,
               "fact_errors": 0, "adopted": 0, "hit": 0, "miss": 0, "mixed": 0, "last": ""} for i in ids}
    seen = set()
    for n, row in enumerate(rows, start=2):
        where = _where("rounds.csv", row, n)
        pid = row.get("persona", "")
        if pid not in out:
            raise ValueError(f"{where}: unknown persona '{pid}'")
        _check_shape(row, where)
        _check_category(row, where)
        _check_ids(row, where)
        if row.get("outcome") not in OUTCOMES:
            raise ValueError(f"{where}: outcome must be one of {sorted(OUTCOMES)}")
        key = (row["thread"], int(row["round"]), pid)
        if key in seen:
            raise ValueError(f"{where}: duplicate row for this thread, round and persona")
        seen.add(key)
        try:
            counts = {k: int(row[k]) for k in COUNTS}
            adopted = int(row["adopted"]) if (row.get("adopted") or "").strip() else 0
        except (TypeError, ValueError):
            raise ValueError(f"{where}: counts must be whole numbers") from None
        if min(*counts.values(), adopted) < 0:
            raise ValueError(f"{where}: counts cannot be negative")
        if counts["survived"] > counts["proposals"] or adopted > counts["proposals"]:
            raise ValueError(f"{where}: survived and adopted cannot exceed proposals")
        rec = out[pid]
        rec["rounds"] += 1
        for k, v in counts.items():
            rec[k] += v
        rec["adopted"] += adopted
        rec["last"] = max(rec["last"], row["date"])
        if row["outcome"] != "pending":
            rec[row["outcome"]] += 1
    return out


def method_trend(rows):
    rated = pending = used = total = 0
    rating_sum = 0
    seen = set()
    for n, row in enumerate(rows, start=2):
        where = _where("outcomes.csv", row, n)
        _check_shape(row, where)
        _check_category(row, where)
        _check_ids(row, where)
        key = (row["thread"], int(row["round"]))
        if key in seen:
            raise ValueError(f"{where}: duplicate row for this thread and round")
        seen.add(key)
        rating = (row.get("rating") or "").strip()
        used_raw = (row.get("ideas_used") or "").strip()
        try:
            ideas_total = int(row["ideas_total"])
            ideas_used = int(used_raw) if used_raw else None
            value = int(rating) if rating else None
            if value is not None and ideas_used is None:
                raise ValueError
        except (TypeError, ValueError):
            raise ValueError(f"{where}: ideas and rating must be whole numbers") from None
        if ideas_total < 0 or (ideas_used is not None and ideas_used < 0):
            raise ValueError(f"{where}: idea counts cannot be negative")
        if value is None:
            pending += 1
            continue
        if not 1 <= value <= 5:
            raise ValueError(f"{where}: rating must be 1 to 5")
        if ideas_used > ideas_total:
            raise ValueError(f"{where}: ideas_used is larger than ideas_total")
        rated += 1
        rating_sum += value
        used += ideas_used
        total += ideas_total
    return {
        "rated": rated,
        "pending": pending,
        "avg_rating": "n/a" if rated == 0 else f"{rating_sum / rated:.1f}",
        "adoption": "n/a" if total == 0 else f"{round(100 * used / total)}%",
    }


def rate(rec, kind):
    if kind == "survival":
        num, den = rec["survived"], rec["proposals"]
    else:
        num, den = rec["hit"], rec["hit"] + rec["miss"] + rec["mixed"]
    return "n/a" if den == 0 else f"{round(100 * num / den)}%"


def table(summary):
    lines = ["| persona | rounds | proposals | survival | fact errors | adopted | hit rate |",
             "|---|---|---|---|---|---|---|"]
    for pid, rec in summary.items():
        if rec["rounds"] == 0:
            continue
        lines.append(f"| `{pid}` | {rec['rounds']} | {rec['proposals']} | {rate(rec, 'survival')} | "
                     f"{rec['fact_errors']} | {rec['adopted']} | {rate(rec, 'hit')} |")
    if len(lines) == 2:
        lines.append("| (no rounds yet) | | | | | | |")
    return "\n".join(lines)


def method_line(trend):
    return (f"Method: {trend['rated']} rated round(s), {trend['pending']} awaiting an outcome; "
            f"average rating {trend['avg_rating']} of 5; ideas used {trend['adoption']}.")


def brief(summary):
    return "\n".join(f"{pid}: rounds {r['rounds']}, last {r['last'] or 'never'}, survival {rate(r, 'survival')}, "
                     f"fact errors {r['fact_errors']}, hit rate {rate(r, 'hit')}"
                     for pid, r in summary.items())


def replace_block(doc, body):
    if doc.count(START) != 1 or doc.count(END) != 1 or doc.index(START) > doc.index(END):
        raise ValueError("scoreboard markers must appear exactly once each, start before end")
    head, rest = doc.split(START, 1)
    _, tail = rest.split(END, 1)
    return f"{head}{START}\n{body}\n{END}{tail}"


def _replace_file(path, text):
    """Write beside the target, then swap it in, so an interrupt never leaves a truncated file."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def main(argv=None):
    ap = argparse.ArgumentParser(description="Per-persona track record and method trend")
    ap.add_argument("--write", action="store_true", help="update README.md and personas/roster.md")
    ap.add_argument("--brief", action="store_true", help="one line per persona, for casting")
    args = ap.parse_args(argv)
    roster_path = ROOT / "personas" / "roster.md"
    ids = roster_ids(roster_path.read_text(encoding="utf-8"))
    try:
        rows = parse_rows((ROOT / "scorecards" / "rounds.csv").read_text(encoding="utf-8"), ROUNDS_HEADER)
        out_rows = parse_rows((ROOT / "scorecards" / "outcomes.csv").read_text(encoding="utf-8"), OUTCOMES_HEADER)
        summary = summarize(rows, ids)
        trend = method_trend(out_rows)
    except ValueError as exc:
        print(f"score: {exc}", file=sys.stderr)
        return 1
    if args.brief:
        print(brief(summary))
        print(method_line(trend))
        return 0
    body = table(summary) + "\n\n" + method_line(trend)
    if args.write:
        # Build both files before writing either, so a broken one leaves both untouched.
        targets = (ROOT / "README.md", roster_path)
        try:
            texts = [replace_block(path.read_text(encoding="utf-8"), body) for path in targets]
        except ValueError as exc:
            print(f"score: {exc}", file=sys.stderr)
            return 1
        for path, text in zip(targets, texts):
            _replace_file(path, text)
    print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
