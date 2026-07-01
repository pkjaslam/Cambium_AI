#!/usr/bin/env python3
"""learning_delivery -- enforce that a build/analysis run delivers a learning artifact.

A run is a BUILD/ANALYSIS run if any phase id is in the build-phase set OR the plan's
request text matches the build pattern. If it is, the run must not close without a filled
learning artifact: either agent_outputs/learning_packet.md or a generated lab HTML under
demo/learning_lab.html or academy/labs/*.html.

"Filled" = the file exists, is non-empty, and does NOT contain the literal token __FILL__.

Usage:
  python3 tools/learning_delivery.py check [--state agent_outputs/run_state.json] [--root .]
  python3 tools/learning_delivery.py deliver [--root .]     # print the packet body to stdout
                                                             # so the orchestrator can deliver it in chat

Exit:
  check:   0 = not a build/analysis run, OR learning was delivered.
           1 = IS a build/analysis run AND no filled artifact exists (close-out must be blocked).
  deliver: 0 = artifact found and printed.
           1 = no filled artifact to deliver (missing or still has __FILL__).

Importable functions (used by tests):
  is_build_run(plan)            -> bool
  learning_delivered(root)      -> (bool, str)   (delivered?, artifact_path_or_reason)
  deliver_learning(root)        -> (bool, str)   (delivered?, body_or_reason) — body is the full artifact text
"""
from __future__ import annotations
import argparse, glob, json, os, re, sys

import cambium_io  # UTF-8 guard + data_home() for plugin-safe path resolution

ROOT_DEFAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Phase ids that mark a build/analysis run
BUILD_PHASE_IDS = {"build", "design", "execution", "learn", "experiment"}

# Request text pattern (case-insensitive)
BUILD_REQUEST_RE = re.compile(
    r"build|analy|model|develop|implement|pipeline|study|experiment", re.IGNORECASE
)

# ---------------------------------------------------------------------------
# Core logic (importable)
# ---------------------------------------------------------------------------

def is_build_run(plan: dict) -> bool:
    """Return True if the plan represents a build/analysis run.

    Checks:
    - any phase id in BUILD_PHASE_IDS, OR
    - plan.request matches BUILD_REQUEST_RE.
    """
    phases = plan.get("phases") or []
    for phase in phases:
        pid = phase.get("id", "")
        if pid in BUILD_PHASE_IDS:
            return True
    request = plan.get("request", "")
    if request and BUILD_REQUEST_RE.search(str(request)):
        return True
    return False


def _is_filled(path: str) -> bool:
    """A file is 'filled' when it exists, is non-empty, and has no __FILL__ tokens."""
    if not os.path.exists(path):
        return False
    try:
        content = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return False
    if not content.strip():
        return False
    return "__FILL__" not in content


def learning_delivered(root: str) -> tuple[bool, str]:
    """Check whether a filled learning artifact exists under *root*.

    The caller is responsible for passing the right root (the CLI defaults it to
    data_home(), the writable run-data dir). This function checks ONLY that root,
    so a stub under one root never passes by finding a real artifact elsewhere.

    Returns (True, artifact_path) if delivered, else (False, reason_string).
    Checks in order:
      1. agent_outputs/learning_packet.md
      2. demo/learning_lab.html
      3. academy/labs/*.html  (any file)
    """
    def _search_root(r: str):
        packet = os.path.join(r, "agent_outputs", "learning_packet.md")
        if _is_filled(packet):
            return (True, packet)
        demo_lab = os.path.join(r, "demo", "learning_lab.html")
        if _is_filled(demo_lab):
            return (True, demo_lab)
        labs_pattern = os.path.join(r, "academy", "labs", "*.html")
        for lab_path in sorted(glob.glob(labs_pattern)):
            if _is_filled(lab_path):
                return (True, lab_path)
        return None

    result = _search_root(root)
    if result:
        return result

    # nothing found -- build the reason message
    packet = os.path.join(root, "agent_outputs", "learning_packet.md")
    reasons = []
    if os.path.exists(packet):
        content = open(packet, encoding="utf-8", errors="replace").read()
        if "__FILL__" in content:
            reasons.append(
                f"  - {packet} exists but still contains __FILL__ tokens (stub, not filled)"
            )
        elif not content.strip():
            reasons.append(f"  - {packet} is empty")
    else:
        reasons.append(
            f"  - {packet} does not exist"
        )

    if not reasons:
        reasons.append("  - no filled learning artifact found in checked locations")

    fix_msg = (
        "To fix:\n"
        "  Option A) Have the teaching-assistant fill templates/LEARNING_PACKET.md and copy it to\n"
        "            agent_outputs/learning_packet.md (remove all __FILL__ tokens).\n"
        "  Option B) Generate a lab:  python3 tools/gen_learning_lab.py --demo\n"
        "            or place a filled HTML under academy/labs/<name>.html"
    )
    return (False, "\n".join(reasons) + "\n" + fix_msg)


