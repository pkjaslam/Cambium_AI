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


# ---------------------------------------------------------------------------
# arXiv and PubMed sources (added) -- fully offline, fixture-driven.
# ---------------------------------------------------------------------------

ARXIV_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2101.00001v2</id>
    <published>2021-01-04T00:00:00Z</published>
    <title>Deep learning for cover crop mapping</title>
    <summary>We present a segmentation model for remote-sensing imagery.</summary>
    <author><name>Jane Smith</name></author>
    <author><name>Bob Lee</name></author>
    <arxiv:doi>10.1000/arxdoi</arxiv:doi>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/1912.09999v1</id>
    <published>2019-12-20T00:00:00Z</published>
    <title>Soil organic carbon dynamics</title>
    <summary>A theoretical treatment.</summary>
    <author><name>A. Author</name></author>
  </entry>
</feed>"""

PUBMED_ESUMMARY = {
    "result": {
        "uids": ["33000001"],
        "33000001": {
            "title": "CRISPR editing of maize for drought resistance",
            "pubdate": "2020 Mar",
            "fulljournalname": "The Plant Journal",
            "authors": [{"name": "Doe J"}, {"name": "Roe K"}],
            "articleids": [
                {"idtype": "pubmed", "value": "33000001"},
                {"idtype": "doi", "value": "10.1111/tpj.12345"},
            ],
        },
    }
}


def test_parse_arxiv_fixture():
    rows = ps.parse_arxiv(ARXIV_ATOM)
    assert len(rows) == 2
    r = rows[0]
    assert r["title"] == "Deep learning for cover crop mapping"
    assert r["authors"] == ["Jane Smith", "Bob Lee"]
    assert r["year"] == 2021 and r["arxiv_id"] == "2101.00001"
    assert r["doi"] == "10.1000/arxdoi" and r["source"] == "arxiv"
    assert r["venue"] == "arXiv"
    # An entry without a DOI still parses and falls back to its abs URL.
    r2 = rows[1]
    assert r2["arxiv_id"] == "1912.09999" and r2["doi"] is None
    assert r2["url"].endswith("1912.09999v1") or "1912.09999" in r2["url"]


def test_parse_pubmed_fixture():
    r = ps.parse_pubmed(PUBMED_ESUMMARY)[0]
    assert r["title"] == "CRISPR editing of maize for drought resistance"
    assert r["authors"] == ["Doe J", "Roe K"] and r["year"] == 2020
    assert r["pmid"] == "33000001" and r["doi"] == "10.1111/tpj.12345"
    assert r["venue"] == "The Plant Journal" and r["source"] == "pubmed"


def test_search_injects_offline_arxiv_fetcher():
    # The fetchers= seam replaces the network entirely; no request is made.
    rows = ps.search("cover crop mapping", source="arxiv",
                     fetchers={"arxiv": lambda q, limit: ps.parse_arxiv(ARXIV_ATOM)})
    assert rows and rows[0]["source"] == "arxiv"
    # The lexical rerank puts the on-topic title first.
    assert rows[0]["title"] == "Deep learning for cover crop mapping"


def test_search_injects_offline_pubmed_fetcher():
    rows = ps.search("crispr maize", source="pubmed",
                     fetchers={"pubmed": lambda q, limit: ps.parse_pubmed(PUBMED_ESUMMARY)})
    assert rows and rows[0]["source"] == "pubmed"
    assert rows[0]["pmid"] == "33000001"


def test_source_failure_degrades_to_skip_not_crash():
    def boom(q, limit):
        raise RuntimeError("simulated network failure")
    # A failing source must yield [] gracefully, never propagate the exception.
    assert ps.search("anything", source="pubmed", fetchers={"pubmed": boom}) == []
    # And a failing source ahead of a good one is skipped, not fatal.
    rows = ps.search("cover crop", source="best",
                     fetchers={"semanticscholar": boom, "openalex": boom,
                               "crossref": lambda q, limit: ps.parse_arxiv(ARXIV_ATOM)})
    assert rows and rows[0]["title"] == "Deep learning for cover crop mapping"


def test_input_json_fixture_builds_offline_fetchers(tmp_path):
    import json
    fixture = {"pubmed": PUBMED_ESUMMARY, "arxiv": ARXIV_ATOM}
    path = tmp_path / "fx.json"
    path.write_text(json.dumps(fixture), encoding="utf-8")
    fetchers = ps._load_input_json(str(path))
    assert set(fetchers) == {"pubmed", "arxiv"}
    # Each built fetcher returns the parsed records without any network call.
    rows = ps.search("maize", source="pubmed", fetchers=fetchers)
    assert rows and rows[0]["source"] == "pubmed"
