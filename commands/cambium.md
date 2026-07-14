---
description: Run a task the Cambium way — Orchestrator + the needed councils, with a live run board, real named agents, and a human approval gate before anything is finalized.
argument-hint: <what you want done>
---

Run the following request **the Cambium way**, not solo.

Request: $ARGUMENTS

> ⛔ **FIRST PAINT — do this literally before writing ANY prose.** Your very first action is to run:
>
> ```
> python3 tools/cambium_start.py "$ARGUMENTS"
> ```
>
> Show its output (the branded run board). It resets the run state, prints the text board, writes
> `agent_outputs/run_board.html`, and tells you what to do next. **In Cowork, paint the in-chat live board:
> run `python3 tools/gen_inline_board.py` and pass its stdout to `mcp__visualize__show_widget` (title
> "Cambium run board") so the Director sees the agent boxes + clickable gate in chat — and also publish
> `run_board.html` as a reopenable artifact with `create_artifact` (keep its id). Re-render both each phase.**
> Do NOT answer this request in plain text. If you find yourself about to reply without having shown the
> board, STOP and run the command above first. A plain-text answer to `/cambium` is the one failure this
> command exists to prevent.

> **BOARD-IN-MESSAGE — the Director does NOT see tool stdout.** A board that only exists in a collapsed
> bash result was never shown. After `cambium_start.py`, run `python3 tools/run_trace.py --board --compact "$ARGUMENTS"`
> and paste its output into your reply in a code fence. Then, in Cowork, ALSO paint the visual surfaces
> (inline widget + sidebar artifact) as enhancements. **RENDER-LADDER:** text-in-message is the guaranteed
> layer and always comes first; if `show_widget` / `create_artifact` / the visualize server is absent or
> errors, retry once, then continue without it. A run never stalls on a rendering surface, and a failed
> enhancement never cancels the text.

Hand off to the **Orchestrator** and present the run as the four acts in **docs/concepts/PRESENTATION.md** (read it; it
is the contract). The Cambium way must never look generic — the Director always sees which **named agents**
are working, on what, and where the gates are.

**Act I — Opening (before any work).** The `cambium_start.py` call above IS Act I. After the board is shown
(and, in Cowork, published as the "Cambium run board" artifact), add one plain sentence: how many
specialists, councils, and gates are about to run. Then, as you proceed, keep the live board current with
`python3 tools/run_state.py phase <N>` + `python3 tools/run_trace.py --html --out agent_outputs/run_board.html "$ARGUMENTS"`
and push it to the SAME artifact with `update_artifact`. Do not dispatch before the opening board is shown.

**Act II — Live phases (dispatch REAL agents).** Decompose the goal and dispatch only the councils the
task needs — Scouts (prior-art / methods / landscape), Labs (theory / methods / domain / statistics),
**Verification** (rigor / methodology / evidence / domain + referee), Execution (experiments / ablation /
iteration), Support (record / docs / figures / tidy), plus Pre-Award / Faculty / Governance when relevant.
For each agent, **spawn the real sub-agent** with the Task tool: `subagent_type` = `cambium-institute:<agent-name>`
(e.g. `cambium-institute:scout-landscape`, `cambium-institute:verify-rigor`), and `description` = its
**"Council · Role"** label so the native cards read consistently. Run independent agents in the same phase
**in parallel**. Maintain the live board with `tools/run_state.py` (no hand-edited JSON): at the start of a
phase run `python3 tools/run_state.py phase <N> --note "<what's happening>"`; after the agents write their
`agent_outputs/<name>.md`, run `python3 tools/run_state.py sync --phase <N>` to auto-lift each agent's
finding, then re-emit `python3 tools/run_trace.py --board "$ARGUMENTS"` (it auto-discovers
`agent_outputs/run_state.json`) and, in Cowork, regenerate `run_board.html` and push it with
`update_artifact` (same id) — so the Director watches ✓ done · ▶ now · ○ waiting advance live, with each
agent's one-line finding. Keep `agent_outputs/findings_ledger.csv` current.

