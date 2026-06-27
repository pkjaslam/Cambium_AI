---
name: project-management
description: Run an awarded or multi-part project — work breakdown, milestone schedule, deliverables register, roles/responsibilities (RACI), meeting cadence, risk log, and status tracking against plan. Use when planning a project timeline, breaking work into tasks/milestones, coordinating people or subawards, tracking deliverables and deadlines, or running status/risk reviews. Trigger on "project plan", "work breakdown", "milestones", "Gantt", "deliverables", "timeline", "RACI", "risk log", "status report". Pairs with the program-manager and convener agents.
---

# Project management — plan, track, and de-risk delivery

Turns an approved scope into a schedule people can actually execute and a status anyone can read at a
glance.

## Work breakdown (WBS)
Decompose scope → workstreams → tasks. Each task: owner, estimate, dependencies, and a definition of
done. Roll tasks up to **milestones** tied to dates and deliverables.

## Schedule
Order tasks by dependency; mark the critical path (the chain that sets the end date). Express as a simple
table or a text Gantt:
```
Aim 1  ████████░░░░░░  M1 (wk6): data ready
Aim 2      ░░░██████░░  M2 (wk10): model built
Write          ░░░░████  M3 (wk14): report
```

## Deliverables register
| ID | Deliverable | Owner | Due | Status | Depends on |
|----|-------------|-------|-----|--------|------------|
Keep status honest: not-started / on-track / at-risk / done. "At-risk" early beats "late" later.

## Roles (RACI)
For each major task mark who is Responsible, Accountable, Consulted, Informed. One Accountable per task.
For multi-institution awards: subaward scopes, reporting lines, and who signs off each deliverable.

## Cadence & comms
Set a meeting rhythm (e.g., weekly standup, monthly PI review) with agendas + action items. Every action
has an owner and a due date; track open actions to closure (hand stragglers to the feedback-router).

## Risk log
| Risk | Likelihood | Impact | Mitigation | Owner | Trigger |
Review risks at each cadence; promote a triggered risk into a tracked task.

## Status reporting
Report against plan: % milestones on track, what slipped and why, decisions needed, next-period focus.
Honest status, no spin — surface slippage with a recovery plan.

## Guardrails
- A plan without owners and dates is a wish; assign both.
- Track to the baseline; when scope changes, re-baseline explicitly rather than silently sliding dates.
- Escalate blockers early; the human decides priority trade-offs.
