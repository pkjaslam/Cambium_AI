#!/usr/bin/env python3
"""Evidence-discipline validator for the Cambium.

Turns the output contract from convention into a check you can run (and wire into CI).
Scans agent_outputs/findings_ledger.csv and reports:
  - rows whose claim_tier is not in the allowed set
  - rows with empty evidence (evidence-or-silence violation)
  - open P0 findings (release blockers)
  - 'Asserted' claims that have not been downgraded or evidenced
Emits governance/provenance.json (a starter provenance manifest) and exits non-zero on any blocker.

Usage:  python3 governance/validate.py [path/to/findings_ledger.csv]
"""
import csv, sys, json, os, datetime

TIERS = {"Proved", "Code-verified", "Asserted", "Open", "info"}
LEDGER = sys.argv[1] if len(sys.argv) > 1 else "agent_outputs/findings_ledger.csv"

def main():
    if not os.path.exists(LEDGER):
        print(f"[validate] no ledger at {LEDGER} (nothing to check yet)"); return 0
    rows = list(csv.DictReader(open(LEDGER, newline="", encoding="utf-8")))
    problems, blockers, agents = [], [], set()
    by_tier = {}
    for r in rows:
        tier = (r.get("claim_tier") or "").strip()
        sev  = (r.get("severity") or "").strip().upper()
        ev   = (r.get("evidence") or "").strip()
        st   = (r.get("status") or "").strip().lower()
        for a in (r.get("agents") or "").split(","):
            if a.strip(): agents.add(a.strip())
        by_tier[tier] = by_tier.get(tier, 0) + 1
        if tier and tier not in TIERS:
            problems.append(f"  bad claim_tier '{tier}' in {r.get('id')}")
        if not ev:
            problems.append(f"  EVIDENCE-OR-SILENCE violation: {r.get('id')} has no evidence")
        if sev == "P0" and st in ("", "open"):
            blockers.append(f"  OPEN P0 (release blocker): {r.get('id')} — {r.get('issue','')[:60]}")
        if tier == "Asserted" and st in ("", "open"):
            problems.append(f"  un-downgraded ASSERTED claim: {r.get('id')}")

    manifest = {
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "ledger": LEDGER, "n_findings": len(rows),
        "tiers": by_tier, "agents_involved": sorted(agents),
        "model": os.environ.get("AI_MODEL", "<set AI_MODEL env to record>"),
        "note": "Provenance manifest. Pair with the AI Use Statement.",
    }
    os.makedirs("governance", exist_ok=True)
    json.dump(manifest, open("governance/provenance.json", "w"), indent=2)

    print(f"[validate] {len(rows)} findings | tiers={by_tier} | agents={len(agents)}")
    if problems:
        print("[validate] WARNINGS:"); print("\n".join(problems))
    if blockers:
        print("[validate] BLOCKERS (do not release):"); print("\n".join(blockers))
        print("[validate] -> provenance.json written; FAILED (open P0).")
        return 1
    print("[validate] OK: no open P0; provenance.json written.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
