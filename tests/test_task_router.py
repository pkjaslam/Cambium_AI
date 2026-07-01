"""Task router tests -- orphan-agent fix (partnership-liaison, program-manager).

Two agents in the "partner" council were never dispatched by any phase builder:
  - partnership-liaison (outreach, invitation drafts, one-page briefs, contact pipeline)
  - program-manager     (post-award project management: work breakdown, milestones,
                          subaward coordination, reporting deadlines)

This file asserts both are now reachable, and that adding them did not regress the
existing grant classification or double-book obvious report/grant tasks.
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import task_router


def _agents(phases):
    return {a for p in phases for g in p["groups"] for a in g["agents"]}


def test_grant_still_classifies_and_includes_partnership_liaison():
    r = task_router.route("draft the proposal for an NSF AFRI grant with our partner institution")
    assert r["type"] == "grant"
    assert "partnership-liaison" in _agents(r["phases"])
    # collaborator-scout and convener must still be there too (minimal change, not a regression)
    assert {"collaborator-scout", "convener"} <= _agents(r["phases"])


def test_post_award_project_task_routes_to_project_and_dispatches_program_manager():
    r = task_router.route("manage the awarded project milestones and subawards")
    assert r["type"] == "project"
    assert "program-manager" in _agents(r["phases"])
    assert "convener" in _agents(r["phases"])


def test_project_type_has_a_human_gate():
    phases = task_router.plan_for_type("project")
    gates = [p["gate"]["id"] for p in phases if p["gate"]]
    assert "G-plan" in gates


def test_project_type_ends_in_closeout_like_every_other_type():
    phases = task_router.plan_for_type("project")
    assert phases[-1]["id"] == "closeout"


def test_project_does_not_steal_a_plain_grant_or_report_task():
    # a genuine pre-award proposal request must still route to grant, not project
    assert task_router.route("write an NSF AFRI grant proposal")["type"] == "grant"
    # a plain status report must still route to report, not project
    assert task_router.route("make a progress report for the team")["type"] == "report"


def test_no_orphan_agents_every_agent_reachable_by_some_task_type():
    """Every roster agent must be dispatched by at least one plan_for_type(), except the
    orchestrator, which is the conductor that runs the plan and is never a dispatched sub-agent."""
    all_agents = {a for agents in task_router.CMAP.values() for a in agents} - {"orchestrator"}
    routed = set()
    for typ, _, _ in task_router.TYPES:
        routed |= _agents(task_router.plan_for_type(typ))
    missing = all_agents - routed
    assert not missing, f"orphan agents never dispatched by any route: {sorted(missing)}"
