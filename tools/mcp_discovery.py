#!/usr/bin/env python3
"""mcp_discovery — the toolsmith's live MCP awareness.

For any run, the toolsmith should ask "is there a connected MCP that beats the base model here, and which
council should use it?" This tool answers that honestly: it reads the host's MCP config files (whatever it
can see on disk) and the curated routing map (governance/mcp_map.yml), then proposes which MCP each council
should use. It NEVER connects or installs anything; the toolsmith presents this at the provisioning gate and
a human approves (see docs/governance/TOOL_POLICY.md).

Honest ceiling: a standalone tool cannot confirm a server is live and authenticated inside the host session
(that is runtime state). It reports a server as "configured" when it appears in a config file, and as
"available to add" when it is in the curated map but not configured. It does not claim a server is working.

  python3 tools/mcp_discovery.py                 # full routing manifest (configured + available-to-add)
  python3 tools/mcp_discovery.py --task "review the literature on cover crops"   # prioritize relevant MCPs
  python3 tools/mcp_discovery.py --configured     # only servers found in a config file
"""
from __future__ import annotations
import argparse, json, os, re, sys
import cambium_io  # noqa: F401 — reconfigures stdout/stderr to UTF-8 on Windows

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATHS = [".mcp.json", ".claude/settings.json", ".claude/settings.local.json",
                os.path.expanduser("~/.claude.json")]

def load_map():
    p = os.path.join(ROOT, "governance", "mcp_map.yml")
    try:
        import yaml
        return (yaml.safe_load(open(p, encoding="utf-8")) or {}).get("servers", [])
    except Exception:
        return []

def configured_servers():
    """Server names found in any MCP config file on disk (configured, not necessarily live)."""
    found = set()
    for rel in CONFIG_PATHS:
        path = rel if os.path.isabs(rel) else os.path.join(ROOT, rel)
        if not os.path.exists(path):
            continue
        try:
            d = json.load(open(path, encoding="utf-8"))
        except Exception:
            continue
        for key in ("mcpServers", "mcp_servers", "servers"):
            block = d.get(key) or {}
            if isinstance(block, dict):
                found |= set(block.keys())
            elif isinstance(block, list):
                found |= {s.get("name", "") for s in block if isinstance(s, dict)}
    return {f for f in found if f}

def _norm(s): return re.sub(r"[^a-z0-9]", "", (s or "").lower())

def discover(task=None):
    servers = load_map()
    conf = configured_servers()
    confn = {_norm(c) for c in conf}
    rows = []
    terms = re.findall(r"[a-z0-9]+", task.lower()) if task else []
    for s in servers:
        name = s.get("name", "")
        status = "configured" if _norm(name) in confn else "available to add"
        relevance = 0
        if terms:
            hay = (name + " " + s.get("purpose", "") + " " + " ".join(s.get("match", []))).lower()
            relevance = sum(1 for t in set(terms) if len(t) > 2 and t in hay)
        rows.append({"name": name, "purpose": s.get("purpose", ""), "councils": s.get("councils", []),
                     "status": status, "relevance": relevance})
    # sort: configured first, then relevance, then name
    rows.sort(key=lambda r: (r["status"] != "configured", -r["relevance"], r["name"]))
    return rows, conf

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default=None, help="prioritize MCPs relevant to this request")
    ap.add_argument("--configured", action="store_true", help="only servers found in a config file")
    a = ap.parse_args(argv)
    rows, conf = discover(a.task)
    if a.configured:
        rows = [r for r in rows if r["status"] == "configured"]
    n_conf = sum(1 for r in rows if r["status"] == "configured")
    print(f"[mcp_discovery] {n_conf} configured · {len(rows)-n_conf} available to add"
          + (f" · prioritized for: {a.task}" if a.task else ""))
    print("[mcp_discovery] proposal only — nothing connects without approval at the provisioning gate.\n")
    for r in rows:
        rel = f"  (relevant x{r['relevance']})" if r.get("relevance") else ""
        print(f"  {r['status']:<16} {r['name']:<18} -> {', '.join(r['councils'])}{rel}")
        print(f"  {'':<16} {r['purpose']}")
    if not conf:
        print("\n[mcp_discovery] note: no MCP config file found on disk; showing the curated map only. "
              "If MCPs are connected in the host UI, the toolsmith still proposes them here for approval.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
