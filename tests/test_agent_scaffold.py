"""tests/test_agent_scaffold.py -- retirement stub contract for tools/agent_scaffold.py.

The real behavior moved to tools/new_agent.py and tools/new_skill.py; the ported feature coverage lives in
tests/test_new_agent.py and tests/test_new_skill.py. This file only pins the stub contract:
pointer on stderr, exit code 3, legacy flags ignored.
"""
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
STUB = REPO_ROOT / "tools" / "agent_scaffold.py"


def run_stub(*args):
    return subprocess.run([sys.executable, str(STUB), *args],
                          capture_output=True, text=True)


def test_stub_exits_3_and_points_to_keeper():
    r = run_stub()
    assert r.returncode == 3
    assert "RETIRED: use tools/new_agent.py" in r.stderr


def test_stub_mentions_help_hint():
    r = run_stub()
    assert "--help" in r.stderr
    assert "one release" in r.stderr


def test_stub_ignores_legacy_flags_same_contract():
    r = run_stub("--kind", "agent", "--name", "x-y", "--description", "d", "--dir", "/tmp/x")
    assert r.returncode == 3
    assert "RETIRED" in r.stderr
