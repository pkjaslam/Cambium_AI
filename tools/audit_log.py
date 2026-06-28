#!/usr/bin/env python3
"""audit_log — turn-level, append-only audit trail (review Fix #2 residual).

Gate-level records (GATES.md, CONTRIBUTION_LEDGER) already capture decisions; this closes the remaining
gap: a single timestamped row per AI interaction that joins the user query, the agent + model, the AI
response, and the final human action. Content is stored as a **sha256 hash, not plaintext**, so the trail
is verifiable and tamper-evident without persisting regulated/PII text (see governance/REGULATED_DATA.md).

  python3 tools/audit_log.py log --gate G2 --agent scout-landscape --model claude-sonnet-4-6 \
       --query-file q.txt --response-file r.txt [--human-action APPROVE] [--note "..."]
  python3 tools/audit_log.py log --gate G2 --agent x --model m --query "text" --response "text"
  python3 tools/audit_log.py show [--n 20]        # tail the trail
  python3 tools/audit_log.py verify               # re-hash chain; exit 1 if any row was tampered

Append-only JSONL at governance/audit_trail.jsonl. Each row carries a `chain` hash over the previous
row + this row's fields, so editing or deleting a past row breaks the chain (detected by `verify`).
Exit: 0 ok · 1 verify failure / bad args.
"""
import argparse, hashlib, json, os, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAIL = os.path.join(ROOT, "governance", "audit_trail.jsonl")
SALT = "cambium-audit-v1"  # tamper-evidence salt (not a secret)

def _sha(*parts):
    return hashlib.sha256(("\x1f".join(str(p) for p in parts) + SALT).encode("utf-8", "replace")).hexdigest()

def _hash_text(s):
    return hashlib.sha256((s or "").encode("utf-8", "replace")).hexdigest()

def _last_chain():
    if not os.path.exists(TRAIL):
        return "GENESIS"
    last = "GENESIS"
    for line in open(TRAIL, encoding="utf-8"):
        line = line.strip()
        if line:
            try: last = json.loads(line).get("chain", last)
            except Exception: pass
    return last

def append(gate, agent, model, query, response, human_action, note):
    os.makedirs(os.path.dirname(TRAIL), exist_ok=True)
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    prev = _last_chain()
    qh, rh = _hash_text(query), _hash_text(response)
    row = {"ts": ts, "gate": gate, "agent": agent, "model": model,
           "query_sha": qh, "response_sha": rh,
           "human_action": human_action or "", "note": note or "", "prev": prev}
    row["chain"] = _sha(prev, ts, gate, agent, model, qh, rh, row["human_action"])
    with open(TRAIL, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
    return row

def verify():
    if not os.path.exists(TRAIL):
        print("[audit_log] no trail yet (nothing to verify)."); return 0
    prev = "GENESIS"; n = 0
    for i, line in enumerate(open(TRAIL, encoding="utf-8"), 1):
        line = line.strip()
        if not line: continue
        r = json.loads(line); n += 1
        if r.get("prev") != prev:
            print("[audit_log] BROKEN CHAIN at row %d: prev mismatch (a row was inserted/deleted)." % i); return 1
        expect = _sha(prev, r["ts"], r["gate"], r["agent"], r["model"], r["query_sha"], r["response_sha"], r["human_action"])
        if r.get("chain") != expect:
            print("[audit_log] TAMPERED row %d: a field was edited after logging." % i); return 1
        prev = r["chain"]
    print("[audit_log] OK: %d row(s), hash chain intact." % n); return 0

def _read(path, inline):
    if path and os.path.exists(path):
        return open(path, encoding="utf-8", errors="replace").read()
    return inline or ""

def main(argv=None):
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd")
    pl = sub.add_parser("log")
    pl.add_argument("--gate", default="-"); pl.add_argument("--agent", required=True); pl.add_argument("--model", required=True)
    pl.add_argument("--query"); pl.add_argument("--query-file"); pl.add_argument("--response"); pl.add_argument("--response-file")
    pl.add_argument("--human-action", default=""); pl.add_argument("--note", default="")
    ps = sub.add_parser("show"); ps.add_argument("--n", type=int, default=20)
    sub.add_parser("verify")
    a = ap.parse_args(argv)
    if a.cmd == "log":
        row = append(a.gate, a.agent, a.model, _read(a.query_file, a.query), _read(a.response_file, a.response),
                     a.human_action, a.note)
        print("[audit_log] logged %s · %s · %s · chain=%s…" % (row["gate"], row["agent"], row["model"], row["chain"][:12]))
        return 0
    if a.cmd == "show":
        if not os.path.exists(TRAIL): print("[audit_log] (empty)"); return 0
        rows = [l for l in open(TRAIL, encoding="utf-8") if l.strip()][-a.n:]
        for l in rows:
            r = json.loads(l)
            print("%s  %-4s  %-22s  %-22s  %s" % (r["ts"], r["gate"], r["agent"], r["model"], r["human_action"]))
        return 0
    if a.cmd == "verify":
        return verify()
    ap.print_help(); return 0

if __name__ == "__main__":
    sys.exit(main())
