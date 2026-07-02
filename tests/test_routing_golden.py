"""tests/test_routing_golden.py -- golden routing-fidelity suite for tools/task_router.py.

Freezes the deterministic router's behavior. Each golden file under tests/golden/routing/
captures route(task) for one canned task (all eight task types plus type-detection edge
cases: keyword ties, ambiguous wording, zero-keyword fallback). Every test here re-runs the
LIVE router and compares it to the frozen golden, so silent routing drift -- a changed type,
a moved gate, a phase that appears or disappears, an agent added to or dropped from a group --
becomes a red test that names the task and the field that drifted.

If a router change is INTENTIONAL, re-freeze current behavior:
    python3 tools/gen_routing_golden.py

Also asserts structural invariants on every routed plan:
  - every routed agent exists in .claude/agents/ (by frontmatter name)
  - the conductor (orchestrator) is never dispatched as a worker
  - every plan has phases, every phase has groups, every group has agents
  - any plan with a drafting/writeup deliverable carries a release gate

Uses only stdlib + pytest. The golden shape is built by gen_routing_golden.golden_for(), the
same code path the generator uses, so the comparison cannot diverge from regeneration.
"""
import glob
import json
import os
import subprocess
import sys

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import gen_routing_golden as G
import task_router

GOLDEN_DIR = os.path.join(_REPO, "tests", "golden", "routing")
GOLDEN_FILES = sorted(glob.glob(os.path.join(GOLDEN_DIR, "*.json")))
GOLDEN_IDS = [os.path.basename(p) for p in GOLDEN_FILES]

REGEN = "If this change is INTENTIONAL, regenerate the golden: python3 tools/gen_routing_golden.py"

# Gates that release a finished written deliverable to the human:
# G-release ("release / publish the deliverable?") and G5 ("release report?" / "release the video?").
RELEASE_GATE_IDS = {"G-release", "G5"}

CONDUCTOR = "orchestrator"


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _drift(task, field, golden_side, routed_side):
    """Assertion message: which task, which field drifted, both sides compactly, regen hint."""
    return (
        "routing drift for task %r: field %r drifted.\n"
        "  golden: %s\n"
        "  routed: %s\n"
        "%s" % (
            task,
            field,
            json.dumps(golden_side, sort_keys=True),
            json.dumps(routed_side, sort_keys=True),
            REGEN,
        )
    )


