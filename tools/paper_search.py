#!/usr/bin/env python3
"""paper_search — grounded scholarly retrieval for the Scouts/Librarian (no API key required).

Queries free, open scholarly APIs and returns structured, citable records (title, authors, year, venue,
DOI, URL, citation count, abstract snippet), then applies a lexical relevance rerank. Sources:
  - Semantic Scholar Graph API (~200M papers, free, rate-limited) — the default when reachable.
  - OpenAlex (CC0) and Crossref — cross-disciplinary fallbacks.
  - arXiv (export.arxiv.org Atom API) — preprints in physics/CS/math/stat/q-bio/econ.
  - PubMed (NCBI E-utilities, esearch + esummary) — biomedical and life-science literature.
Also exposes a best-effort citation-graph lookup (reference/citation counts + a few linked titles) for a DOI.

Honest note: the rerank is LEXICAL (query-term overlap weighted by field), not neural embeddings. True
embedding/vector search is a separate, scaffolded item (see docs/reference/BRAIN_ROADMAP.md). Offline-safe:
a network failure for any single source is caught and that source is skipped with a note; a run never
crashes. For fully offline tests, inject canned responses via the `fetchers=` argument to search() or the
`--input-json` CLI flag (a JSON map of source name -> raw API response text/JSON), which replaces the
network entirely.

Usage:
  python3 tools/paper_search.py "cover crop yield meta-analysis" [--limit 8]
      [--source best|semanticscholar|openalex|crossref|arxiv|pubmed]
  python3 tools/paper_search.py --graph 10.1038/s41586-020-2649-2     # citation-graph for a DOI
  python3 tools/paper_search.py "crispr maize" --source pubmed --input-json fixture.json  # offline
Importable:  from tools.paper_search import search, citation_graph
"""
import sys, json, urllib.request, urllib.parse, re
import xml.etree.ElementTree as ET
import cambium_io  # noqa: F401 — reconfigures stdout/stderr to UTF-8 on Windows

UA = {"User-Agent": "Cambium/1.0 (https://github.com/pkjaslam/Cambium_AI; mailto:pkjaslamagrico@gmail.com)"}
S2 = "https://api.semanticscholar.org/graph/v1"
ARXIV_API = "http://export.arxiv.org/api/query"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# All known sources, and the ordered fallback chains per --source choice.
ALL_SOURCES = ("semanticscholar", "openalex", "crossref", "arxiv", "pubmed")
SOURCE_ORDER = {
    "best": ["semanticscholar", "openalex", "crossref"],
    "semanticscholar": ["semanticscholar"],
    "openalex": ["openalex", "crossref"],
    "crossref": ["crossref", "openalex"],
    "arxiv": ["arxiv"],
    "pubmed": ["pubmed"],
}


def _get(url, timeout=15):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout))


def _get_text(url, timeout=15):
    """Fetch a URL and return the decoded response body (for XML APIs)."""
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _abstract(inv):
    if not inv: return ""
    words = sorted(((pos, w) for w, ps in inv.items() for pos in ps))
    return " ".join(w for _, w in words)[:300]


def parse_semanticscholar(obj):
    out = []
    for r in obj.get("data", []) or []:
        ext = r.get("externalIds") or {}
        out.append({
            "title": (r.get("title") or "").strip(),
            "authors": [a.get("name", "") for a in (r.get("authors") or [])[:6]],
            "year": r.get("year"),
            "venue": r.get("venue") or "",
            "doi": ext.get("DOI"),
            "url": ("https://doi.org/" + ext["DOI"]) if ext.get("DOI") else (r.get("url") or ""),
            "citations": r.get("citationCount", 0) or 0,
            "abstract": (r.get("abstract") or "")[:300],
            "source": "semanticscholar",
        })
    return out


