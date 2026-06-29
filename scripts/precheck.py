#!/usr/bin/env python3
"""Pre-push check: run the test suite before a push is allowed.

Run this yourself before pushing:

    python scripts/precheck.py

or let the bundled git pre-push hook run it for you (see .githooks/pre-push).

It runs the full pytest suite. If anything is red it exits non-zero, so a
failing commit never leaves your machine, the same failures your CI would
catch, caught locally first. Honest note: this catches what pytest catches; it
is not a substitute for CI, just an early warning.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    print("[precheck] running the test suite (pytest -q) ...")
    try:
        result = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT)
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
