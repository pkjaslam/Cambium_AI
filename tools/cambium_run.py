#!/usr/bin/env python3
"""Cambium auto-runner — turns the agent specs into running workers.

Within a phase, independent agents run CONCURRENTLY (each model call = one session) via a
thread pool; phases run in order; the run STOPS at every human gate. This is I/O-bound, so
concurrency (not CPU cores) is the lever; the real ceiling is your API rate limit + budget.

Modes:
  (default) dry-run : prints the exact execution plan — which agents run in parallel, the model
                      each uses (from the router), and where it stops for you. No API calls.
  --live            : actually calls the model per agent concurrently. Needs ANTHROPIC_API_KEY.
  --resume <phase>  : continue after you approved a gate.

Usage:
  python3 tools/cambium_run.py "<task / RFP path>"            # dry-run plan
  python3 tools/cambium_run.py "<task>" --live --max 5        # live, 5 concurrent sessions
  python3 tools/cambium_run.py "<task>" --resume <phase> --live  # continue AFTER an approved gate (token-enforced)
"""
import os, sys, json, time, csv, subprocess, concurrent.futures as cf
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
    """Return ordered list of (label, [agents], concurrent?) for a phase."""
    out = []
    for key in ("parallel","then","consult","then_parallel","verify_parallel","review"):
        if key in phase:
            ags = phase[key]; conc = "parallel" in key
            out.append((key, ags, conc))
    return out

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
    plan = load_yaml(os.path.join(ROOT,"phases.yml"))
    prov, tiers, cards, mr = router()
    runlbl = time.strftime("%Y%m%d-%H%M%S")
    outdir = os.path.join(ROOT, "agent_outputs", "autorun-"+runlbl)

    print("="*64)
    print("CAMBIUM AUTO-RUNNER  |  task: %s" % task)
    print("mode: %s  |  provider: %s  |  max concurrent sessions: %d" %
          ("LIVE" if live else "DRY-RUN (plan only)", prov, maxc))
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
        if "gate" in ph:
            g = ph["gate"]
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
