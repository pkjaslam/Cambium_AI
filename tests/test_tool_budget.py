"""tool budget: the toolkit is frozen at a deliberate size (tools/tool_budget.json).

doctor.py check [9] enforces it: growing tools/*.py past the budget fails until the
budget is bumped in the same commit (naming, in the CHANGELOG entry, the number the
new tool moves). doctor.py runs its checks at import time, so these tests compile
just the tool_budget_status function out of its AST instead of importing the module.
"""
import ast, glob, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCTOR = os.path.join(ROOT, "tools", "doctor.py")


def _load_tool_budget_status():
    tree = ast.parse(open(DOCTOR, encoding="utf-8").read())
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "tool_budget_status")
    ns = {"os": os, "glob": glob, "json": json, "ROOT": ROOT}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), DOCTOR, "exec"), ns)
    return ns["tool_budget_status"]


tool_budget_status = _load_tool_budget_status()


def _fake_root(tmp_path, n_tools, budget=None, budget_raw=None):
    """Build a synthetic repo root: tools/ with n_tools .py files and an optional budget file."""
    (tmp_path / "tools").mkdir(parents=True)
    for i in range(n_tools):
        (tmp_path / "tools" / ("tool_%d.py" % i)).write_text("print('hi')\n", encoding="utf-8")
    if budget_raw is not None:
        (tmp_path / "tools" / "tool_budget.json").write_text(budget_raw, encoding="utf-8")
    elif budget is not None:
        (tmp_path / "tools" / "tool_budget.json").write_text(
            json.dumps({"budget": budget, "rationale": "test", "set": "2026-07-01"}), encoding="utf-8")
    return str(tmp_path)


def test_current_repo_within_budget():
    ok, msg = tool_budget_status(ROOT)
    assert ok, msg
    n = len(glob.glob(os.path.join(ROOT, "tools", "*.py")))
    assert msg.startswith("%d/" % n) and "within budget" in msg


def test_budget_file_is_well_formed_and_pins_the_count():
    d = json.load(open(os.path.join(ROOT, "tools", "tool_budget.json"), encoding="utf-8"))
    assert isinstance(d["budget"], int) and d["budget"] > 0
    assert "CHANGELOG" in d["rationale"]          # the bump rule names where the number lives
    assert set(d) >= {"budget", "rationale", "set"}
    assert len(glob.glob(os.path.join(ROOT, "tools", "*.py"))) <= d["budget"]


def test_over_budget_fails_with_bump_message(tmp_path):
    root = _fake_root(tmp_path, n_tools=3, budget=2)
    ok, msg = tool_budget_status(root)
    assert not ok
    assert "3 tools > budget 2" in msg
    assert "remove tools" in msg and "bump" in msg


def test_at_and_under_budget_pass(tmp_path):
    at = _fake_root(tmp_path / "at", n_tools=3, budget=3)
    ok, msg = tool_budget_status(at)
    assert ok and "3/3" in msg
    under = _fake_root(tmp_path / "under", n_tools=2, budget=3)
    ok, msg = tool_budget_status(under)
    assert ok and "2/3" in msg


def test_malformed_budget_file_fails(tmp_path):
    bad_json = _fake_root(tmp_path / "a", n_tools=1, budget_raw="{not json at all")
    ok, msg = tool_budget_status(bad_json)
    assert not ok and "malformed" in msg
    bad_value = _fake_root(tmp_path / "b", n_tools=1, budget_raw='{"budget": "plenty"}')
    ok, msg = tool_budget_status(bad_value)
    assert not ok and "malformed" in msg


def test_missing_budget_file_fails(tmp_path):
    root = _fake_root(tmp_path, n_tools=1)
    ok, msg = tool_budget_status(root)
    assert not ok and "missing" in msg
