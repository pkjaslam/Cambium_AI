#!/usr/bin/env python3
"""run_fidelity -- a per-run close-out scorecard that makes orchestrator skips visible.

Advisory and post-hoc: it never blocks a run, it never mints or checks a gate token
(that is gate_lock.py's job), and it runs AFTER the fact so the Director can see what
the orchestrator actually did versus what task_router.route(task) expected. A gap on
this card is a prompt for the human to say "redo X" -- it is not an error and it does
not stop anything.

Four checks, each measured from a real, on-disk record (honest where the signal is weak):

  1. agent coverage  -- expected agents from route(task) vs which of those agents have
                         a matching agent_outputs/<name>.md file on disk.
  2. phase progress   -- did agent_outputs/run_state.json advance past phase 1.
  3. gate recorded    -- is a gate decision present, either in run_state.json's "gate"
                         block or as a dated row in governance/GATES.md's Approvals log.
  4. learning delivered -- reuses tools/learning_delivery.py's own check (single source
                         of truth; this tool does not re-implement that logic).

Usage:
  python3 tools/run_fidelity.py "the task"
  python3 tools/run_fidelity.py "the task" --root /path/to/repo
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cambium_io  # noqa: F401 -- UTF-8 stdout/stderr guard on Windows
import task_router
import learning_delivery

ROOT_DEFAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# Individual checks -- each returns (status, detail) where status is
# "pass", "gap", or "unknown" (weak/no signal, stated honestly, not scored as a fail)
# ---------------------------------------------------------------------------

def _expected_agents(task: str) -> list[str]:
    """Flat, de-duplicated, ordered list of agent ids route(task) expects."""
    r = task_router.route(task)
    seen, out = set(), []
    for p in r["phases"]:
        for g in p["groups"]:
            for a in g["agents"]:
                if a not in seen:
                    seen.add(a)
                    out.append(a)
    return out


def _agent_output_files(root: str) -> set[str]:
    """Basenames (no extension) of every .md file under agent_outputs/."""
    dirpath = os.path.join(root, "agent_outputs")
    if not os.path.isdir(dirpath):
        return set()
    return {
        os.path.splitext(f)[0]
        for f in os.listdir(dirpath)
        if f.endswith(".md")
    }


def check_agent_coverage(task: str, root: str) -> dict:
    """Expected agents from route(task) vs agents that produced an agent_outputs/<name>.md.

    Matching is by filename stem equal to the agent id (hyphen or underscore both
    accepted, since agent names appear both ways across the repo's tools)."""
    expected = _expected_agents(task)
    produced = _agent_output_files(root)
    produced_norm = {p.replace("_", "-") for p in produced}

    covered = [a for a in expected if a.replace("_", "-") in produced_norm]
    missing = [a for a in expected if a.replace("_", "-") not in produced_norm]

    if not expected:
        return {
            "check": "Agent coverage",
            "status": "unknown",
            "detail": "route(task) expected no agents; nothing to check.",
        }

    n_expected, n_covered = len(expected), len(covered)
    status = "pass" if n_covered == n_expected else "gap"
    detail = f"{n_covered}/{n_expected} expected agent(s) produced an agent_outputs/*.md file"
    if missing:
        detail += f"; missing: {', '.join(missing[:8])}" + (" ..." if len(missing) > 8 else "")
    return {"check": "Agent coverage", "status": status, "detail": detail}


def _load_run_state(root: str) -> dict | None:
    path = os.path.join(root, "agent_outputs", "run_state.json")
    if not os.path.exists(path):
        return None
    try:
        return json.load(open(path, encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def check_phase_progress(root: str) -> dict:
    """Did run_state.json advance past phase 1."""
    state = _load_run_state(root)
    if state is None:
        return {
            "check": "Phase progress",
            "status": "unknown",
            "detail": "agent_outputs/run_state.json not found; cannot assess phase progress.",
        }
    phase = state.get("phase")
    if phase is None:
        return {
            "check": "Phase progress",
            "status": "gap",
            "detail": "run_state.json exists but 'phase' is not set (run may not have started).",
        }
    status = "pass" if isinstance(phase, int) and phase > 1 else "gap"
    return {
        "check": "Phase progress",
        "status": status,
        "detail": f"run_state.json reports phase={phase}"
        + ("" if status == "pass" else " (did not advance past phase 1)"),
    }


def check_gate_recorded(root: str) -> dict:
    """A gate decision is present, either in run_state.json's 'gate' block
    (armed = pending, not yet a recorded decision) or as a dated row in
    governance/GATES.md's Approvals log (a real recorded decision)."""
    state = _load_run_state(root)
    state_gate = (state or {}).get("gate")

    gates_path = os.path.join(root, "governance", "GATES.md")
    approvals_rows = 0
    if os.path.exists(gates_path):
        try:
            text = open(gates_path, encoding="utf-8", errors="replace").read()
        except OSError:
            text = ""
        # Approvals log rows look like: | 2026-06-26 | G2 | ... | APPROVE ... |
        approvals_rows = len(re.findall(r"\|\s*\d{4}-\d{2}-\d{2}\s*\|", text))

    if approvals_rows > 0:
        return {
            "check": "Gate recorded",
            "status": "pass",
            "detail": f"governance/GATES.md Approvals log has {approvals_rows} dated row(s).",
        }
    if state_gate:
        return {
            "check": "Gate recorded",
            "status": "gap",
            "detail": (
                f"run_state.json has an armed gate ({state_gate.get('id', '?')}) "
                "but no dated decision found in governance/GATES.md Approvals log."
            ),
        }
    if state is None and not os.path.exists(gates_path):
        return {
            "check": "Gate recorded",
            "status": "unknown",
            "detail": "neither run_state.json nor governance/GATES.md found; cannot assess.",
        }
    return {
        "check": "Gate recorded",
        "status": "gap",
        "detail": "no gate decision found in run_state.json or governance/GATES.md.",
    }


def check_learning_delivered(root: str) -> dict:
    """Reuse learning_delivery.py's own check -- single source of truth, not re-implemented here."""
    state = _load_run_state(root)
    plan = state if state is not None else {}
    if not learning_delivery.is_build_run(plan):
        return {
            "check": "Learning delivered",
            "status": "unknown",
            "detail": "not a build/analysis run per learning_delivery.is_build_run(); learning not required.",
        }
    delivered, artifact_or_reason = learning_delivery.learning_delivered(root)
    if delivered:
        try:
            rel = os.path.relpath(artifact_or_reason, root)
        except ValueError:
            rel = artifact_or_reason
        return {"check": "Learning delivered", "status": "pass", "detail": f"artifact found: {rel}"}
    return {
        "check": "Learning delivered",
        "status": "gap",
        "detail": "build/analysis run but no filled learning artifact found (see learning_delivery.py).",
    }


def run_fidelity_checks(task: str, root: str) -> list[dict]:
    """Run all four checks. Returns a flat list of result dicts."""
    return [
        check_agent_coverage(task, root),
        check_phase_progress(root),
        check_gate_recorded(root),
        check_learning_delivered(root),
    ]


# ---------------------------------------------------------------------------
# Scorecard renderer
# ---------------------------------------------------------------------------

_STATUS_LABEL = {"pass": "pass", "gap": "gap", "unknown": "weak signal"}


def build_scorecard(task: str, root: str) -> str:
    results = run_fidelity_checks(task, root)
    n_pass = sum(1 for r in results if r["status"] == "pass")
    n_gap = sum(1 for r in results if r["status"] == "gap")
    n_unknown = sum(1 for r in results if r["status"] == "unknown")

    lines: list[str] = []
    lines.append("# Run fidelity scorecard (advisory, post-hoc)")
    lines.append("")
    lines.append(
        "> This scorecard is advisory and post-hoc. It compares what "
        "`task_router.route(task)` expected against what actually happened on disk, "
        "after the run. A gap here is a prompt for the human to say \"redo X\"; it "
        "does not block anything and it mints no gate token."
    )
    lines.append("")
    lines.append(f"**Task:** {task}")
    lines.append(f"**Root:** {root}")
    lines.append(f"**Checks:** {len(results)} | **pass:** {n_pass} | **gap:** {n_gap} | **weak signal:** {n_unknown}")
    lines.append("")
    lines.append("| Check | Status | Detail |")
    lines.append("|---|---|---|")
    for r in results:
        status_cell = _STATUS_LABEL.get(r["status"], r["status"])
        if r["status"] == "gap":
            status_cell = f"**{status_cell}**"
        lines.append(f"| {r['check']} | {status_cell} | {r['detail']} |")
    lines.append("")

    if n_gap == 0 and n_unknown == 0:
        overall = "All checks pass against what route(task) expected. Advisory only; this is not a compliance sign-off."
    elif n_gap == 0:
        overall = (
            f"No gaps found, but {n_unknown} check(s) had a weak or missing signal "
            "(honest 'weak signal', not scored as a failure). Advisory only."
        )
    else:
        overall = (
            f"{n_gap} gap(s) found against what route(task) expected. Advisory and "
            "post-hoc: no run was blocked. If a gap is real, tell the orchestrator to redo that step."
        )
    lines.append(f"**Overall:** {overall}")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description=(
            "Per-run close-out scorecard: agent coverage, phase progress, gate "
            "recorded, learning delivered. Advisory and post-hoc; never blocks."
        )
    )
    ap.add_argument("task", help="The task originally routed, e.g. \"win an NSF grant on soil health\".")
    ap.add_argument(
        "--root",
        default=ROOT_DEFAULT,
        help="Repo root to inspect for agent_outputs/, run_state.json, and governance/GATES.md.",
    )
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root)
    print(build_scorecard(args.task, root))
    return 0


if __name__ == "__main__":
    sys.exit(main())
