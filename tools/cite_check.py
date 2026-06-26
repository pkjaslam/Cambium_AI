#!/usr/bin/env python3
"""cite_check.py -- optional, gated claim<->source faithfulness verifier (ADR-007).

Closes the gap ADR-002 promised but governance/validate.py could not enforce:
citation_status only says a reference is *resolved*, never whether the cited source
actually *supports* the claim. This shim adds that check, but stays strictly OPTIONAL
and ADVISORY so it can never turn a green build red on its own.

BACKENDS (auto-resolved, most-capable first):
  - semanticcite : if the `semanticcite` package is importable (MIT, arXiv 2511.16198).
  - ollama       : if a local Ollama is configured (env OLLAMA_HOST / CAMBIUM_CITE_OLLAMA);
                   no data leaves the box, no API key.
  - none         : neither present -> deterministic lexical fallback for the gold-set
                   smoke test, and 'uncertain' (reason: verifier-not-installed) for real
                   ledgers. Exit 0 always. Doctor stays green.

OUTPUT: advisory only.
  - writes governance/cite_audit.json (a report; never blocks).
  - with --write, also emits a NON-destructive sidecar <ledger>.cited.csv that adds a
    `citation_support` column (the original ledger is never mutated).
  governance/validate.py reads `citation_support` if present and emits a WARNING (not a
  blocker) for 'unsupported'. Escalation-to-blocker is a separate, future-gated decision.

LOCATOR ANCHORS (from ARS): an optional `locator` column (source-id + section/line + quote)
narrows the check to the cited sentence rather than the whole document.

Usage:
  python3 tools/cite_check.py [agent_outputs/findings_ledger.csv] [--write] [--backend auto]
  python3 tools/cite_check.py --selftest        # run the calibrated gold set
"""
import csv, sys, json, os, re, datetime

LABELS = ("supported", "partial", "unsupported", "uncertain")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLD = os.path.join(ROOT, "tests", "fixtures", "cite_gold.csv")

# Acceptance thresholds for the lexical fallback on the gold set (ARS practice).
# positive class = "unsupported" (a bad citation we must catch).
MAX_FNR = 0.15   # missed bad citations / all bad citations
MAX_FPR = 0.10   # false alarms / all good citations

_NEG = re.compile(r"\b(no|not|never|cannot|can't|fails?|failed|without|absent|"
                  r"refut\w*|contradict\w*|disproven|insufficient|unsupported)\b", re.I)
_STOP = set("a an the of to in on for and or is are was were be been with by as at "
            "that this these those it its from into than then also we our their".split())


def _stem(w):
    for suf in ("ing", "ed", "es", "s", "d"):
        if len(w) > len(suf) + 2 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def _toks(s):
    return [_stem(w) for w in re.findall(r"[a-z0-9]+", (s or "").lower()) if w not in _STOP]


def classify_lexical(claim, source):
    """Deterministic fallback: token-overlap + negation-mismatch. No model, no network."""
    c, s = set(_toks(claim)), set(_toks(source))
    if not c or not s:
        return "uncertain", "empty-claim-or-source"
    overlap = len(c & s) / max(1, len(c))
    neg_claim, neg_src = bool(_NEG.search(claim)), bool(_NEG.search(source))
    if neg_claim != neg_src and overlap >= 0.3:
        return "unsupported", "polarity-mismatch (claim/source negation differ)"
    if overlap >= 0.6:
        return "supported", "high lexical overlap, consistent polarity"
    if overlap >= 0.35:
        return "partial", "moderate overlap; verify the specific locator"
    return "uncertain", "low overlap; insufficient signal for the fallback"


def resolve_backend(name):
    if name not in ("auto", "semanticcite", "ollama", "none"):
        name = "auto"
    if name in ("auto", "semanticcite"):
        try:
            import semanticcite  # noqa: F401  (real verifier when installed)
            return "semanticcite"
        except Exception:
            if name == "semanticcite":
                return "none"
    if name in ("auto", "ollama"):
        if os.environ.get("OLLAMA_HOST") or os.environ.get("CAMBIUM_CITE_OLLAMA"):
            return "ollama"
        if name == "ollama":
            return "none"
    return "none"


