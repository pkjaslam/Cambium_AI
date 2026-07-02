"""Test that run_state reset stamps started_at and sync ignores stale prior-run files.
Regression guard for the cross-run findings leak (boards showing a previous run's findings)."""
import json, os, subprocess, sys, time, tempfile, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RS = os.path.join(ROOT, "tools", "run_state.py")


def _run(cwd, *args):
    return subprocess.run([sys.executable, RS, *args], cwd=cwd,
                          capture_output=True, text=True)


def test_reset_stamps_started_at_and_clears():
    d = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(d, "agent_outputs"))
        _run(d, "reset", "--note", "fresh")
        st = json.load(open(os.path.join(d, "agent_outputs", "run_state.json")))
        assert st["findings"] == {}
        assert st["note"] == "fresh"
        assert "started_at" in st and st["started_at"] > 0
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_sync_ignores_stale_files_from_earlier_runs():
    d = tempfile.mkdtemp()
    try:
        ao = os.path.join(d, "agent_outputs"); os.makedirs(ao)
        # a STALE file from a "previous run" (old mtime)
        stale = os.path.join(ao, "old-agent.md")
        open(stale, "w").write("## Decision\nstale finding from a previous run\n")
        os.utime(stale, (time.time() - 9999, time.time() - 9999))
        # reset stamps started_at = now
        _run(d, "reset", "--note", "new run")
        # a FRESH file written after reset
        open(os.path.join(ao, "new-agent.md"), "w").write("## Decision\nfresh finding\n")
        _run(d, "sync")
        st = json.load(open(os.path.join(ao, "run_state.json")))
        assert "new-agent" in st["findings"], "fresh file should be synced"
        assert "old-agent" not in st["findings"], "stale prior-run file must be ignored"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_phase_prints_repaint_reminder():
    """`phase N` must print a RE-PAINT banner so the in-chat board never silently goes stale."""
    d = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(d, "agent_outputs"))
        r = _run(d, "phase", "2", "--note", "Scouts surveying")
        assert "RE-PAINT THE BOARD NOW" in r.stdout
        # existing phase-update output must still be present (no removal of prior behavior)
        assert "phase=2" in r.stdout
        st = json.load(open(os.path.join(d, "agent_outputs", "run_state.json")))
        assert st["phase"] == 2
    finally:
        shutil.rmtree(d, ignore_errors=True)


# --- SSOT plan writing + findings/status + quiet repaint (audit #1/#2/#9) ---

def test_reset_writes_the_routed_plan():
    """reset --note TASK routes TASK and writes the plan into run_state.json, making it the
    single source of truth for plan + progress + findings (audit #1)."""
    d = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(d, "agent_outputs"))
        _run(d, "reset", "--note", "Build a web app dashboard")
        st = json.load(open(os.path.join(d, "agent_outputs", "run_state.json")))
        assert st.get("plan"), "reset must write a plan block"
        assert st["plan"]["type"] == "software"
        assert len(st["plan"]["phases"]) >= 3
        # each phase carries council + agents [council, role, id]
        p0 = st["plan"]["phases"][0]
        assert "council" in p0 and "agents" in p0
        assert len(p0["agents"][0]) >= 3
        assert "agent_status" in st and "findings" in st
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_finding_sets_status_done_and_status_cmd_sets_state():
    """`finding <agent> "..."` records the finding AND marks the agent done; `status` sets a
    live status without a finding (audit #2)."""
    d = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(d, "agent_outputs"))
        _run(d, "reset", "--note", "Build a web app dashboard")
        _run(d, "finding", "lab-methods", "Chose a component-driven architecture")
        _run(d, "status", "lab-domain", "working")
        st = json.load(open(os.path.join(d, "agent_outputs", "run_state.json")))
        assert st["findings"]["lab-methods"] == "Chose a component-driven architecture"
        assert st["agent_status"]["lab-methods"] == "done"
        assert st["agent_status"]["lab-domain"] == "working"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_phase_repaint_is_quiet_by_default():
    """`phase N` prints a ONE-LINE repaint nudge with the exact command, NOT the full HTML
    board fragment (audit #9). The fragment only appears with --emit."""
    d = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(d, "agent_outputs"))
        r = _run(d, "phase", "2")
        # the nudge and the command are present
        assert "RE-PAINT THE BOARD NOW" in r.stdout
        assert "gen_inline_board.py" in r.stdout
        # but NOT the HTML fragment (no board markup dumped into the transcript)
        for marker in ("<div", "<style", "cb-ag", "<!doctype"):
            assert marker not in r.stdout, f"quiet repaint leaked HTML marker: {marker}"
        # and the whole output stays small (a nudge, not a 16KB fragment)
        assert len(r.stdout) < 800
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_phase_emit_flag_prints_fragment():
    """With --emit, the caller explicitly opts into the inline board fragment."""
    d = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(d, "agent_outputs"))
        _run(d, "reset", "--note", "Build a web app dashboard")
        r = _run(d, "phase", "2", "--emit")
        assert "RE-PAINT THE BOARD NOW" in r.stdout
        # the fragment (or its container) is present when explicitly requested
        assert ("cb-ag" in r.stdout) or ("board fragment" in r.stdout)
    finally:
        shutil.rmtree(d, ignore_errors=True)
