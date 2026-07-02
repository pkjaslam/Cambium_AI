#!/usr/bin/env python3
"""run_state — maintain the live run-board state (agent_outputs/run_state.json).

The Orchestrator updates this file as a Cambium run advances; tools/run_trace.py auto-discovers it and
draws the live board + HTML dashboard from it — so findings, leaderboard, and the gate banner populate
WITHOUT hand-editing JSON. The headline win is `sync`: it reads each agent's own output file and lifts a
one-line finding automatically, so the board fills in as agents report back.

Subcommands (state file defaults to agent_outputs/run_state.json; override with --file PATH):
  plan "<task>"                                (re)route <task> and write the plan into run_state.json (SSOT)
  phase N [--note "..."]                       set the current phase (+ optional now-note)
  finding <agent> "<one-line>" [--status S]    record one agent's finding (S=done by default); marks it done
  status <agent> <queued|working|done>         set one agent's live status without a finding
  loop <position>                              set loop_position (intra-phase iterate cursor, for handoff)
  gate <ID> "<decision>" [--rec R] [--kind K]  arm the gate banner (K = GATE | Checkpoint)
  cleargate                                    remove the gate banner (after APPROVE)
  lead "agent:score,agent:score,..."           set the leaderboard
  sync [--phase N] [--from DIR]                auto-fill findings from <DIR>/*.md "## Decision" lines
  show                                         print the JSON
  reset                                        start a fresh state file

Typical loop the Orchestrator runs each phase:
  python3 tools/run_state.py phase 2 --note "Scouts surveying the landscape"
  # … dispatch the real agents; they each write agent_outputs/<name>.md …
  python3 tools/run_state.py sync --phase 2          # lifts each agent's Decision line into the board
  python3 tools/run_trace.py --board "<request>"     # auto-reads run_state.json

Note: `phase` prints a ONE-LINE "RE-PAINT THE BOARD NOW" nudge plus the exact repaint command, so the
in-chat board never silently goes stale after phase 1 WITHOUT dumping a 16KB HTML fragment into the
transcript. Pass `--emit` to `phase` when you actually want the rendered board fragment inline.
"""
import sys, os, json, glob, re, time
import cambium_io  # noqa: F401 — reconfigures stdout/stderr to UTF-8 on Windows

ROOT = os.getcwd()
DEFAULT = os.path.join("agent_outputs", "run_state.json")
SKIP = {"run_state.json", "findings_ledger.csv", "master_synthesis.md", "leaderboard.md"}


def _file(args):
    if "--file" in args:
        return args[args.index("--file") + 1]
    return DEFAULT


def _opt(args, flag, default=None):
    return args[args.index(flag) + 1] if flag in args else default