def _roster_names():
    """Agent names as declared in .claude/agents/*.md frontmatter (name: <id>)."""
    names = set()
    for p in glob.glob(os.path.join(_REPO, ".claude", "agents", "*.md")):
        if os.path.basename(p).upper() == "README.MD":
            continue
        with open(p, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        if not text.startswith("---"):
            continue
        for line in text.splitlines()[1:]:
            if line.strip() == "---":
                break
            if line.startswith("name:"):
                names.add(line.split(":", 1)[1].strip())
                break
    return names


def _routed_agents(plan):
    return {a for p in plan["phases"] for g in p["groups"] for a in g["agents"]}


# ---------------------------------------------------------------------------
# Suite plumbing: goldens exist, match the generator's canned list, cover all types
# ---------------------------------------------------------------------------

def test_goldens_exist():
    assert GOLDEN_FILES, (
        "no golden files found in tests/golden/routing/ -- generate them: "
        "python3 tools/gen_routing_golden.py"
    )


def test_golden_dir_matches_canned_list():
    on_disk = set(GOLDEN_IDS)
    managed = {fname for fname, _ in G.CANNED_TASKS}
    assert on_disk == managed, (
        "tests/golden/routing/ does not match gen_routing_golden.CANNED_TASKS.\n"
        "  missing on disk: %s\n"
        "  stray on disk:   %s\n"
        "%s" % (sorted(managed - on_disk), sorted(on_disk - managed), REGEN)
    )


def test_every_router_type_is_covered():
    """The canned set must exercise EVERY task type the router supports."""
    covered = {_load(p)["type"] for p in GOLDEN_FILES}
    all_types = {name for name, _, _ in task_router.TYPES}
    missing = sorted(all_types - covered)
    assert not missing, (
        "router types with no golden coverage: %s -- add a canned task per missing type "
        "to gen_routing_golden.CANNED_TASKS and regenerate." % missing
    )


def test_gen_routing_golden_check_mode_is_green():
    """--check must exit 0 on a fresh checkout; byte-level freeze of the golden files."""
    r = subprocess.run(
        [sys.executable, os.path.join(_REPO, "tools", "gen_routing_golden.py"), "--check"],
        cwd=_REPO, capture_output=True, text=True,
    )
    assert r.returncode == 0, (
        "gen_routing_golden.py --check failed:\n%s\n%s\n%s" % (r.stdout, r.stderr, REGEN)
    )


# ---------------------------------------------------------------------------
# Golden fidelity: re-run route() and compare field by field
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", GOLDEN_FILES, ids=GOLDEN_IDS)
def test_routing_matches_golden(path):
    golden = _load(path)
    task = golden["task"]
    routed = G.golden_for(task)

    # 1) task type
    assert routed["type"] == golden["type"], _drift(task, "type", golden["type"], routed["type"])

    # 2) phase ids, in order
    golden_ids = [p["id"] for p in golden["phases"]]
    routed_ids = [p["id"] for p in routed["phases"]]
    assert routed_ids == golden_ids, _drift(task, "phase ids", golden_ids, routed_ids)

    # 3) gate ids, aligned with the phase order
    golden_gates = [p["gate_id_or_null"] for p in golden["phases"]]
    routed_gates = [p["gate_id_or_null"] for p in routed["phases"]]
    assert routed_gates == golden_gates, _drift(task, "gate ids", golden_gates, routed_gates)

    # 4) per-phase agent sets (by group; agent lists are sorted, so this is set equality)
    for gp, rp in zip(golden["phases"], routed["phases"]):
        assert rp["agents_by_group"] == gp["agents_by_group"], _drift(
            task,
            "phase %r agents_by_group" % gp["id"],
            gp["agents_by_group"],
            rp["agents_by_group"],
        )

    # 5) sorted union of all agents across the plan
    assert routed["all_agents_sorted"] == golden["all_agents_sorted"], _drift(
        task, "all_agents_sorted", golden["all_agents_sorted"], routed["all_agents_sorted"]
    )


# ---------------------------------------------------------------------------
# Structural invariants on every routed plan (fresh route(), not the frozen file)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", GOLDEN_FILES, ids=GOLDEN_IDS)
def test_invariant_every_routed_agent_exists_in_roster(path):
    task = _load(path)["task"]
    plan = task_router.route(task)
    roster = _roster_names()
    assert roster, "no agent frontmatter names found under .claude/agents/"
    unknown = sorted(_routed_agents(plan) - roster)
    assert not unknown, (
        "task %r routes to agents with no .claude/agents/ definition (frontmatter name): %s"
        % (task, unknown)
    )


@pytest.mark.parametrize("path", GOLDEN_FILES, ids=GOLDEN_IDS)
def test_invariant_conductor_is_never_a_worker(path):
    task = _load(path)["task"]
    plan = task_router.route(task)
    offending = [
        (p["id"], g["label"])
        for p in plan["phases"] for g in p["groups"] if CONDUCTOR in g["agents"]
    ]
    assert not offending, (
        "task %r dispatches the conductor (%s) as a worker in (phase, group): %s"
        % (task, CONDUCTOR, offending)
    )


@pytest.mark.parametrize("path", GOLDEN_FILES, ids=GOLDEN_IDS)
def test_invariant_every_phase_and_group_is_nonempty(path):
    task = _load(path)["task"]
    plan = task_router.route(task)
    assert plan["phases"], "task %r routed to a plan with no phases" % task
    for p in plan["phases"]:
        assert p["groups"], "task %r: phase %r has no groups" % (task, p["id"])
        for g in p["groups"]:
            assert g["agents"], (
                "task %r: phase %r group %r has an empty agent list" % (task, p["id"], g["label"])
            )


@pytest.mark.parametrize("path", GOLDEN_FILES, ids=GOLDEN_IDS)
def test_invariant_writeup_deliverable_carries_release_gate(path):
    """Any plan that drafts a written deliverable (a writeup phase / write-up group) must also
    carry a human release gate (G-release or G5) somewhere in the plan, so the finished document
    cannot ship on G4 findings-approval alone."""
    task = _load(path)["task"]
    plan = task_router.route(task)
    has_writeup = any(
        p["id"] == "writeup" or any(g["label"] == "write-up" for g in p["groups"])
        for p in plan["phases"]
    )
    if not has_writeup:
        return
    gate_ids = {p["gate"]["id"] for p in plan["phases"] if p.get("gate")}
    assert gate_ids & RELEASE_GATE_IDS, (
        "task %r drafts a written deliverable but its plan has no release gate %s; gates present: %s"
        % (task, sorted(RELEASE_GATE_IDS), sorted(gate_ids))
    )
