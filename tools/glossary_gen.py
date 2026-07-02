#!/usr/bin/env python3
"""glossary_gen -- RETIRED in v1.38.0, superseded by tools/glossary_builder.py.

Kept for one release as a pointer stub so old scripts and docs fail loudly
instead of silently: it prints where the behavior went and exits 3.
The docs/ + skills/ default scan target, SKILL.md frontmatter extraction,
the "term - definition" line rule, and exit-1-on-empty semantics all
live in tools/glossary_builder.py.
"""
import sys

import cambium_io  # noqa: F401


def main(argv=None) -> int:
    print("RETIRED: use tools/glossary_builder.py", file=sys.stderr)
    print("This stub is kept for one release as a pointer; run "
          "python3 tools/glossary_builder.py --help for the current interface.", file=sys.stderr)
    return 3


if __name__ == "__main__":
    sys.exit(main())
