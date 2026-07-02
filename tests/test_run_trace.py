import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import run_trace

def test_mermaid_has_flow_gate_and_orchestrator():
    m = run_trace.mermaid("summarize this grant call and tell me whether to apply")
    assert "flowchart TD" in m and "\U0001f6a6" in m and "Orchestration" in m

def test_text_plan_lists_gate():
    t = run_trace.text("draft proposal")
    assert "Cambium plan" in t and "GATE" in t

def test_svg_renders_with_gate():
    s = run_trace.svg("summarize this grant call and tell me whether to apply")
    assert s.startswith("<svg") and s.rstrip().endswith("</svg>") and "GATE" in s

def test_status_board_marks_now_done_waiting():
    s = run_trace.status("draft the grant proposal", 4)
    assert s.startswith("<svg") and "NOW" in s and "✓" in s and "▶" in s and "○" in s
    t = run_trace.text("draft the grant proposal", 4)
    assert "✓" in t and "▶" in t and "○" in t


# --- SSOT + councils strip legibility (audit #3/#5, #7) ---
import json as _json, tempfile as _tmp, subprocess as _sub


def test_councils_strip_uses_white_circle_not_middot():
    """The not-started glyph must be the Unicode WHITE CIRCLE, not '.', which collides with
    the ' . ' separator and reads blank, e.g. 'Orchestration . . Labs' (audit #7)."""
    # non-live board (no phase) is the case that used to read blank
    t = run_trace.board_text("Build a web app dashboard", cur_phase=None)
    line = [l for l in t.splitlines() if l.strip().startswith("Councils:")][0]
    assert "○" in line, "councils strip must use WHITE CIRCLE for not-started"
    # and the strip must not degenerate to only separators/spaces after each council name
    assert "Orchestration ○" in line


def test_board_reads_plan_from_run_state_and_counts_match_router():
    """When run_state.json carries a plan (the SSOT), the text board renders THAT plan and
    its counts match the plan's own totals (audit #3/#5)."""
    import task_router
    task = "Build a web app dashboard"
    state = {"phase": 2, "note": task, "plan": task_router.plan_state(task),
             "findings": {}, "agent_status": {}}
    n_ag = sum(len(p["agents"]) for p in state["plan"]["phases"])
    n_gt = sum(1 for p in state["plan"]["phases"] if p["gate"])
    t = run_trace.board_text(task, cur_phase=2, state=state)
    assert f"{n_ag} specialists" in t
    assert f"{n_gt} human gate" in t


def test_no_agent_id_twice_in_a_single_phase_view():
    """Within any one phase, no agent id is rendered as a duplicate chip (audit #7)."""
    import task_router
    for p in task_router.plan_phases("Build a web app dashboard"):
        ids = [a[2] for a in p["agents"]]
        assert len(ids) == len(set(ids)), f"duplicate agent in phase {p['label']}: {ids}"


def test_cross_surface_count_agreement_from_one_run_state():
    """THE flagship check (audit #1/#3/#5): the text board and BOTH HTML boards, reading the
    SAME run_state.json, report identical agent / council / gate counts."""
    import task_router
    import gen_board_pro as BP
    import gen_inline_board as IB
    task = "Review the codebase for security vulnerabilities before release"
    state = {"phase": 2, "note": task, "plan": task_router.plan_state(task),
             "findings": {}, "agent_status": {}}
    f = _tmp.mktemp(suffix=".json"); _json.dump(state, open(f, "w"))

    # expected canonical counts from the ONE plan
    phs = state["plan"]["phases"]
    n_ag = sum(len(p["agents"]) for p in phs)
    n_co = len({a[0] for p in phs for a in p["agents"]})
    n_gt = sum(1 for p in phs if p["gate"])

    text = run_trace.board_text(task, cur_phase=2, state=state)
    pro = BP.render(f, task)
    inline = IB.render(f, task)

    assert f"{n_ag} specialists" in text and f"{n_ag} specialists" in pro and f"{n_ag} agents" in inline
    assert f"{n_co} councils" in text and f"{n_co} councils" in pro and f"{n_co} councils" in inline
    assert f"{n_gt} human gate" in text and f"{n_gt} human gate" in pro and f"{n_gt} gate" in inline
