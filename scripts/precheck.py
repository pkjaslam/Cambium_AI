#!/usr/bin/env python3
"""Pre-push check: run the test suite before a push is allowed.

Run this yourself before pushing:

    python scripts/precheck.py

or let the bundled git pre-push hook run it for you (see .githooks/pre-push).

It runs the full pytest suite under Python's UTF-8 mode, so the suite behaves on
Windows the same way it does on Linux CI. Cambium's tools print Unicode (em
dashes and box-drawing glyphs); a default Windows cp1252 console would crash
them and fail tests that pass on CI. Forcing UTF-8 here makes local match CI.

If anything is red it exits non-zero, so a failing commit never leaves your
machine. Honest note: this catches what pytest catches; it is not a substitute
for CI, just an early warning.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    # UTF-8 mode for pytest AND every tool subprocess the tests spawn (env is
    # inherited), so Windows decodes/encodes Unicode the way Linux CI does.
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    print("[precheck] running the test suite (pytest -q, UTF-8 mode) ...")
    try:
        result = subprocess.run(
            [sys.executable, "-X", "utf8", "-m", "pytest", "-q"],
            cwd=ROOT,
            env=env,
        )
    except FileNotFoundError:
        print("[precheck] python/pytest not found. Install with: pip install pytest pyyaml")
        return 1
    if result.returncode != 0:
        print("\n[precheck] FAILED. Fix the red tests above before pushing.")
        return result.returncode
    print("\n[precheck] all tests passed. Safe to push.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
