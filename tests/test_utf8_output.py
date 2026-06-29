"""test_utf8_output.py — verify the UTF-8 stdout/stderr guard is in place.

These tests are OS-agnostic (pass on Linux and Windows) and do NOT require a
narrow-encoding terminal.  They check two things:
  1. tools/cambium_io.py exists and reconfigures streams without raising.
  2. Every tool known to print non-ASCII glyphs imports cambium_io near the top.
"""
import ast
import importlib.util
import io
import os
import sys
import types

import pytest

TOOLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools")

# ── helpers ──────────────────────────────────────────────────────────────────

def _src(name):
    """Return source text of a file in tools/."""
    return open(os.path.join(TOOLS_DIR, name), encoding="utf-8").read()

def _imports_cambium_io(src):
    """True if 'import cambium_io' appears in the source (simple text check)."""
    return "import cambium_io" in src

# ── test 1: cambium_io.py itself ─────────────────────────────────────────────

def test_cambium_io_exists():
    p = os.path.join(TOOLS_DIR, "cambium_io.py")
    assert os.path.exists(p), "tools/cambium_io.py is missing"

def test_cambium_io_is_valid_python():
    src = _src("cambium_io.py")
    # ast.parse raises SyntaxError on bad files
    tree = ast.parse(src)
    assert tree is not None

def test_cambium_io_reconfigures_without_error():
    """Import cambium_io in process; it must not raise even on a StringIO stream."""
    # Swap stdout/stderr to StringIO (which lacks .reconfigure) to prove the
    # try/except swallows the AttributeError gracefully.
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    try:
        # Force a re-import by removing cached module if present
        if "cambium_io" in sys.modules:
            del sys.modules["cambium_io"]
        spec = importlib.util.spec_from_file_location(
            "cambium_io", os.path.join(TOOLS_DIR, "cambium_io.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)   # must not raise
    finally:
        sys.stdout = old_out
        sys.stderr = old_err

# ── test 2: every glyph-printing tool imports the guard ───────────────────────

GLYPH_TOOLS = [
    "gate_lock.py",
    "data_scan.py",
    "enforce.py",
    "roles_check.py",
    "run_trace.py",
    "cambium_start.py",
    "finding_audit.py",
    "gen_board_pro.py",
    "gate.py",
    "doctor.py",
    "consistency_check.py",
    "paper_search.py",
    "closeout.py",
    "mcp_discovery.py",
    "institution_profile.py",
    "audit_log.py",
    "run_state.py",
    "statusline.py",
    "handoff.py",
    "whoami.py",
]

@pytest.mark.parametrize("tool", GLYPH_TOOLS)
def test_tool_imports_cambium_io(tool):
    path = os.path.join(TOOLS_DIR, tool)
    if not os.path.exists(path):
        pytest.skip(f"{tool} not found in tools/")
    src = open(path, encoding="utf-8").read()
    assert _imports_cambium_io(src), (
        f"{tool} prints non-ASCII glyphs but does not 'import cambium_io'. "
        "Add 'import cambium_io  # noqa: F401' after the stdlib imports."
    )

@pytest.mark.parametrize("tool", GLYPH_TOOLS)
def test_tool_is_valid_python(tool):
    path = os.path.join(TOOLS_DIR, tool)
    if not os.path.exists(path):
        pytest.skip(f"{tool} not found in tools/")
    src = open(path, encoding="utf-8").read()
    ast.parse(src)   # raises SyntaxError if broken
