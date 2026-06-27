# 04 · Post-Award Run-Lab (stages 4–6, gate G4) — *demonstrated, not just described*

This is the part most "AI scientist" demos skip: after the award, does the work actually **run, get
audited, and reproduce**? Here it does — every claim below is backed by a file you can execute yourself.

## Stage 4 — Provision & build
The Execution council provisions the method and writes the analysis as **deterministic, seeded-free,
stdlib-only** code so it reproduces bit-for-bit:

```
examples/e2e-worked-example/code/analysis.py   # 12-plot paired field trial, fixed data, no RNG
```

## Stage 5 — Run & verify (the audit *executes* the code)
`verify-evidence` does not read-and-opine; it **runs the script and reproduces the headline number**:

```
$ python3 code/analysis.py
n=12 mean_gain=3.058 sd=0.406 t=26.12 ci95=[2.829,3.288]
HEADLINE: treatment increased yield by 3.06 bu/acre (95% CI 2.83-3.29, t=26.1, n=12)
```

That headline becomes finding **F1**, tier **`Code-verified`**, in `findings_ledger.csv` — and the
evidence cell carries the run command (`python3 code/analysis.py`), so `governance/validate.py`
accepts it as Code-verified rather than Asserted. F2 (rainfall interaction) is honestly logged
**`Open`** — not every aim resolves, and the ledger says so.

### Machine-checkable provenance (not a string match)
`tools/provenance.py` re-runs F1's command, hashes **command + script + output**, and writes
`provenance_manifest.json`. Anyone can re-verify reproduction:

```
$ python3 tools/provenance.py check examples/e2e-worked-example/provenance_manifest.json \
      --cwd examples/e2e-worked-example
[provenance] OK: all claims reproduce.
```

If the code or its output ever drifts, the hash changes and `check` exits non-zero — `Code-verified`
means *a script actually ran and still produces this number*, by construction.

## Stage 6 — Gate G4: accept results?
The **gate interlock** refuses to open G4 while the ledger has a release-blocking finding:

```
$ python3 tools/gate.py G4 --ledger examples/e2e-worked-example/findings_ledger.csv
[validate] OK: no blockers.
  ⛩ GATE G4 — clear of blockers; open for the Director's APPROVE / REVISE / REJECT.
```

> **G4 DECISION CARD** (verbatim, as the Director sees it)
> - **Verified:** F1 — treatment +3.06 bu/acre (95% CI 2.83–3.29), reproduced + hashed.
> - **Open:** F2 — rainfall interaction model not yet fit; carried forward, not hidden.
> - **Asserted:** F3 — design is a valid paired comparison (argued, not run).
> - **Independent check:** `tools/finding_audit.py` found no completion claim lacking evidence.
> - **Decision required:** `APPROVE` → proceed to reporting · `REVISE` → fit F2 first · `REJECT`.

Nothing past this point is finalized without the human `APPROVE`. That is the whole point: the
machine does the labor and the audit; the **person** owns the call.

---

*Reproduce this entire stage yourself:* from the repo root,
`python3 code/analysis.py` (in `examples/e2e-worked-example/`), then the `provenance.py check`,
`validate.py`, and `gate.py` commands above. Cambium's CI runs the last three on every push.
