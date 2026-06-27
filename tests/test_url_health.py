"""ADR-027: tests for the advisory citation-URL liveness check.
Run: pytest -q   (from the repo root)

Guarantees:
  * tools/url_health.py is OFFLINE-SAFE and deterministic (no network by default):
    every URL is classified 'unchecked', the tool always exits 0, and it writes
    governance/url_audit.json.
  * governance/validate.py honors an optional `url_status` column as an ADVISORY
    WARNING only - never a blocker - and is silent when the value is clean/absent
    (back-compat).
"""
import os, sys, subprocess, json, tempfile, csv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import url_health  # noqa: E402


def run(rel, *args):
    return subprocess.run([sys.executable, rel, *args], cwd=ROOT, capture_output=True, text=True)


# ---- url_health.py: offline default is a deterministic advisory no-op ----
def _ledger_urls(rows, header):
    fd, path = tempfile.mkstemp(suffix=".csv"); os.close(fd)
    with open(path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(header)
        for r in rows:
            w.writerow(r)
    return path


def test_url_health_offline_is_unchecked_and_exits_zero():
    hdr = ["id", "issue", "agents", "severity", "claim_tier", "evidence", "status", "action"]
    p = _ledger_urls(
        [["U1", "x", "a", "P2", "Asserted",
          "see https://example.com/paper and http://dead.example/x", "open", "fix"]],
        hdr)
    res = run("tools/url_health.py", p)
    assert res.returncode == 0
    assert "offline" in res.stdout
    # no network probing -> nothing is flagged hallucinated/stale
    assert "ADVISORY" not in res.stdout
    os.remove(p)


def test_url_health_extracts_and_classifies_unchecked():
    rows = [{"evidence": "ref https://a.test/1 https://a.test/1", "action": "https://b.test/2"}]
    urls = url_health.extract_urls(rows)
    assert urls == ["https://a.test/1", "https://b.test/2"]  # ordered + de-duplicated
    assert url_health.classify("https://a.test/1", net=False) == "unchecked"


def test_url_health_writes_audit_json():
    hdr = ["id", "issue", "agents", "severity", "claim_tier", "evidence", "status", "action"]
    p = _ledger_urls([["U1", "x", "a", "P2", "Asserted", "https://example.com/q", "open", "fix"]], hdr)
    run("tools/url_health.py", p)
    audit = os.path.join(ROOT, "governance", "url_audit.json")
    assert os.path.exists(audit)
    data = json.load(open(audit))
    assert data["network_checked"] is False
    assert data["n_urls"] >= 1
    os.remove(p)


def test_url_health_missing_ledger_is_graceful():
    res = run("tools/url_health.py", "no/such/ledger.csv")
    assert res.returncode == 0
    assert "nothing to check" in res.stdout


# ---- validate.py: url_status is advisory (warns, never blocks) ----
def _ledger_url_status(rows):
    fd, path = tempfile.mkstemp(suffix=".csv"); os.close(fd)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "issue", "agents", "severity", "claim_tier", "evidence",
                    "status", "citation_status", "repro", "url_status"])
        for r in rows:
            w.writerow(r)
    return path


def test_validate_hallucinated_url_is_advisory_not_blocker():
    p = _ledger_url_status([["U1", "x", "a", "P2", "Code-verified",
                             "$ python check.py -> ok", "closed", "resolved", "done", "hallucinated"]])
    res = run("governance/validate.py", p)
    assert res.returncode == 0
    assert "URL-LIVENESS ADVISORY" in res.stdout
    os.remove(p)


def test_validate_stale_url_is_advisory_not_blocker():
    p = _ledger_url_status([["U1", "x", "a", "P2", "Code-verified",
                             "$ python check.py -> ok", "closed", "resolved", "done", "stale-archived"]])
    res = run("governance/validate.py", p)
    assert res.returncode == 0
    assert "URL-LIVENESS ADVISORY" in res.stdout
    os.remove(p)


def test_validate_live_url_is_silent():
    p = _ledger_url_status([["U1", "x", "a", "P2", "Code-verified",
                             "$ python check.py -> ok", "closed", "resolved", "done", "live"]])
    res = run("governance/validate.py", p)
    assert res.returncode == 0
    assert "URL-LIVENESS ADVISORY" not in res.stdout
    os.remove(p)
