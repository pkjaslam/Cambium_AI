# Development Playbook — the post-award engine

*The proven build-verify-synthesize-revise loop, run once a project is in Development. Budget is
unlimited; waste is not (`OUTPUT_CONTRACT.md`).*

## Trigger phrases
| Say | Runs |
|---|---|
| `run lab` | Full dev cycle: Scouts+Labs+Execution -> Verification -> Synthesis -> (approve) Revision -> Validation |
| `run lab review-only` | Reports + synthesis, no edits |
| `run verification` | The audit boards re-attack the current work |
| `run scouts` | Refresh prior-art / methods / landscape |
| `apply P0` | Document Office applies approved fixes |
| `run research lab` | Innovation mode: find a stronger contribution |

## Phases
A **Generate & run** (Scouts, Labs, Execution - parallel) ->
B **Verify** (the 3 Opus boards + domain board run the code) ->
C **Synthesize** (Orchestrator -> `synthesis/master_synthesis.md` + ledger + leaderboard;
  conflicts: code-verified wins; priority Theory>Evidence>Literature>Experiments>Writing) ->
D **Revise** (approval-gated: P0 auto, P1 before/after, P2 recommendations; logged in change_log.md) ->
E **Validate** (re-run 07/08/09 + a scout; emit accept/minor/major/reject + reject-probability).

## Stop condition
No unresolved P0 and reject-probability <=15%.

## Why this is the strong configuration
Verification runs code (findings are evidence, not opinion) · one contract + one ledger make many
agents mergeable · specialize -> verify -> synthesize -> (gated) write keeps unverified claims out of
the deliverable · resumable + single-writer + lane discipline means re-runs cost only what changed.
