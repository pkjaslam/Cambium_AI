#!/usr/bin/env python3
"""dispatch_plan -- turn route(task) into a literal, copy-ready dispatch script.

The orchestrator (an LLM in the Cowork chat path) has near-zero agent-naming decisions
left: this reads tools/task_router.py's route(task) -- the same CMAP, phase/group
structure already in the repo -- and renders one Markdown block per phase with the
EXACT Task(...) call to make for every agent, in order, with parallel groups marked
and a literal "STOP: gate <id>" line wherever route() places a gate.

It is purely derived from route(): it reads nothing else, invents nothing, and cannot
drift from what the router decides. If route() changes, this output changes with it.
It does NOT read phases.yml -- that is a separate, hand-authored static plan consumed
by cambium_run.py; route() and phases.yml are two different plans today (see
agent_outputs/research-engineer.md for the design note on that gap).

This is a formatting tool, not a runtime interlock: nothing forces the orchestrator to
use it, and nothing here mints a gate token. Real gate enforcement lives in
gate_lock.py (called from cambium_run.py --resume).

Usage:
  python3 tools/dispatch_plan.py "the task"
  python3 tools/dispatch_plan.py "the task" --profile "interests: soil health; expertise: agronomy"
  python3 tools/dispatch_plan.py "the task" --format txt
"""
from __future__ import annotations
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cambium_io  # noqa: F401 -- UTF-8 stdout/stderr guard on Windows
import task_router


def _stub_prompt(task: str, agent: str, role_label: str) -> str:
    """One-line prompt stub for a Task(...) call. Short on purpose -- the real
    per-agent instructions live in .claude/agents/<agent>.md; this is a pointer,
    not a replacement for the agent's own spec."""
    task_short = " ".join(str(task).split())
    if len(task_short) > 90:
        task_short = task_short[:89] + "..."
    return f"TASK: {task_short}\\nRole: {role_label}. Be concise; cite sources where relevant."


def _role_label(agent: str) -> str:
    """Human-readable role label derived from the agent id, e.g. scout-landscape -> Scout Landscape."""
    return agent.replace("-", " ").title()


def dispatch_plan(task: str, profile: str | None = None, format: str = "md") -> str:
    """Build the literal, copy-ready dispatch block for *task*.

    Returns a Markdown string: for each phase in route(task)["phases"], a heading,
    then one line per agent giving the exact Task(...) call. Parallel groups are
    marked; every gate route() places renders as a "STOP: gate <id>" line.

    format="txt" renders the same content without Markdown heading/list markup
    (plain indented text), for callers that cannot render Markdown.
    """
    r = task_router.route(task)
    lines: list[str] = []
    md = format != "txt"

    if md:
        lines.append(f"# Dispatch plan: {task}")
        lines.append("")
        lines.append(
            f"Derived from `task_router.route()` -- type **{r['type']}**, "
            f"{r['n_agents']} agent(s), {len(r['phases'])} phase(s). "
            "Do not invent agent names or skip phases; execute this block verbatim."
        )
        lines.append("")
    else:
        lines.append(f"DISPATCH PLAN: {task}")
        lines.append(
            f"(from task_router.route() -- type={r['type']}, agents={r['n_agents']}, phases={len(r['phases'])})"
        )
        lines.append("")

    for p in r["phases"]:
        pid = p["id"]
        if md:
            lines.append(f"## PHASE: {pid}")
            lines.append("")
        else:
            lines.append(f"PHASE: {pid}")

        for g in p["groups"]:
            label = g["label"]
            agents = g["agents"]
            parallel = bool(g.get("parallel")) and len(agents) > 1

            if md:
                tag = " (run in parallel -- one message block, all Task() calls together)" if parallel else " (sequential)"
                lines.append(f"### Group: {label}{tag}")
                lines.append("")
            else:
                tag = " [PARALLEL -- dispatch together]" if parallel else " [sequential]"
                lines.append(f"  Group: {label}{tag}")

            for agent in agents:
                role_label = f"{label} / {agent}"
                prompt = _stub_prompt(task, agent, role_label)
                desc = f"{label.title()} - {_role_label(agent)}"
                call = (
                    f'Task(subagent_type="cambium-institute:{agent}", '
                    f'description="{desc}", '
                    f'prompt="{prompt}")'
                )
                if md:
                    lines.append(f"- [ ] {call}")
                else:
                    lines.append(f"    {call}")
            if md:
                lines.append("")

        if p.get("gate"):
            gid = p["gate"]["id"]
            decision = p["gate"].get("decision", "your decision")
            stop_line = f'STOP: gate {gid} - {decision}. Show the gate card and wait.'
            if md:
                lines.append(f"> **{stop_line}**")
                lines.append("")
            else:
                lines.append(f"  {stop_line}")
                lines.append("")

    if md:
        lines.append("---")
        lines.append(
            "This block is purely derived from `route()`; it cannot drift from the "
            "router's decision. It is a formatting aid, not a runtime interlock -- "
            "real gate enforcement is `gate_lock.py` (see `cambium_run.py --resume`)."
        )

    if profile:
        # profile is accepted for CLI/API parity with route()'s researcher-profile
        # guard (task_router.require_researcher_profile), but route() itself does
        # not consume profile, so this is documented, not silently dropped.
        note = f"(researcher profile supplied: {str(profile)[:60]})"
        lines.append("")
        lines.append(note if not md else f"*{note}*")

    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=(
            "Turn task_router.route(task) into a literal, copy-ready dispatch script "
            "so the orchestrator executes a plan instead of inventing one."
        )
    )
    ap.add_argument("task", help="The task to route, e.g. \"win an NSF grant on soil health\".")
    ap.add_argument(
        "--profile",
        default=None,
        help="Optional researcher profile string (interests/expertise), passed through for record only.",
    )
    ap.add_argument(
        "--format",
        choices=["md", "txt"],
        default="md",
        help="Output format (default: md).",
    )
    args = ap.parse_args(argv)

    print(dispatch_plan(args.task, profile=args.profile, format=args.format))
    return 0


if __name__ == "__main__":
    sys.exit(main())
