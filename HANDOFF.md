# HANDOFF: orchestrator-fidelity fix (RESOLVED: nothing to resume)

> **RESOLVED 2026-07-01 (v1.36.0).** This handoff completed: the four-piece fidelity design plus the
> orphan routing shipped in v1.35.0 (gate G-fidelity), and the independent-review closeout that followed
> shipped in v1.36.0 (gates G-ledger-repair, G-dashboard-amend). Kept for the record only.

Written 2026-06-30 before a session restart to reconnect the folder mount so tests can run live.
All work is on disk. The design from this run is in agent_outputs/research-engineer.md and
agent_outputs/verify-methodology.md.

## What the run was doing
The Director asked for the real fix to a recurring problem: the chat-path orchestrator sometimes does
not send the routed agents and improvises instead. Design phase finished (Execution + Verification), the
gate was presented, and the Director then asked to VERIFY every agent has a real assigned task before
approving, then chose to restart to restore the sandbox mount so the build can be tested live.

## Approved design (bring to the gate, then build)
Four pieces plus an orphan-routing precondition:
1. dispatch_plan.py: turn route(task) into the literal, copy-ready agent Task calls per phase, with
   stop-at-gate lines, so the orchestrator executes a plan instead of inventing one.
2. run_fidelity.py: a per-run close-out scorecard comparing route()'s expected agents/phases/gate/learning
   against the real records (agent_outputs/*.md, run_state.json, GATES.md, learning_delivery). Advisory,
   post-hoc, shown to the Director so skips are visible. Two highest-value checks: agent coverage, phase progress.
3. THE DEEP FIX (needs the mount + tests, do this now that we are reconnected): make tools/cambium_run.py
   consume route(task) instead of the static, disconnected phases.yml, so real code-driven gate enforcement
   (gate_lock.py tokens) covers every task type, not just grant/research. Run the full suite before shipping.
4. Honest two-modes docs: chat /cambium is convenient best-effort; the programmatic runner is strict and
   guaranteed. Nesting an orchestrator sub-agent is unverified, so do not promise it.

## Orphan finding (fix as part of the build) -- the Director's precondition
Audited all 46 agents against tools/task_router.py CMAP and the phase builders. 44 are dispatched by some
route; the orchestrator is the conductor. TWO are orphans, never dispatched by any task type:
- partnership-liaison (Partnerships council): the grant path only dispatches collaborator-scout and convener.
  Fix: add a partnerships step to the grant path (or a light partnerships task type) so it is routed.
- program-manager (Partnerships council): there is NO post-award / project-management task type in TYPES.
  Fix: add a post-award "project" task type (work breakdown, milestones, subaward tracking, reporting cadence)
  so program-manager runs.
After this, every one of the 46 is reachable and run_fidelity can honestly check agent coverage.

## Director's decision options (re-present at the gate on resume)
- Approve all four + orphan routing (now testable live since the mount is back), OR
- Approve 1, 2, 4 + orphan routing; defer 3.
Recommended now that tests can run: all four + orphan routing, verified with pytest before push.

## Also pending (separate, already staged this session)
- Repo cleanup git rm script was handed to the Director (untrack agent_outputs, drop branded/stale files);
  still needs running on their machine, then push.
- examples/ai4ra/ needs a careful de-brand RENAME (referenced by rules_handoff.py + tests), not a delete.
- On push: push_cambium.bat regenerates assets + tool index and sync_version stamps the version (now 1.33.0
  in manifests; CHANGELOG is at 1.34.0, so the next push bumps everything to 1.34.0).

## To resume
Say "resume the orchestrator-fidelity fix". Confirm the mount is back (bash can read the repo), re-present the
gate, and on APPROVE build the orphan routes + the chosen pieces, running pytest live before declaring done.
