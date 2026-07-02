"""closeout.py and task_router.py: doc-drift detector + advisory close-out review tests."""
import os, sys, re, tempfile, shutil
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import closeout as C

# ---- existing tests (unchanged) ----

def test_changelog_date_parses():
    d = C.latest_changelog_date()
    assert d and re.match(r"\d{4}-\d{2}-\d{2}", d)

def test_roadmap_has_last_updated():
    assert C.doc_last_updated("docs/reference/ROADMAP.md") is not None

def test_no_drift_right_now():
    # after the Support sweep, the forward docs should be current
    assert C.check_drift() == []

def test_drift_compare_logic():
    # the core rule: an older doc date than the changelog is drift
    assert "2026-06-26" < "2026-06-27"   # the exact comparison closeout uses

def test_readme_tool_count_matches():
    # closeout's README check: the stated tool count must equal the actual tools/ count (no prose drift)
    problems, unref = C.check_readme_tools()
    assert not any("README says" in p for p in problems), problems

# ---- new tests ----

def test_outreach_in_closeout_plan():
    """Change 1: outreach must be a named agent in the _closeout() phase group."""
    import task_router as TR
    phase = TR._closeout()
    all_agents = [a for g in phase["groups"] for a in g["agents"]]
    assert "outreach" in all_agents, (
        f"outreach not found in closeout phase agents; got: {all_agents}"
    )

def test_version_badge_match_detects_mismatch(tmp_path):
    """Change 2a: check_version_badge() must flag a badge version that differs from CHANGELOG."""
    # Build a minimal fake repo tree in tmp_path
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        "# Changelog\n\n## 2.0.0 - 2026-07-01 - big release\n\nsome notes\n",
        encoding="utf-8"
    )
    readme = tmp_path / "README.md"
    # badge says 1.0.0 but changelog says 2.0.0 -- should flag drift
    readme.write_text(
        '<img src="https://img.shields.io/badge/version-1.0.0-green">\n',
        encoding="utf-8"
    )

    # Patch ROOT inside the closeout module temporarily
    orig_root = C.ROOT
    try:
        C.ROOT = str(tmp_path)
        problems = C.check_version_badge()
    finally:
        C.ROOT = orig_root

    assert problems, "Expected a version badge mismatch problem, got none"
    assert any("1.0.0" in p and "2.0.0" in p for p in problems), (
        f"Problem message did not mention both versions: {problems}"
    )

def test_version_badge_match_passes_when_same(tmp_path):
    """check_version_badge() returns no problems when badge version matches CHANGELOG."""
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        "# Changelog\n\n## 1.5.0 - 2026-07-01 - stable\n\nnotes\n",
        encoding="utf-8"
    )
    readme = tmp_path / "README.md"
    readme.write_text(
        '<img src="https://img.shields.io/badge/version-1.5.0-green">\n',
        encoding="utf-8"
    )

    orig_root = C.ROOT
    try:
        C.ROOT = str(tmp_path)
        problems = C.check_version_badge()
    finally:
        C.ROOT = orig_root

    assert problems == [], f"Expected no problems on matching versions, got: {problems}"

def test_skills_coverage_flags_undescribed(tmp_path):
    """Change 2b: check_skills_coverage() must flag a skill whose name is absent from README and docs."""
    # Set up a fake skills/ dir with two skills
    skills_dir = tmp_path / "skills"
    described_skill = skills_dir / "data-wrangling"
    described_skill.mkdir(parents=True)
    (described_skill / "SKILL.md").write_text("# data-wrangling\n", encoding="utf-8")

    undescribed_skill = skills_dir / "secret-skill"
    undescribed_skill.mkdir(parents=True)
    (undescribed_skill / "SKILL.md").write_text("# secret-skill\n", encoding="utf-8")

    # README mentions data-wrangling but not secret-skill
    readme = tmp_path / "README.md"
    readme.write_text(
        "We use the data-wrangling skill in our pipeline.\n",
        encoding="utf-8"
    )

    # No docs/ dir in tmp_path, so only README is searched

    orig_root = C.ROOT
    try:
        C.ROOT = str(tmp_path)
        count, undescribed = C.check_skills_coverage()
    finally:
        C.ROOT = orig_root

    assert count == 2, f"Expected 2 skills, got {count}"
    assert "secret-skill" in undescribed, (
        f"Expected secret-skill to be flagged as undescribed, got: {undescribed}"
    )
    assert "data-wrangling" not in undescribed, (
        f"data-wrangling should be considered described, got undescribed: {undescribed}"
    )

def test_skills_coverage_no_skills_dir(tmp_path):
    """check_skills_coverage() returns 0 skills gracefully when skills/ does not exist."""
    orig_root = C.ROOT
    try:
        C.ROOT = str(tmp_path)
        count, undescribed = C.check_skills_coverage()
    finally:
        C.ROOT = orig_root

    assert count == 0
    assert undescribed == []

# ---- ADR discipline (advisory signal) ----

def test_adr_signal_fires_on_architectural_entry_with_stale_decisions(tmp_path):
    """check_adr_signal(): architectural words in the top CHANGELOG entry + a DECISIONS.md
    older than CHANGELOG.md on disk => an advisory suggestion to record an ADR."""
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        "# Changelog\n\n## 2.0.0 - 2026-07-01 - restructure\n\n"
        "Added a new council and retired the legacy execution path.\n",
        encoding="utf-8"
    )
    dec_dir = tmp_path / "docs" / "reference"
    dec_dir.mkdir(parents=True)
    decisions = dec_dir / "DECISIONS.md"
    decisions.write_text("# Decisions\n", encoding="utf-8")
    old = os.path.getmtime(str(changelog)) - 3600
    os.utime(str(decisions), (old, old))

    orig_root = C.ROOT
    try:
        C.ROOT = str(tmp_path)
        msg = C.check_adr_signal()
    finally:
        C.ROOT = orig_root

    assert msg, "Expected an advisory ADR suggestion, got None"
    assert "ADR" in msg and "new council" in msg and "retire" in msg, msg


def test_adr_signal_silent_when_not_architectural_or_decisions_fresh(tmp_path):
    """check_adr_signal(): no signal on a non-architectural entry, and no signal when
    DECISIONS.md is at least as fresh as CHANGELOG.md (the ADR was plausibly written)."""
    changelog = tmp_path / "CHANGELOG.md"
    dec_dir = tmp_path / "docs" / "reference"
    dec_dir.mkdir(parents=True)
    decisions = dec_dir / "DECISIONS.md"
    decisions.write_text("# Decisions\n", encoding="utf-8")

    orig_root = C.ROOT
    try:
        C.ROOT = str(tmp_path)

        # non-architectural entry, stale DECISIONS.md: silent
        changelog.write_text(
            "# Changelog\n\n## 2.0.1 - 2026-07-01 - tidy\n\nFixed a typo in the README.\n",
            encoding="utf-8"
        )
        old = os.path.getmtime(str(changelog)) - 3600
        os.utime(str(decisions), (old, old))
        assert C.check_adr_signal() is None

        # architectural entry, but DECISIONS.md fresher than CHANGELOG.md: silent
        changelog.write_text(
            "# Changelog\n\n## 2.1.0 - 2026-07-01 - protocol change\n\n"
            "Reworked the handoff protocol between councils.\n",
            encoding="utf-8"
        )
        newer = os.path.getmtime(str(changelog)) + 3600
        os.utime(str(decisions), (newer, newer))
        assert C.check_adr_signal() is None
    finally:
        C.ROOT = orig_root
