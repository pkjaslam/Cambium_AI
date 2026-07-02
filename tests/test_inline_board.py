"""gen_inline_board: the in-chat show_widget fragment reads the SAME run_state as the sidebar
board and renders findings, per-agent status, a collapsed 'Up next' strip, and deduped chips.

Regression guard for audit #1/#2 (findings come alive), #4 (queued wall collapsed), and #7
(no duplicate live chip). Offline, stdlib + tmp files only.
"""
import json, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import gen_inline_board as G

# reuse the same live-state shape the sidebar-board test uses
from test_board_pro import _LIVE_STATE


def _render():
    f = tempfile.mktemp(suffix=".json"); json.dump(_LIVE_STATE, open(f, "w"))
    return G.render(f, "Build a web app dashboard")


def test_findings_from_map_render_inline():
    h = _render()
    assert "shadcn/ui plus Vite beats rebuilding" in h
    assert "Chose a component-driven architecture" in h
    assert "Design is sound; flagged two risks" in h


def test_queued_wall_collapsed_inline():
    """A large not-started set must NOT emit one card per queued agent; it collapses into
    an 'Up next' strip (audit #4)."""
    h = _render()
    # real agent cards are <div class="cb-ag"> (not the .cb-ag CSS rule)
    n_cards = len(re.findall(r'<div class="cb-ag"[ >]', h))
    # only phase 1 (1 agent) + phase 2 (3 agents) render as cards; the rest collapse.
    assert n_cards == 4, f"expected 4 rendered cards, got {n_cards}"
    assert ">queued</div>" not in h        # no queued cards at all in this state
    assert "cb-upnext" in h and "Up next" in h
    assert "Execution (3)" in h            # collapsed council + count


def test_per_agent_status_inline():
    h = _render()
    assert h.count(">done</div>") == 2       # toolsmith (phase1 done) + lab-methods
    assert h.count(">working</div>") == 2    # lab-domain + faculty-expert


def test_no_duplicate_chip_inline():
    """lab-domain recurs across phases but renders once in a single view (audit #7)."""
    h = _render()
    assert len(re.findall(r'cb-ag".*?>Domain<', h, re.S)) == 1


def test_zero_findings_start_does_not_crash_inline():
    st = {"phase": None, "note": "fresh", "plan": _LIVE_STATE["plan"], "findings": {}, "agent_status": {}}
    f = tempfile.mktemp(suffix=".json"); json.dump(st, open(f, "w"))
    frag = G.render(f, "fresh")
    assert "Cambium" in frag and "cb-ag" in frag   # renders without raising


def test_finding_escaped_inline():
    st = {"phase": 2, "note": "x", "plan": {"phases": [
        {"council": "Labs", "label": "Design", "gate": None,
         "agents": [["Labs", "Methods", "lab-methods"]]}]},
        "findings": {"lab-methods": "<b>x</b>"}, "agent_status": {"lab-methods": "working"}}
    f = tempfile.mktemp(suffix=".json"); json.dump(st, open(f, "w"))
    h = G.render(f, "x")
    assert "<b>x</b>" not in h and "&lt;b&gt;" in h


def test_cli_writes_fragment():
    f = tempfile.mktemp(suffix=".json"); json.dump(_LIVE_STATE, open(f, "w"))
    out = tempfile.mktemp(suffix=".html")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "gen_inline_board.py"),
                        "--state", f, "--out", out], capture_output=True, text=True)
    assert r.returncode == 0 and os.path.exists(out)
    assert "Cambium" in open(out, encoding="utf-8").read()
