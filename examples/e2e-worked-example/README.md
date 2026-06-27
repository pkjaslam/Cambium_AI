# End-to-end worked example — a full artifact chain

A complete, runnable Cambium run from a funding call to a verified, provenance-linked result. It
demonstrates the lifecycle, the gates, the evidence contract, and the **machine-checkable provenance
manifest** (`tools/provenance.py`).

## The chain (RFP → verified result)
| Stage | Gate | Artifact |
|---|---|---|
| RFP intake | **G1** pursue? | [`00_rfp_brief.md`](00_rfp_brief.md) |
| Ideation / aims | **G2** which idea? | [`01_aims.md`](01_aims.md) |
| Proposal | **G3** submit? | [`02_proposal_excerpt.md`](02_proposal_excerpt.md) |
| Development + verification | — | [`code/analysis.py`](code/analysis.py) (deterministic) |
| Findings ledger | — | [`findings_ledger.csv`](findings_ledger.csv) (one **Code-verified**, one **Asserted**, one **Open**) |
| Provenance | — | [`provenance_manifest.json`](provenance_manifest.json) — links claim `F1` → rerun cmd + script hash + output hash |
| Post-award run-lab | **G4** accept results? | [`04_postaward_runlab.md`](04_postaward_runlab.md) — *demonstrated* execution → audit → reproduce → gate |
| Report | **G5** release? | [`03_report.md`](03_report.md) |

## Reproduce it yourself
```bash
# re-run the headline computation
python3 examples/e2e-worked-example/code/analysis.py
# re-verify EVERY Code-verified claim against its recorded hash (FAILS if any output drifts)
python3 tools/provenance.py check examples/e2e-worked-example/provenance_manifest.json
# (re)build the manifest from the ledger
python3 tools/provenance.py build examples/e2e-worked-example/findings_ledger.csv --cwd examples/e2e-worked-example
```
The headline number (**3.06 bu/acre**) in the report is not asserted — it is reproduced and hashed.
