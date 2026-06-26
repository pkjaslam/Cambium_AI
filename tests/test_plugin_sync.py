import os, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _read(rel):
    return {os.path.basename(p): open(p, encoding="utf-8").read()
            for p in glob.glob(os.path.join(ROOT, rel, "*.md"))}
def test_plugin_agents_match_source():
    src, dst = _read(".claude/agents"), _read("agents")
    assert set(src) == set(dst), f"agents/ out of sync (run tools/sync_plugin_agents.py): {set(src) ^ set(dst)}"
    drift = [k for k in src if src[k] != dst[k]]
    assert not drift, f"content drift in agents/: {drift}"
