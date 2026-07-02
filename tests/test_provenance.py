"""Test the provenance manifest: build runs+hashes Code-verified claims; check fails on drift."""
import json, os, subprocess, sys, tempfile, textwrap
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL=os.path.join(ROOT,"tools","provenance.py")
def _run(*a,cwd=None): return subprocess.run([sys.executable,TOOL,*a],cwd=cwd,capture_output=True,text=True)
def _setup(d,headline="42"):
    os.makedirs(os.path.join(d,"code"),exist_ok=True)
    open(os.path.join(d,"code","a.py"),"w").write(f"print('HEADLINE {headline}')\n")
    open(os.path.join(d,"ledger.csv"),"w").write(
        "id,claim_tier,evidence,action\nF1,Code-verified,x,cmd: python3 code/a.py\nF2,Asserted,y,n/a\n")
def test_build_then_check_passes():
    d=tempfile.mkdtemp(); _setup(d)
    r=_run("build",os.path.join(d,"ledger.csv"),"--cwd",d); assert r.returncode==0, r.stderr
    m=json.load(open(os.path.join(d,"provenance_manifest.json")))
    assert len(m["entries"])==1 and m["entries"][0]["claim_id"]=="F1"   # only Code-verified
    assert m["entries"][0]["output_sha256"]
    c=_run("check",os.path.join(d,"provenance_manifest.json"),"--cwd",d)
    assert c.returncode==0 and "all claims reproduce" in c.stdout
def test_check_fails_on_output_drift():
    d=tempfile.mkdtemp(); _setup(d,"42")
    _run("build",os.path.join(d,"ledger.csv"),"--cwd",d)
    open(os.path.join(d,"code","a.py"),"w").write("print('HEADLINE 999')\n")   # tamper
    c=_run("check",os.path.join(d,"provenance_manifest.json"),"--cwd",d)
    assert c.returncode==1 and ("DRIFTED" in c.stdout or "FAILED" in c.stdout)

def test_normal_command_reproduces_after_shell_false():
    """A plain argv command (python3 code/a.py) still builds and re-checks OK with shell=False."""
    d = tempfile.mkdtemp(); _setup(d, "7")
    b = _run("build", os.path.join(d, "ledger.csv"), "--cwd", d)
    assert b.returncode == 0, b.stderr
    m = json.load(open(os.path.join(d, "provenance_manifest.json")))
    assert m["entries"][0]["rerun_cmd"] == "python3 code/a.py"
    assert m["entries"][0]["exit_code"] == 0
    c = _run("check", os.path.join(d, "provenance_manifest.json"), "--cwd", d)
    assert c.returncode == 0 and "all claims reproduce" in c.stdout


def test_shell_metacharacters_do_not_spawn_a_second_process():
    """Security fix: `;` must NOT chain a second command through a shell.

    Under shell=True the string `python3 code/a.py ; touch PWNED` would execute BOTH the
    python AND the `touch`, creating the sentinel PWNED. Under shell=False the tail is passed
    to python3 as literal argv tokens (`;`, `touch`, `PWNED`); no shell parses them, so the
    second command never runs. The decisive, tool-level assertion is that the sentinel file
    is NEVER created no matter what the first program's exit code happens to be.
    """
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "code"), exist_ok=True)
    open(os.path.join(d, "code", "a.py"), "w").write("print('HEADLINE 1')\n")
    open(os.path.join(d, "ledger.csv"), "w").write(
        "id,claim_tier,evidence,action\n"
        "F1,Code-verified,x,cmd: python3 code/a.py ; touch PWNED\n")
    b = _run("build", os.path.join(d, "ledger.csv"), "--cwd", d)
    assert b.returncode in (0, 1), b.stdout + b.stderr  # build ran; exit code is not the point
    # The decisive assertion: the chained `touch` NEVER executed.
    assert not os.path.exists(os.path.join(d, "PWNED")), "shell metacharacter spawned a second process"


def test_ampersand_chain_does_not_spawn_a_second_process():
    """`&&` must also be inert: it is passed through as a literal argv token, not a shell op."""
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "code"), exist_ok=True)
    open(os.path.join(d, "code", "a.py"), "w").write("print('HEADLINE 1')\n")
    open(os.path.join(d, "ledger.csv"), "w").write(
        "id,claim_tier,evidence,action\n"
        "F1,Code-verified,x,cmd: python3 code/a.py && touch PWNED2\n")
    b = _run("build", os.path.join(d, "ledger.csv"), "--cwd", d)
    assert b.returncode in (0, 1), b.stdout + b.stderr
    assert not os.path.exists(os.path.join(d, "PWNED2")), "&& spawned a second process"


def test_leading_metacharacter_token_fails_to_find_a_program():
    """A command whose FIRST token is a shell metacharacter must fail to find that program.

    shlex.split turns `; touch PWNED3` into ['; ', 'touch', 'PWNED3'] (first token ';'), which
    is not an executable. With shell=False this fails closed (no program named ';'), so the
    claim does not reproduce -> the build exits 1 and, again, no sentinel file is created. This
    is the "fails to find a program named with those tokens rather than executing them" case.
    """
    d = tempfile.mkdtemp()
    open(os.path.join(d, "ledger.csv"), "w").write(
        "id,claim_tier,evidence,action\n"
        "F1,Code-verified,x,cmd: ; touch PWNED3\n")
    b = _run("build", os.path.join(d, "ledger.csv"), "--cwd", d)
    assert b.returncode == 1, b.stdout + b.stderr  # nothing reproduced (no such program ';')
    assert not os.path.exists(os.path.join(d, "PWNED3")), "leading metacharacter spawned a process"
    m = json.load(open(os.path.join(d, "provenance_manifest.json")))
    assert m["entries"][0]["exit_code"] != 0
