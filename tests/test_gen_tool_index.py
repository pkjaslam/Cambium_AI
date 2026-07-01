"""tests/test_gen_tool_index.py

Tests for tools/gen_tool_index.py.

1. extract_purpose() returns a non-empty purpose for a sample "name -- purpose"
   docstring.
2. The generated markdown (render_markdown over a real scan of tools/) contains
   a known tool name, budget_review.py.

Uses tmp dirs only where file I/O is needed; the module is loaded directly
from its file path so the test does not depend on tools/ being on sys.path.
"""

import importlib.util
import pathlib
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL_PATH = REPO_ROOT / "tools" / "gen_tool_index.py"


def _load_gen_tool_index():
    spec = importlib.util.spec_from_file_location("gen_tool_index", TOOL_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gti = _load_gen_tool_index()


# ---------------------------------------------------------------------------
# Test 1: extractor returns a non-empty purpose for a sample docstring
# ---------------------------------------------------------------------------

def test_extract_purpose_returns_non_empty_for_sample_docstring():
    sample_source = '''"""sample_tool -- do the one thing this tool does well.

More detail below that should be ignored for the one-line purpose.
"""
import os
'''
    purpose = gti.extract_purpose(sample_source, "sample_tool.py")
    assert isinstance(purpose, str)
    assert purpose.strip() != ""
    assert purpose == "do the one thing this tool does well."


def test_extract_purpose_falls_back_to_filename_when_no_docstring():
    sample_source = "import os\nprint('no docstring here')\n"
    purpose = gti.extract_purpose(sample_source, "mystery_tool.py")
    assert purpose == "mystery_tool"


def test_extract_purpose_falls_back_to_filename_for_empty_docstring():
    sample_source = '"""   """\nimport os\n'
    purpose = gti.extract_purpose(sample_source, "blank_tool.py")
    assert purpose == "blank_tool"


# ---------------------------------------------------------------------------
# Test 2: generated markdown contains a known tool name (budget_review)
# ---------------------------------------------------------------------------

def test_generated_markdown_contains_known_tool_name():
    rows = gti.build_inventory()
    names = [name for name, _purpose in rows]
    assert "budget_review.py" in names, "budget_review.py should be discovered in tools/"

    markdown = gti.render_markdown(rows)
    assert "budget_review.py" in markdown


def test_generator_skips_itself_and_init():
    rows = gti.build_inventory()
    names = {name for name, _purpose in rows}
    assert "gen_tool_index.py" not in names
    assert "__init__.py" not in names


def test_render_markdown_uses_tmp_scanned_dir():
    """Build a small fake tools/ dir in a tmp dir and confirm discovery + purpose
    extraction work against it directly (isolated from the real repo)."""
    with tempfile.TemporaryDirectory() as td:
        tmp_tools = pathlib.Path(td)
        (tmp_tools / "gen_tool_index.py").write_text("# self, should be skipped\n", encoding="utf-8")
        (tmp_tools / "__init__.py").write_text("", encoding="utf-8")
        (tmp_tools / "widget_maker.py").write_text(
            '"""widget_maker -- build a widget from a spec."""\n', encoding="utf-8"
        )

        original_tools_dir = gti.TOOLS_DIR
        gti.TOOLS_DIR = tmp_tools
        try:
            rows = gti.build_inventory()
        finally:
            gti.TOOLS_DIR = original_tools_dir

        assert rows == [("widget_maker.py", "build a widget from a spec.")]

        markdown = gti.render_markdown(rows)
        assert "widget_maker.py" in markdown
        assert "build a widget from a spec." in markdown


def test_no_em_dashes_in_generated_markdown():
    rows = gti.build_inventory()
    markdown = gti.render_markdown(rows)
    EM_DASH = "—"
    assert EM_DASH not in markdown, "Em dash found in TOOL_INDEX.md output -- use a hyphen instead."
