# Code Quality CI

This repo ships two complementary CI workflows:

- `.github/workflows/validate.yml` enforces the **honesty / governance contract**
  (agent frontmatter, ledger gates, version consistency, provenance). Unchanged
  except for a note here; do not remove its steps.
- `.github/workflows/quality.yml` (this document) adds **code-quality** checks:
  a cross-platform test matrix, linting, typing, security, and coverage.

The guiding rule: **be honest about what gates and what only informs.** A check is
GATING only when the current tree passes it cleanly *without editing source*. Everything
else is ADVISORY (`continue-on-error`) so it reports a signal without blocking a merge on
pre-existing conditions. No check below rewrites code under `tools/`, `web/`, or `tests/`.

## Gating vs advisory (at a glance)

| Check | Mode | Scope | Observed result on v1.40.0 |
|---|---|---|---|
| Test matrix (pytest) | **GATING** | ubuntu-latest + windows-latest, Python 3.11 & 3.12 | 1224 passed (Linux baseline) |
| Ruff (lint) | **GATING** | whole repo, config in `pyproject.toml` | 0 issues with the selected ruleset |
| Black `--check` | advisory | whole repo (frontend excluded) | 264 files would reformat |
| Mypy | advisory | `tools/` only | 20 errors + 3 notes in 12 files (115 files checked) |
| Bandit | advisory | `tools/` + `web/` | 63 low, 8 medium, 0 high (22,653 LOC) |
| pip-audit | advisory | `requirements.txt` | no known vulnerabilities |
| Coverage | advisory | `tools/`, `governance/`, `mcp_server/`, `web/server/` | 54.7 percent line (floor 40, non-blocking) |

## Why the test matrix is the high-value gate

The single most valuable addition here is running the **existing** suite on
**windows-latest** as well as **ubuntu-latest**. Cross-platform defects, for example a
Windows cross-drive `os.path.relpath` crash that raises `ValueError` because two paths sit
on different drive letters, are invisible on a Linux-only runner. They surface only when a
Windows contributor pushes. Running the suite on both operating systems moves that class of
bug into CI, where it blocks the merge, instead of onto a user's machine. Both Python 3.11
and 3.12 are exercised so version-specific behavior is covered too. This job is GATING: the
suite must pass on every cell of the matrix.

If a test is genuinely OS-specific in a way the code cannot control, mark it with
`@pytest.mark.skipif(sys.platform == "win32", reason="...")` (or the inverse) and note it
here. As of v1.40.0 the suite passes on the Linux baseline with no skips required; the
Windows cells are expected to pass identically.

## Why Ruff is gating (and how it stays green without code edits)

Ruff is GATING because the current tree passes `ruff check .` with **exit 0** and **zero
edits to source**. The configuration in `pyproject.toml` (`[tool.ruff]`) makes this honest
rather than hollow:

- **Selected**: `E`, `W`, `F`, `I`. This keeps the genuinely dangerous lints fully active:
  undefined names (`F821`), redefinitions (`F811`), identity/tuple bugs (`F632`, `F631`),
  malformed format strings, and the rest of pyflakes. Every one of those high-value codes
  is already **zero** across all 267 Python files, so gating on them costs nothing today and
  catches a real bug the moment one is introduced (verified: a probe file with `F821`/`F632`
  fails the check).
- **Ignored** (pure style, not defects): `E501` line length, `E701`/`E702`/`E703` compound
  statements, `E401`/`E402` import placement, `E722` bare except, `E731`, `E741`, and the
  `W29x` whitespace codes. These are formatting choices; the codebase is intentionally not
  auto-formatted, and gating on them would demand a mass reformat we explicitly are not doing.
- **Per-file-ignores**: the only remaining pyflakes findings are cosmetic (unused import
  `F401`, empty f-string `F541`, unused local `F841`) and live entirely in tests, tools,
  generators, and eval scripts. They are waived *where they occur* rather than by editing
  files, so the same checks stay gating for any new core module.

Import **order** is reported by the isort ruleset but auto-sorting is disabled and the noisy
`I001` is ignored; ruff never rewrites files in CI (`ruff check`, not `ruff check --fix`).

## Why the rest is advisory

- **Black** is `--check --diff` only. The repo is not black-formatted on purpose (264 files
  would change). We surface the diff as a courtesy; applying it would be a huge, unrelated,
  cross-cutting change and is out of scope.
- **Mypy** runs non-strict over `tools/` with `ignore_missing_imports` and
  `follow_imports = silent`. It reports 20 errors plus a few notes; these are untyped-body
  notes and a couple of attribute/assignment findings, not runtime failures, so it does not
  gate. One file, `tools/deterministic_checks.py`, contains a documentation line beginning
  `# type:` that mypy misreads as a PEP 484 type comment and rejects; CPython 3.10, ruff, and
  pytest all accept the file, so it is excluded from mypy (with a `follow_imports = skip`
  override so importers do not re-trip it). This is a mypy-parser quirk, documented rather
  than "fixed" by editing the file.
- **Bandit** scans `tools/` and `web/` and finds 63 low plus 8 medium issues, no highs. The
  lows are overwhelmingly `subprocess` usage (`B404`/`B603`/`B607`) in the framework's own CLI
  tools and a handful of `try/except/pass` guards; the mediums are `urllib` `urlopen` calls
  (`B310`). These are reviewed and expected for a tool that shells out to its own scripts and
  fetches from known endpoints; they are advisory, not a merge blocker.
- **pip-audit** audits the declared dependencies in `requirements.txt` and currently reports
  no known vulnerabilities. It stays advisory so a newly disclosed upstream CVE informs the
  team without abruptly turning every build red before anyone can react.
- **Coverage** runs the suite under `coverage.py` and prints the report with a low
  `--cov-fail-under=40` floor. Coverage is a trend signal here, not a gate; we do not block a
  merge on a coverage number.

  One test, `tests/test_redteam_intakes.py::test_policy_diff_payloads_and_oversized`,
  asserts a 10-second wall-clock budget. It passes in the normal (gating) suite but can
  fail *only under coverage*, because coverage tracing slows the subprocess it spawns past
  10 seconds. The process return code is still correct; only the timing assertion trips.
  This is a measurement artifact, not a code defect, and it is one more reason the coverage
  job is advisory (`continue-on-error`) while the gating test-matrix job runs without
  coverage and stays green. The number above is line coverage; the CI config enables branch
  coverage, which reports a slightly lower figure over the same non-blocking floor.

## Local developer setup

Install the same tools CI uses, then enable the pre-commit hooks:

```bash
pip install -r requirements-dev.txt -c constraints.txt
pre-commit install            # run the hooks on every commit
pre-commit run --all-files    # run them once over the whole tree
```

`.pre-commit-config.yaml` mirrors the CI checks: ruff in **check-only** mode (no autofix, so
it never rewrites your tracked source), black `--check`, trailing-whitespace and
end-of-file fixers on the files you stage, a YAML check, a large-file guard, and a local
`no-em-dash` guard (house rule: no em dashes in authored text). Bypass in an emergency with
`git commit --no-verify`. The hooks are for local use and are **not** required by CI.

## Refreshing the numbers

```bash
ruff check .                                              # gating: expect exit 0
python3 -m pytest tests/ -q                               # gating: expect all green
mypy tools/                                               # advisory
bandit -r tools/ web/ -x web/frontend-r3f,web/frontend   # advisory
pip-audit -r requirements.txt                            # advisory
python3 -m coverage run --source=tools,governance,mcp_server,web/server -m pytest tests/ -q && python3 -m coverage report
```
