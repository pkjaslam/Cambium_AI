#!/usr/bin/env python3
"""closeout -- advisory close-out review for the Support council (PRESENTATION Act IV).

These checks are signals for the orchestrator and the human to weigh. They are NOT a lock
on a run. The decision about whether a run is complete rests with the orchestrator's judgment
and the researcher, not with this script. Per the Director's decision: honest, advisory,
judgment-based. Exit non-zero is a repo-tidy signal for CI, not a run veto.

Run this after ANY change. It checks that the institute's forward memory has not drifted
behind the code, verifies the README version badge matches CHANGELOG, counts skills coverage,
and prints the CLOSEOUT_CHECKLIST so Support refreshes EVERY doc.

Usage: python3 tools/closeout.py
Exit: 0 = memory is current, checks passed  |  1 = drift / a check failed (signals follow-up).
"""
import os, re, sys, subprocess
import cambium_io  # noqa: F401 -- reconfigures stdout/stderr to UTF-8 on Windows
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORWARD_DOCS = ["docs/reference/ROADMAP.md"]  # docs that carry a 'Last updated: YYYY-MM-DD' line

def latest_changelog_date():
    p = os.path.join(ROOT, "CHANGELOG.md")
    if not os.path.exists(p): return None
    dates = re.findall(r"^## \d[\d.]*\s*-\s*(\d{4}-\d{2}-\d{2})", open(p, encoding="utf-8").read(), re.M)
    return max(dates) if dates else None

def latest_changelog_version():
    """Return the version string from the latest CHANGELOG heading (e.g. '1.29.0')."""
    p = os.path.join(ROOT, "CHANGELOG.md")
    if not os.path.exists(p): return None
    m = re.search(r"^## (\d[\d.]*)\s*-", open(p, encoding="utf-8").read(), re.M)
    return m.group(1) if m else None

def doc_last_updated(rel):
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p): return None
    m = re.search(r"Last updated:\s*(\d{4}-\d{2}-\d{2})", open(p, encoding="utf-8").read())
    return m.group(1) if m else None

def check_drift():
    problems = []
    cl = latest_changelog_date()
    for rel in FORWARD_DOCS:
        d = doc_last_updated(rel)
        if cl and d and d < cl:
            problems.append(f"{rel} 'Last updated' {d} is OLDER than the latest CHANGELOG entry {cl} -- refresh it.")
        elif cl and d is None:
            problems.append(f"{rel} has no 'Last updated:' date to check.")
    return problems

CHECKLIST = """  CLOSE-OUT CHECKLIST (the Support council refreshes ALL of these, not just the CHANGELOG):
    [ ] CHANGELOG.md -- new entry      [ ] DECISIONS.md -- ADR (if architectural)
    [ ] governance/GATES.md -- gate    [ ] README -- counts + roadmap paragraph
    [ ] docs/reference/ROADMAP.md -- + bump 'Last updated'   [ ] docs/start-here/USE_CAMBIUM.md / docs/start-here/FAQ.md (if user-facing)
    [ ] docs/governance/POSITIONING.md / docs/concepts/PHILOSOPHY.md (if claims moved)   [ ] consistency_check + doctor + pytest green
    [ ] janitor -- no stray files / doc drift"""

def check_readme_tools():
    """README must state the right tool count AND name every tool somewhere in the docs (catches prose drift)."""
    import glob, re
    problems = []
    tools = [os.path.basename(p)[:-3] for p in glob.glob(os.path.join(ROOT, "tools", "*.py"))]
    docs = ""
    for d in ("README.md", "docs/reference/ROADMAP.md", "docs/concepts/INSTITUTE.md"):
        p = os.path.join(ROOT, d)
        if os.path.exists(p): docs += open(p, encoding="utf-8").read()
    rd = os.path.join(ROOT, "README.md")
    if os.path.exists(rd):
        m = re.search(r"(\d+)\s+tools", open(rd, encoding="utf-8").read())
        if m and int(m.group(1)) != len(tools):
            problems.append(f"README says '{m.group(1)} tools' but tools/ has {len(tools)} .py files.")
    unref = [t for t in tools if t not in docs]
    return problems, unref

def check_version_badge():
    """README version badge should match the latest CHANGELOG version heading.

    Advisory signal: a mismatch means the badge was not bumped after a release.
    This does not block a run; it informs the orchestrator that a doc refresh may be due.
    """
    problems = []
    rd = os.path.join(ROOT, "README.md")
    if not os.path.exists(rd):
        return problems
    readme_text = open(rd, encoding="utf-8").read()
    m = re.search(r"img\.shields\.io/badge/version-([^-?&\s\"]+)", readme_text)
    badge_version = m.group(1) if m else None
    changelog_version = latest_changelog_version()
    if badge_version and changelog_version and badge_version != changelog_version:
        problems.append(
            f"Version badge in README ({badge_version}) does not match latest CHANGELOG heading ({changelog_version})."
            " (advisory: bump the badge when you cut a release)"
        )
    return problems

