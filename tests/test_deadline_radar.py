"""tests/test_deadline_radar.py -- retirement stub contract for tools/deadline_radar.py.

The real behavior moved to tools/award_calendar.py; the ported feature coverage lives in
tests/test_award_calendar.py. This file only pins the stub contract:
pointer on stderr, exit code 3, legacy flags ignored.
"""
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
STUB = REPO_ROOT / "tools" / "deadline_radar.py"


def run_stub(*args):
    return subprocess.run([sys.executable, str(STUB), *args],
                          capture_output=True, text=True)


def test_stub_exits_3_and_points_to_keeper():
    r = run_stub()
    assert r.returncode == 3
    assert "RETIRED: use tools/award_calendar.py" in r.stderr


def test_stub_mentions_help_hint():
    r = run_stub()
    assert "--help" in r.stderr
    assert "one release" in r.stderr


def test_stub_ignores_legacy_flags_same_contract():
    r = run_stub("--add", "name=X,funder=Y,deadline=2026-12-01")
    assert r.returncode == 3
    assert "RETIRED" in r.stderr
