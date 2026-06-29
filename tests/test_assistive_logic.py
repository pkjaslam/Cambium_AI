"""Tests for the two AI-assists-not-replaces logic gates added to task_router.py.

Change 1: G-release gate fires on the writeup path (research/data/report),
          between _writeup() and _closeout(). No scholarly deliverable can be
          finalized without explicit human approval of the finished document.
          G4 approves findings only; G-release approves the deliverable itself.

Change 2: require_researcher_profile() is the hard G0 precondition for
          generative/pre-award paths (research, data, report, grant).
          If the profile is absent or empty, it returns a NEEDS_RESEARCHER_INPUT
          stop dict. The run engine must call this BEFORE starting a generative
          run and halt until the researcher supplies interests/expertise.
          Display-only callers (boards, trace) do not need to call the guard.
"""
import importlib.util
import os
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = importlib.util.spec_from_file_location(
    "task_router", os.path.join(HERE, "..", "tools", "task_router.py")
)
tr = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tr)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _phase_ids(phases):
    return [p["id"] for p in phases]

def _gate_ids(phases):
    return [p["gate"]["id"] for p in phases if p.get("gate")]


# ---------------------------------------------------------------------------
# Change 1: G-release appears on all writeup paths
# ---------------------------------------------------------------------------

class TestWriteupReleaseGate:
    """G-release must appear on research/data paths, before closeout.

    report is excluded on purpose: _report() already ends with its own G5
    "release report?" gate, so adding G-release would double the release gate."""

    def test_research_plan_contains_g_release(self):
        phases = tr.plan_for_type("research")
        assert "G-release" in _gate_ids(phases), (
            "research plan missing G-release gate -- finished manuscripts need a human release gate"
        )

    def test_data_plan_contains_g_release(self):
        phases = tr.plan_for_type("data")
        assert "G-release" in _gate_ids(phases), (
            "data plan missing G-release gate"
        )

    def test_report_keeps_its_own_release_gate(self):
        # report already ends with its own G5 "release report?" gate, so it must
        # NOT also get G-release (that would be two human release gates on one run).
        ids = _gate_ids(tr.plan_for_type("report"))
        assert "G5" in ids, "report plan should keep its own G5 release gate"
        assert "G-release" not in ids, (
            "report must not have G-release: it would duplicate G5"
        )

    def test_g_release_comes_before_closeout(self):
        """G-release must fire BEFORE closeout on every writeup path."""
        for typ in ("research", "data"):
            phases = tr.plan_for_type(typ)
            ids = _phase_ids(phases)
            assert "release" in ids, f"{typ}: no 'release' phase"
            assert "closeout" in ids, f"{typ}: no 'closeout' phase"
            assert ids.index("release") < ids.index("closeout"), (
                f"{typ}: 'release' phase must precede 'closeout'"
            )

    def test_g_release_comes_after_writeup(self):
        """G-release must fire AFTER the writeup phase on every writeup path."""
        for typ in ("research", "data"):
            phases = tr.plan_for_type(typ)
            ids = _phase_ids(phases)
            assert "writeup" in ids, f"{typ}: no 'writeup' phase"
            assert "release" in ids, f"{typ}: no 'release' phase"
            assert ids.index("writeup") < ids.index("release"), (
                f"{typ}: 'writeup' phase must precede 'release' gate phase"
            )

    def test_g_release_gate_id_and_decision_text(self):
        """G-release must carry the canonical gate id and a human-readable decision."""
        phases = tr.plan_for_type("research")
        release_phases = [p for p in phases if p["id"] == "release"]
        assert release_phases, "research: no 'release' phase"
        gate = release_phases[0].get("gate")
        assert gate is not None, "release phase has no gate"
        assert gate["id"] == "G-release", f"expected G-release, got {gate['id']}"
        assert "decision" in gate and gate["decision"], "G-release gate missing decision text"

    def test_non_writeup_paths_do_not_have_g_release(self):
        """Paths that do not produce a written deliverable should not have G-release."""
        for typ in ("software", "video", "grant"):
            phases = tr.plan_for_type(typ)
            assert "G-release" not in _gate_ids(phases), (
                f"{typ}: unexpected G-release gate -- only writeup paths need it"
            )

    def test_closeout_always_last(self):
        """Closeout must remain the final phase on every task type."""
        for typ_name, _, _ in tr.TYPES:
            phases = tr.plan_for_type(typ_name)
            assert phases[-1]["id"] == "closeout", (
                f"{typ_name}: closeout is not the final phase"
            )

    def test_paper_route_contains_g_release_before_closeout(self):
        """End-to-end: routing a research task yields a plan with G-release before closeout."""
        r = tr.route("run a hypothesis study on soil carbon")
        phases = r["phases"]
        ids = _phase_ids(phases)
        gate_ids = _gate_ids(phases)
        assert "G-release" in gate_ids, "routed research plan missing G-release"
        assert ids.index("release") < ids.index("closeout")


# ---------------------------------------------------------------------------
# Change 2: researcher profile guard -- require_researcher_profile() unit tests
# ---------------------------------------------------------------------------

