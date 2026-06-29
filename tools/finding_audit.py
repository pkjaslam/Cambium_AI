#!/usr/bin/env python3
"""finding_audit — independent check on agents' self-reported findings (eval suggestion #6).

The run board lifts each agent's own `## Decision` line; agents have been observed claiming completion
or verification they didn't actually do. This scans agent_outputs/*.md and FLAGS any output that asserts
done/verified/green WITHOUT supporting evidence (a command marker, a file:line, or real tool output like
"consistency"/"doctor"/"pytest"/"passed"). Advisory: exit 1 lists unsupported self-reports for a human to
check; it does not trust the agent's word as proof.

Usage: python3 tools/finding_audit.py [--dir agent_outputs]
"""
import sys, os, re, glob
import cambium_io  # noqa: F401 — reconfigures stdout/stderr to UTF-8 on Windows
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLAIM = re.compile(r"\b(code-verified|all green|tests? pass|shipped|done|verified green|PASS\b|complete)\b", re.I)
EVID  = re.compile(r"(cmd:|```|\$ |\bfile:|\bline \d|consistency|doctor|pytest|passed|exit 0|sha256|reproduce)", re.I)
SKIP  = {"run_state.json","findings_ledger.csv","HANDOFF.md","master_synthesis.md","leaderboard.md"}

def audit(d):
    flags = []
    for p in sorted(glob.glob(os.path.join(d, "*.md"))):
        if os.path.basename(p) in SKIP: continue
        t = open(p, encoding="utf-8", errors="replace").read()
        if CLAIM.search(t) and not EVID.search(t):
            flags.append(os.path.relpath(p, ROOT))
    if flags:
        print("[finding_audit] UNSUPPORTED self-reports (claim completion/verification, no evidence):")
        for f in flags: print("  ?  " + f)
        print(f"[finding_audit] {len(flags)} flagged — a human/integrity-officer should verify before trusting.")
        return 1
    print("[finding_audit] OK: every completion/verification claim carries evidence (or none made).")
    return 0

def main():
    a = sys.argv[1:]
    d = a[a.index("--dir")+1] if "--dir" in a else os.path.join(ROOT, "agent_outputs")
    return audit(d)

if __name__ == "__main__": sys.exit(main())
