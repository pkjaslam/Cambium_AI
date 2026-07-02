#!/usr/bin/env python3
"""revision_matrix -- RETIRED in v1.38.0, superseded by tools/rebuttal_matrix.py.

Kept for one release as a pointer stub so old scripts and docs fail loudly
instead of silently: it prints where the behavior went and exits 3.
Reviewer/Referee sectioning with per-point reviewer attribution and the
empty-file exit code 2 live in tools/rebuttal_matrix.py; its UNADDRESSED
status plus --strict replaces the old TODO --stats gate.
"""
import sys

import cambium_io  # noqa: F401


def main(argv=None) -> int:
    print("RETIRED: use tools/rebuttal_matrix.py", file=sys.stderr)
    print("This stub is kept for one release as a pointer; run "
          "python3 tools/rebuttal_matrix.py --help for the current interface.", file=sys.stderr)
    return 3


if __name__ == "__main__":
    sys.exit(main())
