# Efficacy study: recruiting log and run runbook

The v1 human-judged efficacy study is built and pre-registered (`V1_DESIGN.md`, `PROTOCOL.md`, `BUDGET.md`,
and the harness in this directory). What remains is external: the live model runs and two arm-blind human
raters plus an adjudicator. This file is the recruiting log and the one-command runbook so the maintainer's
part is a short, ordered checklist. It fabricates no data and starts no run on its own.

## Status
- Design and harness: DONE (in this directory).
- Model runs: NOT STARTED (needs an API key or a claude login).
- Raters: NOT RECRUITED. Panel decided: one university RA or grad rater, one professional annotator, one
  adjudicator. Rater rate set by the Director. Budget about 31 rater-hours (see BUDGET.md).

## Recruiting log (fill as you go)
| Date | Person or role | Contact sent | Accepted | Calibration done | Notes |
|---|---|---|---|---|---|
|  | rater A (RA/grad) |  |  |  |  |
|  | rater B (professional annotator) |  |  |  |  |
|  | adjudicator |  |  |  |  |

The invitation email, rubric one-pager, and calibration instructions are drafted in the workspace file
`rater_recruitment_packet.md`; personalize and send them.

## Runbook (the ordered human steps)
1. Freeze the study commit and set the rater rate. Approve the spend (about model compute plus rater hours).
2. Produce the outputs: `python3 evals/enforcement_study/run_arm.py --arm both` with your API key or login.
3. Blind them: `python3 evals/enforcement_study/blind.py` writes the arm-blind rater packet and a sealed
   manifest you keep. Never let a rater see the manifest.
4. Recruit the three people above; run the five-item calibration round first; require Cohen kappa >= 0.6
   before real scoring.
5. Each rater scores in `rater_ui.html` and exports `ratings_<id>.json`.
6. Analyze: `python3 evals/enforcement_study/analyze_stage2.py --ratings panel/ratings_*.json` writes
   `RESULTS_V1.md`. Pre-commit the sample size and seed; no peeking, no optional stopping.
7. Publish the result whichever way it points; regenerate the dashboard (it reads RESULTS) and update the
   README claim to match the evidence.

## Honesty
A null is a real, publishable outcome and is reported as such. The panel is the instrument; the model spend
just produces the outputs they read. Nothing here can be run to completion without the people and the spend.
