# ADR-0001: Multi-tenancy, a database layer, and horizontal scale

- **Status:** proposed (specced, not built) - 2026-07-02
- **Context:** Evaluations 02, 03, and 07 flag that Cambium keeps all run state in flat files
  (`run_state.json` as the single source of truth, CSV and JSONL ledgers) and reads the network with
  blocking `urllib`. That is correct and auditable for one researcher on one machine, which is the design
  center. It does not support several institutions running concurrently against one shared instance with
  isolation between them, nor high request throughput. The eval itself says to scope this only when a real
  consortium need exists; today there is none, so building an untestable database and isolation layer now
  would add large surface area with no user.
- **Decision:** Do not build a database or multi-tenancy layer yet. Keep the flat-file single source of
  truth as the supported model. Record here the shape the change would take so it is ready to build when a
  consortium need is real, and so no one silently half-builds it in the meantime.
- **Design sketch (when built):**
  - Introduce a storage interface behind the current `run_state` and ledger reads and writes, with two
    implementations: the existing flat-file backend (default, unchanged for the solo user) and a database
    backend (PostgreSQL) selected by an environment variable.
  - Tenancy: a tenant id on every run and ledger row; every query scoped by tenant; no cross-tenant reads.
    Row-level isolation enforced in the storage layer, not in prompts.
  - Concurrency: connection pooling and per-run advisory locks so two workers cannot corrupt a run.
  - Migration: a one-way exporter from the flat-file store into the database so existing runs carry over;
    the audit hash chain (`audit_log.py`) must be preserved across the move and re-verified after.
  - Keep the markdown gate ledger readable by an auditor even with a database behind it: mirror gate rows
    to `governance/GATES.md` on write, so the human-readable audit trail never depends on database access.
- **Alternatives considered:**
  - SQLite instead of PostgreSQL: simpler, but does not give real multi-writer concurrency for several
    institutions; rejected for the consortium case, acceptable as a middle step for a single busy lab.
  - Keep flat files and add file locking only: cheapest, but does not give tenant isolation; this is the
    status quo and stays the supported model until a consortium need appears.
- **Consequences:** Until built, Cambium remains single-tenant and single-machine, which is honest and is
  what the README says. When built, it gains isolation and scale at the cost of an operational database and
  the migration and audit-continuity work above. The storage interface should be introduced first, on its
  own, so the two backends can be swapped without touching tool logic.
- **Evidence pointer:** current model is `tools/run_state.py`, the ledgers under `governance/`, and the
  audit chain in `tools/audit_log.py`. This ADR is the record that the gap is known and deliberately deferred.
