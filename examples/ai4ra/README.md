# AI4RA-aligned tools: ten-second quickstart

Every command below runs with no extra setup (stdlib fallbacks). The optional
libraries in `requirements-ai4ra.txt` make some of them stronger, and each tool
tells you which path it used.

All sample data here is fake and labeled ILLUSTRATIVE.

## Screen a document for PII (Security pillar)

```
python3 tools/pii_screen.py --in examples/ai4ra/sample_award_notice.txt
```

Flags the email, phone, SSN, IP, and Luhn-valid card in the sample. Raw values are
never printed. Add `--redact --out cleaned.txt` to write a cleaned copy.

## Validate a Vandalizer rules handoff, then review a budget (Flexibility, compliance)

```
python3 tools/rules_handoff.py --rules examples/ai4ra/solicitation_rules.example.json
python3 tools/budget_review.py \
    --rules examples/ai4ra/solicitation_rules.example.json \
    --budget examples/ai4ra/budget.example.json
```

The first checks the handoff matches the agreed schema; the second flags budget
issues against those rules. Both are advisory: a human makes the final call.

## Emit a TaMPER record and Four-Pillars self-check (Reporting)

```
python3 tools/tamper_record.py --title "My deliverable" --format md
```

Writes a Task, Model, Prompt, Evaluation, Reporting record plus a Security,
Accuracy, Reproducibility, Flexibility self-check. Use `--format json` or `prov`.

## Catalog a run's outputs as FAIR data (Objective 1)

```
python3 tools/fair_descriptor.py
```

Writes a `datapackage.json` so the run's outputs are Findable, Accessible,
Interoperable, and Reusable.

See `docs/ai4ra_alignment.md` for how each tool maps to AI4RA's objectives,
the Four Pillars, and the TaMPER workflow.
