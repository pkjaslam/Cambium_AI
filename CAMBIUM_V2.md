# Cambium v2 — deeper research capability

*v2 makes Cambium not just **plan and judge** research but actually **do** it — adopting the best,
web-verified mechanisms from the leading research-agent systems, and rebalancing the roster toward
doers. Honest attribution: these ideas are inspired by prior systems; Cambium's contribution is
integrating them under one human-governed, evidence-tiered, CI-checked lifecycle.*

## New agents (34 → 39) — all doers/referees, no new admin
| Agent | Council | Tier | Fills the gap |
|---|---|---|---|
| `34-lab-statistics` | Labs | opus | a statistical-analysis **doer** (was advisor-only): fits models, CIs, power, multiplicity, diagnostics |
| `35-exec-iteration` | Execution | sonnet | budget-aware **diagnose→tune→re-run** loop with branch/prune tree-search (was single-shot) |
| `36-research-engineer` | Execution | sonnet | clean, tested, **reproducible** experiment code + envs/seeds/Makefiles |
| `37-referee` | Verification | opus | **venue-rubric reviewer**: accept/major/minor/reject per criterion + reject-probability |
| `38-idea-tournament` | Pre-Award | sonnet | **Elo pairwise** hypothesis ranking + reflect/evolve (replaces noisy 0–10 scoring) |

## Adopted mechanisms (verified) and their source
| Adopted | Inspired by | Where it lives in Cambium |
|---|---|---|
| Literature **novelty gate** before committing to an idea | Sakana *AI Scientist* | upgraded `01-scout-prior-art` + a check before Gate G2 |
| **Generate → reflect → rank (Elo) → evolve** idea tournament | Google *AI Co-Scientist* | `38-idea-tournament` (+ `26-ideation-facilitator`) |
| **Scored self-refinement** loop (mle/paper-solver style) | *Agent Laboratory* | `35-exec-iteration` (experiments) + `37-referee` feedback (deliverable) |
| **Tree-search** experiment exploration (budget-aware) | *AI Scientist* (BFTS) | `35-exec-iteration` |
| **Automated reviewer** scoring vs a venue rubric | *AI Scientist* | `37-referee` |
| **Cross-project institutional memory / recall** | *AutoGen* | upgraded `14-record-keeper` |

## NOT adopted (already present or superior in Cambium)
Recorded human-approval gates, manager/router dispatch, code-running verification, field-agnostic
faculty, an explicit governance policy — Cambium already has these; the competitors mostly don't.

## New loops / protocols (see DEVELOPMENT_PLAYBOOK.md)
- **Idea Tournament** (`run tournament`) — Elo-ranked, faculty-judged, evolve rounds → ranked slate → G2.
- **Novelty Gate** — `01-scout-prior-art` returns a novelty score + nearest prior art before G2; a near-duplicate is flagged.
- **Refinement Loop** (`iterate experiment`) — `35-exec-iteration` improves until target/plateau/budget; `37-referee` drives deliverable revision until the score clears.
- **Referee pass** (`referee`) — score the draft vs the target venue before G3/G6.
- **Adversarial Debate** — for a contested claim, two verify boards argue opposing sides and a third judges (run inside `run verification`).

## Roster balance
v1: ~5 doers : ~14 support. v2 adds 4 doers + 1 referee → execution capacity roughly doubles, with no
new administrative overhead.
