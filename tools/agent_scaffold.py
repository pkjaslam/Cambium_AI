#!/usr/bin/env python3
"""agent_scaffold -- RETIRED in v1.38.0, superseded by tools/new_agent.py and tools/new_skill.py.

Kept for one release as a pointer stub so old scripts and docs fail loudly
instead of silently: it prints where the behavior went and exits 3.
The agent scaffold (dual agents/ + .claude/agents/ cards, kebab and model
checks incl. option-like --name folding) lives in tools/new_agent.py; the
skill scaffold (skills/<name>/SKILL.md) lives in tools/new_skill.py.
"""
import sys

import cambium_io  # noqa: F401


def main(argv=None) -> int:
    print("RETIRED: use tools/new_agent.py (agents) or tools/new_skill.py (skills)", file=sys.stderr)
    print("This stub is kept for one release as a pointer; run "
          "python3 tools/new_agent.py --help or python3 tools/new_skill.py --help for the current interface.", file=sys.stderr)
    return 3


if __name__ == "__main__":
    sys.exit(main())
