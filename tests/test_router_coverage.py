"""Guard: routing coverage must never silently regress.

Fails CI if (a) any council drops to zero routed agents across all task types, or
(b) the Support close-out (record-keeper, integrity-officer, janitor) is missing from
any single task type. Locks in ADR-016.
"""
import importlib.util
import os

HERE = os.path.dirname(__file__)
SPEC = importlib.util.spec_from_file_location(
    "task_router", os.path.join(HERE, "..", "tools", "task_router.py")
)
tr = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tr)

TYPES = [n for n, _, _ in tr.TYPES]
COUNCIL_OF = {a: c for c, v in tr.CMAP.items() for a in v}


def _agents(phases):
    return {a for p in phases for g in p["groups"] for a in g["agents"]}


def test_every_council_routed_by_some_task_type():
    """No council may be unreachable from every playbook."""
    routed_councils = set()
    for typ in TYPES:
        for a in _agents(tr.plan_for_type(typ)):
            if a in COUNCIL_OF:
                routed_councils.add(COUNCIL_OF[a])
    missing = set(tr.CMAP) - routed_councils
    assert not missing, f"councils never routed by any task type: {sorted(missing)}"


def test_support_closeout_on_every_task_type():
    """Housekeeping must run on every task, not just some."""
    need = {"record-keeper", "integrity-officer", "janitor"}
    for typ in TYPES:
        agents = _agents(tr.plan_for_type(typ))
        assert need <= agents, f"{typ}: missing Support close-out {sorted(need - agents)}"


def test_document_office_writes_research_report_data():
    """The final-deliverable writer is routed where a written deliverable is produced."""
    for typ in ("research", "report", "data"):
        assert "document-office" in _agents(tr.plan_for_type(typ)), f"{typ}: no document-office"
