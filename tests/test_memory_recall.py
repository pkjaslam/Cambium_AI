"""tests/test_memory_recall.py -- Unit tests for tools/memory_recall.py.

Tests cover:
  1. Index builds from real repo records (or degrades gracefully on empty repo).
  2. A query for a known topic returns hits with provenance fields populated.
  3. Graceful behavior when sentence-transformers is absent (default lexical path).
  4. Empty query returns empty results without error.
  5. Missing source files are skipped gracefully.
  6. CSV row chunking preserves line numbers.
  7. Score ordering: a highly relevant doc outranks an irrelevant one.
  8. Query for OKF export returns a relevant source.
  9. Real-repo smoke test: index builds without error.
"""

import csv
import sys
from pathlib import Path

import pytest

# Make `tools` importable when running from repo root
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "tools"))

import memory_recall as mr


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mini_repo(tmp_path: Path) -> Path:
    """Create a minimal fake repo tree mirroring Cambium's curated sources."""
    ao = tmp_path / "agent_outputs"
    ao.mkdir(parents=True)

    # findings_ledger.csv with known-topic rows
    ledger = ao / "findings_ledger.csv"
    with open(ledger, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "topic", "finding", "gate"])
        w.writerow(["F001", "learning packet", "Agents recall prior findings via learning packets", "G2"])
        w.writerow(["F002", "OKF export", "OKF export bundles markdown with provenance links", "G4"])
        w.writerow(["F003", "gate lock", "Gate tokens are one-time-use and cryptographically signed", "G3"])

    # A markdown agent output
    md = ao / "sprint_notes.md"
    md.write_text(
        "# Sprint Notes\n\nThe learning packet approach was chosen to reduce redundant work "
        "across runs. Each agent deposits findings into the ledger before starting related tasks. "
        "OKF export consolidates these for external review.\n",
        encoding="utf-8",
    )

    # governance/GATES.md
    gov = tmp_path / "governance"
    gov.mkdir()
    gates = gov / "GATES.md"
    gates.write_text(
        "# GATES\n\n## G2: idea chosen\nApproved. Learning packet design accepted.\n\n"
        "## G4: results verified\nOKF export validated by verify-evidence.\n",
        encoding="utf-8",
    )

    # docs/concepts/ md
    docs = tmp_path / "docs" / "concepts"
    docs.mkdir(parents=True)
    (docs / "OVERVIEW.md").write_text(
        "# Cambium Overview\n\nCambium is a deterministic, auditable AI research institute.\n"
        "Memory recall allows agents to query past findings before starting new work.\n",
        encoding="utf-8",
    )

    return tmp_path


def _set_cache(tmp_path: Path):
    """Point module-level cache at a temp location. Returns (orig_dir, orig_file)."""
    orig_dir = mr.CACHE_DIR
    orig_file = mr.CACHE_FILE
    mr.CACHE_DIR = tmp_path / ".cambium_memory"
    mr.CACHE_FILE = mr.CACHE_DIR / "index.json"
    return orig_dir, orig_file


def _restore_cache(orig_dir, orig_file):
    mr.CACHE_DIR = orig_dir
    mr.CACHE_FILE = orig_file


# ---------------------------------------------------------------------------
# Test 1: build_index returns expected structure
# ---------------------------------------------------------------------------

def test_build_index_structure(tmp_path):
    root = _make_mini_repo(tmp_path)
    orig_dir, orig_file = _set_cache(tmp_path)
    try:
        idx = mr.build_index(root)
        assert "chunks" in idx
        assert "sources" in idx
        assert "chunk_count" in idx
        assert idx["chunk_count"] > 0
        assert idx["chunk_count"] == len(idx["chunks"])
        assert mr.CACHE_FILE.exists()
    finally:
        _restore_cache(orig_dir, orig_file)


# ---------------------------------------------------------------------------
# Test 2: query returns relevant hit with all provenance fields
# ---------------------------------------------------------------------------

def test_query_learning_packet_returns_provenance(tmp_path):
    root = _make_mini_repo(tmp_path)
    orig_dir, orig_file = _set_cache(tmp_path)
    try:
        idx = mr.build_index(root)
        results = mr.query_index("learning packet", top_k=3, index=idx, use_dense=False)
        assert len(results) >= 1
        top = results[0]
        assert "source" in top
        assert "chunk_idx" in top
        assert "line_start" in top
        assert "snippet" in top
        assert "score" in top
        assert top["source"] != ""
        assert top["line_start"] >= 1
    finally:
        _restore_cache(orig_dir, orig_file)


# ---------------------------------------------------------------------------
# Test 3: query for "OKF export" returns a relevant hit
# ---------------------------------------------------------------------------

def test_query_okf_export_returns_hit(tmp_path):
    root = _make_mini_repo(tmp_path)
    orig_dir, orig_file = _set_cache(tmp_path)
    try:
        idx = mr.build_index(root)
        results = mr.query_index("OKF export", top_k=5, index=idx, use_dense=False)
        assert len(results) >= 1
        sources = [r["source"] for r in results]
        assert any(
            "findings_ledger" in s or "sprint_notes" in s or "GATES" in s
            for s in sources
        )
    finally:
        _restore_cache(orig_dir, orig_file)


