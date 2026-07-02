#!/usr/bin/env python3
"""rebuttal_matrix -- build a reviewer-response matrix from review comments.

Splits a plain-text reviews file into numbered points and merges optional
prepared responses into a Markdown response matrix with a per-point status.
An organizational aid for rebuttals and response-to-reviewers letters; it
is advisory, not a certification that any response is adequate. It never
writes or invents responses: points without a prepared response are marked
UNADDRESSED.

Reviewer sections (ported from the retired tools/revision_matrix.py): a line
starting with "Reviewer <n>" or "Referee <n>" (case-insensitive) begins a
new reviewer section, and every point in it is attributed to that reviewer
in a Reviewer column. Text before the first header, or a file with no
headers at all, falls back to "Reviewer 1". Known limit: a continuation
line that itself starts with "Reviewer <n>" will start a new section.

Point splitting rules (mechanical and deterministic):
  - a blank line ends the current point
  - a line whose first non-space characters are "-", "*", or a number
    (optionally followed by ".", ")", or ":") starts a new point
  - every other line continues the current point
Known limit: a continuation line that happens to begin with a bare number
will start a new point; keep points separated by blank lines to avoid this.
Reviewer wording is kept verbatim (whitespace collapsed for the table).

--responses YAML maps point ids to prepared responses:
  P1:
    response: what you will say to the reviewer
    change_made: what changed in the manuscript
    evidence: where the proof lives (section, table, script)
  2: "a bare string is treated as the response text"
Ids may be written P1, p1, or 1 and refer to points in parse order.

Exit codes:
  0  -- matrix built (UNADDRESSED rows are advisory findings)
  1  -- invalid input (missing or unparseable files, or no review points
        found), or --strict with at least one UNADDRESSED point
  2  -- reviews file empty or whitespace-only (ported from the retired
        revision_matrix), or argparse usage errors (argparse default)

Usage:
  python3 tools/rebuttal_matrix.py --reviews reviews.txt
  python3 tools/rebuttal_matrix.py --reviews reviews.txt --responses responses.yml
  python3 tools/rebuttal_matrix.py --reviews reviews.txt --responses responses.yml --strict --out matrix.md
"""
from __future__ import annotations
import argparse
import os
import re
import sys

# UTF-8 stdout guard
import cambium_io  # noqa: F401

try:
    import yaml
except ImportError:  # pyyaml is expected in this repo
    yaml = None

TOOL = "rebuttal_matrix"

MARKER_RE = re.compile(r"^\s*(?:[-*]\s+|\d+\s*[.):]\s*|\d+\s+)")
# Ported from the retired tools/revision_matrix.py:
REVIEWER_HEADER_RE = re.compile(r"^\s*(Reviewer|Referee)\s+(\d+)\b", re.IGNORECASE)


