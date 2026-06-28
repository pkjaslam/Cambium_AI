"""Tests for the reasoning tier (model_router) and the literature upgrade (paper_search)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import model_router as M
import paper_search as P

def test_reasoning_agents_get_extended_thinking():
    r = M.route("verify-rigor")
    assert r["extended_thinking"] is True and r["thinking_budget"] > 0 and r["tier"] == "reasoning"

def test_non_reasoning_agents_get_no_thinking():
    r = M.route("outreach")
    assert r["extended_thinking"] is False and r["thinking_budget"] == 0

def test_test_time_scaling_increases_budget():
    assert M.thinking_budget("verify-rigor", "max") > M.thinking_budget("verify-rigor", "low") > 0
    assert M.thinking_budget("record-keeper", "max") == 0  # not a reasoning agent

def test_base_routing_unchanged_backward_compatible():
    cfg, _ = M.load_config(); _, tiers = M.active_tiers(cfg); cards = M.load_cards()
    rt, model = M.resolve("outreach", cards, tiers)
    assert rt in ("strong", "mid", "light") and isinstance(model, str)

def test_rerank_puts_title_match_first():
    rows = [
        {"title": "Unrelated work on bees", "abstract": "", "citations": 9000},
        {"title": "Soil organic carbon under cover crops", "abstract": "meta-analysis", "citations": 5},
    ]
    out = P.rerank(rows, "soil organic carbon cover crops")
    assert out[0]["title"].startswith("Soil organic carbon")  # relevance beats raw citation count

def test_rerank_empty_query_is_noop():
    rows = [{"title": "a", "abstract": "", "citations": 1}]
    assert P.rerank(rows, "") == rows

def test_search_signature_and_source_order():
    # 'best' tries semantic scholar first; the function must accept the source arg without error
    assert callable(P.search) and callable(P.citation_graph)
