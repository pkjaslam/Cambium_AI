---
name: cambium-mode
description: Ask the user how to run a substantial task — Solo (plain, fast, no gates) or the Cambium way (Orchestrator + councils + a human approval gate) — BEFORE starting. Use at the start of any non-trivial request such as evaluate, review, analyze, research, brainstorm, design a study, write a proposal/report/paper, or check results. Do NOT use for quick chat, simple factual lookups, or tiny one-step edits.
---

# Cambium mode picker

Cambium does not take over automatically and never asks "solo or Cambium?" on its own.
This skill adds that choice: before any substantial task, offer the user the two ways to work,
then run the one they pick.

## When to trigger
Trigger at the **start** of a substantial request — anything that would take multiple steps or
produce a real deliverable: *evaluate / review / assess, analyze, research a topic, brainstorm or
rank ideas, design a study or experiment, write a proposal / report / paper / draft, build a budget,
check or reproduce results, prepare a deck.*

Do **not** trigger for: casual conversation, a quick factual question, a one-line lookup, or a
trivial single-step edit. When in doubt for a borderline case, ask briefly rather than assume.

## What to do
1. **Offer the choice and wait.** Present two options (in Cowork, render them as a quick
   pick using the question/choice UI; otherwise ask in one short line):

   - **Solo** — plain Claude handles it directly. Fast, conversational, no councils, no gate.
     Best for drafts, quick looks, and low-stakes work.
   - **Cambium way** — run the institute. The **Orchestrator** dispatches only the councils the
     task needs (Scouts for prior work, Labs to build, **Verification** to audit, Execution to run
     experiments, Support to package), and **stops at a one-page gate card**
     (*decision · options · risks · recommendation · APPROVE / REVISE / REJECT*) before anything is
     finalized. Best for decisions, evaluations, anything that must be trustworthy or submitted.

2. **Honor the answer.**
   - **Solo** → just do the task directly. Don't invoke councils or gates.
   - **Cambium way** → hand off to the Orchestrator workflow: name each council as you use it,
     keep the findings ledger, and present the gate card for the user's APPROVE / REVISE / REJECT
     before delivering. Never finalize, submit, or publish without that approval.

3. **Remember the choice for the session if asked.** If the user says something like "always
   Cambium" or "stay solo from now on," skip the question for the rest of the session and run that
   mode by default until they change it.

## Notes
- The user is always the decider ("the Director"). This skill only surfaces the choice — it does
  not pick for them.
- Equivalent manual triggers exist as slash commands: `/solo <task>` and `/cambium <task>`. If the
  user used one of those, do not ask again — just run that mode.
