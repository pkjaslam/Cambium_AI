#!/usr/bin/env python3
"""pii_screen -- screen text for personal and sensitive data before it is handled or shared.

Research administration handles documents that carry confidential and personally
identifiable information, so AI4RA's first pillar is Security. This tool screens text
for likely PII and reports what it found, where, and how confident it is, so a human
can decide what to redact. It can also produce a redacted copy.

Two engines, chosen automatically:
  - If Microsoft Presidio (presidio-analyzer) is installed, it is used for rich,
    multi-entity detection.
  - Otherwise a stdlib regular-expression screener runs: email, US phone, US SSN,
    credit card (Luhn-checked), and IP address.

Honest by design:
  - This is a SCREEN, not a guarantee. It flags likely PII; it does not promise to
    catch everything, and a human must review before any document is shared.
  - It never prints the raw PII value. Reports show the entity type, the character
    span, a confidence score, and a masked snippet. Use --redact to write a cleaned copy.

Usage:
  python3 tools/pii_screen.py --in path/to/file.txt
  python3 tools/pii_screen.py --in file.txt --redact --out cleaned.txt
  python3 tools/pii_screen.py --in file.txt --report report.md
"""
from __future__ import annotations
import argparse
import os
import re
import sys

import cambium_io  # noqa: F401  (UTF-8 stdout guard)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Priority: more specific / validated entities win when spans overlap.
_PRIORITY = {
    "CREDIT_CARD": 5,
    "US_SSN": 4,
    "EMAIL_ADDRESS": 3,
    "PHONE_NUMBER": 2,
    "IP_ADDRESS": 1,
}

_PATTERNS = [
    ("EMAIL_ADDRESS", re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"), 0.7),
    ("US_SSN", re.compile(r"\b\d{3}[-\s]\d{2}[-\s]\d{4}\b"), 0.75),
    ("PHONE_NUMBER", re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"), 0.6),
    ("IP_ADDRESS", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), 0.6),
    ("CREDIT_CARD", re.compile(r"\b(?:\d[ -]?){13,16}\b"), 0.55),
]


def _luhn_ok(digits: str) -> bool:
    """Standard Luhn checksum. digits is a string of 0-9 only."""
    if not (13 <= len(digits) <= 19):
        return False
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = ord(ch) - 48
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _ip_ok(text: str) -> bool:
    parts = text.split(".")
    return len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)


def scan_regex(text: str) -> list:
    """Return findings via the stdlib screener. Each finding is a dict; no raw value is stored."""
    raw: list[dict] = []
    for entity, pattern, score in _PATTERNS:
        for m in pattern.finditer(text):
            s, e = m.start(), m.end()
            matched = m.group()
            conf = score
            if entity == "CREDIT_CARD":
                digits = re.sub(r"\D", "", matched)
                if not _luhn_ok(digits):
                    continue
                conf = 0.9
            if entity == "IP_ADDRESS" and not _ip_ok(matched):
                continue
            raw.append({"entity_type": entity, "start": s, "end": e, "score": conf})
    return _dedupe_overlaps(raw)


def _dedupe_overlaps(findings: list) -> list:
    """Keep the highest-priority finding when spans overlap; return sorted by start."""
    chosen: list[dict] = []
    for f in sorted(findings, key=lambda x: (-_PRIORITY.get(x["entity_type"], 0), x["start"])):
        if any(not (f["end"] <= c["start"] or f["start"] >= c["end"]) for c in chosen):
            continue
        chosen.append(f)
    return sorted(chosen, key=lambda x: x["start"])


def scan_presidio(text: str):
    """Return (findings, True) via Presidio, or (None, False) if Presidio is unavailable."""
    try:
        from presidio_analyzer import AnalyzerEngine  # optional, heavy dependency
    except Exception:
        return None, False
    try:
        engine = AnalyzerEngine()
        results = engine.analyze(text=text, language="en")
        findings = [
            {"entity_type": r.entity_type, "start": r.start, "end": r.end, "score": round(float(r.score), 3)}
            for r in results
        ]
        return _dedupe_overlaps(findings), True
    except Exception:
        return None, False


def scan(text: str) -> tuple:
    """Screen text. Returns (findings, engine_name). Prefers Presidio, falls back to regex."""
    findings, used = scan_presidio(text)
    if used:
        return findings, "presidio"
    return scan_regex(text), "stdlib-regex"


def redact(text: str, findings: list, label_mask: bool = True) -> str:
    """Return a redacted copy. Replaces each span with [<ENTITY>] (or [REDACTED])."""
    out = text
    for f in sorted(findings, key=lambda x: x["start"], reverse=True):
        token = f"[{f['entity_type']}]" if label_mask else "[REDACTED]"
        out = out[: f["start"]] + token + out[f["end"]:]
    return out


def masked_snippet(text: str, f: dict, pad: int = 12) -> str:
    """A short context window with the PII replaced by its type. Never returns raw PII."""
    s = max(0, f["start"] - pad)
    e = min(len(text), f["end"] + pad)
    before = text[s:f["start"]].replace("\n", " ")
    after = text[f["end"]:e].replace("\n", " ")
    return f"...{before}[{f['entity_type']}]{after}..."


def build_report(text: str, findings: list, engine: str, source: str) -> str:
    from collections import Counter
    counts = Counter(f["entity_type"] for f in findings)
    L: list[str] = []
    L.append("# PII screening report (a screen, not a guarantee)")
    L.append("")
    L.append("> This report flags likely personal or sensitive data for human review. "
             "It does not guarantee that all PII was found. A human must review before sharing. "
             "Raw values are never shown here.")
    L.append("")
    L.append(f"**Source:** {source}")
    L.append(f"**Engine:** {engine}")
    L.append(f"**Findings:** {len(findings)}")
    L.append("")
    if counts:
        L.append("| Entity type | Count |")
        L.append("|---|---|")
        for ent, n in sorted(counts.items()):
            L.append(f"| {ent} | {n} |")
        L.append("")
        L.append("## Locations (values masked)")
        L.append("")
        L.append("| # | Entity | Span | Score | Context |")
        L.append("|---|---|---|---|---|")
        for i, f in enumerate(findings, 1):
            L.append(f"| {i} | {f['entity_type']} | {f['start']}-{f['end']} | {f['score']} | {masked_snippet(text, f)} |")
        L.append("")
    else:
        L.append("No likely PII was flagged by this screen. Human review is still advised.")
        L.append("")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Screen a text file for likely PII. A screen, not a guarantee.")
    ap.add_argument("--in", dest="infile", required=True, help="Path to the text file to screen.")
    ap.add_argument("--report", default=None, help="Write the Markdown report to this path (default: stdout).")
    ap.add_argument("--redact", action="store_true", help="Write a redacted copy of the input.")
    ap.add_argument("--out", default=None, help="Path for the redacted copy (with --redact).")
    args = ap.parse_args(argv)

    if not os.path.exists(args.infile):
        print(f"[pii_screen] ERROR: input not found: {args.infile}", file=sys.stderr)
        return 2
    text = open(args.infile, encoding="utf-8", errors="replace").read()
    findings, engine = scan(text)

    report = build_report(text, findings, engine, os.path.basename(args.infile))
    if args.report:
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"[pii_screen] {len(findings)} finding(s) via {engine}. Report: {args.report}")
    else:
        sys.stdout.write(report)

    if args.redact:
        out = args.out or (os.path.splitext(args.infile)[0] + ".redacted" + os.path.splitext(args.infile)[1])
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(redact(text, findings))
        print(f"[pii_screen] wrote redacted copy: {out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
