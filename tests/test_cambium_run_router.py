"""Tests for cambium_run.py's router-driven phase plan (the phases.yml <-> route() disconnect fix).

Proves: (1) the router_plan_to_phases adapter faithfully carries route()'s phase count and gate
ids into the shape cambium_run's main() loop executes; (2) agent_groups() reads the adapter's
"groups" shape identically to how it reads phases.yml's legacy fixed-key shape; (3) load_plan()
picks phases.yml by default when present, --from-router when asked, and route() as an auto-detect
fallback when phases.yml is absent; (4) none of this touches gate_lock token minting/verification
-- only tests plan-building. No live API calls anywhere in this file.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import cambium_run as cr
import task_router as tr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_router_plan_to_phases_preserves_phase_count():
    route_result = tr.route("a software task")
    adapted = cr.router_plan_to_phases(route_result)
    assert len(adapted) == len(route_result["phases"])


def test_router_plan_to_phases_preserves_gate_ids_in_order():
    route_result = tr.route("a software task")
    adapted = cr.router_plan_to_phases(route_result)
    expected_gate_ids = [p["gate"]["id"] for p in route_result["phases"] if p.get("gate")]
    actual_gate_ids = [p["gate"]["id"] for p in adapted if p.get("gate")]
    assert actual_gate_ids == expected_gate_ids
    assert len(expected_gate_ids) > 0  # sanity: software plan does carry gates


def test_router_plan_to_phases_preserves_phase_ids_in_order():
    route_result = tr.route("a software task")
    adapted = cr.router_plan_to_phases(route_result)
    assert [p["id"] for p in adapted] == [p["id"] for p in route_result["phases"]]


def test_router_plan_to_phases_fills_default_approver():
    route_result = tr.route("a software task")
    adapted = cr.router_plan_to_phases(route_result)
    for p in adapted:
        if p.get("gate"):
            assert p["gate"]["approver"]  # never empty/missing


def test_router_plan_to_phases_no_gate_stays_none_not_missing_key():
    route_result = tr.route("a software task")
    adapted = cr.router_plan_to_phases(route_result)
    for p in adapted:
        assert "gate" in p  # key always present
        if route_result["phases"][adapted.index(p)].get("gate") is None:
            assert p["gate"] is None


def test_agent_groups_reads_router_shape_same_as_legacy_shape():
    # router/adapter shape: {"groups": [{"label","parallel","agents"}]}
    router_phase = {"id": "x", "groups": [
        {"label": "scouts", "parallel": True, "agents": ["a", "b", "c"]},
        {"label": "faculty", "parallel": False, "agents": ["d"]},
    ]}
    out = cr.agent_groups(router_phase)
    assert out == [("scouts", ["a", "b", "c"], True), ("faculty", ["d"], False)]

    # legacy phases.yml shape: fixed keys directly on the phase dict
    legacy_phase = {"id": "y", "parallel": ["a", "b", "c"], "consult": ["d"]}
    out2 = cr.agent_groups(legacy_phase)
    assert out2 == [("parallel", ["a", "b", "c"], True), ("consult", ["d"], False)]


def test_agent_groups_single_agent_group_is_not_marked_concurrent():
    # a "parallel" group with only one agent should not be flagged concurrent (matches
    # legacy behavior: conc = "parallel" in key AND len(ags) > 1 is checked by callers,
    # but agent_groups itself also encodes this for the router shape).
    router_phase = {"id": "x", "groups": [{"label": "solo", "parallel": True, "agents": ["a"]}]}
    out = cr.agent_groups(router_phase)
    assert out == [("solo", ["a"], False)]


def test_load_plan_uses_phases_yml_by_default_when_present():
    assert os.path.exists(os.path.join(ROOT, "phases.yml")), "this test assumes phases.yml ships in the repo"
    plan, routed_type = cr.load_plan("wildlife corridor", [])
    assert routed_type is None  # phases.yml path never sets a routed_type
    ids = [p["id"] for p in plan["phases"]]
    assert ids == ["intake", "ideation", "proposal", "development", "reporting"]


def test_load_plan_from_router_flag_builds_from_route():
    plan, routed_type = cr.load_plan("build a dashboard app", ["--from-router"])
    route_result = tr.route("build a dashboard app")
    assert routed_type == route_result["type"] == "software"
    assert len(plan["phases"]) == len(route_result["phases"])
    assert [p["id"] for p in plan["phases"]] == [p["id"] for p in route_result["phases"]]
    gate_ids_plan = [p["gate"]["id"] for p in plan["phases"] if p.get("gate")]
    gate_ids_route = [p["gate"]["id"] for p in route_result["phases"] if p.get("gate")]
    assert gate_ids_plan == gate_ids_route


def test_load_plan_auto_detects_router_when_phases_yml_missing(tmp_path, monkeypatch):
    # simulate a checkout without phases.yml by pointing cr.ROOT at an empty temp dir
    monkeypatch.setattr(cr, "ROOT", str(tmp_path))
    plan, routed_type = cr.load_plan("clean the dataset", [])
    route_result = tr.route("clean the dataset")
    assert routed_type == route_result["type"] == "data"
    assert [p["id"] for p in plan["phases"]] == [p["id"] for p in route_result["phases"]]


def test_load_plan_from_router_covers_non_grant_task_types():
    # this is the core fix: task types other than grant/research now get a real phase plan,
    # not silently falling through to phases.yml's grant/research-only shape.
    for task, expected_type in [
        ("audit and harden this codebase", "review"),
        ("clean the dataset", "data"),
        ("write the annual report", "report"),
    ]:
        plan, routed_type = cr.load_plan(task, ["--from-router"])
        route_result = tr.route(task)
        assert routed_type == expected_type == route_result["type"]
        assert len(plan["phases"]) == len(route_result["phases"])
        for p_plan, p_route in zip(plan["phases"], route_result["phases"]):
            assert p_plan["id"] == p_route["id"]
            groups_plan = cr.agent_groups(p_plan)
            groups_route_labels = [g["label"] for g in p_route["groups"]]
            assert [g[0] for g in groups_plan] == groups_route_labels
