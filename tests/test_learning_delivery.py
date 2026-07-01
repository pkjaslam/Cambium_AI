"""Tests for tools/learning_delivery.py — learning delivery enforcement.

All tests use isolated tmp dirs; they never touch the live agent_outputs/.
"""
import glob as _glob
import json
import os
import subprocess
import sys
import tempfile
import shutil

# Make the tools/ directory importable
_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))
import learning_delivery as LD

SCRIPT = os.path.join(_REPO, "tools", "learning_delivery.py")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_root():
    """Return a fresh tmp directory that mimics the repo layout."""
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "agent_outputs"), exist_ok=True)
    return d


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def _run_state(root, phases, request="build a model"):
    """Write a minimal run_state.json under root/agent_outputs/."""
    state = {
        "plan": {
            "phases": phases,
            "request": request,
        }
    }
    path = os.path.join(root, "agent_outputs", "run_state.json")
    _write(path, json.dumps(state))
    return path


def _cli(root, extra_args=None):
    """Run `python3 learning_delivery.py check --root <root>` and return (returncode, stdout)."""
    cmd = [sys.executable, SCRIPT, "check", "--root", root]
    if extra_args:
        cmd.extend(extra_args)
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def _cli_deliver(root, extra_args=None):
    """Run `python3 learning_delivery.py deliver --root <root>` and return (returncode, stdout)."""
    cmd = [sys.executable, SCRIPT, "deliver", "--root", root]
    if extra_args:
        cmd.extend(extra_args)
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


# ---------------------------------------------------------------------------
# is_build_run unit tests
# ---------------------------------------------------------------------------

def test_is_build_run_phase_id_build():
    plan = {"phases": [{"id": "build"}], "request": "something"}
    assert LD.is_build_run(plan) is True


def test_is_build_run_phase_id_design():
    plan = {"phases": [{"id": "design"}], "request": "something"}
    assert LD.is_build_run(plan) is True


def test_is_build_run_phase_id_execution():
    plan = {"phases": [{"id": "execution"}], "request": "something"}
    assert LD.is_build_run(plan) is True


def test_is_build_run_phase_id_learn():
    plan = {"phases": [{"id": "learn"}], "request": "something"}
    assert LD.is_build_run(plan) is True


def test_is_build_run_phase_id_experiment():
    plan = {"phases": [{"id": "experiment"}], "request": "something"}
    assert LD.is_build_run(plan) is True


def test_is_build_run_request_pattern_build():
    plan = {"phases": [{"id": "intake"}], "request": "build a pipeline"}
    assert LD.is_build_run(plan) is True


def test_is_build_run_request_pattern_analy():
    plan = {"phases": [{"id": "intake"}], "request": "analyze this dataset"}
    assert LD.is_build_run(plan) is True


def test_is_build_run_request_pattern_model():
    plan = {"phases": [{"id": "intake"}], "request": "train a model"}
    assert LD.is_build_run(plan) is True


def test_is_build_run_request_pattern_develop():
    plan = {"phases": [{"id": "intake"}], "request": "develop the feature"}
    assert LD.is_build_run(plan) is True


def test_is_build_run_non_build_plan():
    plan = {"phases": [{"id": "intake"}, {"id": "closeout"}], "request": "write a memo"}
    assert LD.is_build_run(plan) is False


def test_is_build_run_empty_phases_no_request():
    plan = {"phases": [], "request": ""}
    assert LD.is_build_run(plan) is False


# ---------------------------------------------------------------------------
# learning_delivered unit tests
# ---------------------------------------------------------------------------

def test_learning_delivered_packet_filled():
    d = _make_root()
    try:
        packet = os.path.join(d, "agent_outputs", "learning_packet.md")
        _write(packet, "# Learning Packet\n\nWe built a service that does X.\n")
        ok, artifact = LD.learning_delivered(d)
        assert ok is True
        assert "learning_packet.md" in artifact
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_learning_delivered_packet_stub_not_filled():
    d = _make_root()
    try:
        packet = os.path.join(d, "agent_outputs", "learning_packet.md")
        _write(packet, "# Learning Packet\n\n__FILL__\n")
        ok, reason = LD.learning_delivered(d)
        assert ok is False
        assert "__FILL__" in reason
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_learning_delivered_no_artifact():
    d = _make_root()
    try:
        ok, reason = LD.learning_delivered(d)
        assert ok is False
        assert "does not exist" in reason or "no filled" in reason
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_learning_delivered_demo_lab():
    d = _make_root()
    try:
        lab = os.path.join(d, "demo", "learning_lab.html")
        _write(lab, "<html><body>A learning lab.</body></html>")
        ok, artifact = LD.learning_delivered(d)
        assert ok is True
        assert "learning_lab.html" in artifact
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_learning_delivered_academy_lab():
    d = _make_root()
    try:
        lab = os.path.join(d, "academy", "labs", "intro.html")
        _write(lab, "<html><body>Academy lab content.</body></html>")
        ok, artifact = LD.learning_delivered(d)
        assert ok is True
        assert "intro.html" in artifact
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_learning_delivered_academy_lab_with_fill_token_not_counted():
    d = _make_root()
    try:
        lab = os.path.join(d, "academy", "labs", "stub.html")
        _write(lab, "<html><body>__FILL__</body></html>")
        ok, reason = LD.learning_delivered(d)
        assert ok is False
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_learning_delivered_empty_packet_not_filled():
    d = _make_root()
    try:
        packet = os.path.join(d, "agent_outputs", "learning_packet.md")
        _write(packet, "")
        ok, reason = LD.learning_delivered(d)
        assert ok is False
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------------------
# CLI integration tests (subprocess)
# ---------------------------------------------------------------------------

