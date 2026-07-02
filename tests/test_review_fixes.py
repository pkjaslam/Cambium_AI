"""UI first-paint + the two genuine review gaps (turn-level audit log, document draft-diff)."""
import json, os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _run(tool, *a, **kw):
    return subprocess.run([sys.executable, os.path.join(ROOT, "tools", tool), *a],
                          cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)

# ---- cambium_start: one-command first paint -------------------------------
def test_cambium_start_paints_board_and_banner():
    r = _run("cambium_start.py", "smoke test task", timeout=40)
    assert "CAMBIUM INSTITUTE" in r.stdout            # text board rendered
    assert "FIRST PAINT COMPLETE" in r.stdout          # imperative banner
    assert "do NOT answer in plain text" in r.stdout
    assert os.path.exists(os.path.join(ROOT, "agent_outputs", "run_board.html"))

# ---- audit_log: tamper-evident turn-level trail (Fix #2) ------------------
def test_audit_log_chain_detects_tampering():
    trail = tempfile.mktemp(suffix=".jsonl")
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import importlib, audit_log
    importlib.reload(audit_log)
    audit_log.TRAIL = trail
    audit_log.append("G1", "rfp-analyst", "claude-sonnet-4-6", "q1", "r1", "APPROVE", "")
    audit_log.append("G2", "idea-tournament", "claude-opus-4-8", "q2", "r2", "REVISE", "")
    assert audit_log.verify() == 0
    rows = [json.loads(l) for l in open(trail) if l.strip()]
    rows[0]["human_action"] = "REJECT"                 # edit a logged field
    open(trail, "w").write("\n".join(json.dumps(r) for r in rows) + "\n")
    assert audit_log.verify() == 1                     # chain breaks

def test_audit_log_hashes_not_plaintext():
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import importlib, audit_log
    importlib.reload(audit_log); audit_log.TRAIL = tempfile.mktemp(suffix=".jsonl")
    row = audit_log.append("G1", "a", "m", "SENSITIVE QUERY 123-45-6789", "resp", "APPROVE", "")
    assert "SENSITIVE" not in json.dumps(row) and "123-45-6789" not in json.dumps(row)
    assert len(row["query_sha"]) == 64                 # stored as sha256, not text

# ---- draft_diff: document-level AI-vs-human change record (Fix #4) --------
def test_draft_diff_records_change_ratio():
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import draft_diff as D
    assert D.change_ratio("alpha beta", "alpha beta") == 0.0          # no human change
    assert D.change_ratio("alpha beta", "gamma delta epsilon") == 1.0  # fully rewritten

def test_draft_diff_cli_writes_ledger_and_diff():
    ai = tempfile.mktemp(suffix=".md"); fin = tempfile.mktemp(suffix=".md")
    open(ai, "w").write("camera traps only\n")
    open(fin, "w").write("camera traps and eDNA sampling validated against survey data\n")
    r = _run("draft_diff.py", "--ai-draft", ai, "--human-final", fin, "--doc", "test-doc")
    assert r.returncode == 0 and "change_ratio=" in r.stdout
    assert os.path.exists(os.path.join(ROOT, "governance", "DRAFT_CORRECTION_LEDGER.csv"))
