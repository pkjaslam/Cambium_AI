"""End-to-end run-board tests: DRIVE tools/run_state.py the real way, then render both HTML
boards (and the text board) and assert the recorded findings actually surface.

Why this file exists (the integration gap the unit tests missed): the older board tests
hand-BUILD the run_state dict with a 1-based `phase` (e.g. phase=2). But run_state.py `phase N`
stores N verbatim and the Orchestrator drives it 0-BASED -- the intake phase is `phase 0`. A
state written by the real driver at `phase 0` was classified as "waiting" by every 1-based
renderer, so the running phase's agents and their findings never rendered on EITHER HTML board.
These tests reproduce the real path end to end (subprocess -> run_state.json -> render) so that
regression cannot come back. Offline (task_router routing only), stdlib + tmp files.

Regression for: findings-from-map by agent id (audit #1/#2) AND the phase-cursor normalization
(a driver-written `phase 0` must render its running phase).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
RS = os.path.join(TOOLS, "run_state.py")
sys.path.insert(0, TOOLS)

import gen_board_pro as BP        # noqa: E402
import gen_inline_board as IB     # noqa: E402
import run_trace                  # noqa: E402

TASK = "draft an NSF proposal on soil-carbon monitoring"
F1 = "Fit found, 71 days to deadline"
F2 = "5 criteria, impacts weighted 30%"


def _rs(cwd, *args):
    """Run run_state.py in *cwd* exactly as the Orchestrator does (no hand-built dict)."""
    r = subprocess.run([sys.executable, RS, *args], cwd=cwd, capture_output=True, text=True)
    assert r.returncode == 0, f"run_state.py {args} failed: {r.stderr or r.stdout}"
    return r


def _drive_repro(cwd, second_status="done"):
    """The EXACT repro sequence, driven through run_state.py: reset -> phase 0 -> two findings.
    Returns the path to the run_state.json the driver wrote."""
    os.makedirs(os.path.join(cwd, "agent_outputs"), exist_ok=True)
    _rs(cwd, "reset", "--note", TASK)
    _rs(cwd, "phase", "0")
    _rs(cwd, "finding", "rfp-radar", F1)
    _rs(cwd, "finding", "rfp-analyst", F2, "--status", second_status)
    return os.path.join(cwd, "agent_outputs", "run_state.json")


def test_run_state_writes_zero_based_phase_and_plan():
    """Guard the premise: the real driver writes phase=0 (0-based) plus the routed plan and the
    findings/status maps -- the shape the boards must render. If run_state's contract changes,
    this fails loudly rather than the boards silently going blank again."""
    d = tempfile.mkdtemp()
    try:
        state = _drive_repro(d)
        st = json.load(open(state, encoding="utf-8"))
        assert st["phase"] == 0                     # driver is 0-based
        assert st.get("plan") and st["plan"]["phases"][0]["agents"], "reset must route a plan"
        # agents are BARE 3-tuples in the plan; findings/status live in the top-level maps
        assert len(st["plan"]["phases"][0]["agents"][0]) == 3
        assert st["findings"] == {"rfp-radar": F1, "rfp-analyst": F2}
        assert st["agent_status"]["rfp-radar"] == "done"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_phase_zero_state_renders_running_phase():
    """The core regression: a driver-written `phase 0` must resolve to a live ("now") phase,
    not "waiting". Uses the shared loader both boards go through."""
    d = tempfile.mkdtemp()
    try:
        state = _drive_repro(d)
        _dd, phases, cur, _note = BP.load(state)
        assert BP.status_of(0, cur) == "now", "phase 0 must render the first phase as running"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_findings_surface_on_both_boards_via_render():
    """render() on BOTH boards, fed the driver-written state, must contain both findings."""
    d = tempfile.mkdtemp()
    try:
        state = _drive_repro(d)
        pro = BP.render(state, TASK)
        inline = IB.render(state, TASK)
        for out, name in ((pro, "board_pro"), (inline, "inline_board")):
            assert F1 in out, f"{name} is missing the first finding"
            assert F2 in out, f"{name} is missing the second finding"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_findings_surface_on_both_boards_via_cli():
    """The literal repro: pipe each board CLI and grep the finding. gen_board_pro emits its HTML
    to stdout when piped; gen_inline_board writes its fragment to stdout by default."""
    d = tempfile.mkdtemp()
    try:
        state = _drive_repro(d)
        pro = subprocess.run([sys.executable, os.path.join(TOOLS, "gen_board_pro.py"),
                              "--state", state, "--stdout"], capture_output=True, text=True)
        inline = subprocess.run([sys.executable, os.path.join(TOOLS, "gen_inline_board.py"),
                                 "--state", state], capture_output=True, text=True)
        assert pro.returncode == 0 and inline.returncode == 0
        assert F1 in pro.stdout and F2 in pro.stdout, "gen_board_pro CLI did not print findings"
        assert F1 in inline.stdout and F2 in inline.stdout, "gen_inline_board CLI did not print findings"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_script_finding_is_escaped_end_to_end():
    """A finding containing markup, recorded through run_state.py, must be HTML-escaped on both
    boards (untrusted text; house rule). Driven the real way, not hand-built."""
    d = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(d, "agent_outputs"), exist_ok=True)
        _rs(d, "reset", "--note", TASK)
        _rs(d, "phase", "0")
        _rs(d, "finding", "rfp-radar", "<script>alert(1)</script>")
        state = os.path.join(d, "agent_outputs", "run_state.json")
        for out in (BP.render(state, TASK), IB.render(state, TASK)):
            assert "<script>alert(1)</script>" not in out, "raw script must not appear"
            assert "&lt;script&gt;" in out, "script must be HTML-escaped"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_text_board_agrees_on_counts_for_same_state():
    """The text board (run_trace --board), reading the SAME driver-written state, must report
    the same agent / council / gate counts as the plan the boards render (cross-surface
    agreement for a real phase-0 state)."""
    d = tempfile.mkdtemp()
    try:
        state = _drive_repro(d)
        st = json.load(open(state, encoding="utf-8"))
        phs = st["plan"]["phases"]
        n_ag = sum(len(p["agents"]) for p in phs)
        n_co = len({a[0] for p in phs for a in p["agents"]})
        n_gt = sum(1 for p in phs if p["gate"])

        text = run_trace.board_text(TASK, cur_phase=st["phase"], state=st)
        pro = BP.render(state, TASK)
        inline = IB.render(state, TASK)

        assert f"{n_ag} specialists" in text and f"{n_ag} specialists" in pro and f"{n_ag} agents" in inline
        assert f"{n_co} councils" in text and f"{n_co} councils" in pro and f"{n_co} councils" in inline
        assert f"{n_gt} human gate" in text and f"{n_gt} human gate" in pro and f"{n_gt} gate" in inline
        # and the text board shows the findings for the same state
        assert F1 in text and F2 in text
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_working_status_surfaces_finding_on_both_boards():
    """A finding recorded with --status working (agent still going) still renders on both boards
    inside the running phase, marked working (not queued)."""
    d = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(d, "agent_outputs"), exist_ok=True)
        _rs(d, "reset", "--note", TASK)
        _rs(d, "phase", "0")
        _rs(d, "finding", "rfp-radar", F1, "--status", "working")
        state = os.path.join(d, "agent_outputs", "run_state.json")
        pro = BP.render(state, TASK)
        inline = IB.render(state, TASK)
        assert F1 in pro and F1 in inline
        # board_pro tags the agent card class; inline shows a "working" chip
        assert re.search(r'class="agent working"[^>]*>(?:(?!</div>).)*?Rfp Radar', pro, re.S)
        assert ">working</div>" in inline
    finally:
        shutil.rmtree(d, ignore_errors=True)
