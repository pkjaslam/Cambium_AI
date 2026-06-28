# Cambium brain roadmap (honest)

An external evaluation argued Cambium leads on governance but trails on reasoning, research depth, and
autonomous execution, and proposed 12 intelligence upgrades. We adopt its direction, not its numbers, and
we tier everything by what can be built without fakery. This document was produced the Cambium way (Scouts
verified the claims, the Integrity Officer tiered the capabilities, gated at G1).

## How much to trust the evaluation
Scouts checked its claims. Verdict: 7 of 10 competitor claims are real (Sakana Fugu, DeepMind Co-Scientist's
Nature paper, Mimosa, EvoScientist, OpenAI o3, DeepSeek R1, Paperguide all verified). Treat the specific
benchmark numbers with caution: Elicit's accuracy stats are unaudited vendor self-claims, Biomni is ~150
tools not "100+" and "BioLab" was not found, and "GPT-5 / Gemini 3 Pro" are imprecise version labels. The
"6.1 to 8.5 out of 10" score is a heuristic, not a measured benchmark, and we treat it as **Asserted**.

## The non-negotiable guardrails
The fastest way to lose Cambium's only real moat is to ship stubs that look like capability. So:
- No stub may be presented as working capability. The web bridge runs in **simulation** today
  (`run_agent_live()` raises NotImplementedError); any demo must carry a visible SIMULATION label.
- "Most capable / best research framework" stays **Asserted** until we actually run a public benchmark
  (ScienceAgentBench, ReplicationBench). We do not claim a ranking we have not measured.
- Keep the eight gates, the evidence contract, the deterministic checks, and MIT self-hosting.

## The 12 capabilities, tiered honestly

| # | Capability | Tier | Honest note |
|---|---|---|---|
| 2 | Reasoning / extended thinking + test-time budget | **Buildable now** | Claude-native; no new dependency |
| 3 | Dynamic MCP tool discovery | **Buildable now** | Scan available MCP servers; gate before use |
| 7 | Multi-agent debate / devil's advocate | **Buildable now** | Uses the Claude agents we already have |
| 9 | DAG / graph orchestration | **Buildable now** | Real engine; replaces flat phases |
| 10 | Statistical computing (R / Python execution) | **Buildable now** | Local execution + provenance |
| 11 | Telemetry / observability | **Buildable now** | Extends cost_log + doctor |
| 1 | Multi-model mixture-of-agents | **Partial / scaffold** | Provider-pluggable seam; multi-provider needs your keys. A Claude self-consistency ensemble is real today |
| 5 | Semantic search + knowledge graph | **Partial / scaffold** | Semantic Scholar + citation graph + lightweight rerank are real; a full embedding KG at scale is not |
| 6 | Persistent agent memory + self-evolution | **Partial / scaffold** | A memory ledger is real; "self-evolving workflows" is not, and we will not claim it |
| 8 | Multimodal | **Partial / scaffold** | Vision via Claude is real; audio/video needs external infra |
| 4 | Autonomous Docker sandbox | **External dependency** | Needs Docker we do not control here; spec only |
| 12 | Domain foundation models (AlphaFold etc) | **External dependency** | Needs external services and weights; spec only |

## First increment (greenlit at G1)
1. **Reasoning tier.** Map the verification boards to Claude extended thinking, with a test-time "think
   harder" budget for the hardest gates (proof soundness, power analysis, methodology). Claude-native, real.
2. **Literature depth.** Add Semantic Scholar (~200M papers, free API) and citation-graph traversal to
   `paper_search.py`, with a lightweight lexical relevance rerank. Real, free, a genuine jump over 8 keyword hits.

Fast follow (the Integrity Officer's pick): a challenger / devil's-advocate pass at each gate, turning
rubber-stamp review into an adversarial check. Pure prompt + routing, buildable now.

## Sequence (no fake timelines)
- **Now:** the two real wins above.
- **Next (buildable):** MCP discovery, the debate / challenger pass, a persistent-memory ledger, telemetry.
- **Later (scaffold + your keys/infra):** multi-provider MoA, embeddings at scale, multimodal audio/video,
  DAG orchestration.
- **Spec only (external):** Docker sandbox, domain foundation models.

The formula stays honest: add the intelligence layer on top of the trust layer, and never trade the second
for the first.