class TestResearcherProfileGuard:
    """require_researcher_profile() must block when profile is absent/empty."""

    def test_none_profile_is_blocked(self):
        result = tr.require_researcher_profile(None)
        assert result is not None
        assert result.get("stop") == "needs-researcher-input"

    def test_empty_string_profile_is_blocked(self):
        result = tr.require_researcher_profile("")
        assert result is not None
        assert result.get("stop") == "needs-researcher-input"

    def test_whitespace_only_string_is_blocked(self):
        result = tr.require_researcher_profile("   ")
        assert result is not None
        assert result.get("stop") == "needs-researcher-input"

    def test_empty_dict_profile_is_blocked(self):
        result = tr.require_researcher_profile({})
        assert result is not None
        assert result.get("stop") == "needs-researcher-input"

    def test_dict_with_empty_fields_is_blocked(self):
        result = tr.require_researcher_profile({"interests": "", "expertise": "  "})
        assert result is not None
        assert result.get("stop") == "needs-researcher-input"

    def test_nonempty_string_profile_is_allowed(self):
        result = tr.require_researcher_profile("soil science and remote sensing")
        assert result is None, "non-empty profile string should be allowed"

    def test_dict_with_interests_is_allowed(self):
        result = tr.require_researcher_profile({"interests": "precision agriculture"})
        assert result is None

    def test_dict_with_expertise_is_allowed(self):
        result = tr.require_researcher_profile({"interests": "", "expertise": "machine learning"})
        assert result is None

    def test_dict_with_both_fields_is_allowed(self):
        result = tr.require_researcher_profile({"interests": "food systems", "expertise": "LCA"})
        assert result is None

    def test_stop_dict_has_g0_gate_field(self):
        result = tr.require_researcher_profile(None)
        assert result["gate"] == "G0"

    def test_stop_dict_message_mentions_user_profile(self):
        result = tr.require_researcher_profile({})
        assert "USER_PROFILE" in result["message"], (
            "stop message should mention USER_PROFILE.md so researcher knows what to fill"
        )


# ---------------------------------------------------------------------------
# Change 2 (pattern): the run-engine pattern must check profile before running
# ---------------------------------------------------------------------------

class TestProfileGuardRunPattern:
    """The guard pattern: check profile -> if blocked, stop; else route and run.

    This is the contract the run engine (cambium_run, MCP server) must follow
    for generative task types. These tests assert the contract is correct.
    """

    def test_empty_profile_blocks_research_generative_type(self):
        """classify() + require_researcher_profile() together block empty profile on research tasks."""
        task = "run an experiment on soil nitrogen"
        typ, _ = tr.classify(task)
        assert typ in tr.GENERATIVE_TYPES, f"expected generative type, got {typ}"
        stop = tr.require_researcher_profile(None)
        assert stop is not None and stop["stop"] == "needs-researcher-input"

    def test_empty_profile_blocks_data_generative_type(self):
        task = "analyze the dataset of field yields"
        typ, _ = tr.classify(task)
        assert typ in tr.GENERATIVE_TYPES
        stop = tr.require_researcher_profile("")
        assert stop is not None

    def test_empty_profile_blocks_report_generative_type(self):
        task = "write a summary report of the project findings"
        typ, _ = tr.classify(task)
        assert typ in tr.GENERATIVE_TYPES
        stop = tr.require_researcher_profile({})
        assert stop is not None

    def test_empty_profile_blocks_grant_generative_type(self):
        task = "submit an NSF proposal for climate research"
        typ, _ = tr.classify(task)
        assert typ in tr.GENERATIVE_TYPES
        stop = tr.require_researcher_profile(None)
        assert stop is not None

    def test_populated_profile_allows_research_task(self):
        """With a non-empty profile, the guard clears and route() returns a full plan."""
        task = "run an experiment on soil nitrogen"
        typ, _ = tr.classify(task)
        assert typ in tr.GENERATIVE_TYPES
        stop = tr.require_researcher_profile({"interests": "nitrogen cycling", "expertise": "agronomy"})
        assert stop is None, "populated profile should clear the guard"
        # only now should we call route()
        r = tr.route(task)
        assert "phases" in r and r["type"] == "research"

    def test_populated_profile_string_allows_task(self):
        task = "analyze the dataset of field yields"
        stop = tr.require_researcher_profile("precision ag and remote sensing")
        assert stop is None
        r = tr.route(task)
        assert "phases" in r

    def test_software_type_not_generative(self):
        """Software/review/video tasks are not GENERATIVE_TYPES; no profile needed."""
        task = "build a web app for data entry"
        typ, _ = tr.classify(task)
        assert typ not in tr.GENERATIVE_TYPES, f"{typ} should not be generative"

    def test_review_type_not_generative(self):
        task = "review and audit the codebase for security"
        typ, _ = tr.classify(task)
        assert typ not in tr.GENERATIVE_TYPES

    def test_video_type_not_generative(self):
        task = "make a video explainer for the grant results"
        typ, _ = tr.classify(task)
        assert typ not in tr.GENERATIVE_TYPES

    def test_needs_researcher_input_constant_has_required_fields(self):
        """The NEEDS_RESEARCHER_INPUT constant must have stop, gate, and message fields."""
        nri = tr.NEEDS_RESEARCHER_INPUT
        assert nri["stop"] == "needs-researcher-input"
        assert nri["gate"] == "G0"
        assert "message" in nri and len(nri["message"]) > 20