def parse_openalex(obj):
    out = []
    for r in obj.get("results", []):
        out.append({
            "title": (r.get("title") or "").strip(),
            "authors": [a["author"]["display_name"] for a in r.get("authorships", [])[:6] if a.get("author")],
            "year": r.get("publication_year"),
            "venue": ((r.get("primary_location") or {}).get("source") or {}).get("display_name") or "",
            "doi": (r.get("doi") or "").replace("https://doi.org/", "") or None,
            "url": r.get("doi") or r.get("id"),
            "citations": r.get("cited_by_count", 0),
            "abstract": _abstract(r.get("abstract_inverted_index")),
            "source": "openalex",
        })
    return out


def parse_crossref(obj):
    out = []
    for r in obj.get("message", {}).get("items", []):
        out.append({
            "title": (r.get("title") or [""])[0].strip(),
            "authors": [f"{a.get('given','')} {a.get('family','')}".strip() for a in r.get("author", [])[:6]],
            "year": (r.get("issued", {}).get("date-parts", [[None]])[0] or [None])[0],
            "venue": (r.get("container-title") or [""])[0],
            "doi": r.get("DOI"),
            "url": ("https://doi.org/" + r["DOI"]) if r.get("DOI") else r.get("URL"),
            "citations": r.get("is-referenced-by-count", 0),
            "abstract": (r.get("abstract") or "")[:300],
            "source": "crossref",
        })
    return out


# arXiv Atom namespaces.
_ATOM = "{http://www.w3.org/2005/Atom}"
_ARXIV_NS = "{http://arxiv.org/schemas/atom}"


def _arxiv_id_from_url(url):
    """Reduce an arXiv entry id URL to the bare id (e.g. '2101.00001v2' -> '2101.00001')."""
    tail = (url or "").rstrip("/").rsplit("/", 1)[-1]
    return re.sub(r"v\d+$", "", tail)


def parse_arxiv(xml_text):
    """Parse an arXiv Atom feed (string) into normalized records.

    Pulls title, authors, published year, the arXiv id, the DOI when the
    entry declares one, and the abstract/summary. Malformed XML raises
    (the caller catches it and skips the source).
    """
    root = ET.fromstring(xml_text)
    out = []
    for entry in root.findall(f"{_ATOM}entry"):
        title = (entry.findtext(f"{_ATOM}title") or "").strip()
        title = re.sub(r"\s+", " ", title)
        authors = []
        for au in entry.findall(f"{_ATOM}author"):
            name = (au.findtext(f"{_ATOM}name") or "").strip()
            if name:
                authors.append(name)
        published = entry.findtext(f"{_ATOM}published") or ""
        ym = re.match(r"(\d{4})", published)
        year = int(ym.group(1)) if ym else None
        entry_id = entry.findtext(f"{_ATOM}id") or ""
        arxiv_id = _arxiv_id_from_url(entry_id)
        doi = (entry.findtext(f"{_ARXIV_NS}doi") or "").strip() or None
        summary = re.sub(r"\s+", " ", (entry.findtext(f"{_ATOM}summary") or "").strip())
        url = ("https://doi.org/" + doi) if doi else (entry_id or ("https://arxiv.org/abs/" + arxiv_id))
        out.append({
            "title": title,
            "authors": authors[:6],
            "year": year,
            "venue": "arXiv",
            "doi": doi,
            "arxiv_id": arxiv_id,
            "url": url,
            "citations": 0,   # arXiv Atom carries no citation count
            "abstract": summary[:300],
            "source": "arxiv",
        })
    return out


