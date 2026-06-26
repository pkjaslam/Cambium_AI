"""Tests for the ADR-007 claim<->source faithfulness check (cite_check.py + validate.py).
Run: pytest -q   (from the repo root)

These assert three things the ADR promises:
  1. cite_check degrades cleanly with NO verifier installed (advisory no-op, exit 0).
  2. the lexical fallback meets the calibrated gold-set thresholds (FNR/FPR).
  3. validate.py honors the optional `citation_support` column without breaking back-compat.
"""
import os, sys, subprocess, tempfile, csv
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import cite_check


def run(rel, *args):
    return subprocess.run([sys.executable, rel, *args], cwd=ROOT, capture_output=True, text=True)


# ---- 1. graceful no-op: forcing backend=none never fails, even on a cited ledger ----
def test_cite_check_noop_backend_none_exit0():
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "issue", "source"])
        w.writerow(["R1", "claim text", "some cited source"])
        path = f.name
    try:
        r = run("tools/cite_check.py", path, "--backend", "none")
        assert r.returncode == 0, r.stderr
        assert "advisory no-op" in (r.stdout + r.stderr).lower()
    finally:
        os.unlink(path)


def test_cite_check_no_ledger_exit0():
    r = run("tools/cite_check.py", "does_not_exist.csv", "--backend", "none")
    assert r.returncode == 0


# ---- 2. calibrated gold set passes the FNR/FPR acceptance thresholds ----
def test_cite_check_selftest_passes_thresholds():
    r = run("tools/cite_check.py", "--selftest")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "PASS" in r.stdout


def test_lexical_polarity_and_overlap():
    assert cite_check.classify_lexical(
        "the estimator is unbiased under random sampling",
        "under random sampling the estimator is unbiased")[0] == "supported"
    assert cite_check.classify_lexical(
        "the estimator is unbiased under random sampling",
        "under random sampling the estimator is biased and not consistent")[0] == "unsupported"


# ---- 3. validate.py back-compat + advisory warning on 'unsupported' ----
def _ledger(rows, header):
    f = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="")
    w = csv.DictWriter(f, fieldnames=header)
    w.writeheader()
    for r in rows:
        w.writerow(r)
    f.close()
    return f.name


def test_validate_backcompat_without_column():
    header = ["id", "issue", "agents", "severity", "claim_tier", "evidence", "status", "action"]
    rows = [{"id": "F1", "issue": "ok", "agents": "exec", "severity": "P2",
             "claim_tier": "Code-verified", "evidence": "$ pytest -> exit 0",
             "status": "closed", "action": "none"}]
    path = _ledger(rows, header)
    try:
        r = run("governance/validate.py", path)
        assert r.returncode == 0, r.stdout + r.stderr
    finally:
        os.unlink(path)


def test_validate_advisory_warning_is_not_a_blocker():
    header = ["id", "issue", "agents", "severity", "claim_tier", "evidence",
              "status", "action", "citation_support"]
    rows = [{"id": "F2", "issue": "claim", "agents": "verify-evidence", "severity": "P2",
             "claim_tier": "Asserted", "evidence": "see source", "status": "closed",
             "action": "none", "citation_support": "unsupported"}]
    path = _ledger(rows, header)
    try:
        r = run("governance/validate.py", path)
        assert r.returncode == 0, r.stdout + r.stderr
        assert "citation_support" in r.stdout.lower() or "advisory" in r.stdout.lower()
    finally:
        os.unlink(path)