def deliver_learning(root: str) -> tuple[bool, str]:
    """Return (True, full_artifact_text) if a filled artifact exists under *root*, else (False, reason).

    This is the "delivery" counterpart to learning_delivered(): where that function only
    confirms an artifact exists, this one hands back the actual body so the caller (the CLI's
    `deliver` subcommand, or the orchestrator programmatically) can print/post it in chat --
    so "filed" and "delivered" become the same action instead of two steps that can drift apart.
    """
    ok, artifact_or_reason = learning_delivered(root)
    if not ok:
        return (False, artifact_or_reason)
    try:
        body = open(artifact_or_reason, encoding="utf-8", errors="replace").read()
    except OSError as exc:
        return (False, f"  - {artifact_or_reason} could not be read: {exc}")
    return (True, body)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _load_plan(state_path: str) -> dict | None:
    """Load plan from run_state.json. Returns None if missing."""
    if not os.path.exists(state_path):
        return None
    try:
        data = json.load(open(state_path, encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    # run_state.json may embed the plan under "plan" or at top level
    if "plan" in data and isinstance(data["plan"], dict):
        return data["plan"]
    # treat the whole state as the plan (phases key at top level)
    return data


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Check that a build/analysis run delivered a learning artifact."
    )
    sub = ap.add_subparsers(dest="cmd")
    chk = sub.add_parser("check", help="Check learning delivery for the current run.")
    # Default state path through data_home() so it resolves correctly in plugin installs.
    # In the dev/repo/test case, data_home() == ROOT, so behavior is unchanged.
    chk.add_argument(
        "--state",
        default=os.path.join("agent_outputs", "run_state.json"),
        help="Path to run_state.json, resolved against --root if relative (default: agent_outputs/run_state.json)",
    )
    chk.add_argument(
        "--root",
        default=cambium_io.data_home(),
        help="Root to search for run data and artifacts (default: data_home(), the writable run-data dir)",
    )

    dlv = sub.add_parser(
        "deliver",
        help="Print the full learning packet/lab body to stdout so the orchestrator can deliver it in chat.",
    )
    dlv.add_argument(
        "--root",
        default=cambium_io.data_home(),
        help="Root to search for the learning artifact (default: data_home(), the writable run-data dir)",
    )
    dlv.add_argument(
        "--print",
        dest="print_flag",
        action="store_true",
        help="Same as running `deliver` (kept for the --print spelling some callers expect).",
    )

    a = ap.parse_args(argv)

    if a.cmd == "deliver":
        root = os.path.abspath(a.root)
        ok, body_or_reason = deliver_learning(root)
        if ok:
            print(body_or_reason)
            return 0
        print("[learning] Cannot deliver -- no filled learning artifact found:")
        print(body_or_reason)
        return 1

    if a.cmd != "check":
        ap.print_help()
        return 2

    state_path = a.state
    root = os.path.abspath(a.root)

    # Resolve state_path relative to root if not absolute
    if not os.path.isabs(state_path):
        state_path = os.path.join(root, state_path)

    plan = _load_plan(state_path)
    if plan is None:
        print(
            f"[learning] run_state.json not found at {state_path}; "
            "cannot assess -- learning check skipped."
        )
        return 0

    if not is_build_run(plan):
        print("[learning] not a build/analysis run; learning not required")
        return 0

    delivered, artifact_or_reason = learning_delivered(root)
    if delivered:
        try:
            rel = os.path.relpath(artifact_or_reason, root)
        except ValueError:
            rel = artifact_or_reason
        print(f"[learning] artifact: {rel}")
        print("[learning] OK: learning delivered.")
        return 0

    print("[learning] Missing learning artifact:")
    print(artifact_or_reason)
    print("[learning] -> FAILED: a build/analysis run must deliver learning.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
