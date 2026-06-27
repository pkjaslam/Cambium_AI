#!/usr/bin/env python3
"""provenance — a machine-checkable provenance manifest for Code-verified claims.

Each `Code-verified` claim in a findings ledger must carry a rerun command (an `evidence`/`action`
field containing `cmd: <command>`). This tool RE-RUNS each such command, hashes the command + any
referenced script file + the captured output, and writes a manifest linking claim -> rerun + hashes.
`--check` re-runs everything and FAILS (exit 1) if any output hash drifts — turning "Code-verified by
convention" into "Code-verified by reproduction".

Ledger schema (CSV): id,issue,agents,severity,claim_tier,evidence,status,action  (extra columns ok).
Rerun command: put `cmd: <shell command>` in the row's `evidence` or `action` cell.

Usage:
  python3 tools/provenance.py build <ledger.csv> [--out manifest.json] [--cwd DIR]
  python3 tools/provenance.py check <manifest.json> [--cwd DIR]
"""
import sys, os, re, csv, json, time, hashlib, subprocess, shlex

def sha(b): return hashlib.sha256(b if isinstance(b,bytes) else b.encode()).hexdigest()

def _cmd_of(row):
    for k in ("evidence","action"):
        v=(row.get(k) or "")
        m=re.search(r"cmd:\s*(.+)", v)
        if m: return m.group(1).strip()
    return None

def _script_hashes(cmd, cwd):
    """Hash any local script files referenced as args in the command."""
    out={}
    for tok in shlex.split(cmd):
        p=os.path.join(cwd,tok)
        if os.path.isfile(p):
            out[tok]=sha(open(p,"rb").read())
    return out

def _run(cmd, cwd):
    r=subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=120)
    return r.returncode, (r.stdout or "")

def build(ledger, out, cwd):
    rows=list(csv.DictReader(open(ledger,encoding="utf-8")))
    entries=[]
    for row in rows:
        if (row.get("claim_tier") or "").strip().lower()!="code-verified": continue
        cid=row.get("id") or row.get("issue","?")
        cmd=_cmd_of(row)
        if not cmd:
            entries.append({"claim_id":cid,"status":"NO_CMD","note":"Code-verified row has no `cmd:` rerun command"}); continue
        rc,output=_run(cmd,cwd)
        entries.append({
            "claim_id":cid, "tier":"Code-verified", "rerun_cmd":cmd, "exit_code":rc,
            "script_sha256":_script_hashes(cmd,cwd), "output_sha256":sha(output),
            "output_preview":output.strip().splitlines()[-1][:120] if output.strip() else "",
            "verified_at":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
        })
    manifest={"schema":"cambium-provenance-1","ledger":os.path.basename(ledger),"cwd":cwd,"entries":entries}
    json.dump(manifest, open(out,"w"), indent=2)
    ok=sum(1 for e in entries if e.get("exit_code")==0)
    print(f"[provenance] wrote {out} — {len(entries)} Code-verified claim(s), {ok} reran exit 0")
    return 0 if all(e.get("exit_code",1)==0 for e in entries if "exit_code" in e) else 1

def check(manifest, cwd):
    m=json.load(open(manifest)); cwd=cwd or m.get("cwd",".")
    bad=0
    for e in m["entries"]:
        if "rerun_cmd" not in e: print(f"  - {e['claim_id']}: {e.get('status','?')}"); continue
        rc,output=_run(e["rerun_cmd"],cwd)
        h=sha(output); shifted=[t for t,hh in e.get("script_sha256",{}).items()
                                if os.path.isfile(os.path.join(cwd,t)) and sha(open(os.path.join(cwd,t),'rb').read())!=hh]
        if h==e["output_sha256"] and not shifted: print(f"  ok   {e['claim_id']}  output hash matches")
        else:
            bad+=1; print(f"  X    {e['claim_id']}  "+("OUTPUT DRIFTED" if h!=e['output_sha256'] else f"SCRIPT CHANGED: {shifted}"))
    print(f"[provenance] {'OK: all claims reproduce.' if not bad else f'FAILED: {bad} claim(s) drifted.'}")
    return 1 if bad else 0

def main():
    a=sys.argv[1:]
    if not a or a[0] not in ("build","check"): print(__doc__); return 0
    cwd=a[a.index("--cwd")+1] if "--cwd" in a else os.path.dirname(os.path.abspath(a[1])) or "."
    if a[0]=="build":
        out=a[a.index("--out")+1] if "--out" in a else os.path.join(cwd,"provenance_manifest.json")
        return build(a[1], out, cwd)
    return check(a[1], cwd)

if __name__=="__main__": sys.exit(main())
