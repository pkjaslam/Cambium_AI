"""Tests for mcp_discovery (the toolsmith's live MCP awareness)."""
import os, sys
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import mcp_discovery as M

def test_map_loads_servers():
    pytest.importorskip("yaml")
    rows, _ = M.discover()
    assert len(rows) >= 8 and all("councils" in r and "status" in r for r in rows)

def test_task_prioritizes_relevant_sources():
    pytest.importorskip("yaml")
    rows, _ = M.discover("clinical trial biomedical literature review")
    names = [r["name"] for r in rows]
    assert names.index("PubMed") < names.index("GitHub")  # biomedical beats code repo

def test_routing_assigns_councils():
    pytest.importorskip("yaml")
    rows, _ = M.discover()
    pubmed = next(r for r in rows if r["name"] == "PubMed")
    assert "Scouts" in pubmed["councils"]

def test_status_values_are_honest():
    pytest.importorskip("yaml")
    rows, _ = M.discover()
    assert all(r["status"] in ("configured", "available to add") for r in rows)

def test_configured_detection_is_graceful():
    # must never raise even when config files are missing or malformed
    c = M.configured_servers()
    assert isinstance(c, set)
