#!/usr/bin/env python3
"""Advisory citation-URL liveness check for Cambium (ADR-027).

Closes the gap between policy and capability: Cambium's citation stack verifies a
reference's *identity* (DOI / Crossref / venue, via the librarian) but never tested
whether the cited **URL actually resolves**, nor distinguished a dead-but-archived
link from a fabricated one that never existed. This shim does that, advisory-only.

Inspired by `urlhealth` (Rao et al., 2026, arXiv:2604.03173), which measured that
3-13% of LLM/agent citation URLs are *hallucinated* (no live page and no Wayback
record) and 5-18% are non-resolving. Those figures are EXTERNAL measurement, not a
Cambium result.

CONTRACT (mirrors tools/cite_check.py / ADR-007):
  * Import-guarded + OFFLINE-SAFE. The DEFAULT path makes **no network calls**: every
    URL is classified UNCHECKED and the tool is a deterministic advisory no-op, so CI
    stays reproducible and never breaks on a flaky network.
  * Network checking is strictly opt-in via env `CAMBIUM_URL_NET=1` (or `--net`). When
    enabled it prefers the published `urlhealth` package if importable, else falls back
    to a stdlib liveness + Wayback-availability probe. Any network error degrades to
    UNCHECKED for that URL; the tool never raises and always exits 0 (advisory).
  * Classifications (lowercase, matching governance/validate.py's `url_status` column):
      live            - resolves now (HTTP < 400)
      stale-archived  - does not resolve now but has a Wayback record (link rot)
      hallucinated    - does not resolve now AND no Wayback record (likely never existed)
      unchecked       - not probed (offline default, or probe error)
  * Writes governance/url_audit.json (summary + per-URL). Optional non-destructive
    `<ledger>.urlcheck.csv` sidecar with `--sidecar` (never edits the ledger).

Usage:
  python3 tools/url_health.py [path/to/findings_ledger.csv] [--net] [--sidecar]
Provisioning: the `urlhealth` package + the Wayback API are recorded at the
provisioning gate (TOOL_POLICY.md) but NOT installed by this tool.
"""
import csv, sys, os, re, json, datetime

LEDGER_DEFAULT = "agent_outputs/findings_ledger.csv"
URL_RE = re.compile(r"https?://[^\s)>\]\"']+")
URL_COLUMNS = ("url", "citation_url", "source_url", "reference_url")
# columns we also scan for inline URLs when no explicit URL column is present
TEXT_COLUMNS = ("evidence", "action", "issue", "citation_status")

VALID = ("live", "stale-archived", "hallucinated", "unchecked")


def _net_enabled(argv):
    return ("--net" in argv) or (os.environ.get("CAMBIUM_URL_NET", "").strip() in ("1", "true", "yes"))


def extract_urls(rows):
    """Return ordered, de-duplicated URLs found across the ledger rows."""
    seen, urls = set(), []
    for r in rows:
        cells = []
        for c in URL_COLUMNS:
            v = (r.get(c) or "").strip()
            if v:
                cells.append(v)
        for c in TEXT_COLUMNS:
            v = (r.get(c) or "")
            cells.extend(URL_RE.findall(v))
        for u in cells:
            u = u.rstrip(".,;")
            if u.startswith("http") and u not in seen:
                seen.add(u)
                urls.append(u)
    return urls


def _classify_with_urlhealth(url):
    """Use the published urlhealth package if available; return a class str or None."""
    try:
        import urlhealth  # type: ignore
    except Exception:
        return None
    try:
        res = urlhealth.check(url)  # best-effort; package API may differ
        s = str(getattr(res, "status", res)).lower()
        if "halluc" in s:
            return "hallucinated"
        if "stale" in s or "archive" in s:
            return "stale-archived"
        if "live" in s or "ok" in s or "200" in s:
            return "live"
    except Exception:
        return None
    return None


def _classify_stdlib(url, timeout=6):
    """Stdlib fallback: live? else Wayback record? else hallucinated. Never raises."""
    import urllib.request, urllib.error, urllib.parse
    # 1) liveness
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "cambium-url-health/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if int(getattr(resp, "status", 200)) < 400:
                return "live"
    except urllib.error.HTTPError as e:
        if e.code < 400:
            return "live"
        # fall through to archive check on 4xx/5xx
    except Exception:
        pass  # connection/timeout -> try archive
    # 2) Wayback availability API -> stale-archived vs hallucinated
    try:
        api = "https://archive.org/wayback/available?url=" + urllib.parse.quote(url, safe="")
        req = urllib.request.Request(api, headers={"User-Agent": "cambium-url-health/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
        snap = (data.get("archived_snapshots") or {}).get("closest") or {}
        if snap.get("available"):
            return "stale-archived"
        return "hallucinated"
    except Exception:
        return "unchecked"  # could not reach the archive -> stay advisory-silent


def classify(url, net):
    if not net:
        return "unchecked"
    return _classify_with_urlhealth(url) or _classify_stdlib(url)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    net = _net_enabled(argv)
    want_sidecar = "--sidecar" in argv
    positional = [a for a in argv if not a.startswith("-")]
    ledger = positional[0] if positional else LEDGER_DEFAULT

    if not os.path.exists(ledger):
        print("[url_health] no ledger at %s (nothing to check yet)" % ledger)
        return 0

    rows = list(csv.DictReader(open(ledger, newline="", encoding="utf-8")))
    urls = extract_urls(rows)
    results = [{"url": u, "url_status": classify(u, net)} for u in urls]

    counts = {k: 0 for k in VALID}
    for r in results:
        counts[r["url_status"]] = counts.get(r["url_status"], 0) + 1

    manifest = {
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "ledger": ledger,
        "network_checked": bool(net),
        "n_urls": len(urls),
        "counts": counts,
        "urls": results,
        "note": ("Advisory URL-liveness audit (ADR-027). OFFLINE default = all 'unchecked'. "
                 "Set CAMBIUM_URL_NET=1 (or --net) to probe. Never a release blocker."),
    }
    os.makedirs("governance", exist_ok=True)
    json.dump(manifest, open("governance/url_audit.json", "w"), indent=2)

    if want_sidecar:
        side = ledger + ".urlcheck.csv"
        with open(side, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["url", "url_status"])
            for r in results:
                w.writerow([r["url"], r["url_status"]])

    mode = "network" if net else "offline (advisory no-op)"
    print("[url_health] %d URLs | %s | %s | governance/url_audit.json written"
          % (len(urls), mode, counts))
    flagged = [r for r in results if r["url_status"] in ("hallucinated", "stale-archived")]
    if flagged:
        print("[url_health] ADVISORY (not a blocker): %d URL(s) flagged - set the ledger 'url_status' "
              "column and let librarian/integrity-officer review:" % len(flagged))
        for r in flagged:
            print("  %s -> %s" % (r["url"], r["url_status"]))
    return 0  # advisory: always exit 0


if __name__ == "__main__":
    sys.exit(main())
