"""gen_board_pro: the premium run board renders from real run state, all placeholders filled."""
import json, os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import gen_board_pro as B

STATE = {"phase": 2, "note": "verification underway",
 "plan": {"type": "cambium", "request": "Test request",
  "phases": [
   {"council": "Execution", "label": "Build it", "agents": [["Execution","Research Engineer","research-engineer","did the thing"]]},
   {"council": "Verification", "label": "Check it", "agents": [["Verification","Evidence","verify-evidence"]],
    "gate": {"id": "G-test", "decision": "Ship it?"}},
   {"council": "Support", "label": "Close out", "agents": [["Support","Record Keeper","record-keeper"]]}]}}

def _render():
    f = tempfile.mktemp(suffix=".json"); json.dump(STATE, open(f, "w"))
    return B.render(f, "Test request")

def test_renders_full_html_no_placeholders():
    h = _render()
    assert h.startswith("<!doctype html") and "CAMBIUM INSTITUTE" in h
    assert "{req}" not in h and "{pct}" not in h and "{cards}" not in h

def test_status_done_now_waiting():
    # phase index 0 done (cur=2>1), index 1 now (cur==2), index 2 waiting
    assert B.status_of(0, 2) == "done" and B.status_of(1, 2) == "now" and B.status_of(2, 2) == "waiting"

def test_active_gate_card_shown_when_pending():
    h = _render()
    assert "GATE G-test - your decision" in h and "Ship it?" in h
    assert "APPROVE" in h and "REVISE" in h and "REJECT" in h

def test_agent_finding_rendered():
    assert "did the thing" in _render()

def test_progress_reflects_done_phases():
    # 1 of 3 done -> 33%
    h = _render(); assert "33%" in h

def test_cli_writes_file():
    f = tempfile.mktemp(suffix=".json"); json.dump(STATE, open(f, "w"))
    out = tempfile.mktemp(suffix=".html")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "gen_board_pro.py"),
                        "--state", f, "--out", out], capture_output=True, text=True)
    assert r.returncode == 0 and os.path.exists(out) and "CAMBIUM" in open(out).read()


# --- live-board upgrades: findings-from-map merge, per-agent status, collapsed queued ---

# A run_state with a PLAN (the SSOT shape run_state.py writes) + findings recorded via the
# findings map (as `run_state.py finding <agent> "..."` does), NOT embedded in the agent tuples.
_LIVE_STATE = {
    "phase": 2, "note": "Design underway",
    "plan": {"type": "software", "request": "Build a web app dashboard", "phases": [
        {"council": "Support", "label": "Provision",
         "agents": [["Support", "Toolsmith", "toolsmith"]],
         "gate": {"id": "G-provision", "decision": "approve the toolchain?", "kind": "Checkpoint"}},
        {"council": "Labs", "label": "Design", "gate": None,
         "agents": [["Labs", "Methods", "lab-methods"], ["Labs", "Domain", "lab-domain"],
                    ["Faculty", "Faculty Expert", "faculty-expert"]]},
        {"council": "Execution", "label": "Build", "gate": None,
         "agents": [["Execution", "Experiments", "exec-experiments"],
                    ["Execution", "Ablation", "exec-ablation"],
                    ["Execution", "Research Engineer", "research-engineer"]]},
        {"council": "Verification", "label": "Verify",
         "agents": [["Verification", "Evidence", "verify-evidence"], ["Labs", "Domain", "lab-domain"]],
         "gate": {"id": "G-build", "decision": "accept the build?", "kind": "Checkpoint"}}]},
    "findings": {
        "toolsmith": "shadcn/ui plus Vite beats rebuilding",
        "lab-methods": "Chose a component-driven architecture",
        "faculty-expert": "Design is sound; flagged two risks"},
    "agent_status": {"lab-methods": "done", "lab-domain": "working", "faculty-expert": "working",
                     "toolsmith": "done"},
}


def _render_live():
    f = tempfile.mktemp(suffix=".json"); json.dump(_LIVE_STATE, open(f, "w"))
    return B.render(f, "Build a web app dashboard")


def test_findings_from_map_render_in_board_pro():
    """Findings recorded via run_state.py's findings map (not embedded in the plan) must
    surface on the board -- this is the audit #1/#2 fix (findings come alive)."""
    h = _render_live()
    assert "shadcn/ui plus Vite beats rebuilding" in h
    assert "Chose a component-driven architecture" in h
    assert "Design is sound; flagged two risks" in h


def test_per_agent_status_inside_running_phase():
    """Within the running phase, each agent reads its OWN status: a done agent shows done,
    a working agent shows working (audit #2)."""
    h = _render_live()
    import re
    seg = re.search(r"Phase 2.*?</section>", h, re.S).group(0)
    def cls(role):
        m = re.search(r'agent (done|working|queued)[^>]*>(?:(?!</div>).)*?' + re.escape(role), seg, re.S)
        return m.group(1) if m else None
    assert cls("Methods") == "done"        # lab-methods status=done
    assert cls("Domain") == "working"      # lab-domain status=working
    assert cls("Faculty Expert") == "working"


def test_queued_phases_collapse_to_upnext_strip():
    """Not-yet-started phases collapse into a compact 'Up next' strip instead of one card
    per queued agent (audit #4)."""
    h = _render_live()
    assert "Up next" in h and 'class="upnext"' in h
    # the Build phase (phase 3, waiting) must NOT emit its agents as full cards
    assert "cambium-institute:exec-ablation" not in h
    assert "cambium-institute:exec-experiments" not in h
    # its council appears in the strip with a count instead
    assert "Execution (3)" in h


def test_no_duplicate_agent_chip_in_a_single_view():
    """lab-domain recurs across design + verify, but the rendered view shows its chip once
    (audit #7 dedup)."""
    assert _render_live().count("cambium-institute:lab-domain") == 1


def test_atype_is_dispatchable_id():
    """The agent type line is the dispatchable cambium-institute:<id>, and the id is BARE."""
    assert "cambium-institute:lab-methods" in _render_live()


def test_zero_findings_just_started_run_does_not_crash():
    """A just-started run (plan present, no findings, phase None) still renders (constraint)."""
    st = {"phase": None, "note": "fresh", "plan": _LIVE_STATE["plan"], "findings": {}, "agent_status": {}}
    f = tempfile.mktemp(suffix=".json"); json.dump(st, open(f, "w"))
    h = B.render(f, "fresh")
    assert h.startswith("<!doctype html") and "{cards}" not in h


def test_finding_text_is_escaped():
    """Findings are untrusted-ish and must be HTML-escaped (constraint)."""
    st = {"phase": 2, "note": "x", "plan": {"phases": [
        {"council": "Labs", "label": "Design", "gate": None,
         "agents": [["Labs", "Methods", "lab-methods"]]}]},
        "findings": {"lab-methods": "<script>alert(1)</script>"},
        "agent_status": {"lab-methods": "working"}}
    f = tempfile.mktemp(suffix=".json"); json.dump(st, open(f, "w"))
    h = B.render(f, "x")
    assert "<script>alert(1)</script>" not in h
    assert "&lt;script&gt;" in h
