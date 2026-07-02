"""Accessibility (WCAG 2.1 AA) regression guard for the HTML renderers.

For each surface that emits HTML - the gate card, the sidebar run board, the in-chat board, the
benchmark dashboard, and the static command center - assert the a11y features added in the WCAG pass
are present: a visually-hidden sr-only summary, a prefers-reduced-motion media query, a focus-visible
rule, semantic role/aria attributes, aria-live on the live boards, keyboard-operable gate buttons, and
that user-supplied text stays HTML-escaped. Offline; stdlib + tmp files only.
"""
import json, os, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import gen_gate_card as GC
import gen_board_pro as BP
import gen_inline_board as IB
import gen_dashboard as GD

Q = chr(34)
ROLE_LIST = "role=" + Q + "list" + Q
ROLE_LISTITEM = "role=" + Q + "listitem" + Q
ROLE_GROUP = "role=" + Q + "group" + Q
ROLE_REGION = "role=" + Q + "region" + Q
ARIA_LIVE = "aria-live=" + Q + "polite" + Q
RM = "prefers-reduced-motion"
SR_HIDE = "position:absolute;width:1px;height:1px"

_STATE = {
    "phase": 2, "note": "Design underway",
    "plan": {"type": "software", "request": "Build a web app dashboard", "phases": [
        {"council": "Support", "label": "Provision",
         "agents": [["Support", "Toolsmith", "toolsmith"]],
         "gate": {"id": "G-provision", "decision": "approve the toolchain?"}},
        {"council": "Labs", "label": "Design", "gate": None,
         "agents": [["Labs", "Methods", "lab-methods"], ["Labs", "Domain", "lab-domain"]]},
        {"council": "Verification", "label": "Verify",
         "agents": [["Verification", "Evidence", "verify-evidence"]],
         "gate": {"id": "G-build", "decision": "accept the build?"}}]},
    "findings": {"toolsmith": "shadcn/ui plus Vite beats rebuilding",
                 "lab-methods": "Chose a component-driven architecture"},
    "agent_status": {"toolsmith": "done", "lab-methods": "done", "lab-domain": "working"},
    "gate": {"id": "G-build", "decision": "accept the build?"}}

def _state_file():
    f = tempfile.mktemp(suffix=".json"); json.dump(_STATE, open(f, "w")); return f

def _board_pro():
    return BP.render(_state_file(), "Build a web app dashboard")

def _inline():
    return IB.render(_state_file(), "Build a web app dashboard")

def _gate():
    return GC.build_gate_card("G-7", "Ship the draft budget?", {"decision_needed": "Decide now."})

def _dash_stub():
    return {k: "x" for k in ("grade","tests","skipped","gauntlet","agents","councils","gates",
            "grounded","checks_total","model_judged","tools","policy_enforced","leads","partial",
            "gap","t_fcr","t_n","t_ci","b_fcr","b_n","b_ci","h","p","diff","diff_ci",
            "cite_t","cite_tn","cite_b","cite_bn")}

def _dashboard_html():
    return open(os.path.join(ROOT, "dashboard.html"), encoding="utf-8").read()

def _has_sr_only_that_hides(h):
    assert "sr-only" in h, "no sr-only element/class"
    assert SR_HIDE in h, "sr-only CSS must actually hide (clip-rect pattern)"
    assert "clip:rect(0 0 0 0)" in h

def _has_sendprompt(h):
    for verb in ("APPROVE", "REVISE", "REJECT"):
        assert ("sendPrompt(" + chr(39) + verb) in h

# --- gate card ---
def test_gate_sr_only_summary():
    _has_sr_only_that_hides(_gate())

def test_gate_reduced_motion_and_focus_visible():
    h = _gate(); assert RM in h and "focus-visible" in h

def test_gate_region_role_and_aria_label():
    h = _gate(); assert ROLE_GROUP in h and "aria-label=" in h

