"""Test the scholarly-retrieval parsers (no network — fixture-driven)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import paper_search as ps

def test_parse_openalex_fixture():
    fx = {"results": [{
        "title": "Cover crops increase yield",
        "authorships": [{"author": {"display_name": "A. Smith"}}, {"author": {"display_name": "B. Lee"}}],
        "publication_year": 2021, "primary_location": {"source": {"display_name": "Agronomy J."}},
        "doi": "https://doi.org/10.1/x", "id": "https://openalex.org/W1", "cited_by_count": 42,
        "abstract_inverted_index": {"Cover": [0], "crops": [1], "help": [2]}}]}
    r = ps.parse_openalex(fx)[0]
    assert r["title"] == "Cover crops increase yield"
    assert r["authors"] == ["A. Smith", "B. Lee"] and r["year"] == 2021
    assert r["venue"] == "Agronomy J." and r["doi"] == "10.1/x" and r["citations"] == 42
    assert r["abstract"] == "Cover crops help" and r["source"] == "openalex"

def test_parse_crossref_fixture():
    fx = {"message": {"items": [{
        "title": ["A study"], "author": [{"given": "J", "family": "Doe"}],
        "issued": {"date-parts": [[2019]]}, "container-title": ["Nature"],
        "DOI": "10.2/y", "is-referenced-by-count": 7, "abstract": "We show X."}]}}
    r = ps.parse_crossref(fx)[0]
    assert r["title"] == "A study" and r["authors"] == ["J Doe"] and r["year"] == 2019
    assert r["doi"] == "10.2/y" and r["url"] == "https://doi.org/10.2/y" and r["citations"] == 7

def test_abstract_reconstruction_and_empty():
    assert ps._abstract({"a": [1], "b": [0]}) == "b a"
    assert ps._abstract(None) == ""
