#!/usr/bin/env python3
"""flashcards -- RETIRED in v1.38.0, superseded by tools/flashcards_export.py.

Kept for one release as a pointer stub so old scripts and docs fail loudly
instead of silently: it prints where the behavior went and exits 3.
The "**term**: definition" and "term - definition" input shapes (term
capped at 6 words, first occurrence wins) live in tools/flashcards_export.py,
which also reads Q:/A: lines, glossary tables, quizzes, and Learning Lab
JSON, and exports TSV/CSV/JSON plus a review schedule. The in-browser SM-2
HTML reviewer was retired with this tool.
"""
import sys

import cambium_io  # noqa: F401


def main(argv=None) -> int:
    print("RETIRED: use tools/flashcards_export.py", file=sys.stderr)
    print("This stub is kept for one release as a pointer; run "
          "python3 tools/flashcards_export.py --help for the current interface.", file=sys.stderr)
    return 3


if __name__ == "__main__":
    sys.exit(main())
