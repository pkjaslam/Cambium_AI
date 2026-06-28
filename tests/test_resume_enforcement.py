"""Enforced --resume: a gate cannot be bypassed by re-running (review #4/#5/#6/#10).

Proves the runner refuses to continue past a gate without a valid gate_lock token, that gate.py --mint
(the approval) creates that token only with a real contribution, and that resume then proceeds."""
import json, os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _tool(t, *a): return subprocess.run([sys.executable, os.path.join(ROOT, "tools", t), *a],
                                         cwd=ROOT, capture_output=True, text=True, timeout=40)

_CONTRIB = {
 "hypothesis": ("My hypothesis for this gate is that connectivity across the three largest habitat patches "
                "matters more than corridor length because fragmentation at those pinch points most limits "
                "focal species dispersal and recovery across the entire funded project period here today now."),
 "reasoning": ("My reasoning rests on my own field experience on this landscape where measured corridor width "
               "drove animal usage far more than length, so I deliberately choose the connectivity first option "
               "despite its higher survey cost which I personally judge clearly worthwhile for these questions."),
 "choice": "A — connectivity-first", "socratic": "Risk: camera traps miss nocturnal use, so I add eDNA sampling."}

# ---- gate.py --mint = the approval that creates the enforceable token ------
def test_mint_refuses_bare_approval():
    g = "G-test-bare-" + str(os.getpid())
    r = _tool("gate.py", g, "--approver", "Jaslam", "--mint")
    assert r.returncode == 1 and "requires a Director contribution" in r.stdout
    assert not os.path.exists(os.path.join(ROOT, "governance", "gate_tokens", g + ".json"))

def test_mint_with_contribution_creates_token():
    g = "G-test-mintok-" + str(os.getpid())
    c = tempfile.mktemp(suffix=".json"); json.dump(_CONTRIB, open(c, "w"))
    r = _tool("gate.py", g, "--require-contribution", "--contribution", c, "--approver", "Jaslam", "--mint")
    assert r.returncode == 0 and "token minted" in r.stdout
    assert _tool("gate_lock.py", "require", g).returncode == 0   # the exact call cambium_run makes

# ---- the enforcement mechanism cambium_run --resume relies on -------------
def test_require_blocks_unminted_gate():
    assert _tool("gate_lock.py", "require", "G-test-never-" + str(os.getpid())).returncode == 1

# ---- cambium_run --resume integration ------------------------------------
def test_resume_bad_phase_errors():
    assert _tool("cambium_run.py", "x", "--resume", "nonsense").returncode == 1

def test_resume_missing_arg_errors():
    assert _tool("cambium_run.py", "x", "--resume").returncode == 1

def test_resume_proceeds_only_with_token():
    # mint the real G2 token (phase 'ideation'), then resume must proceed and skip completed phases
    c = tempfile.mktemp(suffix=".json"); json.dump(_CONTRIB, open(c, "w"))
    assert _tool("gate.py", "G2", "--require-contribution", "--contribution", c, "--approver", "Jaslam", "--mint").returncode == 0
    r = _tool("cambium_run.py", "wildlife corridor", "--resume", "ideation")
    assert r.returncode == 0 and "resuming after approved gate" in r.stdout
    assert "### PHASE: proposal" in r.stdout and "### PHASE: intake" not in r.stdout
