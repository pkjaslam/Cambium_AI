# CLAIM LINEAGE — <Project Name>
*Attach to every deliverable that makes headline claims. Maintained by `14-record-keeper`;
consumed by `09-verify-evidence` + `37-referee` for root-cause before G5.
The framework-only, infrastructure-free version of PROV-AGENT (W3C PROV + MCP;
arXiv 2508.02866). Adopt the convention, not the engine — no Flowcept/Redis/Kafka.
Pairs with REPRODUCIBILITY_CHECKLIST.md (run-grain) and provenance.json (deliverable-grain);
this file is **claim-grain**: each headline claim → the agent/council, input, and decision
that produced it, so a surprising or faulty claim can be traced to its first input.*

## Why
`provenance.json` records *which models + agents* a deliverable used; `run_trace.py`
shows *which council is working now*. Neither answers PROV-AGENT's root-cause queries:
**Q1** given a claim, what is the full lineage back to the first input? **Q5** where did a
faulty claim originate and what downstream claims did it contaminate? This sheet records the
minimal edges to answer both — by hand, in Markdown, with zero new infrastructure.

## How to use
1. List every **headline claim/number** in the deliverable (abstract claims, key figures,
   reported metrics). One row each.
2. For each, fill the edges below. Leave `Used` empty only if the claim is genuinely
   input-free (e.g. a definition) — an empty `Used` on an empirical claim is a **red flag**.
3. `Evidence tier` must match the claim's wording (Proved / Code-verified / Asserted / Open).
4. Reviewers (`09-verify-evidence`, `37-referee`) trace each row back before the G5 gate.

## Claim lineage table
*One row per headline claim. Mirrors PROV-AGENT's claim → agent → tool → prompt/input chain.*

| claim_id | claim (short) | evidence_tier | generated_by (council · agent) | used (input artifact / dataset / citation id) | informed_by (prompt / decision / ADR ref) |
| --- | --- | --- | --- | --- | --- |
| C1 |  |  |  |  |  |
| C2 |  |  |  |  |  |
| C3 |  |  |  |  |  |

- **claim_id** — stable id (C1, C2, …) reusable in the ledger and the report.
- **evidence_tier** — Proved / Code-verified / Asserted / Open (must match the claim's wording).
- **generated_by** — the council and agent that produced it (e.g. `Labs · lab-statistics`,
  `Verification · verify-evidence`). Use the run_trace council vocabulary.
- **used** — the concrete input(s): dataset/table id, result file, or citation id from the
  bibliography. This is the edge that makes Q1 traceable.
- **informed_by** — optional upstream decision/prompt/ADR the claim depends on (enables Q5
  and catches silent supersession — e.g. a claim resting on a since-superseded ADR).

## Root-cause checks (manual, before G5)
- [ ] Every headline claim has a row.
- [ ] No empirical claim has an empty `used` edge.
- [ ] Each `evidence_tier` matches the claim's wording (no overclaim vs. OUTPUT_CONTRACT).
- [ ] Q1 spot-check: pick one surprising claim, trace `used` → … → first input. Path resolves.
- [ ] Q5 spot-check: pick one input; list the claims that depend on it (forward trace).
- [ ] No claim's `informed_by` points at a superseded/duplicate ADR.

## Reuse-first guardrail
This is a **convention**, not a service. It wraps the existing `provenance.json` (deliverable
manifest) and `run_trace.py` (live board). Do **not** stand up a provenance engine. Counts stay
46·11·8. A future optional read-only helper to auto-answer Q1/Q5 from these rows is a separate
human build gate — see `DECISIONS.md` ADR-015.

Result: PASS / PASS-WITH-CONDITIONS / FAIL —  (reviewer, date)
