#!/usr/bin/env python3
"""Mirror .claude/agents/*.md into agents/ — the plugin's auto-discovery copy.

Cambium stores its roster in .claude/agents/ (used by the template + Cowork folder method), but the
installable plugin auto-discovers from agents/. This keeps the two identical so a pushed plugin never
drifts from the source roster. Run before every commit (wired into push_cambium.bat).
"""
import os, glob, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = os.path.join(ROOT, ".claude", "agents")
DST  = os.path.join(ROOT, "agents")
os.makedirs(DST, exist_ok=True)
src = {os.path.basename(p) for p in glob.glob(os.path.join(SRC, "*.md"))}
dst = {os.path.basename(p) for p in glob.glob(os.path.join(DST, "*.md"))}
for f in src:                                   # copy/overwrite every source agent
    shutil.copyfile(os.path.join(SRC, f), os.path.join(DST, f))
for f in (dst - src):                           # drop agents removed from the source
    os.remove(os.path.join(DST, f))
print("[sync_plugin_agents] agents/ mirrors .claude/agents/ -> %d agents (added/updated %d, removed %d)"
      % (len(src), len(src), len(dst - src)))
