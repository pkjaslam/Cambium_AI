"""Tests for tools/pii_screen.py. Stdlib + tmp dirs only. Exercises the regex engine.

Security-critical invariant: a screening report must never echo the raw PII value.
"""
import os
import sys
import tempfile

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import pii_screen as P


def _types(findings):
    return {f["entity_type"] for f in findings}


def test_detects_email():
    findings = P.scan_regex("contact me at jane.doe@example.org please")
    assert "EMAIL_ADDRESS" in _types(findings)


def test_detects_ssn():
    findings = P.scan_regex("SSN 123-45-6789 on file")
    assert "US_SSN" in _types(findings)


def test_detects_phone():
    findings = P.scan_regex("call (208) 555-0134 today")
    assert "PHONE_NUMBER" in _types(findings)


def test_credit_card_requires_luhn():
    # valid Visa test number (passes Luhn)
    good = P.scan_regex("card 4111 1111 1111 1111 expires soon")
    assert "CREDIT_CARD" in _types(good)
    # 16 digits that fail Luhn should not be flagged as a card
    bad = P.scan_regex("ref 4111 1111 1111 1112 zzz")
    assert "CREDIT_CARD" not in _types(bad)


def test_detects_ip_and_rejects_bad_octets():
    good = P.scan_regex("server at 192.168.0.1 listening")
    assert "IP_ADDRESS" in _types(good)
    bad = P.scan_regex("version 999.999.999.999 here")
    assert "IP_ADDRESS" not in _types(bad)


def test_clean_text_has_no_findings():
    findings = P.scan_regex("The quick brown fox jumps over the lazy dog.")
    assert findings == []


def test_overlaps_are_deduped():
    # a credit card span can also look like a phone span; only one wins
    findings = P.scan_regex("4111 1111 1111 1111")
    spans = [(f["start"], f["end"]) for f in findings]
    for i in range(len(spans)):
        for j in range(i + 1, len(spans)):
            a, b = spans[i], spans[j]
            assert a[1] <= b[0] or a[0] >= b[1], "findings overlap"


def test_redact_removes_raw_value():
    text = "email jane.doe@example.org and SSN 123-45-6789"
    findings = P.scan_regex(text)
    cleaned = P.redact(text, findings)
    assert "jane.doe@example.org" not in cleaned
    assert "123-45-6789" not in cleaned
    assert "[EMAIL_ADDRESS]" in cleaned
    assert "[US_SSN]" in cleaned


def test_report_never_shows_raw_pii():
    text = "reach jane.doe@example.org or SSN 123-45-6789"
    findings = P.scan_regex(text)
    report = P.build_report(text, findings, "stdlib-regex", "x.txt")
    assert "jane.doe@example.org" not in report
    assert "123-45-6789" not in report
    # but the entity types are named
    assert "EMAIL_ADDRESS" in report and "US_SSN" in report


def test_report_says_screen_not_guarantee():
    report = P.build_report("clean", [], "stdlib-regex", "x.txt")
    assert "not a guarantee" in report.lower()


def test_no_em_dash():
    text = "ssn 123-45-6789"
    report = P.build_report(text, P.scan_regex(text), "stdlib-regex", "x.txt")
    assert chr(0x2014) not in report


def test_scan_returns_engine_name():
    _findings, engine = P.scan("hello jane.doe@example.org")
    assert engine in ("presidio", "stdlib-regex")


def test_cli_report_and_redact(tmp_path):
    src = tmp_path / "doc.txt"
    src.write_text("email jane.doe@example.org SSN 123-45-6789", encoding="utf-8")
    report = tmp_path / "rep.md"
    out = tmp_path / "clean.txt"
    rc = P.main(["--in", str(src), "--report", str(report), "--redact", "--out", str(out)])
    assert rc == 0
    cleaned = out.read_text(encoding="utf-8")
    assert "123-45-6789" not in cleaned
    assert "jane.doe@example.org" not in cleaned
    rep = report.read_text(encoding="utf-8")
    assert "jane.doe@example.org" not in rep


def test_cli_missing_file_returns_2(tmp_path):
    rc = P.main(["--in", str(tmp_path / "nope.txt")])
    assert rc == 2
