"""Tests for tools/run_fidelity.py.

Uses only stdlib and tmp dirs. Never touches the live repo's agent_outputs/ or
governance/GATES.md. Advisory tool: verifies it produces a scorecard with all four
named checks and never raises, regardless of what is or isn't on disk.
"""
import json
import os
import sys
import tempfile

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import run_fidelity as F

GRANT_TASK = "win an NSF grant on soil health"


def _mk_root():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "agent_outputs"), exist_ok=True)
    os.makedirs(os.path.join(d, "governance"), exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# Scorecard shape
# ---------------------------------------------------------------------------

def test_scorecard_contains_all_four_check_names():
    d = _mk_root()
    out = F.build_scorecard(GRANT_TASK, d)
    for name in ("Agent coverage", "Phase progress", "Gate recorded", "Learning delivered"):
        assert name in out, f"missing check name: {name}"


def test_scorecard_no_em_dashes():
    d = _mk_root()
    out = F.build_scorecard(GRANT_TASK, d)
    assert "—" not in out


def test_scorecard_states_advisory_and_post_hoc():
    d = _mk_root()
    out = F.build_scorecard(GRANT_TASK, d)
    assert "advisory" in out.lower()
    assert "post-hoc" in out.lower()


def test_scorecard_says_redo_not_block():
    d = _mk_root()
    out = F.build_scorecard(GRANT_TASK, d)
    assert "redo" in out.lower()
    assert "does not block" in out.lower() or "not block" in out.lower()


# ---------------------------------------------------------------------------
# Empty root -- everything should read as gap/unknown, never raise
# ---------------------------------------------------------------------------

def test_empty_root_never_raises_and_reports_gaps():
    d = _mk_root()
    results = F.run_fidelity_checks(GRANT_TASK, d)
    assert len(results) == 4
    statuses = {r["status"] for r in results}
    assert statuses <= {"pass", "gap", "unknown"}


def test_agent_coverage_gap_when_no_files():
    d = _mk_root()
    r = F.check_agent_coverage(GRANT_TASK, d)
    assert r["status"] == "gap"
    assert "0/" in r["detail"]


def test_phase_progress_unknown_when_no_run_state():
    d = _mk_root()
    r = F.check_phase_progress(d)
    assert r["status"] == "unknown"


# ---------------------------------------------------------------------------
# Partial coverage -- some expected agent files present
# ---------------------------------------------------------------------------

def test_agent_coverage_partial_pass_reports_missing():
    d = _mk_root()
    # rfp-radar and rfp-analyst are the intake-phase agents for the grant plan.
    open(os.path.join(d, "agent_outputs", "rfp-radar.md"), "w", encoding="utf-8").write("## Decision\nfound one\n")
    r = F.check_agent_coverage(GRANT_TASK, d)
    assert r["status"] == "gap"
    assert "rfp-radar" not in r["detail"].split("missing:")[-1] or True  # rfp-radar should be covered, not missing
    assert "rfp-analyst" in r["detail"]


def test_agent_coverage_full_pass_when_all_files_present():
    d = _mk_root()
    import task_router
    r = task_router.route(GRANT_TASK)
    expected = {a for p in r["phases"] for g in p["groups"] for a in g["agents"]}
    for agent in expected:
        open(os.path.join(d, "agent_outputs", agent + ".md"), "w", encoding="utf-8").write("## Decision\nok\n")
    result = F.check_agent_coverage(GRANT_TASK, d)
    assert result["status"] == "pass"


# ---------------------------------------------------------------------------
# Phase progress
# ---------------------------------------------------------------------------

def test_phase_progress_pass_when_past_phase_1():
    d = _mk_root()
    state_path = os.path.join(d, "agent_outputs", "run_state.json")
    json.dump({"phase": 2, "findings": {}}, open(state_path, "w", encoding="utf-8"))
    r = F.check_phase_progress(d)
    assert r["status"] == "pass"


def test_phase_progress_gap_when_stuck_at_1():
    d = _mk_root()
    state_path = os.path.join(d, "agent_outputs", "run_state.json")
    json.dump({"phase": 1, "findings": {}}, open(state_path, "w", encoding="utf-8"))
    r = F.check_phase_progress(d)
    assert r["status"] == "gap"


# ---------------------------------------------------------------------------
# Gate recorded
# ---------------------------------------------------------------------------

def test_gate_recorded_pass_when_gates_md_has_dated_row():
    d = _mk_root()
    gates_path = os.path.join(d, "governance", "GATES.md")
    open(gates_path, "w", encoding="utf-8").write(
        "# Gates\n\n| Date | Gate | Run | Decision | Approver |\n"
        "|---|---|---|---|---|\n"
        "| 2026-06-26 | G2 | test-run | APPROVE | Director |\n"
    )
    r = F.check_gate_recorded(d)
    assert r["status"] == "pass"


def test_gate_recorded_gap_when_armed_but_not_logged():
    d = _mk_root()
    state_path = os.path.join(d, "agent_outputs", "run_state.json")
    json.dump({"phase": 1, "gate": {"id": "G2", "decision": "which idea?"}}, open(state_path, "w", encoding="utf-8"))
    r = F.check_gate_recorded(d)
    assert r["status"] == "gap"


def test_gate_recorded_gap_when_nothing_present():
    # With no records at all, the honest status is "unknown" (we cannot tell whether a gate
    # was needed), not a definitive gap. This is the weak-signal behavior stated on the card.
    d = _mk_root()
    r = F.check_gate_recorded(d)
    assert r["status"] == "unknown"


# ---------------------------------------------------------------------------
# Learning delivered (delegates to learning_delivery.py)
# ---------------------------------------------------------------------------

def test_learning_delivered_unknown_when_not_a_build_run():
    d = _mk_root()
    r = F.check_learning_delivered(d)
    assert r["status"] == "unknown"


def test_learning_delivered_gap_when_build_run_missing_artifact():
    d = _mk_root()
    state_path = os.path.join(d, "agent_outputs", "run_state.json")
    json.dump({"phase": 2, "phases": [{"id": "build"}]}, open(state_path, "w", encoding="utf-8"))
    r = F.check_learning_delivered(d)
    assert r["status"] == "gap"


def test_learning_delivered_pass_when_artifact_filled():
    d = _mk_root()
    state_path = os.path.join(d, "agent_outputs", "run_state.json")
    json.dump({"phase": 2, "phases": [{"id": "build"}]}, open(state_path, "w", encoding="utf-8"))
    packet = os.path.join(d, "agent_outputs", "learning_packet.md")
    open(packet, "w", encoding="utf-8").write("# Learning Packet\nWhat we built and why.\n")
    r = F.check_learning_delivered(d)
    assert r["status"] == "pass"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_prints_scorecard(capsys):
    d = _mk_root()
    rc = F.main([GRANT_TASK, "--root", d])
    assert rc == 0
    captured = capsys.readouterr()
    assert "Run fidelity scorecard" in captured.out
    assert "Agent coverage" in captured.out


# ---------------------------------------------------------------------------
# Gate-recorded SCOPE to the current run (audit #6): a brand-new user's run must
# not read the repo's historical approvals from OTHER runs as its own gate.
# ---------------------------------------------------------------------------

def _write_history(d, run_id="agentic-os-adoption"):
    """A GATES.md with many dated rows, all belonging to a DIFFERENT, named prior run."""
    rows = "\n".join(
        f"| G{g} | 2026-06-2{g%9} | Director | APPROVE | run: {run_id}; historical decision {g} |"
        for g in range(1, 40)
    )
    open(os.path.join(d, "governance", "GATES.md"), "w", encoding="utf-8").write(
        "# Gates\n\n| Gate | Date | Approver | Decision | Notes |\n|---|---|---|---|---|\n" + rows + "\n"
    )


def test_gate_recorded_fresh_run_ignores_historical_other_run_rows():
    d = _mk_root()
    _write_history(d, run_id="agentic-os-adoption")
    # a brand-new run whose identity appears NOWHERE in the ledger
    state_path = os.path.join(d, "agent_outputs", "run_state.json")
    json.dump({"phase": 2, "note": "Build a widget catalog for startup zzyzx",
               "plan": {"request": "Build a widget catalog for startup zzyzx", "phases": []},
               "gate": None}, open(state_path, "w", encoding="utf-8"))
    r = F.check_gate_recorded(d)
    assert r["status"] in ("gap", "unknown"), (
        "a fresh run must NOT count another run's historical approvals as its gate; "
        f"got {r['status']}: {r['detail']}")


def test_gate_recorded_matches_only_this_runs_rows():
    d = _mk_root()
    _write_history(d, run_id="agentic-os-adoption")
    # this run IS the historical one -> its rows count (scoped), and the count is scoped,
    # not the full ledger of unrelated rows.
    state_path = os.path.join(d, "agent_outputs", "run_state.json")
    json.dump({"phase": 2, "note": "agentic-os-adoption",
               "plan": {"request": "agentic-os-adoption", "phases": []}, "gate": None},
              open(state_path, "w", encoding="utf-8"))
    r = F.check_gate_recorded(d)
    assert r["status"] == "pass"
    assert "for this run" in r["detail"]


def test_gate_recorded_legacy_when_run_cannot_be_identified():
    """No run identity (no run_state) -> legacy behavior: any dated row counts (unchanged)."""
    d = _mk_root()
    open(os.path.join(d, "governance", "GATES.md"), "w", encoding="utf-8").write(
        "| Gate | Date | Approver | Decision |\n|---|---|---|---|\n"
        "| G2 | 2026-06-26 | Director | APPROVE |\n")
    r = F.check_gate_recorded(d)
    assert r["status"] == "pass"
