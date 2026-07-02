"""Offline tests for cite_export -- BibTeX/RIS reformatting and export.

All fixtures are written to a tmp_path; no network is ever touched.
"""
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import cite_export as ce  # noqa: E402

TOOL = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "tools", "cite_export.py")

SAMPLE_BIB = """\
@article{smith2020cover,
  title = {Cover crops increase soil organic carbon},
  author = {Smith, Jane and Lee, Bob},
  year = {2020},
  journal = {Agronomy Journal},
  doi = {https://doi.org/10.1000/xyz123},
  url = {https://doi.org/10.1000/xyz123}
}

@inproceedings{doe2019proc,
  title = {A grounded study of methods},
  author = {Doe, John},
  year = {2019},
  booktitle = {Proceedings of Things}
}
"""

SAMPLE_CSV = """\
title,authors,year,doi,venue,url
Cover crops increase yield,"Smith, Jane; Lee, Bob",2021,10.1/x,Agronomy J.,https://example.org/a
Rainfall effects on maize,Doe John,2019,,Field Crops,
"""


def _write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return str(p)


def _run(args):
    """Invoke the CLI as a subprocess; return (rc, stdout, stderr)."""
    proc = subprocess.run([sys.executable, TOOL, *args],
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def test_bib_roundtrips_to_valid_bibtex(tmp_path):
    path = _write(tmp_path, "refs.bib", SAMPLE_BIB)
    records = ce.parse_bib(path)
    keys = {r["key"] for r in records}
    assert keys == {"smith2020cover", "doe2019proc"}
    out = ce.to_bibtex(records)
    # Well-formed entries for both keys, and the DOI prefix was normalized.
    assert "@article{smith2020cover," in out
    assert "@inproceedings{doe2019proc," in out
    assert "doi = {10.1000/xyz123}" in out  # https://doi.org/ stripped
    # Balanced braces overall (every { has a matching }).
    assert out.count("{") == out.count("}")
    # Re-parsing our own output yields the same keys (a real round-trip).
    reparsed = ce.parse_bib(_write(tmp_path, "again.bib", out))
    assert {r["key"] for r in reparsed} == keys


def test_bib_produces_valid_ris(tmp_path):
    path = _write(tmp_path, "refs.bib", SAMPLE_BIB)
    ris = ce.to_ris(ce.parse_bib(path))
    # Required RIS tags are present.
    assert "TY  - " in ris
    assert "TI  - Cover crops increase soil organic carbon" in ris
    assert "ER  - " in ris
    # One TY and one ER per record (two records here).
    assert ris.count("TY  - ") == 2
    assert ris.count("ER  - ") == 2
    # Journal article maps to JOUR; conference paper to CPAPER.
    assert "TY  - JOUR" in ris and "TY  - CPAPER" in ris
    assert "PY  - 2020" in ris and "DO  - 10.1000/xyz123" in ris


def test_findings_csv_to_bibtex_with_synthesized_keys(tmp_path):
    path = _write(tmp_path, "cites.csv", SAMPLE_CSV)
    records = ce.load_findings(path)
    keys = {r["key"] for r in records}
    # firstauthor + year keys, synthesized deterministically.
    assert keys == {"smith2021", "john2019"}
    out = ce.to_bibtex(records)
    assert "@article{smith2021," in out
    assert "author = {Smith, Jane; Lee, Bob}" in out
    assert "journal = {Agronomy J.}" in out
    # The row with an empty DOI/URL simply omits those fields.
    assert "@article{john2019," in out


def test_missing_title_strict_exits_1(tmp_path):
    csv_text = "title,authors,year\n,No Title Person,2020\nHas title,Someone,2021\n"
    path = _write(tmp_path, "mt.csv", csv_text)
    rc, _out, err = _run(["--findings", path, "--strict"])
    assert rc == 1
    assert "strict" in err.lower() and "title" in err.lower()
    # Without --strict the same input exits 0 (record kept).
    rc2, _o2, _e2 = _run(["--findings", path])
    assert rc2 == 0


def test_deterministic_output_same_bytes(tmp_path):
    path = _write(tmp_path, "refs.bib", SAMPLE_BIB)
    out_a = tmp_path / "a.bib"
    out_b = tmp_path / "b.bib"
    rc1, _, _ = _run(["--bib", path, "--out", str(out_a)])
    rc2, _, _ = _run(["--bib", path, "--out", str(out_b)])
    assert rc1 == 0 and rc2 == 0
    assert out_a.read_bytes() == out_b.read_bytes()
    # RIS is deterministic too.
    assert ce.to_ris(ce.parse_bib(path)) == ce.to_ris(ce.parse_bib(path))


def test_special_character_handling(tmp_path):
    csv_text = (
        "title,authors,year\n"
        "Analysis of A & B with \\path and 100% recall,\"O'Neil, Sam\",2022\n"
    )
    path = _write(tmp_path, "sp.csv", csv_text)
    records = ce.load_findings(path)
    bib = ce.to_bibtex(records)
    # Backslash is escaped so the BibTeX value stays valid.
    assert "\\\\path" in bib
    # Ampersand and percent are legal inside a {..} value and pass through.
    assert "A & B" in bib and "100% recall" in bib
    # Braces stay balanced despite the special characters.
    assert bib.count("{") == bib.count("}")
    # RIS keeps the raw characters (line-oriented, no LaTeX escaping).
    ris = ce.to_ris(records)
    assert "\\path" in ris and "A & B" in ris


def test_format_both_writes_two_files(tmp_path):
    path = _write(tmp_path, "refs.bib", SAMPLE_BIB)
    base = tmp_path / "export"
    rc, out, _ = _run(["--bib", path, "--format", "both", "--out", str(base)])
    assert rc == 0
    bib_path = tmp_path / "export.bib"
    ris_path = tmp_path / "export.ris"
    assert bib_path.exists() and ris_path.exists()
    assert "@article{" in bib_path.read_text(encoding="utf-8")
    assert "TY  - " in ris_path.read_text(encoding="utf-8")


def test_missing_file_exits_1(tmp_path):
    rc, _out, err = _run(["--bib", str(tmp_path / "nope.bib")])
    assert rc == 1
    assert "not found" in err.lower()


def test_cli_help_exits_0():
    rc, out, _ = _run(["--help"])
    assert rc == 0
    assert "cite_export" in out or "BibTeX" in out
