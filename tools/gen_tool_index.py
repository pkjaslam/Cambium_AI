#!/usr/bin/env python3
"""gen_tool_index -- auto-generate tools/TOOL_INDEX.md, the inventory of every
tool that already exists in tools/.

The orchestrator improvises when nothing lists the tools that already exist,
so it re-solves problems that already have a script. This scans every
tools/*.py file, pulls a one-line purpose for each from its module docstring,
and writes a single alphabetical Markdown table so the orchestrator (and any
agent) checks this index BEFORE building something new, and reuses instead of
reinventing.

Purpose extraction, in order:
  1. If the module docstring's first meaningful line looks like
     "name -- purpose" or "name - purpose" (the module name followed by a
     dash), the purpose is the text after the dash.
  2. Otherwise the first meaningful (non-empty, non-shebang-echo) line of the
     docstring is used as-is.
  3. If there is no docstring, or it is empty, fall back to the filename
     (without extension) as the purpose so the row is never blank.

Usage:
    python3 tools/gen_tool_index.py            # (re)write tools/TOOL_INDEX.md
    python3 tools/gen_tool_index.py --check    # exit 1 if TOOL_INDEX.md is stale

No em dashes in generated output (plain hyphens only).
"""

import argparse
import ast
import pathlib
import re
import sys

import cambium_io  # noqa: F401 -- UTF-8 guard for Windows

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

TOOLS_DIR = pathlib.Path(__file__).resolve().parent
ROOT = TOOLS_DIR.parent
INDEX_PATH = TOOLS_DIR / "TOOL_INDEX.md"

# Files in tools/ that are not "tools" in the inventory sense.
SELF_NAME = "gen_tool_index.py"
SKIP_NAMES = {SELF_NAME, "__init__.py"}


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def discover_tool_files() -> list:
    """Return sorted list of Path objects for every tools/*.py file, skipping
    gen_tool_index.py itself and any __init__.py."""
    if not TOOLS_DIR.is_dir():
        return []
    files = [
        f for f in TOOLS_DIR.iterdir()
        if f.is_file() and f.suffix == ".py" and f.name not in SKIP_NAMES
    ]
    return sorted(files, key=lambda p: p.name.lower())


# ---------------------------------------------------------------------------
# Purpose extraction
# ---------------------------------------------------------------------------

def _module_docstring(source: str):
    """Return the module docstring text, or None if there isn't one.
    Uses ast so it works regardless of shebang lines or import order."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    return ast.get_docstring(tree)


def _first_meaningful_line(docstring: str):
    """Return the first non-empty line of a docstring, or None."""
    for line in docstring.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return None


# Matches "name -- purpose" or "name - purpose" or "name.py -- purpose" etc.
# The separator is "--", "-", or an em dash (normalized away elsewhere), with
# at least one space on each side.
_NAME_DASH_PURPOSE = re.compile(
    r"^\s*[\w.]+(?:\.py)?\s+(?:--|-|—)\s+(.+)$"
)


def extract_purpose(source: str, filename: str) -> str:
    """Return a one-line purpose string for a tool's source code.

    filename is used only as the final fallback when no usable docstring
    line can be found.
    """
    docstring = _module_docstring(source)
    if docstring:
        line = _first_meaningful_line(docstring)
        if line:
            # Normalize any em/en dash separators to plain hyphens first, so
            # the regex and the final rendered text both stay dash-free.
            normalized = line.replace("—", "--").replace("–", "-")
            m = _NAME_DASH_PURPOSE.match(normalized)
            if m:
                purpose = m.group(1).strip()
            else:
                purpose = normalized.strip()
            if purpose:
                return purpose
    # Fallback: filename without extension
    stem = pathlib.Path(filename).stem
    return stem


def build_inventory() -> list:
    """Return a sorted list of (tool_name, purpose) tuples for every tool."""
    rows = []
    for f in discover_tool_files():
        try:
            source = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            source = ""
        purpose = extract_purpose(source, f.name)
        rows.append((f.name, purpose))
    rows.sort(key=lambda r: r[0].lower())
    return rows


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def _escape_cell(text: str) -> str:
    """Escape pipe characters so a purpose string cannot break the table."""
    return text.replace("|", "\\|")


def render_markdown(rows: list) -> str:
    """Return the full TOOL_INDEX.md content for the given (name, purpose) rows."""
    lines = [
        "# Tool index",
        "",
        "This is the index the orchestrator consults before building anything "
        "new. Check here first: if a tool already does what you need, reuse it "
        "instead of writing a new script. This file is auto-generated by "
        "`tools/gen_tool_index.py` from the one-line purpose in each tool's "
        "module docstring. Do not hand-edit it; rerun the generator instead.",
        "",
        f"Tools indexed: {len(rows)}",
        "",
        "| Tool | What it does |",
        "|---|---|",
    ]
    for name, purpose in rows:
        lines.append(f"| `{name}` | {_escape_cell(purpose)} |")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def check_mode() -> int:
    """Return 0 if the committed TOOL_INDEX.md matches a fresh regen, else 1."""
    rows = build_inventory()
    fresh = render_markdown(rows)
    current = INDEX_PATH.read_text(encoding="utf-8") if INDEX_PATH.exists() else None
    if current == fresh:
        print("[gen_tool_index] --check: TOOL_INDEX.md is up to date.")
        return 0
    print("[gen_tool_index] --check: TOOL_INDEX.md is STALE (rerun without --check to fix).")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate tools/TOOL_INDEX.md, the auto-generated tool inventory."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if the committed TOOL_INDEX.md differs from a fresh regen.",
    )
    args = parser.parse_args()

    if args.check:
        return check_mode()

    rows = build_inventory()
    fresh = render_markdown(rows)
    INDEX_PATH.write_text(fresh, encoding="utf-8")
    print(f"[gen_tool_index] wrote {INDEX_PATH.relative_to(ROOT)} ({len(rows)} tools)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