# ---------------------------------------------------------------------------
# Test 4: sentence-transformers absent -- graceful fallback to lexical
# ---------------------------------------------------------------------------

def test_dense_rerank_absent_is_noop(tmp_path, monkeypatch):
    """Even when sentence-transformers is blocked, query returns lexical results."""
    root = _make_mini_repo(tmp_path)
    orig_dir, orig_file = _set_cache(tmp_path)

    import builtins
    real_import = builtins.__import__

    def block_st(name, *args, **kwargs):
        if name == "sentence_transformers":
            raise ImportError("blocked in test")
        return real_import(name, *args, **kwargs)

    try:
        idx = mr.build_index(root)
        with monkeypatch.context() as m:
            m.setattr(builtins, "__import__", block_st)
            results = mr.query_index("learning packet", top_k=3, index=idx, use_dense=True)
        assert len(results) >= 1
        assert all("source" in r for r in results)
    finally:
        _restore_cache(orig_dir, orig_file)


# ---------------------------------------------------------------------------
# Test 5: empty query returns empty list without crashing
# ---------------------------------------------------------------------------

def test_empty_query_returns_empty(tmp_path):
    root = _make_mini_repo(tmp_path)
    orig_dir, orig_file = _set_cache(tmp_path)
    try:
        idx = mr.build_index(root)
        results = mr.query_index("", top_k=5, index=idx, use_dense=False)
        assert results == []
    finally:
        _restore_cache(orig_dir, orig_file)


# ---------------------------------------------------------------------------
# Test 6: missing source directories are skipped gracefully
# ---------------------------------------------------------------------------

def test_missing_sources_skipped_gracefully(tmp_path):
    """Repo with ONLY a docs dir (no governance, no agent_outputs) must not crash."""
    docs = tmp_path / "docs" / "concepts"
    docs.mkdir(parents=True)
    (docs / "OVERVIEW.md").write_text("Cambium overview text here.", encoding="utf-8")

    orig_dir, orig_file = _set_cache(tmp_path)
    try:
        idx = mr.build_index(tmp_path)
        assert idx["chunk_count"] >= 1
    finally:
        _restore_cache(orig_dir, orig_file)


# ---------------------------------------------------------------------------
# Test 7: score ordering -- relevant doc outranks irrelevant doc
# ---------------------------------------------------------------------------

def test_bm25_score_ordering(tmp_path):
    """The chunk containing query terms should rank above an unrelated chunk."""
    ao = tmp_path / "agent_outputs"
    ao.mkdir(parents=True)
    ledger = ao / "findings_ledger.csv"
    with open(ledger, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "topic", "finding", "gate"])
        w.writerow(["F001", "memory recall", "memory recall is lexical and deterministic", "G1"])
        w.writerow(["F002", "unrelated", "something completely different about budgets", "G2"])

    orig_dir, orig_file = _set_cache(tmp_path)
    try:
        idx = mr.build_index(tmp_path)
        results = mr.query_index("memory recall lexical", top_k=5, index=idx, use_dense=False)
        assert len(results) >= 1
        top_snippet = results[0]["snippet"].lower()
        assert "memory" in top_snippet or "recall" in top_snippet or "lexical" in top_snippet
    finally:
        _restore_cache(orig_dir, orig_file)


# ---------------------------------------------------------------------------
# Test 8: CSV chunking assigns correct line numbers
# ---------------------------------------------------------------------------

def test_csv_chunk_line_numbers(tmp_path):
    ao = tmp_path / "agent_outputs"
    ao.mkdir(parents=True)
    ledger = ao / "findings_ledger.csv"
    with open(ledger, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "finding"])
        w.writerow(["F001", "alpha finding"])
        w.writerow(["F002", "beta finding"])

    # Call with both required arguments
    chunks = mr._chunks_from_csv(ledger, "agent_outputs/findings_ledger.csv")
    assert len(chunks) == 2
    # First data row is line 2 (header = line 1), so line_start should be 2
    assert chunks[0]["line_start"] == 2
    assert chunks[1]["line_start"] == 3


# ---------------------------------------------------------------------------
# Test 9: build_index on real repo records (integration smoke test)
# ---------------------------------------------------------------------------

def test_index_real_repo_smoke():
    """Build index from actual Cambium repo. Accept 0 chunks if all sources missing."""
    smoke_cache = REPO_ROOT / ".cambium_memory" / "_test_smoke"
    smoke_cache.mkdir(parents=True, exist_ok=True)
    orig_dir = mr.CACHE_DIR
    orig_file = mr.CACHE_FILE
    mr.CACHE_DIR = smoke_cache
    mr.CACHE_FILE = smoke_cache / "index.json"
    try:
        idx = mr.build_index(REPO_ROOT)
        assert isinstance(idx["chunk_count"], int)
        assert idx["chunk_count"] >= 0
    finally:
        mr.CACHE_DIR = orig_dir
        mr.CACHE_FILE = orig_file
        if (smoke_cache / "index.json").exists():
            (smoke_cache / "index.json").unlink()
        try:
            smoke_cache.rmdir()
        except OSError:
            pass
