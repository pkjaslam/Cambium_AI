# Cambium — Decision Records (ADR)
*A living log of the load-bearing decisions, so any Claude account (or human) can see WHY, not just what.
Append a new entry for every meaningful architectural/governance decision. Template: templates/DECISION_RECORD.md.*

## ADR-001: Council-based, human-gated institution (not a free agent swarm)
- Date: 2026-06 · Status: Accepted · Decider: Director
- Context: needed a research org, not just "many agents."
- Decision: organize as 11 councils / 46 agents under an Orchestrator, with 8 human gates (G0–G6) and an evidence contract.
- Consequences: every phase stops for a human; nothing ships without approval. Do NOT remove the gates.

## ADR-002: Evidence-tiered output contract, enforced in CI
- Date: 2026-06 · Status: Accepted
- Decision: claim tiers (Proved/Code-verified/Asserted/Open); `governance/validate.py` fails the build on open P0,
  un-evidenced "Code-verified", or unresolved citations.
- Consequences: honesty is a check, not a convention.

## ADR-003: Adopt verified ideas from peer systems
- Date: 2026-06 · Status: Accepted
- Decision: Elo idea-tournament (← AI Co-Scientist), referee/reproducibility/novelty gates (← AI Scientist),
  budget-aware verification (← Agent Lab), Toolsmith provisioning (reuse-beats-rebuild), Task Router, `doctor` self-check
  (← ECC/ruflo metaharness). NOT adopted: becoming a harness/swarm engine — Cambium stays the research-institution layer.
- Consequences: Cambium is the domain layer; it can run ON harnesses like ECC/ruflo, not replace them.

## ADR-004: Multi-account continuity via files + git (not a shared server, yet)
- Date: 2026-06 · Status: Accepted
- Decision: state lives in the repo (PROJECT_STATE/ledger/GATES/ADR); multiple Claude accounts continue from files.
  Hosted multi-user (server+DB+SSO) is a future phase.
- Consequences: works offline today; per-user accounts run agents on their own login (no shared keys).

## ADR-005: Set aside the web-app build; keep the core institute
- Date: 2026-06 · Status: Accepted · Decider: Director
- Decision: moved app/, campus.html, and the app plans to a recoverable trash folder; kept agents, governance, tools, docs.
- Consequences: focus stays on the institute + framework; the app can be revived from trash if wanted.

## ADR-006: Ship an MCP server (alongside the plugin)
- Date: 2026-06 · Status: Accepted · Decider: Director
- Context: Cambium was plugin/template only; users asked to also expose it like the many `npx`/MCP tools they see.
- Decision: add `mcp_server/` — a Python MCP server (official `mcp` SDK / FastMCP, stdio) exposing cambium_plan,
  provision, agents, doctor, grade, validate. Installable via `python -m cambium_mcp.server` or `uvx cambium-mcp`.
- Consequences: Cambium is now usable FROM other AI apps (Claude Desktop/Code, Cursor), not just as a plugin.
  Stays the research-institution domain layer; the MCP is a thin wrapper over existing tools.

## ADR-007: Add real citation verification (SemanticCite) behind a gate -- ACCEPTED
- Date: 2026-06-26 - Status: **Accepted** (human approved 2026-06-26, Director)
- **Implemented (additive, optional, advisory):** `tools/cite_check.py` (import-guarded shim: semanticcite -> local Ollama -> deterministic lexical fallback / advisory no-op; writes `governance/cite_audit.json`; optional non-destructive `<ledger>.cited.csv` sidecar). `governance/validate.py` honors an optional `citation_support` column as an ADVISORY WARNING (never a blocker; absent column = back-compat no-op). One optional line on the `verify-evidence` card (count stays 46). ARS refinements folded in: per-claim `locator` anchors + calibrated 20-tuple gold set (`tests/fixtures/cite_gold.csv`, FNR<0.15/FPR<0.10) + `tests/test_cite_check.py`. SemanticCite recorded at the provisioning gate but NOT installed (TOOL_POLICY.md). Green: consistency 46-11-8, doctor healthy, pytest.

## ADR-008: Add an Interpretation-Fallacy Checklist (experiment-agent ADAPT) -- ACCEPTED
- Date: 2026-06-26 · Status: **Accepted** (human approved 2026-06-26, Director) · Decider: Director
- Context: scan of `experiment-agent` (https://github.com/Imbad0202/experiment-agent, CC-BY-NC-4.0). Its `run`/`manage`/repro-rerun capabilities **duplicate** Cambium's exec-experiments + research-engineer + research-conduct-officer + `lab-statistics` + `verify-rigor` + `templates/REPRODUCIBILITY_CHECKLIST.md` (router grounded: the task routes through 18 agents). The ONE narrow real gap: `grep -ri "fallacy|simpson|survivorship"` = 0 hits — Cambium audited "rigor" abstractly but enumerated no **interpretation-fallacy** taxonomy for a reviewer to run against a results section.
- **Implemented (additive, optional, advisory, framework-only, no CC-BY-NC content copied):** new `templates/INTERPRETATION_FALLACY_CHECKLIST.md` (freshly authored; ~12 fallacies: Simpson's, ecological, survivorship/selection, base-rate neglect, multiple-comparisons/p-hacking, HARKing, optional-stopping, regression-to-mean, confounding, correlation≠causation, overfitting-as-result, significance≠importance), mirroring the REPRODUCIBILITY_CHECKLIST pattern. `governance/validate.py` honors an optional `fallacy_check` column as an ADVISORY WARNING (never a blocker; absent column / clean value = back-compat no-op), mirroring ADR-007's `citation_support`. One optional reference line each on `.claude/agents/34-lab-statistics.md` and `.claude/agents/07-verify-rigor.md` (count stays 46). Tests `test_validate_fallacy_flag_is_advisory_not_blocker` + `test_validate_fallacy_clean_is_silent` in `tests/test_framework.py`. No dependency/install (prose checklist). Counts unchanged: 46·11·8.
- Consequences: reviewers now have a concrete fallacy checklist that lab-statistics runs before reporting numbers and verify-rigor runs when breaking a results claim; fully back-compat (ledgers without the column behave exactly as before). meta-research (https://github.com/AmberLJC/meta-research) evaluated same scan → SKIP (duplicates LIFECYCLE_V3 + phases.yml; "autonomous" framing conflicts with ADR-001/ADR-003). Detail: `cambium_imp/skill-scan/2026-06-26-1046.md`. Green: consistency 46-11-8, doctor healthy, pytest.
