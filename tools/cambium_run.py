#!/usr/bin/env python3
"""Cambium auto-runner — turns the agent specs into running workers.

Within a phase, independent agents run CONCURRENTLY (each model call = one session) via a
thread pool; phases run in order; the run STOPS at every human gate. This is I/O-bound, so
concurrency (not CPU cores) is the lever; the real ceiling is your API rate limit + budget.

Phase source (where the plan comes from):
  default           : reads phases.yml if it exists at repo root (grant/research shape, unchanged).
  --from-router     : force building the phase plan from tools/task_router.py route(task) instead —
                      covers every task type the router classifies (software, review, data, video,
                      report, research, grant), not just the 5 fixed phases.yml phases.
  (auto-detect)     : if phases.yml is missing, falls back to route(task) automatically.
See router_plan_to_phases() below for the adapter that maps route()'s {groups:[...]} shape into
the {parallel/then/consult/...} key-based shape agent_groups() already knows how to execute.
Gate token minting/verification (gate_lock.py) is UNCHANGED either way — only the phase source differs.

Modes:
  (default) dry-run : prints the exact execution plan — which agents run in parallel, the model
                      each uses (from the router), and where it stops for you. No API calls.
  --live            : actually calls the model per agent concurrently. Needs ANTHROPIC_API_KEY.
  --resume <phase>  : continue after you approved a gate.

Usage:
  python3 tools/cambium_run.py "<task / RFP path>"            # dry-run plan
  python3 tools/cambium_run.py "<task>" --live --max 5        # live, 5 concurrent sessions
  python3 tools/cambium_run.py "<task>" --resume <phase> --live  # continue AFTER an approved gate (token-enforced)
  python3 tools/cambium_run.py "build a dashboard" --from-router  # plan from route(), any task type
"""
import os, sys, json, time, csv, subprocess, concurrent.futures as cf
import cambium_io  # noqa: F401 -- reconfigures stdout/stderr to UTF-8 on Windows (glyph-safe printing)
# approx USD per 1M tokens (input, output) — update as model pricing changes
PRICE = {"claude-opus-4-8": (15.0, 75.0), "claude-sonnet-4-6": (3.0, 15.0), "claude-haiku-4-5-20251001": (0.80, 4.0)}
def estimate_cost(model, usage):
    pin, pout = PRICE.get(model, (3.0, 15.0))
    return round(usage.get("input_tokens", 0)/1e6*pin + usage.get("output_tokens", 0)/1e6*pout, 6)
def log_cost(path, row):
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if new: w.writerow(["run","phase","agent","model","input_tokens","output_tokens","wall_s","est_usd"])
        w.writerow(row)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

def load_yaml(p):
    import yaml; return yaml.safe_load(open(p, encoding="utf-8"))

def router():
    import model_router as mr
    cfg, _ = mr.load_config(); prov, tiers = mr.active_tiers(cfg); cards = mr.load_cards()
    return prov, tiers, cards, mr

def agent_groups(phase):
    """Return ordered list of (label, [agents], concurrent?) for a phase.

    Two phase shapes are accepted:
      1. phases.yml shape (legacy): fixed keys directly on the phase dict --
         parallel/then/consult/then_parallel/verify_parallel/review.
      2. router shape (adapter output of router_plan_to_phases): a "groups" list of
         {"label": str, "parallel": bool, "agents": [...]}, already ordered as route()
         produced them. See router_plan_to_phases() for how phase["groups"] is built.
    Both return the same (label, agents, concurrent?) tuples, so every downstream caller
    (main()'s execution loop) works unchanged regardless of which phase source was used.
    """
    if "groups" in phase:
        return [(g["label"], g["agents"], bool(g.get("parallel")) and len(g["agents"]) > 1)
                for g in phase["groups"]]
    out = []
    for key in ("parallel","then","consult","then_parallel","verify_parallel","review"):
        if key in phase:
            ags = phase[key]; conc = "parallel" in key
            out.append((key, ags, conc))
    return out

def router_plan_to_phases(route_result, default_approver="director"):
    """Adapter: map tools/task_router.py route(task)'s plan into the phase list cambium_run
    executes (the same list shape main() iterates, i.e. a list of phase dicts with "id",
    "groups", and optional "gate").

    Why an adapter is needed: route()'s phases use {"id", "groups": [{"label","parallel",
    "agents"}], "gate": {"id","decision"} or None}. phases.yml's phases use fixed keys
    (parallel/then/consult/...) directly on the phase dict, and its gate dict also carries
    "approver". agent_groups() above reads both shapes (see its docstring), so THIS function's
    only job is: (a) pass "id" and "groups" straight through unchanged (no lossy remapping of
    router group labels into the old fixed-key vocabulary), and (b) normalize "gate" so every
    gate dict has "id", "decision", AND "approver" -- route() does not carry an approver, so we
    fill a default ("director") when absent. Gate token minting/verification is untouched;
    this only affects what main() prints and which gate id gate_lock.py is asked to check.

    A phase with no gate keeps "gate": None (never a present-but-empty dict), matching the
    phases.yml convention where phases without a gate simply omit the "gate" key. main()'s
    "if ph.get('gate')" check (not "if 'gate' in ph") treats both as "no gate" safely.

    Returns a list of phase dicts safe to assign to plan["phases"] and iterate exactly like
    the phases.yml path does.
    """
    out_phases = []
    for p in route_result["phases"]:
        gate = p.get("gate")
        if gate is not None:
            gate = {"id": gate["id"], "decision": gate.get("decision", ""),
                     "approver": gate.get("approver") or default_approver}
        out_phases.append({"id": p["id"], "groups": p["groups"], "gate": gate})
    return out_phases

