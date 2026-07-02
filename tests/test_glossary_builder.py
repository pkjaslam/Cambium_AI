"""Tests for tools/glossary_builder.py. Synthetic markdown in tmp_path; offline."""
import os
import subprocess
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))
import glossary_builder as GB

SCRIPT = os.path.join(_REPO, "tools", "glossary_builder.py")

DOC_A = """# Notes on governance

A **gate** is a checkpoint where the run pauses for a human decision.
The `orchestrator` refers to the chief of staff that dispatches specialists.

- Zebra term: a deliberately late-alphabet entry for ordering checks.

## Evidence tier

Evidence tier means the grade of support behind a claim. Second sentence here.
"""

DOC_B = """# Other notes

An **agent** is a named specialist with a single job.

Note: this label line must be skipped.
"""


def _run(args):
    r = subprocess.run([sys.executable, SCRIPT] + args, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def _write(tmp_path):
    d = tmp_path / "docs"
    d.mkdir()
    (d / "a.md").write_text(DOC_A, encoding="utf-8")
    (d / "b.md").write_text(DOC_B, encoding="utf-8")
    return d


def test_help_exits_zero():
    rc, out, _ = _run(["--help"])
    assert rc == 0
    assert "--quiz" in out


def test_rules_and_banner(tmp_path):
    d = _write(tmp_path)
    rc, out, _ = _run(["--sources", str(d)])
    assert rc == 0
    assert "auto-extracted, review before teaching" in out
    assert "- **gate**: is a checkpoint" in out            # bold + is
    assert "- **orchestrator**: refers to the chief" in out  # code + refers to
    assert "- **Zebra term**: a deliberately late-alphabet" in out  # Term: line
    assert "- **Evidence tier**: Evidence tier means the grade" in out  # heading rule
    assert "Second sentence" not in out                    # first sentence only
    assert "**Note**" not in out                           # label stoplist


def test_alphabetized_with_sources(tmp_path):
    d = _write(tmp_path)
    rc, out, _ = _run(["--sources", str(d)])
    assert rc == 0
    entries = [l for l in out.splitlines() if l.startswith("- **")]
    terms = [l.split("**")[1] for l in entries]
    assert terms == sorted(terms, key=str.casefold)
    assert all("(source: " in l and ".md)" in l for l in entries)


def test_quiz_blanks_term(tmp_path):
    d = _write(tmp_path)
    rc, out, _ = _run(["--sources", str(d), "--quiz"])
    assert rc == 0
    assert "Fill-in-the-blank quiz" in out
    quiz = out.split("Fill-in-the-blank quiz")[1]
    # the heading-rule entry repeats its term in the definition: must be blanked
    assert "____ means the grade of support" in quiz
    assert "Evidence tier means the grade" not in quiz
    assert "<summary>Answer</summary>" in quiz


def test_guards(tmp_path):
    d = _write(tmp_path)
    rc, out, _ = _run(["--sources", str(d), "--max-terms", "2"])
    assert rc == 0
    assert sum(1 for l in out.splitlines() if l.startswith("- **")) == 2
    rc, out, _ = _run(["--sources", str(d), "--min-len", "6"])
    assert rc == 0
    assert "- **gate**" not in out          # 4 chars, filtered
    assert "- **orchestrator**" in out
    rc, _, _ = _run(["--sources", str(d), "--max-terms", "0"])
    assert rc == 1


def test_single_file_source(tmp_path):
    f = tmp_path / "one.md"
    f.write_text(DOC_B, encoding="utf-8")
    rc, out, _ = _run(["--sources", str(f)])
    assert rc == 0
    assert "- **agent**" in out


def test_invalid_inputs(tmp_path):
    rc, _, err = _run(["--sources", str(tmp_path / "missing.md")])
    assert rc == 1
    assert "not found" in err
    empty = tmp_path / "empty.md"
    empty.write_text("nothing that defines anything\n", encoding="utf-8")
    rc, _, err = _run(["--sources", str(empty)])
    assert rc == 1
    assert "no term/definition patterns" in err


# ---------------------------------------------------------------------------
# Ported from the retired tools/glossary_gen.py test suite
# ---------------------------------------------------------------------------

SKILL_MD = (
    "---\n"
    "name: statistics\n"
    "description: Rigorous statistical inference done correctly.\n"
    "---\n\n# Statistics\n"
)


def _write_at(root, rel, content):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_default_scan_targets_docs_and_skills(tmp_path):
    _write_at(tmp_path, "docs/a.md", "A **gate** is a checkpoint where the run pauses.\n")
    _write_at(tmp_path, "skills/statistics/SKILL.md", SKILL_MD)
    rc, out, _ = _run(["--root", str(tmp_path)])
    assert rc == 0
    assert "- **gate**" in out
    assert "- **statistics**: Rigorous statistical inference done correctly." in out


def test_skill_frontmatter_keys_not_misread_as_terms(tmp_path):
    _write_at(tmp_path, "skills/statistics/SKILL.md", SKILL_MD)
    rc, out, _ = _run(["--root", str(tmp_path)])
    assert rc == 0
    assert "- **name**" not in out
    assert "- **description**" not in out


def test_empty_default_scan_exits_1(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "skills").mkdir()
    rc, _, err = _run(["--root", str(tmp_path)])
    assert rc == 1
    assert "no markdown files" in err


def test_dash_pattern_at_line_start(tmp_path):
    f = _write_at(tmp_path, "docs/b.md", "Council - A team of related agents.\n")
    rc, out, _ = _run(["--sources", str(f)])
    assert rc == 0
    assert "- **Council**: A team of related agents." in out


def test_dash_pattern_mid_sentence_not_misread(tmp_path):
    f = _write_at(tmp_path, "docs/c.md",
                  "This is a long prose sentence about something - "
                  "and it continues here with more words.\n")
    rc, _, err = _run(["--sources", str(f)])
    # The pseudo-term before " - " is over the 6-word cap: nothing may match.
    assert rc == 1
    assert "no term/definition patterns" in err


def test_dedupe_first_occurrence_wins(tmp_path):
    _write_at(tmp_path, "docs/a.md", "Gatekeeper - First definition wins here.\n")
    _write_at(tmp_path, "docs/z.md", "gatekeeper - A different, later definition.\n")
    rc, out, _ = _run(["--root", str(tmp_path)])
    assert rc == 0
    assert out.count("**Gatekeeper**") + out.count("**gatekeeper**") == 1
    assert "First definition wins here." in out
    assert "A different, later definition." not in out
