# Scout Landscape — Cambium_AI Plugin Gap Analysis
*Generated 2026-06-26 · Quick scan mode*

## Decision (positioning)
Cambium is architecturally sound and differentiates on full-lifecycle governance. Its gaps are concentrated in Cowork surface-layer discoverability and terminal-only tooling that blocks non-developer users.

## Evidence
- Verified: one `plugin.json` at `.claude-plugin/`; no nested duplicate (prior zip bug likely from a now-removed `plugin/` subdir). Current local checkout is clean.
- Verified: 46 agents in both `.claude/agents/` and `agents/` (sync confirmed by `test_plugin_sync.py`).
- Verified: 12 skills in `skills/`, 2 slash commands in `commands/`.
- Verified: CI runs frontmatter check + pytest + doctor + consistency + ledger validation.
- Verified: MCP server ships with 6 tools; `pyproject.toml` is well-formed.
- Verified (Anthropic docs / claude-plugins-official): Cowork surfaces skills prominently; agents are internal delegation targets.

## Gaps / Opportunities (prioritized)

1. **[High] Skill-to-agent discoverability gap** — 12 skills vs 46 agents; most high-value workflows (RFP intake, proposal writing, verification debate) are only reachable via agent internals or trigger phrases buried in docs. Non-terminal Cowork users have no first-class entry point. Fix: add 6-8 lifecycle-phase skills (rfp-intake, proposal, verification, reporting, budget, run-lab) that act as thin wrappers delegating to the Orchestrator, each with tight "Use when / Trigger with" descriptions per Anthropic skill spec.

2. **[High] Cowork zip-packaging fragility** — the prior "two plugin.json" error shows the release packaging is manual and untested. No CI step validates the installable zip. Fix: add a GitHub Actions step that zips the release and asserts exactly one `plugin.json` exists inside; make it a required check on every release tag.

3. **[High] Terminal-only governance tools block Cowork users** — `doctor.py --grade`, `validate.py`, `consistency_check.py` require a terminal. In Cowork (no terminal), users cannot run them. The MCP server exposes equivalents but setup requires manual `claude_desktop_config.json` edits. Fix: add a `health` skill/command that calls the MCP tools (or invokes the scripts via Bash tool internally), making governance checks available in Cowork chat with no terminal.

4. **[Med] `mcp_server/pyproject.toml` version drift** — package is `3.11.0` while `plugin.json` is `3.13.0`. A user installing via uvx gets stale code. Fix: automate version sync assertion in CI; bump both in the same commit.

5. **[Med] No `config.example.yml` wiring in CI or onboarding skill** — `config.example.yml` exists but no skill or command tells a Cowork user to copy it first. TEAM_QUICKSTART.md documents it, but it is a markdown file, not a discoverable entry point. Fix: add a `setup` skill that checks for `config.yml` and scaffolds it from the example, first-run only.

6. **[Med] Agent eval harness is absent** — EVALS.md defines a full rubric (faithfulness, gate discipline, citation integrity) but `tools/agent_eval.py` is flagged "to be wired in v3.2" and missing. CI passes without testing any agent behavior end-to-end. Fix: ship even a minimal smoke-test; add seeded task fixtures per council to `tests/` with deterministic rubric scoring for gate-discipline and citation-integrity sub-scores.

7. **[Med] `plugin.json` missing recommended fields** — `author.email` and `repository` are absent. Anthropic plugin spec lists these as recommended for marketplace search and listing. Fix: add both fields.

8. **[Low] `sync_plugin_agents.py` not enforced in CI** — only called from `push_cambium.bat` (Windows-only). A Linux/Mac contributor who skips it will break `test_plugin_sync`. Fix: call it as the first step in the validate workflow.

9. **[Low] No end-to-end worked example artifact chain** — ROADMAP flags this as priority #1. Fix: publish one complete RFP-to-proposal chain as a static `examples/full-lifecycle/` artifact set; it doubles as an integration test fixture.

10. **[Low] Zip packaging must explicitly exclude local-only dirs** — `cambium_imp/` is gitignored but exists locally; if a contributor packages from a working tree it could pollute the zip. The CI zip step (Gap 2) would catch this, but an explicit `--exclude cambium_imp/` in the packaging script is safer.

## Next Action
Implement Gap 1 (lifecycle skills) and Gap 2 (CI zip validation) together — they directly address the known Cowork install failure mode and are the highest-impact, lowest-risk pair of changes.

## Confidence
Medium-High on gaps 1-5 (directly observed in repo, corroborated by Anthropic plugin docs verified June 2026). Gap 6 inferred from EVALS.md self-description. External best-practice claims verified against anthropics/claude-plugins-official and Anthropic support documentation.
