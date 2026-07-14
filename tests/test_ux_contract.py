"""Regression guard for "the run you can always see" UX fix: three stable rule IDs
(SAME-TURN-GATE, BOARD-IN-MESSAGE, RENDER-LADDER) must show up verbatim where the contract
requires them, the new --compact text board must hold its display-width invariants, and the
gate-arming / first-paint nudges that used to fail silently must actually print.
"""
import os, sys, subprocess, tempfile, shutil, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import run_trace

RUN_STATE = os.path.join(ROOT, "tools", "run_state.py")
RUN_TRACE = os.path.join(ROOT, "tools", "run_trace.py")
RULE_IDS = ("SAME-TURN-GATE", "BOARD-IN-MESSAGE", "RENDER-LADDER")


# --- 1. the three rule IDs (+ the native ask) are in both contracts, verbatim ---

def test_rule_ids_in_contracts():
    """Both the /cambium command contract and PRESENTATION.md (the single source of truth),
    AND the Orchestrator's own system-prompt persona (both mirrored copies), must carry all
    three rule IDs and mention AskUserQuestion -- the agent that actually runs the show has
    to carry the same contract, not just the docs describing it to a reader."""
    rels = ("commands/cambium.md", "docs/concepts/PRESENTATION.md",
            "agents/00-orchestrator.md", ".claude/agents/00-orchestrator.md")
    for rel in rels:
        text = open(os.path.join(ROOT, rel), encoding="utf-8").read()
        for rid in RULE_IDS:
            assert rid in text, f"{rid} missing from {rel}"
        assert "AskUserQuestion" in text, f"AskUserQuestion missing from {rel}"

    # the persona is mirrored to two locations (repo-tracked + the one Claude Code actually
    # loads); they must never drift apart, or only one copy ever gets fixed.
    a = open(os.path.join(ROOT, "agents", "00-orchestrator.md"), encoding="utf-8").read()
    b = open(os.path.join(ROOT, ".claude", "agents", "00-orchestrator.md"), encoding="utf-8").read()
    assert a == b, "agents/00-orchestrator.md and .claude/agents/00-orchestrator.md have DRIFTED"


# --- 2/3. the compact board's own display-width invariants ---

def _w(s):
    """Independent local copy of the wide-aware display-width rule (W/F/A = 2, else 1).
    Deliberately NOT importing run_trace._disp_w -- this checks board_compact's ACTUAL
    output against an independently-written measurement, not the implementation against
    itself."""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F", "A") else 1 for ch in str(s))


# 4 phases: P1 done (with a finding), P2 active (2 agents, 1 finding), P3+P4 waiting.
# Role names are unique per phase on purpose, so "no per-agent line leaked from the done
# phase" can be checked unambiguously (no name shared with the active phase's own roster).
_STATE = {
    "plan": {"type": "cambium", "phases": [
        {"council": "Scouts", "label": "Survey", "gate": None,
         "agents": [["Scouts", "Landscape", "scout-landscape"], ["Scouts", "Timeline", "scout-timeline"]]},
        {"council": "Labs", "label": "Design", "gate": None,
         "agents": [["Labs", "Methods", "lab-methods"], ["Labs", "Domain", "lab-domain"]]},
        {"council": "Execution", "label": "Build", "gate": None,
         "agents": [["Execution", "Research Engineer", "research-engineer"]]},
        {"council": "Support", "label": "Close out", "gate": None,
         "agents": [["Support", "Record Keeper", "record-keeper"]]},
    ]},
    "findings": {
        "scout-landscape": "Prior art is thin; three candidate methods found",
        "lab-methods": "Chose a randomized block design",
    },
    "gate": {"id": "G2", "decision": "which direction do we take for the study?"},
}


def test_compact_board_invariants():
    t = run_trace.board_compact("evaluate soil-carbon monitoring methods", cur_phase=2, state=_STATE)
    lines = t.splitlines()

    # (a) universal cap: every line <= 64 display columns
    for line in lines:
        assert _w(line) <= 64, f"line exceeds 64 display cols ({_w(line)}): {line!r}"

    # (b) decision-tier cap: the header, and the GATE line (the one line carrying a
    # variable {decision} field, which board_compact truncates to 40 display cols by design)
    assert lines[0].startswith("⬢ CAMBIUM")
    assert _w(lines[0]) <= 40
    gate_lines = [l for l in lines if l.startswith("⛩ GATE")]
    assert len(gate_lines) == 1
    assert _w(gate_lines[0]) <= 40

    # (c) all WAITING phases (P3, P4) collapse to exactly ONE line
    next_lines = [l for l in lines if l.startswith("○ Next:")]
    assert len(next_lines) == 1, f"expected exactly one collapsed waiting line, got {next_lines}"

    # (d) no per-agent line for the DONE phase (P1 Scouts) -- rollup only
    assert not any("Landscape" in l for l in lines), "done phase leaked a per-agent line"
    assert not any("Timeline" in l for l in lines), "done phase leaked a per-agent line"
    assert any(l.startswith("✓ P1 Scouts(2)") for l in lines), "done phase rollup line missing"

    # (e) the native-ask nudge is present
    assert any(l.startswith("→ choose below") for l in lines)


def test_compact_board_complete():
    """cur_phase > total renders the run-complete line and NO gate lines (the run is over;
    there is nothing left to act on)."""
    t = run_trace.board_compact("evaluate soil-carbon monitoring methods", cur_phase=99, state=_STATE)
    lines = t.splitlines()
    assert lines[0] == "⬢ CAMBIUM — run complete"
    assert any(l.startswith("✓ Run complete —") for l in lines)
    assert not any(l.startswith("⛩ GATE") for l in lines)
    assert not any(l.startswith("→ choose below") for l in lines)


# --- 4. arming a gate must ALSO print the SAME-TURN-GATE nudge ---

def test_gate_nudge():
    """run_state.py's `gate` subcommand must print the SAME-TURN-GATE nudge in the SAME
    stdout as the arming confirmation -- a gate armed in run_state.json but never painted
    in the message the Director reads is exactly the bug this rule exists to catch."""
    d = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(d, "agent_outputs"))
        env = dict(os.environ, CAMBIUM_HOME=d)  # same temp-isolation spirit as test_run_state.py
        r = subprocess.run([sys.executable, RUN_STATE, "gate", "G2", "which direction?"],
                           cwd=d, env=env, capture_output=True, text=True)
        assert r.returncode == 0
        assert "SAME-TURN-GATE" in r.stdout
    finally:
        shutil.rmtree(d, ignore_errors=True)


# --- 5. cambium_start.py's banner canary ---

def test_start_banner_mentions_board_in_message():
    """Canary on the rule ID itself (not prose): the first-paint banner must literally
    print BOARD-IN-MESSAGE so it survives future rewording of the surrounding sentence."""
    src = open(os.path.join(ROOT, "tools", "cambium_start.py"), encoding="utf-8").read()
    assert "BOARD-IN-MESSAGE" in src


# --- 6. --compact is actually wired into the CLI ---

def test_compact_flag_wired():
    src = open(os.path.join(ROOT, "tools", "run_trace.py"), encoding="utf-8").read()
    assert '"--compact" in a' in src
    d = tempfile.mkdtemp()
    try:
        r = subprocess.run([sys.executable, RUN_TRACE, "--board", "--compact", "demo"],
                           cwd=d, capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        assert "⬢ CAMBIUM" in r.stdout
    finally:
        shutil.rmtree(d, ignore_errors=True)
