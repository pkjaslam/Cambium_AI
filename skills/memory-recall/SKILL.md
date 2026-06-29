---
name: memory-recall
description: Query Cambium's own curated past findings, gate decisions, and agent outputs BEFORE starting related work, to avoid rediscovering known results. Use when beginning any task that may overlap with prior work: literature summaries, method choices, gate outcomes, OKF exports, or anything that was recorded in the findings ledger or agent outputs. Trigger on "what do we already know about", "prior findings", "past decisions", "have we done this before", "recall", "memory". Operated via python3 tools/memory_recall.py.
---

# Memory Recall -- query Cambium's own past findings

Before starting work on any topic that may have been addressed in a prior run, query the
in-house semantic recall index.  This prevents agents from rediscovering known results,
restating overturned decisions, or duplicating effort.

## What is indexed

Only curated, committed records are indexed.  Raw transcripts and temporary files are
deliberately excluded to avoid verbatim-secret risk:

- `agent_outputs/findings_ledger.csv` -- structured findings from all prior runs
- `governance/GATES.md` -- gate decisions and rationales
- `governance/CONTRIBUTION_LEDGER.csv` -- director contributions at each gate
- `agent_outputs/*.md` -- agent output notes
- `docs/**/*.md` -- Cambium concept and reference documentation

The index cache lives at `.cambium_memory/index.json` (gitignored, never committed).

## Mandatory usage rule for record-keeper and all lab agents

Before writing a new finding or starting a related analytical task, run:

```bash
python3 tools/memory_recall.py query "<your topic>" -k 5
```

If the top result has a score above 1.0 and its snippet is directly relevant, read the
full source file before proceeding.  Record in your output which prior findings you
consulted (or that none were found).

## CLI reference

```bash
# Build or rebuild the index (do this once per session, or after new records are committed)
python3 tools/memory_recall.py index

# Query: top-5 results with provenance
python3 tools/memory_recall.py query "learning packet" -k 5

# Query: top-10 results
python3 tools/memory_recall.py query "OKF export gate decision" -k 10

# Help
python3 tools/memory_recall.py --help
```

## Reading results

Each result includes:
- `source` : the curated file path (relative to repo root)
- `line`   : the line number where the chunk starts
- `chunk`  : the chunk index within the file
- `score`  : BM25 relevance score (higher is more relevant)
- `snippet`: a short excerpt for quick assessment

## Python import

```python
from tools.memory_recall import build_index, query_index

idx = build_index()          # or load from cache automatically
results = query_index("learning packet", top_k=5, index=idx)
for r in results:
    print(r["source"], r["line_start"], r["snippet"])
```

## Provenance and auditability

Every result carries full provenance (source file, line, chunk index).  This is a
governance requirement: any recalled finding must be traceable to a specific committed
record.

## Retrieval approach

Primary retrieval is Okapi BM25 implemented in pure Python (zero external dependencies).
If `sentence-transformers` is installed, a dense rerank is applied to the top-50 BM25
candidates.  Its absence is a silent no-op; the lexical result is always returned.  No
benchmark numbers are claimed for either path.

## Limitations

- Only committed, curated records are searchable.  In-progress transcripts and raw
  session logs are intentionally excluded.
- Re-index after committing new agent outputs: `python3 tools/memory_recall.py index`.
- The index cache is not thread-safe for concurrent writes; rebuild sequentially.
- Dense rerank requires `sentence-transformers` and a network download on first use;
  flag this as a non-reproducible step when the model checkpoint changes.
