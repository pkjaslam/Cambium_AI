# Preprint outline: a governed multi-agent research framework with a pre-registered efficacy study

Purpose: a systems-and-methods paper that is publishable whichever way the efficacy study lands, because
the contribution is the governed architecture and the honest, pre-registered evaluation of it, not a
claimed win. This is an outline for the maintainer to develop; it invents no results.

## Working title
Governed multi-agent research assistance: enforcing honesty by construction, and measuring whether it helps.

## Abstract (to write after the v1 study runs)
State the problem (AI speeds research but can overclaim, fabricate citations, outrun judgment, and blur
authorship), the approach (councils plus human gates plus an evidence contract wired to runnable checks),
and the headline number from the v1 study reported honestly, including a null if that is the result.

## 1. Introduction
The risk AI poses to the research record; why a policy page is not enough; the thesis that honesty should be
plumbing (a check in CI, a gate a person signs) rather than a promise.

## 2. Related work
Multi-agent frameworks; research-assistant tooling; evaluation of LLM honesty and hallucination; governance
and provenance in computational science.

## 3. System design
The 46-agent, 11-council architecture; the eight human gates; the four-tier evidence contract; the
deterministic checks (doctor, consistency, enforcement, provenance); routing as code with a golden suite;
the audit hash chain and the readable gate ledger.

## 4. Enforcement by construction
Which controls are enforced by code versus prompt, stated honestly; gate tokens; the tool-budget and
version interlocks; the cross-model adversarial review that found real defects in the framework itself.

## 5. Pre-registered efficacy study
The pre-registration (design in `evals/enforcement_study/V1_DESIGN.md`): does enforced governance reduce
the false-claim rate versus a soft prompt? Arms, the 102-task set, the two arm-blind human raters plus
adjudicator, the power analysis, and the analysis plan. Report the result as it comes out.

## 6. Results
The measured false-claim delta with confidence bounds; secondary outcomes (citation integrity, over-claim
rate); inter-rater reliability. Report a null plainly if that is what the data show.

## 7. Threats to validity
Near-ceiling models, judge generalization, task-set representativeness, single-maintainer construction.

## 8. Discussion and limitations
What a governed framework does and does not buy; the honest boundary that the framework advises and the
human decides.

## 9. Availability
MIT-licensed, local-first, on GitHub; the study harness and pre-registration are in the repository.

## Target venues (author to choose)
A systems or open-science venue, or arXiv cs.SE / cs.HC as a preprint first. The study result does not
gate submission; the honest evaluation is the contribution.
