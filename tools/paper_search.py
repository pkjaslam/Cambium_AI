#!/usr/bin/env python3
"""paper_search — grounded scholarly retrieval for the Scouts/Librarian (no API key required).

Queries free, open scholarly APIs (OpenAlex CC0; Crossref fallback) and returns structured, citable
records — title, authors, year, venue, DOI, URL, citation count, abstract snippet. This grounds Cambium's
deep-search in a real corpus instead of relying on the model's ad-hoc web tool use. Offline-safe: a network
failure returns [] with a note, never crashes a run.

Usage:
  python3 tools/paper_search.py "cover crop yield meta-analysis" [--limit 8] [--source openalex|crossref]
Importable:  from tools.paper_search import search ; rows = search("query", limit=8)
"""
import sys, json, urllib.request, urllib.parse

UA = {"User-Agent": "Cambium/1.0 (https://github.com/IFC-UIDAHO/Cambium_AI; mailto:pkjaslamagrico@gmail.com)"}

def _get(url, timeout=15):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout))

def _abstract(inv):
    if not inv: return ""
    words = sorted(((pos, w) for w, ps in inv.items() for pos in ps))
    return " ".join(w for _, w in words)[:300]

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

def search(query, limit=8, source="openalex"):
    q = urllib.parse.quote(query)
    try:
        if source == "crossref":
            return parse_crossref(_get(f"https://api.crossref.org/works?query={q}&rows={limit}"))
        return parse_openalex(_get(f"https://api.openalex.org/works?search={q}&per-page={limit}&sort=relevance_score:desc"))
    except Exception as e:
        try:  # one fallback to the other source
            other = "crossref" if source == "openalex" else "openalex"
            return search(query, limit, other) if "_retry" not in query else []
        except Exception:
            print(f"[paper_search] offline / API error: {str(e)[:80]} — returning [] (run again online)", file=sys.stderr)
            return []

def main():
    a = sys.argv[1:]
    if not a: print(__doc__); return 0
    src = a[a.index("--source")+1] if "--source" in a else "openalex"
    lim = int(a[a.index("--limit")+1]) if "--limit" in a else 8
    q = " ".join(x for x in a if not x.startswith("--") and x not in (src, str(lim)))
    rows = search(q, lim, src)
    print(f"[paper_search] '{q}' via {src} → {len(rows)} result(s)\n")
    for i, r in enumerate(rows, 1):
        au = ", ".join(r["authors"][:3]) + (" et al." if len(r["authors"]) > 3 else "")
        print(f"{i}. {r['title']} ({r['year']})\n   {au} · {r['venue']} · {r['citations']} cites · {r['url']}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