def load(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return {"phase": None, "note": None, "plan": None, "findings": {}, "agent_status": {},
            "leaderboard": [], "gate": None, "loop_position": None}


def save(path, st):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(st, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def _agent_from_file(p):
    return os.path.basename(p)[:-3].replace("_", "-")


def print_repaint_reminder(path, emit=False):
    """After a phase update, the in-chat board must be repainted or it goes stale.

    QUIET by default (audit #9): prints a ONE-LINE nudge plus the exact command to
    repaint. It does NOT dump the ~16KB HTML board fragment into the transcript. Pass
    emit=True (CLI: `phase ... --emit`) only when the caller actually wants the rendered
    fragment inline (e.g. to pipe straight into show_widget). Never raises."""
    try:
        rel = os.path.relpath(path, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    except ValueError:
        # Windows raises ValueError when path and repo are on different drives (repo on D:,
        # a temp run_state.json on C:). The absolute path is still a valid --state argument.
        rel = os.path.abspath(path)
    print("\n[run_state] RE-PAINT THE BOARD NOW: "
          "python3 tools/gen_inline_board.py --state %s   (or gen_board_pro.py for the sidebar board)"
          % rel)
    if not emit:
        return
    tools_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        if tools_dir not in sys.path:
            sys.path.insert(0, tools_dir)
        import gen_inline_board as gib
        frag = gib.render(path, "")
        print("[run_state] --emit: board fragment below (pass straight to show_widget):\n")
        print(frag)
    except Exception:
        print("[run_state] --emit requested but gen_inline_board is not importable; run the command above.")


def _decision_line(md):
    """First substantive line under a '## Decision' (or '## Decision (…)') heading; else first non-heading line."""
    lines = md.splitlines()
    idx = next((i for i, l in enumerate(lines) if re.match(r"##\s+Decision", l.strip(), re.I)), None)
    pool = lines[idx + 1:] if idx is not None else lines
    for l in pool:
        s = l.strip().lstrip("-*0123456789. ").strip()
        if s and not s.startswith("#") and not s.startswith("*Generated"):
            s = re.sub(r"\s+", " ", s)
            return s[:119] + "…" if len(s) > 120 else s
    return None


def cmd_sync(st, args):
    src = _opt(args, "--from", "agent_outputs")
    ph = _opt(args, "--phase")
    if ph is not None:
        st["phase"] = int(ph)
    started = st.get("started_at")
    n = skipped = 0
    for p in sorted(glob.glob(os.path.join(src, "*.md"))):
        if os.path.basename(p) in SKIP:
            continue
        if started and os.path.getmtime(p) < started - 1:   # stale file from an earlier run — ignore
            skipped += 1
            continue
        try:
            line = _decision_line(open(p, encoding="utf-8").read())
        except Exception:
            line = None
        if line:
            st["findings"][_agent_from_file(p)] = line
            n += 1
    print(f"[run_state] synced {n} finding(s) from {src}/"
          + (f" (ignored {skipped} stale file(s) from earlier runs)" if skipped else ""))
    return st


def _route_plan(task):
    """Build the canonical plan block from task_router (the ONE planner). Best-effort:
    returns None if routing fails so a fresh run still starts (boards handle plan=None)."""
    tools_dir = os.path.dirname(os.path.abspath(__file__))
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    try:
        import task_router
        return task_router.plan_state(task)
    except Exception:
        return None


def merged_plan(st):
    """Return the plan's phases with each agent's live finding + status merged in — the
    single shape every board renders. Each agent becomes [council, role, id, finding];
    status per id is available via the returned status map. Read-only (does not mutate st).

    findings: st["findings"] maps bare-id -> one-line string (set by the `finding` cmd).
    status:   st["agent_status"] maps bare-id -> queued|working|done (queued if absent).
    """
    plan = st.get("plan") or {}
    phases = plan.get("phases") or []
    findings = st.get("findings") or {}
    status = st.get("agent_status") or {}
    out = []
    for ph in phases:
        agents = []
        for a in ph.get("agents", []):
            council = a[0] if len(a) > 0 else ""
            role = a[1] if len(a) > 1 else ""
            aid = a[2] if len(a) > 2 else role
            finding = findings.get(aid, a[3] if len(a) > 3 else "")
            agents.append([council, role, aid, finding])
        out.append({"council": ph.get("council", ""), "label": ph.get("label", ""),
                    "gate": ph.get("gate"), "agents": agents})
    return out, {aid: status.get(aid, "queued") for ph in phases for a in ph.get("agents", []) for aid in [a[2] if len(a) > 2 else (a[1] if len(a) > 1 else "")]}


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return
    cmd = a[0]
    path = _file(a)
    st = load(path)

    if cmd == "reset":
        # Fresh per-run state. `started_at` lets `sync` ignore stale agent_outputs/*.md left by
        # earlier runs (this is what kept cross-run findings leaking onto the board).
        note = _opt(a, "--note")
        # SSOT: route the task now and write the plan into run_state.json so every surface
        # (text board + both HTML boards) renders the SAME phases/agents/gates/counts.
        plan = _route_plan(note) if note else None
        st = {"phase": None, "note": note, "plan": plan, "findings": {}, "agent_status": {},
              "leaderboard": [], "gate": None, "loop_position": None, "started_at": time.time()}
    elif cmd == "phase":
        st["phase"] = int(a[1])
        note = _opt(a, "--note")
        if note is not None:
            st["note"] = note
    elif cmd == "loop":
        st["loop_position"] = a[1]
    elif cmd == "plan":
        # (re)route a task into the plan block without wiping findings/progress.
        st["plan"] = _route_plan(a[1])
        if st.get("note") in (None, ""):
            st["note"] = a[1]
    elif cmd == "finding":
        st["findings"][a[1]] = a[2]
        st.setdefault("agent_status", {})[a[1]] = _opt(a, "--status", "done")
    elif cmd == "status":
        st.setdefault("agent_status", {})[a[1]] = a[2]
    elif cmd == "gate":
        st["gate"] = {"id": a[1], "decision": a[2],
                      "kind": _opt(a, "--kind", "GATE"),
                      "recommendation": _opt(a, "--rec", "")}
    elif cmd == "cleargate":
        st["gate"] = None
    elif cmd == "lead":
        pairs = []
        for tok in a[1].split(","):
            if ":" in tok:
                name, sc = tok.rsplit(":", 1)
                try:
                    pairs.append([name.strip(), int(sc)])
                except ValueError:
                    pass
        st["leaderboard"] = pairs
    elif cmd == "sync":
        st = cmd_sync(st, a)
    elif cmd == "show":
        print(json.dumps(st, ensure_ascii=False, indent=2)); return
    else:
        print(f"unknown subcommand: {cmd}\n"); print(__doc__); return

    save(path, st)
    print(f"[run_state] {path} · phase={st['phase']} · {len(st['findings'])} finding(s)"
          + (" · gate armed" if st.get('gate') else ""))

    if cmd == "phase":
        print_repaint_reminder(path, emit=("--emit" in a))


if __name__ == "__main__":
    main()