def parse_pubmed(summary_obj):
    """Parse an NCBI ESummary JSON result into normalized records.

    Expects the standard esummary shape: {"result": {"uids": [...],
    "<pmid>": {...}, ...}}. Extracts title, authors, year, the PMID, and
    the DOI from the articleids list when present.
    """
    result = (summary_obj or {}).get("result") or {}
    uids = result.get("uids") or [k for k in result.keys() if k != "uids"]
    out = []
    for pmid in uids:
        rec = result.get(pmid)
        if not isinstance(rec, dict):
            continue
        title = (rec.get("title") or "").strip()
        authors = [a.get("name", "") for a in (rec.get("authors") or [])[:6] if a.get("name")]
        pubdate = rec.get("pubdate") or rec.get("sortpubdate") or ""
        ym = re.match(r"(\d{4})", pubdate)
        year = int(ym.group(1)) if ym else None
        venue = rec.get("fulljournalname") or rec.get("source") or ""
        doi = None
        for aid in rec.get("articleids") or []:
            if (aid.get("idtype") or "").lower() == "doi" and aid.get("value"):
                doi = aid["value"].strip()
                break
        url = ("https://doi.org/" + doi) if doi else ("https://pubmed.ncbi.nlm.nih.gov/%s/" % pmid)
        out.append({
            "title": title,
            "authors": authors,
            "year": year,
            "venue": venue,
            "doi": doi,
            "pmid": str(pmid),
            "url": url,
            "citations": 0,   # esummary carries no citation count
            "abstract": "",
            "source": "pubmed",
        })
    return out


_WORD = re.compile(r"[a-z0-9]+")
def rerank(rows, query):
    """Lexical relevance rerank: query-term hits in the title (x3) and abstract (x1), citations as tiebreak."""
    terms = [t for t in _WORD.findall(query.lower()) if len(t) > 2]
    if not terms: return rows
    def score(r):
        title = (r.get("title") or "").lower(); abso = (r.get("abstract") or "").lower()
        s = sum(3 for t in terms if t in title) + sum(1 for t in terms if t in abso)
        return (s, r.get("citations", 0) or 0)
    return sorted(rows, key=score, reverse=True)


# ---------------------------------------------------------------------------
# Per-source network fetchers. Each takes (encoded_query, limit) and returns a
# normalized record list. Registered in DEFAULT_FETCHERS so tests can inject
# offline stand-ins without touching the network.
# ---------------------------------------------------------------------------

def _semanticscholar(q, limit):
    fields = "title,authors,year,venue,externalIds,citationCount,abstract"
    return parse_semanticscholar(_get(f"{S2}/paper/search?query={q}&limit={limit}&fields={fields}"))


def _openalex(q, limit):
    return parse_openalex(_get(
        f"https://api.openalex.org/works?search={q}&per-page={limit}&sort=relevance_score:desc"))


def _crossref(q, limit):
    return parse_crossref(_get(f"https://api.crossref.org/works?query={q}&rows={limit}"))


def _arxiv(q, limit):
    url = (f"{ARXIV_API}?search_query=all:{q}&start=0&max_results={limit}"
           "&sortBy=relevance&sortOrder=descending")
    return parse_arxiv(_get_text(url))


def _pubmed(q, limit):
    """Two-step E-utilities call: esearch for PMIDs, then esummary for metadata."""
    ids = _get(f"{EUTILS}/esearch.fcgi?db=pubmed&retmode=json&retmax={limit}&term={q}")
    pmids = ((ids or {}).get("esearchresult") or {}).get("idlist") or []
    if not pmids:
        return []
    joined = ",".join(pmids)
    return parse_pubmed(_get(f"{EUTILS}/esummary.fcgi?db=pubmed&retmode=json&id={joined}"))


# Name -> fetcher. Kept as a module constant so search() can be given a
# replacement dict (offline tests) without monkeypatching module globals.
DEFAULT_FETCHERS = {
    "semanticscholar": _semanticscholar,
    "openalex": _openalex,
    "crossref": _crossref,
    "arxiv": _arxiv,
    "pubmed": _pubmed,
}


