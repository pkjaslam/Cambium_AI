---
name: citations
description: Build and verify a clean, honest bibliography — resolve DOIs, fetch and normalize BibTeX, de-duplicate references, check that every cited work actually exists, and flag unverifiable or fabricated citations. Use when assembling a reference list, formatting citations (APA/IEEE/Nature/BibTeX), verifying a DOI or venue, cleaning a refs.bib, or checking a draft's citations are real. Trigger on "add references", "cite", "bibliography", "BibTeX", "DOI", "verify the citations", "reference list". Pairs with the librarian agent. Never fabricates a citation.
---

# Citations — real references only

The single worst research-integrity failure for an AI is a **confident, well-formatted citation that
does not exist.** This skill verifies before it cites and refuses to invent.

## The non-negotiable rule
**Never write a citation you have not verified exists.** If you cannot resolve a DOI or find the work,
say so and mark it **Open / unverifiable** — do not paper over it with a plausible-looking entry.

## Resolve & verify
- Resolve DOIs via Crossref (`https://api.crossref.org/works/{doi}`) or `https://doi.org/{doi}`.
- For a title/author, search Crossref / OpenAlex / Semantic Scholar to get the canonical record.
- Confirm: authors, year, title, venue, and that the DOI actually points to the cited work.
- Use the WebSearch / WebFetch tools to confirm existence; record where you verified it.

## Normalize BibTeX
```bibtex
@article{key2023,
  author  = {Last, First and Other, A.},
  title   = {Exact title as published},
  journal = {Venue},
  year    = {2023},
  volume  = {12}, number = {3}, pages = {45--67},
  doi     = {10.xxxx/xxxxx}
}
```
Keys: `lastnameYEARword`. One canonical entry per work.

## De-duplicate & clean refs.bib
- Merge entries with the same DOI/title; keep the most complete one.
- Flag entries missing a DOI or with mismatched year/venue.
- Keep the bibliography sorted and consistent; no orphan keys (cited-but-absent or absent-but-cited).

## Format on request
Map to the target style (APA 7, IEEE, Nature, Chicago, ACM). Keep the underlying BibTeX as the source
of truth and render the style from it.

## Audit a draft's citations
1. Extract every in-text citation key/marker.
2. Confirm each resolves to a real, correct record.
3. Report: verified ✓, needs-fix (wrong metadata), and **unverifiable** (cannot confirm — do not ship).
4. Tag the bibliography **Code-verified** (DOIs resolved) vs **Asserted**.

## Guardrails
- No fabricated authors, titles, DOIs, or page numbers — ever.
- A citation you "remember" but cannot resolve is unverifiable; label it, don't assert it.
- Quotation + attribution must match the source; don't stretch a reference to support a claim it doesn't.
