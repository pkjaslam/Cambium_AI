#!/usr/bin/env python3
"""gen_routing_golden -- regenerate the golden routing-fidelity files for task_router.route().

The golden files under tests/golden/routing/ freeze the deterministic router's behavior for a
canned set of tasks: every task type the router supports (grant, project, review, software,
video, report, data, research) plus type-detection edge cases (keyword ties, ambiguous wording,
zero-keyword fallback). tests/test_routing_golden.py re-runs route() against each golden file,
so silent routing drift -- type, phase ids, gate ids, or dispatched agents -- becomes a red test.

The canned task list lives HERE, as data, so the goldens and their regeneration cannot diverge.
If a router change is INTENTIONAL, rerun this tool to re-freeze current behavior. If a golden
test goes red and you did not mean to change routing, fix the router, not the golden.

Golden shape (json, sorted keys, indent 2):
  {
    "task": "<the canned task string>",
    "type": "<router type>",
    "phases": [{"id": ..., "gate_id_or_null": ..., "agents_by_group": {label: [agents, sorted]}}],
    "all_agents_sorted": [...]
  }

Usage:
  python3 tools/gen_routing_golden.py            # rewrite tests/golden/routing/*.json
  python3 tools/gen_routing_golden.py --check    # exit 1 if regeneration would change any file

Exit codes:
  0  write mode: goldens written / already current; --check: nothing would change
  1  --check only: regeneration would change at least one file, or a stray *.json exists
"""
from __future__ import annotations
import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cambium_io  # noqa: F401 -- UTF-8 stdout/stderr guard on Windows
import task_router

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN_DIR = os.path.join(ROOT, "tests", "golden", "routing")

# One golden file per canned task. Filenames are stable identifiers; the two-digit prefix keeps
# listings in coverage order. Together these cover all eight router types plus the tricky
# classification edges (keyword tie broken by TYPES order, ambiguous wording, zero-hit fallback).
CANNED_TASKS = [
    # -- grant (pre-award) --
    ("01-grant-nsf-soil.json",
     "Win an NSF grant on soil health for Idaho rangelands"),
    ("02-grant-usda-budget.json",
     "Prepare the budget justification for the USDA AFRI solicitation"),
    # -- project (post-award management, distinct from grant) --
    ("03-project-post-award.json",
     "Manage the awarded project: work breakdown, subaward coordination, and the milestone schedule"),
    # -- review --
    ("04-review-security-audit.json",
     "Review the codebase for security vulnerabilities before release"),
    # edge: exact keyword tie (review 2 vs research 2) broken by TYPES order -> review
    ("05-review-vs-research-tie.json",
     "Fix the bug in the simulation model"),
    # -- software --
    ("06-software-webapp-dashboard.json",
     "Build a web app dashboard for the field station"),
    # edge: ambiguous wording, review keyword present but software outweighs it -> software
    ("07-software-vs-review-ambiguous.json",
     "Test the new dashboard feature before deploy"),
    # -- video (beats the weaker research signal from 'study') --
    ("08-video-abstract.json",
     "Make a video abstract for the published study"),
    # -- report --
    ("09-report-quarterly.json",
     "Write the quarterly progress report for the funder"),
    # edge: deck/slides wording chosen so report wins without tripping software keywords
    ("10-report-vs-software-deck.json",
     "Prepare a slides deck summarizing the quarter for the sponsors"),
    # -- data --
    ("11-data-clean-stats.json",
     "Clean the dataset and run statistics on the yield measurements"),
    # -- research --
    ("12-research-benchmark-estimator.json",
     "Design an experiment to benchmark the new estimator"),
    # edge: zero keyword hits anywhere -> default research
    ("13-research-default-no-keywords.json",
     "Help the team with an unusual one-off request"),
    # edge: partnership wording; the router has no partnership type, so this documents the
    # current behavior: zero hits -> default research
    ("14-research-partnership-wording.json",
     "Set up a partnership with the extension office and local growers"),
    # edge: write-up wording with no type keywords -> default research (whose plan carries
    # the writeup phase and the G-release gate)
    ("15-research-writeup-manuscript.json",
     "Write up the verified findings as a manuscript for the journal"),
]

_names = [fname for fname, _ in CANNED_TASKS]
if len(set(_names)) != len(_names):
    raise ValueError("CANNED_TASKS contains duplicate golden filenames")


def golden_for(task):
    """Run the live router on *task* and shape the result into the golden dict."""
    r = task_router.route(task)
    phases = []
    all_agents = set()
    for p in r["phases"]:
        by_group = {}
        for g in p["groups"]:
            label = g["label"]
            if label in by_group:
                raise ValueError(
                    "duplicate group label %r in phase %r for task %r; "
                    "agents_by_group cannot represent it" % (label, p["id"], task))
            by_group[label] = sorted(g["agents"])
            all_agents.update(g["agents"])
        phases.append({
            "id": p["id"],
            "gate_id_or_null": p["gate"]["id"] if p.get("gate") else None,
            "agents_by_group": by_group,
        })
    return {
        "task": task,
        "type": r["type"],
        "phases": phases,
        "all_agents_sorted": sorted(all_agents),
    }


def render(obj):
    """Human-readable golden encoding: sorted keys, indent 2, trailing newline."""
    return json.dumps(obj, indent=2, sort_keys=True) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=(
            "Regenerate tests/golden/routing/*.json from the live task_router.route(), "
            "or verify (--check) that regeneration would change nothing."))
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if regeneration would change any golden file")
    args = ap.parse_args(argv)

    changed, unchanged = [], []
    for fname, task in CANNED_TASKS:
        path = os.path.join(GOLDEN_DIR, fname)
        want = render(golden_for(task))
        have = None
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                have = fh.read()
        if have == want:
            unchanged.append(fname)
        else:
            changed.append(fname)
            if not args.check:
                os.makedirs(GOLDEN_DIR, exist_ok=True)
                with open(path, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(want)

    managed = set(_names)
    stray = sorted(os.path.basename(p)
                   for p in glob.glob(os.path.join(GOLDEN_DIR, "*.json"))
                   if os.path.basename(p) not in managed)

    print("[gen_routing_golden] %d canned task(s) -> %s" %
          (len(CANNED_TASKS), os.path.relpath(GOLDEN_DIR, ROOT)))

    if args.check:
        for f in changed:
            print("  STALE: %s (regeneration would change it)" % f)
        for f in stray:
            print("  STRAY: %s (not in CANNED_TASKS; delete it or add its task to the list)" % f)
        if changed or stray:
            print("[gen_routing_golden] -> FAILED. Regenerate: python3 tools/gen_routing_golden.py")
            return 1
        print("[gen_routing_golden] OK: all %d golden files match the live router." % len(unchanged))
        return 0

    for f in changed:
        print("  wrote %s" % f)
    print("[gen_routing_golden] %d written, %d unchanged." % (len(changed), len(unchanged)))
    for f in stray:
        print("  WARNING stray golden not managed by this tool (left in place): %s" % f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
