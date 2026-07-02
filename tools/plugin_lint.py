#!/usr/bin/env python3
"""plugin_lint -- RETIRED in v1.38.0, superseded by tools/plugin_smoke.py.

Kept for one release as a pointer stub so old scripts and docs fail loudly
instead of silently: it prints where the behavior went and exits 3.
Its checks are now a strict subset of tools/plugin_smoke.py: agent
frontmatter fields and model set, agent-name uniqueness across differently
named files, skill frontmatter, and plugin.json parse + semver.
"""
import sys

import cambium_io  # noqa: F401


def main(argv=None) -> int:
    print("RETIRED: use tools/plugin_smoke.py", file=sys.stderr)
    print("This stub is kept for one release as a pointer; run "
          "python3 tools/plugin_smoke.py --help for the current interface.", file=sys.stderr)
    return 3


if __name__ == "__main__":
    sys.exit(main())
