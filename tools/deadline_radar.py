#!/usr/bin/env python3
"""deadline_radar -- RETIRED in v1.38.0, superseded by tools/award_calendar.py.

Kept for one release as a pointer stub so old scripts and docs fail loudly
instead of silently: it prints where the behavior went and exits 3.
Multi-source ingestion (several files plus repeatable --add, with
de-duplication) and .ics VALARM emission (--alarm-days, default 14) live
in tools/award_calendar.py.
"""
import sys

import cambium_io  # noqa: F401


def main(argv=None) -> int:
    print("RETIRED: use tools/award_calendar.py", file=sys.stderr)
    print("This stub is kept for one release as a pointer; run "
          "python3 tools/award_calendar.py --help for the current interface.", file=sys.stderr)
    return 3


if __name__ == "__main__":
    sys.exit(main())
