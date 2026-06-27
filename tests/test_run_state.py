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
