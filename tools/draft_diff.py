#!/usr/bin/env python3
"""draft_diff — record what a human changed in an AI-drafted deliverable (review Fix #4 residual).

learning_gate.py already change-tracks the Director's contribution JSON at a gate. This generalizes that
to ANY deliverable document (a proposal section, a report): give it the AI draft and the human-edited
final, and it computes a change_ratio + a unified diff, appends a row to governance/DRAFT_CORRECTION_LEDGER.csv,
and writes the diff to governance/draft_corrections/. That turns "the human edited the AI's text" into a
durable, queryable correction record — the learning loop the review asked for, and a partial close on the
AI_POLICY §4 "learning over time" gap.

  python3 tools/draft_diff.py --ai-draft ai.md --human-final final.md --doc "Aim 2 approach" [--author Jaslam]
Exit: 0 ok · 1 bad args.
"""
import argparse, csv, difflib, os, re, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "governance", "DRAFT_CORRECTION_LEDGER.csv")
DIFFDIR = os.path.join(ROOT, "governance", "draft_corrections")

def _words(s): return re.findall(r"[a-zA-Z0-9']+", (s or "").lower())

def change_ratio(ai, human):
    """Fraction of the human's words not present in the AI draft (how much the human changed/added)."""
    H, A = set(_words(human)), set(_words(ai))
    if not H: return 0.0
    return len(H - A) / len(H)

def line_stats(ai, human):
    sm = difflib.SequenceMatcher(None, (ai or "").splitlines(), (human or "").splitlines())
    added = removed = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("replace", "delete"): removed += (i2 - i1)
        if tag in ("replace", "insert"): added += (j2 - j1)
    return added, removed

def append_ledger(row):
    new = not os.path.exists(LEDGER)
    with open(LEDGER, "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if new: w.writerow(["timestamp", "doc", "author", "change_ratio", "lines_added", "lines_removed", "diff"])
        w.writerow(row)

def write_diff(doc, ai, human, ts):
    os.makedirs(DIFFDIR, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", doc.lower()).strip("-")[:40] or "doc"
    path = os.path.join(DIFFDIR, "%s-%s.diff" % (slug, ts.replace(":", "")))
    diff = difflib.unified_diff((ai or "").splitlines(), (human or "").splitlines(),
                                fromfile="ai_draft", tofile="human_final", lineterm="")
    open(path, "w", encoding="utf-8").write("\n".join(diff) or "(no line-level difference)")
    return path

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ai-draft", required=True); ap.add_argument("--human-final", required=True)
    ap.add_argument("--doc", required=True); ap.add_argument("--author", default="Director")
    a = ap.parse_args(argv)
    if not (os.path.exists(a.ai_draft) and os.path.exists(a.human_final)):
        print("[draft_diff] need readable --ai-draft and --human-final files"); return 1
    ai = open(a.ai_draft, encoding="utf-8", errors="replace").read()
    human = open(a.human_final, encoding="utf-8", errors="replace").read()
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    cr = change_ratio(ai, human); added, removed = line_stats(ai, human)
    dpath = write_diff(a.doc, ai, human, ts)
    append_ledger([ts, a.doc, a.author, "%.2f" % cr, added, removed, os.path.relpath(dpath, ROOT)])
    flag = " (LOW human edit — review whether the human engaged)" if cr < 0.15 else ""
    print("[draft_diff] %s: change_ratio=%.2f, +%d/-%d lines, diff=%s%s" %
          (a.doc, cr, added, removed, os.path.relpath(dpath, ROOT), flag))
    return 0

if __name__ == "__main__":
    sys.exit(main())