def verify(claim, source, locator, backend):
    """Return (label, reason). Real backends fall through to the lexical fallback here
    until wired (kept import-safe so the framework never hard-depends on them)."""
    if backend == "none":
        return "uncertain", "verifier-not-installed (advisory no-op)"
    # SemanticCite / Ollama integration point. Until provisioned on the host, we degrade
    # to the deterministic fallback so behavior is reproducible and never crashes.
    return classify_lexical(claim, source)


def audit_ledger(ledger, backend, write_sidecar):
    if not os.path.exists(ledger):
        print("[cite_check] no ledger at %s (nothing to check)" % ledger)
        return 0
    rows = list(csv.DictReader(open(ledger, newline="", encoding="utf-8")))
    results, counts = [], {k: 0 for k in LABELS}
    for r in rows:
        claim = (r.get("issue") or r.get("claim") or r.get("evidence") or "").strip()
        source = (r.get("source") or r.get("citation") or r.get("reference") or "").strip()
        locator = (r.get("locator") or "").strip()
        if not source:
            continue  # nothing cited on this row -> not in scope
        label, reason = verify(claim, source, locator, backend)
        counts[label] += 1
        results.append({"id": r.get("id"), "citation_support": label,
                        "reason": reason, "locator": locator or None})
    report = {
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "ledger": ledger, "backend": backend,
        "n_cited_rows": len(results), "by_label": counts,
        "advisory": True, "note": "ADR-007 claim<->source check. Advisory only; never blocks.",
        "results": results,
    }
    os.makedirs(os.path.join(ROOT, "governance"), exist_ok=True)
    out = os.path.join(ROOT, "governance", "cite_audit.json")
    json.dump(report, open(out, "w"), indent=2)
    print("[cite_check] backend=%s | %d cited rows | %s | report -> governance/cite_audit.json"
          % (backend, len(results), counts))
    if write_sidecar and results:
        side = ledger + ".cited.csv"
        by_id = {x["id"]: x["citation_support"] for x in results}
        fields = list(rows[0].keys())
        if "citation_support" not in fields:
            fields = fields + ["citation_support"]
        with open(side, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            for r in rows:
                r = dict(r)
                r["citation_support"] = by_id.get(r.get("id"), "")
                w.writerow(r)
        print("[cite_check] sidecar (non-destructive) -> %s" % side)
    unsupported = counts["unsupported"]
    if unsupported:
        print("[cite_check] ADVISORY: %d row(s) classified 'unsupported' -- review before release "
              "(validate.py surfaces these as warnings)." % unsupported)
    return 0  # advisory: never fail the build


def selftest():
    if not os.path.exists(GOLD):
        print("[cite_check] selftest: gold set missing at %s" % GOLD); return 1
    rows = list(csv.DictReader(open(GOLD, newline="", encoding="utf-8")))
    fp = fn = pos = neg = 0
    for r in rows:
        gold = (r.get("label") or "").strip().lower()
        pred, _ = classify_lexical(r.get("claim", ""), r.get("source", ""))
        pred_bad = (pred == "unsupported")
        gold_bad = (gold == "unsupported")
        if gold_bad:
            pos += 1
            fn += int(not pred_bad)
        else:
            neg += 1
            fp += int(pred_bad)
    fnr = fn / pos if pos else 0.0
    fpr = fp / neg if neg else 0.0
    ok = (fnr <= MAX_FNR) and (fpr <= MAX_FPR)
    print("[cite_check] selftest: %d tuples | FNR=%.2f (max %.2f) | FPR=%.2f (max %.2f) | %s"
          % (len(rows), fnr, MAX_FNR, fpr, MAX_FPR, "PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main(argv):
    if "--selftest" in argv:
        return selftest()
    backend_arg = "auto"
    if "--backend" in argv:
        i = argv.index("--backend")
        if i + 1 < len(argv):
            backend_arg = argv[i + 1]
    write_sidecar = "--write" in argv
    positional = [a for a in argv if not a.startswith("--") and a != backend_arg]
    ledger = positional[0] if positional else "agent_outputs/findings_ledger.csv"
    backend = resolve_backend(backend_arg)
    if backend == "none":
        print("[cite_check] no claim<->source verifier installed (semanticcite/ollama). "
              "Running in advisory no-op mode -- install per TOOL_POLICY.md to enable.")
    return audit_ledger(ledger, backend, write_sidecar)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