**Cadence (anti-spam, anti-stuck).** Do not repaint the full board in chat between phases. At each phase
boundary emit ONE delta line in your message — like `✓ P2 Scouts done · ▶ P3 Labs (4 agents, ~2–4 min,
silent until they report)` — and keep live motion on the widget/artifact, which update in place. Before
any dispatch expected to run longer than ~30 seconds, say how long it should take and that it is silent
until it returns. Prefer two or three smaller dispatch rounds over one long silent phase. The FULL compact
board appears in-message at exactly three moments: the opening, every gate, and the close-out.

**Act III — The gate (SAME-TURN-GATE, non-negotiable).** A gate exists only when the Director can act on
it in the message you are ending. Announcing a gate and stopping — "waiting at the gate" with nothing to
click or answer — is the exact failure this rule kills. At every gate, in ONE message and in this order:
1. Paste the full compact board, then the **gate essence** as message text (about 15 lines): Decision
   needed · Where we are (one line) · Options (a short list, not a table) · Recommendation · the Section-8
   contribution prompt, all drawn from `templates/GATE_SUMMARY.md`. The FULL 8-section one-pager goes to
   the widget gate card and the sidebar artifact — never a thin gate, but never a wall of text in chat.
2. Make the **native ask**: call `AskUserQuestion` — header `Gate <ID>`, question = the gate decision,
   options `Approve — I'll add my note` / `Revise — I'll say what to change` / `Reject — stop here`. The
   click captures the Director's LEANING. For decision gates, collect the required Section-8 contribution
   right after the click (the essence already says so), then run the `gate.py` interlock before recording;
   low-stakes Checkpoints (provision, release) may finalize on the click alone. If `AskUserQuestion` is
   not available, the LAST line of your message is the typed fallback:
   `Gate <ID> — reply APPROVE, REVISE <what to change>, or REJECT.`
3. **One primary control.** The AskUserQuestion card is THE control; the board's gate line says
   `→ choose below`; widget buttons are secondary. On any render failure the gate still exists via text +
   AskUserQuestion (RENDER-LADDER): never skip the ask, and never end the turn without it.
Record the answer in `governance/GATES.md` only after the interlock opens the gate. Never submit, publish,
or finalize without an APPROVE.

**End-to-end (non-negotiable).** Once the Director chose the Cambium way, the WHOLE task stays Cambium —
including the BUILD/implementation after an approval gate. Dispatch the real Execution/Labs agents
(`research-engineer`, `exec-experiments`, `exec-iteration`, `lab-methods`, …) to do the work; do NOT quietly
build it inline yourself. If solo would genuinely be better (e.g. a trivial mechanical edit), **ask the
Director first** ("run the build Cambium or drop to solo for speed?") — never switch to solo silently.

**Act IV — Close-out (part of done).** After approval and the build, run the Support council automatically
(CHANGELOG + decision record, refreshed docs, verified numbers, stray-file check).

**Then TEACH the Director before you declare done. This is required, not a footnote.** For any build or
analysis run, dispatch the teaching-assistant to produce a learning packet for what was just built (a
plain-language explainer, a glossary, flashcards, and a short quiz, filled from `templates/LEARNING_PACKET.md`
into `agent_outputs/learning_packet.md`), and DELIVER it to the Director directly in the chat. Do not just
file it, and do not skip it. Offer the full interactive Learning Lab (`python3 tools/gen_learning_lab.py`) as
the optional next step. Then run `python3 tools/learning_delivery.py check`: if it fails, learning was not
delivered and the run is NOT done. The whole point of Cambium is that the human stays the one who
understands, so a build that taught the Director nothing has not actually closed out.

Finally, paste the final all-✓ compact board in-message (`--board --compact`) with a 3–5 line "what
shipped" summary.

If the request is missing detail you need (which file, what the deliverable is, where to save it), ask one
short clarifying question first, then proceed.

**Shortcut — `/cambium run example`.** If the request is `run e