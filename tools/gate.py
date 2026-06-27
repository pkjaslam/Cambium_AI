#!/usr/bin/env python3
"""gate — the live gate interlock (eval suggestion #3).

Before a human gate can open, the production findings ledger MUST pass governance/validate.py.
This turns "human-in-the-loop by convention" into an enforced precondition for the whole
validator-checkable surface: an open P0, an un-evidenced `Code-verified` claim, or an unresolved
citation BLOCKS the gate (exit 1) — the Director never even reaches APPROVE on a broken ledger.

Usage:
  python3 tools/gate.py <GATE_ID> [--ledger PATH]   # exit 1 = BLOCKED, exit 0 = open for decision
"""
import sys, os, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def check(gate_id, ledger):
    r = subprocess.run([sys.executable, os.path.join(ROOT, "governance", "validate.py"), ledger],
                       capture_output=True, text=True)
    out = (r.stdout or "").strip() or (r.stderr or "").strip()
    if out: print(out)
    if r.returncode != 0:
        print(f"\n  ⛩ GATE {gate_id} — BLOCKED. Release-blocking findings in {ledger}; "
              f"resolve them before this gate can open.")
        return 1
    print(f"\n  ⛩ GATE {gate_id} — clear of blockers; open for the Director's APPROVE / REVISE / REJECT.")
    return 0

def main():
    a = sys.argv[1:]
    if not a: print(__doc__); return 0
    gate_id = a[0]
    ledger = a[a.index("--ledger")+1] if "--ledger" in a else os.path.join(ROOT,"agent_outputs","findings_ledger.csv")
    if not os.path.exists(ledger):
        print(f"[gate] no production ledger at {ledger} — nothing to block; gate {gate_id} open."); return 0
    return check(gate_id, ledger)

if __name__ == "__main__": sys.exit(main())