def test_gate_buttons_keyboard_operable():
    h = _gate(); _has_sendprompt(h); assert h.count("<button") >= 3

def test_gate_user_text_escaped():
    h = GC.build_gate_card("G-7", "<script>alert(1)</script>", {})
    assert "<script>alert(1)</script>" not in h and "&lt;script&gt;" in h

# --- sidebar board ---
def test_board_pro_sr_only_summary():
    _has_sr_only_that_hides(_board_pro())

def test_board_pro_reduced_motion_and_focus_visible():
    h = _board_pro(); assert RM in h and "focus-visible" in h

def test_board_pro_list_semantics_and_live():
    h = _board_pro(); assert ROLE_LIST in h and ROLE_LISTITEM in h and ARIA_LIVE in h

def test_board_pro_status_label_not_color_only():
    h = _board_pro(); assert "working" in h and "done" in h

def test_board_pro_finding_escaped():
    st = {"phase": 2, "note": "x", "plan": {"phases": [
        {"council": "Labs", "label": "Design", "gate": None,
         "agents": [["Labs", "Methods", "lab-methods"]]}]},
        "findings": {"lab-methods": "<script>alert(1)</script>"},
        "agent_status": {"lab-methods": "working"}}
    f = tempfile.mktemp(suffix=".json"); json.dump(st, open(f, "w"))
    h = BP.render(f, "x")
    assert "<script>alert(1)</script>" not in h and "&lt;script&gt;" in h

# --- in-chat board ---
def test_inline_sr_only_summary():
    _has_sr_only_that_hides(_inline())

def test_inline_reduced_motion_and_focus_visible():
    h = _inline(); assert RM in h and "focus-visible" in h

def test_inline_list_semantics_and_live():
    h = _inline(); assert ROLE_LIST in h and ROLE_LISTITEM in h and ARIA_LIVE in h

def test_inline_gate_buttons_keyboard_operable():
    h = _inline(); _has_sendprompt(h); assert h.count("<button") >= 3

def test_inline_finding_escaped():
    st = {"phase": 2, "note": "x", "plan": {"phases": [
        {"council": "Labs", "label": "Design", "gate": None,
         "agents": [["Labs", "Methods", "lab-methods"]]}]},
        "findings": {"lab-methods": "<b>x</b>"}, "agent_status": {"lab-methods": "working"}}
    f = tempfile.mktemp(suffix=".json"); json.dump(st, open(f, "w"))
    h = IB.render(f, "x")
    assert "<b>x</b>" not in h and "&lt;b&gt;" in h

# --- benchmark dashboard ---
def test_dashboard_gen_sr_only_summary():
    _has_sr_only_that_hides(GD.render(_dash_stub()))

def test_dashboard_gen_reduced_motion_and_focus_visible():
    h = GD.render(_dash_stub()); assert RM in h and "focus-visible" in h

def test_dashboard_gen_region_role():
    h = GD.render(_dash_stub()); assert ROLE_REGION in h and "aria-label=" in h

# --- static command center ---
def test_static_dashboard_sr_only_summary():
    _has_sr_only_that_hides(_dashboard_html())

def test_static_dashboard_reduced_motion_and_focus_visible():
    h = _dashboard_html(); assert RM in h and "focus-visible" in h

def test_static_dashboard_reduced_motion_gates_autoadvance():
    h = _dashboard_html(); assert "matchMedia" in h and "prefers-reduced-motion: reduce" in h

def test_static_dashboard_cards_keyboard_operable():
    h = _dashboard_html()
    assert "role" + chr(39) + "," + chr(39) + "button" in h
    assert "tabIndex=0" in h and "onkeydown" in h and "aria-expanded" in h

def test_static_dashboard_live_and_list_semantics():
    h = _dashboard_html()
    assert ARIA_LIVE in h and ROLE_LIST in h
    assert "role" + chr(39) + "," + chr(39) + "listitem" in h