def search(query, limit=8, source="best", fetchers=None):
    """Query sources in fallback order; return a reranked list (first source with hits wins).

    `fetchers` overrides the per-source network functions with a mapping of
    source name -> callable(encoded_query, limit) -> record list. This is the
    offline-test seam: pass canned parsers and no network is touched. Any
    exception from a fetcher is caught and that source is skipped with a note.
    """
    q = urllib.parse.quote(query)
    order = SOURCE_ORDER.get(source, list(ALL_SOURCES))
    active = dict(DEFAULT_FETCHERS)
    if fetchers:
        active.update(fetchers)
    last = None
    for src in order:
        fn = active.get(src)
        if fn is None:
            continue
        try:
            rows = fn(q, limit)
            if rows:
                return rerank(rows, query)[:limit]
        except Exception as e:
            last = e
            print(f"[paper_search] source '{src}' unavailable ({str(e)[:60]}); skipping it",
                  file=sys.stderr)
            continue
    if last:
        print(f"[paper_search] all sources unreachable: {str(last)[:80]} — returning [] (run again online)",
              file=sys.stderr)
    return []


def citation_graph(doi, timeout=15):
    """Best-effort citation-graph snapshot for a DOI: reference + citation counts and a few influential titles."""
    doi = doi.strip().replace("https://doi.org/", "")
    try:
        base = f"{S2}/paper/DOI:{urllib.parse.quote(doi)}"
        meta = _get(base + "?fields=title,citationCount,referenceCount", timeout)
        cites = _get(base + "/citations?fields=title,year&limit=5", timeout).get("data", [])
        top = [c.get("citingPaper", {}).get("title") for c in cites if c.get("citingPaper")]
        return {"doi": doi, "title": meta.get("title"), "cited_by": meta.get("citationCount"),
                "references": meta.get("referenceCount"), "sample_citing": [t for t in top if t]}
    except Exception as e:
        return {"doi": doi, "error": "citation graph unreachable: " + str(e)[:80]}


def _load_input_json(path):
    """Load a --input-json fixture: {source_name: raw_api_response} and build fetchers.

    The value for each source is passed straight to that source's parser
    (JSON object for the JSON APIs, an Atom XML string for arxiv). This
    replaces the network entirely for offline runs and tests.
    """
    with open(path, encoding="utf-8", errors="replace") as fh:
        raw = json.load(fh)
    if not isinstance(raw, dict):
        raise ValueError("--input-json must be a JSON object mapping source -> response")
    parsers = {
        "semanticscholar": parse_semanticscholar, "openalex": parse_openalex,
        "crossref": parse_crossref, "arxiv": parse_arxiv, "pubmed": parse_pubmed,
    }
    def _make(par, payload):
        # Bind both parser and payload; the returned fetcher ignores its
        # (query, limit) args and just replays the canned response.
        return lambda q, limit: par(payload)

    fetchers = {}
    for src, payload in raw.items():
        parser = parsers.get(src)
        if parser is None:
            continue
        fetchers[src] = _make(parser, payload)
    return fetchers


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a:
        print(__doc__)
        return 0
    if "--graph" in a:
        print(json.dumps(citation_graph(a[a.index("--graph") + 1]), ensure_ascii=False, indent=1))
        return 0
    src = a[a.index("--source") + 1] if "--source" in a else "best"
    lim = int(a[a.index("--limit") + 1]) if "--limit" in a else 8
    fetchers = None
    if "--input-json" in a:
        path = a[a.index("--input-json") + 1]
        try:
            fetchers = _load_input_json(path)
        except Exception as e:
            print(f"[paper_search] ERROR: cannot load --input-json: {str(e)[:80]}", file=sys.stderr)
            return 1
    # The query is every non-flag token that is not itself a flag value.
    flag_vals = set()
    for flag in ("--source", "--limit", "--input-json"):
        if flag in a:
            flag_vals.add(a[a.index(flag) + 1])
    q = " ".join(x for x in a if not x.startswith("--") and x not in flag_vals)
    rows = search(q, lim, src, fetchers=fetchers)
    via = rows[0]["source"] if rows else src
    print(f"[paper_search] '{q}' via {via} → {len(rows)} result(s) (lexical rerank)\n")
    for i, r in enumerate(rows, 1):
        au = ", ".join(r["authors"][:3]) + (" et al." if len(r["authors"]) > 3 else "")
        print(f"{i}. {r['title']} ({r['year']})\n   {au} · {r['venue']} · {r['citations']} cites · {r['url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