def check_skills_coverage():
    """Count skills (dirs under skills/ with a SKILL.md) and flag any not mentioned in README or docs prose.

    Advisory signal only. A skill not mentioned in prose is not an error; it is a prompt
    to consider whether the docs should describe it. The orchestrator decides.
    """
    import glob
    skills_dir = os.path.join(ROOT, "skills")
    skill_names = []
    if os.path.isdir(skills_dir):
        for entry in os.listdir(skills_dir):
            if os.path.isdir(os.path.join(skills_dir, entry)):
                if os.path.exists(os.path.join(skills_dir, entry, "SKILL.md")):
                    skill_names.append(entry)

    # gather prose corpus: README + docs/ subtree
    prose = ""
    rd = os.path.join(ROOT, "README.md")
    if os.path.exists(rd):
        prose += open(rd, encoding="utf-8").read()
    docs_root = os.path.join(ROOT, "docs")
    if os.path.isdir(docs_root):
        for fpath in glob.glob(os.path.join(docs_root, "**", "*.md"), recursive=True):
            prose += open(fpath, encoding="utf-8").read()

    undescribed = [s for s in skill_names if s not in prose]
    return len(skill_names), undescribed

ADR_WORDS = ("new council", "new gate", "execution path", "protocol", "retire", "consolidat")

def check_adr_signal():
    """Advisory: an architectural-sounding release should leave an ADR in DECISIONS.md.

    If the top CHANGELOG entry mentions architectural words (new council, new gate,
    execution path, protocol, retire, consolidat...) and docs/reference/DECISIONS.md is
    older on disk than CHANGELOG.md, suggest recording an ADR (templates/ADR.md). This is
    a suggestion for the orchestrator and the researcher to weigh; it never fails the review.
    """
    cl = os.path.join(ROOT, "CHANGELOG.md")
    dm = os.path.join(ROOT, "docs", "reference", "DECISIONS.md")
    if not (os.path.exists(cl) and os.path.exists(dm)):
        return None
    m = re.search(r"^## .*?(?=^## |\Z)", open(cl, encoding="utf-8").read(), re.M | re.S)
    if not m:
        return None
    top = m.group(0).lower()
    hits = sorted(w for w in ADR_WORDS if w in top)
    if not hits:
        return None
    if os.path.getmtime(dm) >= os.path.getmtime(cl):
        return None
    return ("top CHANGELOG entry sounds architectural (" + ", ".join(hits) + ") but DECISIONS.md "
            "is older than CHANGELOG.md; consider recording an ADR (templates/ADR.md -> docs/reference/DECISIONS.md).")

def main():
    print("=" * 70)
    print("Close-out review (advisory)")
    print("These are signals for the orchestrator and the researcher to weigh.")
    print("They inform judgment; they do not gate or veto a run.")
    print("=" * 70)

    problems = check_drift()

    # version badge check (advisory, but still counted as drift for CI)
    badge_problems = check_version_badge()
    problems += badge_problems

    rp, unref = check_readme_tools(); problems += rp
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "consistency_check.py")],
                       capture_output=True, text=True)
    if r.returncode != 0:
        problems.append("consistency_check FAILED -- counts drifted.")

    # skills coverage (advisory only, not added to problems list)
    skill_count, undescribed_skills = check_skills_coverage()
    print(f"\n  Skills coverage (advisory): {skill_count} skill(s) found under skills/")
    if undescribed_skills:
        print("  (advisory) skills not mentioned in README or docs prose: " + ", ".join(undescribed_skills))
        print("  Note: undescribed skills are a signal to consider documentation, not a hard error.")

    # ADR discipline (advisory only, never added to problems)
    adr = check_adr_signal()
    if adr:
        print("  (advisory) " + adr)

    print(CHECKLIST)
    if unref: print("  (advisory) tools not named in any doc: " + ", ".join(unref))
    print(f"  latest CHANGELOG date: {latest_changelog_date()} | ROADMAP last-updated: {doc_last_updated('docs/reference/ROADMAP.md')}")
    print(f"  latest CHANGELOG version: {latest_changelog_version()}")

    # Learning delivery gate: check that build/analysis runs delivered a learning artifact.
    ld_script = os.path.join(ROOT, "tools", "learning_delivery.py")
    ld_result = subprocess.run(
        [sys.executable, ld_script, "check", "--root", ROOT],
        capture_output=True, text=True
    )
    print(ld_result.stdout.rstrip())
    if ld_result.returncode != 0:
        problems.append(
            "learning not delivered -- teaching is required on a build/analysis run "
            "(run the teaching-assistant or fill templates/LEARNING_PACKET.md -> agent_outputs/learning_packet.md)"
        )

    if problems:
        print("\n[closeout] DRIFT / SIGNALS (orchestrator should review before calling this run complete):")
        for p in problems: print("  x " + p)
        print("\n  (These are repo-tidy signals for CI. The run-level decision rests with the orchestrator.)")
        return 1
    print("\n[closeout] OK: forward docs are current, consistency passes, version badge matches.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
