# INTERPRETATION FALLACY CHECKLIST — <Project Name>
*Attach to any deliverable whose claims rest on a results/statistics section.
Run by `34-lab-statistics` (before reporting numbers) and audited by `07-verify-rigor`
(when breaking the claim). Each "flag" is an ADVISORY signal — record it in the ledger's
optional `fallacy_check` column; `governance/validate.py` surfaces it as a WARNING, never
a blocker. Companion to `REPRODUCIBILITY_CHECKLIST.md`.*

How to use: for every headline result, walk the list. Mark each `[ ] clear` /
`[x] flagged`. If any box is flagged, set the ledger row's `fallacy_check` to the
fallacy name (e.g. `simpsons-paradox`) and write the mitigation in `evidence`.

## Aggregation & subgroup structure
- [ ] **Simpson's paradox** — does the aggregate direction reverse within subgroups? Report the stratified result, not only the pooled one.
- [ ] **Ecological fallacy** — are group-level correlations being read as individual-level effects (or vice versa)?

## Sampling & selection
- [ ] **Survivorship / selection bias** — were failures, dropouts, or non-responders excluded from the sample the claim generalizes to?
- [ ] **Base-rate neglect** — does the interpretation ignore prior prevalence (e.g. a "90% accurate" test on a rare condition)?

## Multiplicity & researcher degrees of freedom
- [ ] **Multiple comparisons / p-hacking** — how many hypotheses/specs were tested? Is the reported p corrected (FDR/Bonferroni) or cherry-picked?
- [ ] **HARKing** — is a hypothesis presented as a priori that was actually formed after seeing the data? Separate exploratory vs confirmatory.
- [ ] **Optional stopping** — was data collection stopped when significance appeared, rather than at a pre-registered N?

## Effect, signal & causality
- [ ] **Regression to the mean** — could an apparent improvement be expected drift from an extreme baseline rather than a real effect?
- [ ] **Confounding** — is a third variable driving both? Is the comparison adjusted, randomized, or just observational?
- [ ] **Correlation ≠ causation** — does the wording assert a causal mechanism the design (observational) cannot support?

## Reporting integrity
- [ ] **Overfitting reported as result** — is the headline number from the training/selection set rather than held-out/test data?
- [ ] **Significance ≠ importance** — is a statistically significant but trivially small effect being sold as practically meaningful? Is uncertainty (CI/SE) reported, not point-only?

Result: CLEAN / FLAGGED (list fallacies) —  (reviewer, date)
*If FLAGGED, every flagged claim must be repaired, downgraded a tier, or explicitly scoped before release.*
