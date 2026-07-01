"""Tests for tools/dispatch_plan.py.

Uses only stdlib. dispatch_plan() is purely derived from task_router.route(), so
these tests check the derived output shape, not a hand-maintained plan.
"""
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import dispatch_plan as D
import task_router


GRANT_TASK = "win an NSF grant on soil health"


def test_output_contains_a_task_call():
    out = D.dispatch_plan(GRANT_TASK)
    assert 'Task(subagent_type="cambium-institute:' in out


def test_output_contains_stop_gate_line():
    out = D.dispatch_plan(GRANT_TASK)
    assert "STOP: gate" in out


def test_grant_task_has_g1_g2_g3_stop_lines():
    """The grant plan has three gates (G1, G2, G3); all three must render as STOP lines."""
    out = D.dispatch_plan(GRANT_TASK)
    for gid in ("G1", "G2", "G3"):
        assert f"STOP: gate {gid}" in out, f"missing STOP line for {gid}"


def test_every_expected_agent_appears_as_a_task_call():
    r = task_router.route(GRANT_TASK)
    out = D.dispatch_plan(GRANT_TASK)
    expected = {a for p in r["phases"] for g in p["groups"] for a in g["agents"]}
    for agent in expected:
        assert f'subagent_type="cambium-institute:{agent}"' in out, f"missing Task() for {agent}"


def test_parallel_groups_are_marked():
    out = D.dispatch_plan(GRANT_TASK)
    assert "parallel" in out.lower()


def test_txt_format_has_no_markdown_headings():
    out = D.dispatch_plan(GRANT_TASK, format="txt")
    assert not out.startswith("# ")
    assert "Task(subagent_type=" in out
    assert "STOP: gate" in out


def test_cannot_drift_from_router_agent_count():
    """dispatch_plan must reference exactly the agents route() returns -- no more, no fewer."""
    r = task_router.route(GRANT_TASK)
    out = D.dispatch_plan(GRANT_TASK)
    n_calls = out.count("Task(subagent_type=")
    n_expected_slots = sum(len(g["agents"]) for p in r["phases"] for g in p["groups"])
    assert n_calls == n_expected_slots


def test_profile_is_recorded_not_dropped():
    out = D.dispatch_plan(GRANT_TASK, profile="interests: soil; expertise: agronomy")
    assert "researcher profile supplied" in out


def test_no_em_dashes():
    out = D.dispatch_plan(GRANT_TASK)
    assert "—" not in out


def test_cli_prints_dispatch_block(capsys):
    rc = D.main([GRANT_TASK])
    assert rc == 0
    captured = capsys.readouterr()
    assert "Task(subagent_type=" in captured.out
    assert "STOP: gate" in captured.out


def test_software_task_has_different_gates_than_grant():
    """A software task must route to its own gates (G-build/G-ship), not the grant gates."""
    out = D.dispatch_plan("build a web app dashboard")
    assert "STOP: gate G-build" in out
    assert "STOP: gate G-ship" in out
