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

## v2 loops & triggers (deeper research)
| Say | Runs |
|---|---|
| `run tournament` | Idea-Tournament: Elo pairwise ranking + faculty judging + evolve rounds -> ranked slate (before G2) |
| `iterate experiment` | exec-iteration: budget-aware diagnose->tune->re-run with branch/prune tree-search |
| `referee` / `referee for <venue>` | Referee scores the deliverable vs the venue rubric (accept/major/minor/reject) before G3/G6 |
| `run verification debate` | two verify boards argue opposing sides of a contested claim; a third judges |
Novelty gate: `01-scout-prior-art` returns a novelty score + nearest prior art automatically before G2;
a near-duplicate idea is flagged for the President. Institutional memory: `14-record-keeper` recalls
relevant prior projects before dispatch.
