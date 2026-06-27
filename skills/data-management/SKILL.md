---
name: data-management
description: Steward datasets responsibly — inventory and document data, define schema/units/types, track provenance, run data-quality and integrity checks, and screen for PII/privacy and licensing issues. Use when receiving a new dataset, writing a data dictionary or data-management plan, checking data quality (nulls, duplicates, outliers, leakage of sensitive fields), documenting provenance, or assessing privacy/PII and usage rights. Trigger on "data dictionary", "schema", "data quality", "provenance", "PII", "privacy", "data management plan", "is this data usable". Pairs with the data-steward agent.
---

# Data management — know your data before you trust it

Bad conclusions usually trace back to undocumented, dirty, or improperly used data. This skill makes the
dataset legible, clean, and safe to use.

## Inventory & data dictionary
For every dataset record: source, owner, date obtained, license/usage rights, and a per-column
dictionary — name, type, units, allowed range/categories, null policy, and meaning. No analysis until
the columns are understood.

## Quality checks (run, don't assume)
```python
import pandas as pd
df = pd.read_csv("data.csv")
df.info(); df.describe(include="all")
df.isna().mean().sort_values(ascending=False)        # null rates
df.duplicated().sum()                                 # exact dupes
# range/category sanity, impossible values, mixed types, date parseability,
# outliers (IQR / z-score), unexpected cardinality, inconsistent units
```
Report: row/col counts, null rates, duplicates, suspicious values, and whether the data actually
supports the intended claims (representativeness, sample size, selection bias).

## Provenance
Keep a traceable chain raw → cleaned → derived: where each came from, every transform (as code, not
manual edits), and a checksum on raw files. Never overwrite raw data.

## Privacy / PII / rights (screen early)
- Flag direct identifiers (name, email, SSN, MRN, exact address, phone) and quasi-identifiers that can
  re-identify in combination (DOB + ZIP + sex).
- Note governance regimes that apply (FERPA for education records, HIPAA-style for health, IRB/consent
  scope, Indigenous data sovereignty). **Recommend** de-identification/aggregation; the human decides.
- Check the license permits the intended use; record it.
- Do not paste sensitive values into prompts, filenames, URLs, or logs.

## Data-management plan (for proposals)
Types & volume · standards/formats · storage & backup · access & sharing · retention · privacy &
ethics · roles. Keep it specific to the project.

## Guardrails
- "The data is fine" is a claim — back it with the quality table.
- Weak/unrepresentative data caps every downstream conclusion; say so explicitly.
- Tag dataset readiness **Code-verified** (checks run) vs **Asserted**.
