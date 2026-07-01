# Two ways to run Cambium: convenient and strict

Cambium runs in two modes with different guarantees. Be honest about which one you are using, because
they are not the same on the question that matters most: does the process actually run as designed.

## Chat mode: /cambium in Cowork or Claude Code (convenient, best-effort)

The orchestrator is a language model following the contract in PRESENTATION.md. It paints the board,
dispatches the routed agents, and stops at the human gates. This is the easy, interactive way to run.

Its honest limit: nothing inside a single chat turn can force a language model to spawn a sub-agent, so a
chat orchestrator can skip steps or improvise. Two aids reduce that, without pretending to remove it:

- `tools/dispatch_plan.py "<task>"` turns `route(task)` into the literal agent calls to make, phase by phase,
  with stop-at-gate lines. The orchestrator executes a plan instead of inventing one.
- `tools/run_fidelity.py "<task>"` prints a close-out scorecard comparing the routed plan against what
  actually happened (which agents produced output, phase progress, gate recorded, learning delivered). A gap
  is shown to you so you can say "redo X". It is advisory and post-hoc, and it never blocks the run.

## Programmatic mode: tools/cambium_run.py (strict, guaranteed)

Here code, not a model, drives the run. It computes the phases (now from `route(task)` for any task type,
via `--from-router`, or from `phases.yml`), invokes the agents in order, and enforces gates with unforgeable
tokens (`gate_lock.py`, minted only after the checks pass). A chat "APPROVE" cannot forge a token. Use this
mode when you need a real guarantee that the process ran as designed.

## Which to use

Use chat mode for interactive, exploratory work; the dispatch plan and the fidelity scorecard make it much
more reliable. Use the programmatic runner when the guarantee matters, because only the runner enforces.

Honest note: nesting a dedicated orchestrator sub-agent, so that an agent rather than the chat assistant does
the dispatching, is not verified on this platform and is not promised here.