def _fail(msg: str) -> None:
    print(f"[{TOOL}] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def split_sections(text: str) -> list[tuple[str, str]]:
    """Return [(reviewer_label, section_text), ...] (ported from the retired
    revision_matrix). With no "Reviewer N" / "Referee N" header anywhere, the
    whole text is one fallback section labeled "Reviewer 1"."""
    lines = text.splitlines()
    headers: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        m = REVIEWER_HEADER_RE.match(line)
        if m:
            headers.append((i, f"{m.group(1).capitalize()} {m.group(2)}"))
    if not headers:
        return [("Reviewer 1", text)]
    sections: list[tuple[str, str]] = []
    if headers[0][0] > 0:
        lead = "\n".join(lines[:headers[0][0]])
        if lead.strip():
            sections.append(("Reviewer 1", lead))
    for idx, (line_no, label) in enumerate(headers):
        end = headers[idx + 1][0] if idx + 1 < len(headers) else len(lines)
        sections.append((label, "\n".join(lines[line_no + 1:end])))
    return sections


def split_points(text: str) -> list[str]:
    """Split review text into points on blank lines and bullet/number markers."""
    points: list[str] = []
    current: list[str] = []

    def flush() -> None:
        if current:
            points.append(" ".join(" ".join(current).split()))
            current.clear()

    for line in text.splitlines():
        if not line.strip():
            flush()
            continue
        if MARKER_RE.match(line):
            flush()
        current.append(line.strip())
    flush()
    return points


def _norm_id(key) -> str | None:
    """Normalize P1 / p1 / 1 / '1' to 'P1'; return None if not a point id."""
    s = str(key).strip().upper()
    if s.startswith("P"):
        s = s[1:]
    if s.isdigit() and int(s) >= 1:
        return f"P{int(s)}"
    return None


def load_responses(path: str | None) -> tuple[dict[str, dict], list[str]]:
    """Return ({point_id: {response, change_made, evidence}}, invalid_keys)."""
    if path is None:
        return {}, []
    if yaml is None:
        _fail("pyyaml is not installed; install pyyaml to use --responses")
    if not os.path.exists(path):
        _fail(f"responses file not found: {path}")
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            data = yaml.safe_load(fh.read())
    except (OSError, yaml.YAMLError) as exc:
        _fail(f"cannot parse responses file: {path}\n  {exc}")
    if data is None:
        return {}, []
    if not isinstance(data, dict):
        _fail(f"responses file must be a mapping of point ids to responses: {path}")
    responses: dict[str, dict] = {}
    invalid: list[str] = []
    for key, value in data.items():
        pid = _norm_id(key)
        if pid is None:
            invalid.append(str(key))
            continue
        if isinstance(value, dict):
            entry = {
                "response": str(value.get("response") or "").strip(),
                "change_made": str(value.get("change_made") or "").strip(),
                "evidence": str(value.get("evidence") or "").strip(),
            }
        else:
            entry = {"response": str(value or "").strip(), "change_made": "", "evidence": ""}
        responses[pid] = entry
    return responses, invalid


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def _cell(text: str) -> str:
    cleaned = " ".join(str(text).split()).replace("|", "\\|")
    return cleaned if cleaned else "(none)"


def build_report(points: list[tuple[str, str]], responses: dict[str, dict],
                 invalid_keys: list[str], reviews_path: str) -> tuple[str, int]:
    """Return (markdown report, number of UNADDRESSED points). points is a
    list of (reviewer_label, point_text) pairs in global parse order."""
    rows = []
    unaddressed_ids: list[str] = []
    for i, (reviewer, point) in enumerate(points, 1):
        pid = f"P{i}"
        entry = responses.get(pid, {"response": "", "change_made": "", "evidence": ""})
        status = "filled" if entry["response"] else "UNADDRESSED"
        if status == "UNADDRESSED":
            unaddressed_ids.append(pid)
        rows.append((pid, reviewer, point, entry, status))

    unknown = sorted(
        (pid for pid in responses if int(pid[1:]) > len(points)),
        key=lambda p: int(p[1:]),
    )

    lines: list[str] = []
    lines.append("# Reviewer response matrix (organizational aid, advisory)")
    lines.append("")
    lines.append(
        "> Built mechanically from the reviewer comments and any prepared "
        "responses. This matrix organizes the work; it is advisory, not a "
        "certification that any response is adequate. The tool never writes "
        "responses: points without one are marked UNADDRESSED."
    )
    lines.append("")
    lines.append(f"**Reviews file:** {reviews_path}")
    lines.append("")
    lines.append("| Point | Reviewer | Reviewer comment | Response | Change made | Evidence | Status |")
    lines.append("|---|---|---|---|---|---|---|")
    for pid, reviewer, point, entry, status in rows:
        lines.append(
            f"| {pid} | {_cell(reviewer)} | {_cell(point)} | {_cell(entry['response'])} | "
            f"{_cell(entry['change_made'])} | {_cell(entry['evidence'])} | {status} |"
        )
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Points parsed: {len(rows)}")
    lines.append(f"- Addressed (response filled): {len(rows) - len(unaddressed_ids)}")
    if unaddressed_ids:
        lines.append(f"- UNADDRESSED: {len(unaddressed_ids)} ({', '.join(unaddressed_ids)})")
    else:
        lines.append("- UNADDRESSED: 0")
    if unknown or invalid_keys:
        lines.append("")
        lines.append("## Notes")
        lines.append("")
        if unknown:
            lines.append(f"- Response ids with no matching point (ignored): {', '.join(unknown)}")
        if invalid_keys:
            lines.append(f"- Response keys that are not valid point ids (ignored): {', '.join(invalid_keys)}")
    lines.append("")
    lines.append(
        "**Point splitting is mechanical (blank lines and bullet or numbered "
        "markers), so verify this matrix against the original review before "
        "sending anything. A human owns the rebuttal.**"
    )
    lines.append("")
    return "\n".join(lines), len(unaddressed_ids)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description=(
            "Build a Markdown reviewer-response matrix from review comments and "
            "prepared responses. Organizational aid; advisory, not a certification."
        )
    )
    ap.add_argument("--reviews", required=True,
                    help="Plain-text file of reviewer comments.")
    ap.add_argument("--responses", default=None,
                    help="YAML mapping of point ids (P1, 2, ...) to "
                         "{response, change_made, evidence} or a bare response string.")
    ap.add_argument("--out", default=None,
                    help="Output path (default: print to stdout).")
    ap.add_argument("--strict", action="store_true",
                    help="Exit 1 if any point is UNADDRESSED.")
    args = ap.parse_args(argv)

    if not os.path.exists(args.reviews):
        _fail(f"reviews file not found: {args.reviews}")
    try:
        with open(args.reviews, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as exc:
        _fail(f"cannot read reviews file: {args.reviews}\n  {exc}")

    if not text.strip():
        # Ported from the retired revision_matrix: an empty comments file is an
        # input-level problem, distinct from "parsed but found nothing" (rc 1).
        print(f"[{TOOL}] ERROR: reviews file is empty: {args.reviews}", file=sys.stderr)
        return 2

    points = [(label, point)
              for label, section_text in split_sections(text)
              for point in split_points(section_text)]
    if not points:
        _fail(f"no review points found in {args.reviews}; is the file empty?")

    responses, invalid_keys = load_responses(args.responses)
    report, unaddressed = build_report(points, responses, invalid_keys, args.reviews)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"[{TOOL}] wrote {args.out}")
    else:
        sys.stdout.write(report)

    if unaddressed:
        print(f"[{TOOL}] advisory: {unaddressed} point(s) UNADDRESSED", file=sys.stderr)
        if args.strict:
            print(f"[{TOOL}] STRICT: unaddressed points remain, exiting 1", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