def load_plan(task, args):
    """Decide where the phase plan comes from: phases.yml (default, backward compatible) or
    tools/task_router.py route(task) (via router_plan_to_phases). Returns {"phases": [...]}.

    Precedence (all three preserve existing behavior when neither flag nor router is involved):
      1. --from-router in args -> always build from route(task), regardless of phases.yml.
      2. phases.yml exists at ROOT -> use it (unchanged default path; existing tests rely on
         this: --resume against the grant/research phase ids intake/ideation/proposal/
         development/reporting must keep working exactly as before).
      3. phases.yml missing -> auto-detect: fall back to route(task) so the runner still works
         for repos/checkouts that do not ship a static phases.yml.
    """
    phases_yml_path = os.path.join(ROOT, "phases.yml")
    use_router = "--from-router" in args or not os.path.exists(phases_yml_path)
    if use_router:
        import task_router as tr
        route_result = tr.route(task)
        return {"phases": router_plan_to_phases(route_result)}, route_result["type"]
    return load_yaml(phases_yml_path), None

def agent_spec(name):
    import glob
    for p in glob.glob(os.path.join(ROOT,".claude","agents","*.md")):
        t = open(p, encoding="utf-8", errors="replace").read()
        if ("name: "+name) in t: return t
    return None

def call_model(model, system, user, key):
    """One model call = one session. Uses Anthropic Messages API via stdlib urllib."""
    import urllib.request, json as J
    body = J.dumps({"model": model, "max_tokens": 1200,
                    "system": system, "messages":[{"role":"user","content":user}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body,
            headers={"x-api-key": key, "anthropic-version":"2023-06-01", "content-type":"application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=120) as r:
        d = J.loads(r.read())
    return d["content"][0]["text"], d.get("usage", {}), round(time.time()-t0, 2)

def main():
    args = sys.argv[1:]
    if not args:
        print('Usage: python3 tools/cambium_run.py "<task / RFP path>" [--live] [--max N]'); return 1
    # Single-command quickstart: `cambium_run.py example` (or `run example`) loads a bundled RFP so a
    # brand-new user sees the whole institute mobilize with NO API key. (dean ask #3)
    EXAMPLE_RFP = "examples/demo-from-scratch/RFP.md"  # relative, for a clean banner
    if args and args[0].lower() in ("example", "run") and (args[0].lower() == "example" or
            (len(args) > 1 and args[1].lower() == "example")):
        args = [EXAMPLE_RFP] + [x for x in args if x.startswith("--")]
        print("[cambium] running the bundled example RFP (no API key needed) — examples/demo-from-scratch/RFP.md\n")
    task = args[0]
    live = "--live" in args
    maxc = int(args[args.index("--max")+1]) if "--max" in args else 5
    key  = os.environ.get("ANTHROPIC_API_KEY")
    who  = os.environ.get("CAMBIUM_USER", "")  # identity stamp on logged actions (review #11)
    # --resume <phase_id>: continue AFTER an approved gate. The gate is enforced, not cosmetic:
    # we refuse to skip past a phase's gate unless a valid gate_lock token exists AND the pace interval cleared.
    resume_phase = None
    if "--resume" in args:
        i = args.index("--resume")
        if i + 1 >= len(args):
            print("[cambium_run] --resume requires a phase id, e.g. --resume ideation"); return 1
        resume_phase = args[i + 1]
    plan, routed_type = load_plan(task, args)
    prov, tiers, cards, mr = router()
    runlbl = time.strftime("%Y%m%d-%H%M%S")
    outdir = os.path.join(ROOT, "agent_outputs", "autorun-"+runlbl)

    print("="*64)
    print("CAMBIUM AUTO-RUNNER  |  task: %s" % task)
    print("mode: %s  |  provider: %s  |  max concurrent sessions: %d" %
          ("LIVE" if live else "DRY-RUN (plan only)", prov, maxc))
    if routed_type:
        print("plan source: task_router.route() [--from-router or auto-detected]  |  routed type: %s" % routed_type)
    if live and not key:
        print("\n[!] --live needs ANTHROPIC_API_KEY in the environment. Showing the plan instead.\n"); live=False
    if live: os.makedirs(outdir, exist_ok=True)

    phases = plan["phases"]
    start_index = 0
    if resume_phase:
        idx = next((j for j, ph in enumerate(phases) if ph.get("id") == resume_phase), None)
        if idx is None:
            print("[cambium_run] no phase id '%s' in phases.yml (ids: %s)" %
                  (resume_phase, ", ".join(ph.get("id","?") for ph in phases))); return 1
        gate = phases[idx].get("gate")
        if gate:
            gid = gate["id"]
            # ENFORCE: the gate must hold a valid, fresh, untampered approval token (minted by gate.py --mint).
            if subprocess.run([sys.executable, os.path.join(ROOT, "tools", "gate_lock.py"), "require", gid],
                              cwd=ROOT).returncode != 0:
                print("[cambium_run] BLOCKED: cannot resume past %s — gate %s is not approved. "
                      "Approve it first:\n    python3 tools/gate.py %s --require-contribution "
                      "--contribution c.json --approver \"<you>\" --mint" % (resume_phase, gid, gid)); return 1
            # ENFORCE: deliberation interval (review #10) — no racing through consecutive gates.
            if subprocess.run([sys.executable, os.path.join(ROOT, "tools", "pace_check.py"), "gate", "--gate", gid],
                              cwd=ROOT).returncode != 0:
                print("[cambium_run] BLOCKED: pace interval not cleared for %s." % gid); return 1
        start_index = idx + 1
        print("[cambium_run] resuming after approved gate of phase '%s' (skipping %d completed phase(s))%s.\n"
              % (resume_phase, start_index, (" — operator: " + who) if who else ""))

    print("="*64)

    current_phase = {"id": "?"}
    def run_one(name):
        model = mr.resolve(name, cards, tiers)[1]
        if not live:
            return name, model, "(planned)"
        spec = agent_spec(name) or ("You are the %s agent for Cambium." % name)
        try:
            txt, usage, wall = call_model(model, spec, "TASK: %s\nDo your job per your spec. Be concise." % task, key)
            open(os.path.join(outdir, name+".md"), "w", encoding="utf-8").write(txt)
            cost = estimate_cost(model, usage)
            log_cost(os.path.join(ROOT, "agent_outputs", "cost_log.csv"),
                     [runlbl, current_phase["id"], name, model, usage.get("input_tokens", 0),
                      usage.get("output_tokens", 0), wall, cost])
            # turn-level audit trail (review #7): hash-chained record of this AI interaction (hashes, not plaintext)
            try:
                subprocess.run([sys.executable, os.path.join(ROOT, "tools", "audit_log.py"), "log",
                                "--gate", current_phase["id"], "--agent", name, "--model", model,
                                "--query", "TASK: %s" % task, "--response", txt,
                                "--note", ("operator=" + who) if who else ""],
                               cwd=ROOT, capture_output=True)
            except Exception:
                pass
            return name, model, "done (%d chars, %ss, ~$%.4f)" % (len(txt), wall, cost)
        except Exception as e:
            return name, model, "ERROR "+str(e)[:80]

    for ph in phases[start_index:]:
        current_phase["id"] = ph["id"]
        print("\n### PHASE: %s" % ph["id"])
        for label, ags, conc in agent_groups(ph):
            tag = "PARALLEL (%d sessions at once)" % min(len(ags),maxc) if conc and len(ags)>1 else "sequential"
            print("  %-14s %s" % (label+":", tag))
            if conc and len(ags)>1:
                with cf.ThreadPoolExecutor(max_workers=maxc) as ex:
                    for name, model, st in ex.map(run_one, ags):
                        print("      • %-26s -> %-26s %s" % (name, model, st))
            else:
                for name in ags:
                    nm, model, st = run_one(name)
                    print("      • %-26s -> %-26s %s" % (nm, model, st))
        g = ph.get("gate")
        if g:
            print("  ╔═ GATE %s — %s  (approver: %s)" % (g["id"], g["decision"], g["approver"]))
            print("  ╚═ STOP. Approve with a real contribution + mint the token, then resume:")
            print("       python3 tools/gate.py %s --require-contribution --contribution c.json --approver \"<you>\" --mint" % g["id"])
            print("       python3 tools/cambium_run.py \"%s\" --resume %s --live   (refuses unless the token exists)" % (task, ph["id"]))
            print("     (human-in-the-loop: the run halts here by design)")
            if live:
                print("\n[auto-runner] paused at %s. Outputs so far in %s" % (g["id"], outdir)); return 0
    print("\n[auto-runner] plan complete." + ("" if live else "  Add --live (with ANTHROPIC_API_KEY) to execute."))
    return 0

if __name__ == "__main__":
    sys.exit(main())
