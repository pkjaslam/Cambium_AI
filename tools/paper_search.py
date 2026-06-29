#!/usr/bin/env python3
"""paper_search — grounded scholarly retrieval for the Scouts/Librarian (no API key required).

Queries free, open scholarly APIs and returns structured, citable records (title, authors, year, venue,
DOI, URL, citation count, abstract snippet), then applies a lexical relevance rerank. Sources:
  - Semantic Scholar Graph API (~200M papers, free, rate-limited; ~200M papers per Semantic Scholar) — the default when reachable.
  - OpenAlex (CC0) and Crossref — graceful fallbacks when Semantic Scholar is rate-limited or offline.
Also exposes a best-effort citation-graph lookup (reference/citation counts + a few linked titles) for a DOI.

Honest note: the rerank is LEXICAL (query-term overlap weighted by field), not neural embeddings. True
embedding/vector search is a separate, scaffolded item (see docs/reference/BRAIN_ROADMAP.md). Offline-safe:
a network failure returns [] with a note, never crashes a run.

Usage:
  python3 tools/paper_search.py "cover crop yield meta-analysis" [--limit 8] [--source best|semanticscholar|openalex|crossref]
  python3 tools/paper_search.py --graph 10.1038/s41586-020-2649-2     # citation-graph for a DOI
Importable:  from tools.paper_search import search, citation_graph
"""
import sys, json, urllib.request, urllib.parse, re
import cambium_io  # noqa: F401 — reconfigures stdout/stderr to UTF-8 on Windows

UA = {"User-Agent": "Cambium/1.0 (https://github.com/pkjaslam/Cambium_AI; mailto:pkjaslamagrico@gmail.com)"}
S2 = "https://api.semanticscholar.org/graph/v1"

def _get(url, timeout=15):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout))

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

def _semanticscholar(q, limit):
    fields = "title,authors,year,venue,externalIds,citationCount,abstract"
    return parse_semanticscholar(_get(f"{S2}/paper/search?query={q}&limit={limit}&fields={fields}"))

def search(query, limit=8, source="best"):
    q = urllib.parse.quote(query)
    order = {"best": ["semanticscholar", "openalex", "crossref"],
             "semanticscholar": ["semanticscholar"], "openalex": ["openalex", "crossref"],
             "crossref": ["crossref", "openalex"]}.get(source, ["semanticscholar", "openalex", "crossref"])
    last = None
    for src in order:
        try:
            if src == "semanticscholar":
                rows = _semanticscholar(q, limit)
            elif src == "crossref":
                rows = parse_crossref(_get(f"https://api.crossref.org/works?query={q}&rows={limit}"))
            else:
                rows = parse_openalex(_get(f"https://api.openalex.org/works?search={q}&per-page={limit}&sort=relevance_score:desc"))
            if rows:
                return rerank(rows, query)[:limit]
        except Exception as e:
            last = e
            continue
    if last:
        print(f"[paper_search] all sources unreachable: {str(last)[:80]} — returning [] (run again online)", file=sys.stderr)
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

def main():
    a = sys.argv[1:]
    if not a: print(__doc__); return 0
    if "--graph" in a:
        print(json.dumps(citation_graph(a[a.index("--graph") + 1]), ensure_ascii=False, indent=1)); return 0
    src = a[a.index("--source")+1] if "--source" in a else "best"
    lim = int(a[a.index("--limit")+1]) if "--limit" in a else 8
    q = " ".join(x for x in a if not x.startswith("--") and x not in (src, str(lim)))
    rows = search(q, lim, src)
    via = rows[0]["source"] if rows else src
    print(f"[paper_search] '{q}' via {via} → {len(rows)} result(s) (lexical rerank)\n")
    for i, r in enumerate(rows, 1):
        au = ", ".join(r["authors"][:3]) + (" et al." if len(r["authors"]) > 3 else "")
        print(f"{i}. {r['title']} ({r['year']})\n   {au} · {r['venue']} · {r['citations']} cites · {r['url']}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
