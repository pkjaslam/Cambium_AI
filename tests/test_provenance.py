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