def test_cli_build_plan_no_artifact_exits_1():
    d = _make_root()
    try:
        _run_state(d, [{"id": "build"}], "build a pipeline")
        rc, out = _cli(d)
        assert rc == 1, f"expected exit 1, got {rc}. output: {out}"
        assert "FAILED" in out
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_cli_build_plan_filled_packet_exits_0():
    d = _make_root()
    try:
        _run_state(d, [{"id": "build"}], "build a pipeline")
        packet = os.path.join(d, "agent_outputs", "learning_packet.md")
        _write(packet, "# Learning Packet\n\nWe built a pipeline that processes data.\n")
        rc, out = _cli(d)
        assert rc == 0, f"expected exit 0, got {rc}. output: {out}"
        assert "OK" in out
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_cli_build_plan_stub_with_fill_exits_1():
    d = _make_root()
    try:
        _run_state(d, [{"id": "build"}], "build a pipeline")
        packet = os.path.join(d, "agent_outputs", "learning_packet.md")
        _write(packet, "# Learning Packet\n\n__FILL__\n")
        rc, out = _cli(d)
        assert rc == 1, f"expected exit 1, got {rc}. output: {out}"
        assert "FAILED" in out
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_cli_non_build_plan_exits_0():
    d = _make_root()
    try:
        _run_state(
            d,
            [{"id": "intake"}, {"id": "closeout"}],
            request="write a memo"
        )
        rc, out = _cli(d)
        assert rc == 0, f"expected exit 0, got {rc}. output: {out}"
        assert "not a build/analysis run" in out
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_cli_missing_run_state_exits_0():
    d = _make_root()
    try:
        # no run_state.json written
        rc, out = _cli(d)
        assert rc == 0, f"expected exit 0 (cannot assess), got {rc}. output: {out}"
        assert "cannot assess" in out or "not found" in out
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_cli_academy_lab_counts_as_delivered():
    d = _make_root()
    try:
        _run_state(d, [{"id": "build"}], "build a pipeline")
        lab = os.path.join(d, "academy", "labs", "run_lab.html")
        _write(lab, "<html><body>A real lab with real content.</body></html>")
        rc, out = _cli(d)
        assert rc == 0, f"expected exit 0, got {rc}. output: {out}"
        assert "OK" in out
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_cli_demo_lab_counts_as_delivered():
    d = _make_root()
    try:
        _run_state(d, [{"id": "experiment"}], "run experiment")
        lab = os.path.join(d, "demo", "learning_lab.html")
        _write(lab, "<html><body>Demo lab content here.</body></html>")
        rc, out = _cli(d)
        assert rc == 0, f"expected exit 0, got {rc}. output: {out}"
        assert "OK" in out
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_cli_custom_state_path():
    d = _make_root()
    try:
        custom_state = os.path.join(d, "custom_state.json")
        state = {
            "plan": {
                "phases": [{"id": "build"}],
                "request": "build a model",
            }
        }
        _write(custom_state, json.dumps(state))
        packet = os.path.join(d, "agent_outputs", "learning_packet.md")
        _write(packet, "# Learning Packet\n\nWe built a model.\n")
        rc, out = _cli(d, ["--state", custom_state])
        assert rc == 0, f"expected exit 0, got {rc}. output: {out}"
        assert "OK" in out
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------------------
# deliver subcommand tests
# ---------------------------------------------------------------------------

def test_deliver_prints_packet_body():
    d = _make_root()
    try:
        packet = os.path.join(d, "agent_outputs", "learning_packet.md")
        _write(packet, "# Learning Packet\n\nWe built a pipeline that processes data.\n")
        rc, out = _cli_deliver(d)
        assert rc == 0, f"expected exit 0, got {rc}. output: {out}"
        assert "We built a pipeline that processes data." in out
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_deliver_missing_artifact_exits_1_with_clear_message():
    d = _make_root()
    try:
        rc, out = _cli_deliver(d)
        assert rc == 1, f"expected exit 1, got {rc}. output: {out}"
        assert "Cannot deliver" in out
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_deliver_stub_with_fill_exits_1():
    d = _make_root()
    try:
        packet = os.path.join(d, "agent_outputs", "learning_packet.md")
        _write(packet, "# Learning Packet\n\n__FILL__\n")
        rc, out = _cli_deliver(d)
        assert rc == 1, f"expected exit 1, got {rc}. output: {out}"
        assert "Cannot deliver" in out
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_check_behavior_unchanged_after_deliver_added():
    """Regression guard: adding `deliver` must not alter `check`'s existing exit codes/output."""
    d = _make_root()
    try:
        _run_state(d, [{"id": "build"}], "build a pipeline")
        rc, out = _cli(d)
        assert rc == 1
        assert "FAILED" in out
    finally:
        shutil.rmtree(d, ignore_errors=True)
