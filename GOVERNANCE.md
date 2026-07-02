# Governance and maintainership

Cambium is currently maintained by one person (M. Jaslam, University of Idaho, Intermountain Forestry
Cooperative). That single-maintainer bus-factor is the honest top risk to the project's continuity, and
this document exists to reduce it: it states how the project is run, how decisions are made, and how a
second maintainer joins.

## How decisions are made
Substantive changes run the Cambium way: they are proposed, built behind the test suite and the doctor
health check, and approved at a human gate recorded in `governance/GATES.md`. Nothing ships on a red
build (the pre-push guard blocks it). The evidence contract and the AI-use policy in
`docs/governance/` bind maintainers as much as contributors.

## Roles
- Maintainer: merges changes, cuts releases, holds the release checklist, answers security reports.
- Contributor: opens issues and pull requests per `CONTRIBUTING.md`; every new feature names the eval
  or check it moves (see `docs/reference/CODE_QUALITY.md`).
- Reviewer: any trusted contributor who reviews pull requests; a second reviewer is required for changes
  to governance, the evidence contract, or a release.

## Becoming a co-maintainer
The project actively wants a second maintainer. The path: land a few substantive, reviewed pull requests;
show you apply the honesty rules (no overclaiming, tests and doctor stay green); then ask. A co-maintainer
gets commit and release rights and shares the security inbox. Two maintainers is the near-term goal so no
single person is a point of failure.

## Releases
Releases are version-stamped from `CHANGELOG.md` by `tools/sync_version.py`, verified by the full gauntlet
(pytest, doctor, consistency, enforcement, provenance), and recorded at a gate. See `PUBLISHING.md` for
the PyPI path once trusted publishing is configured.

## Security
Report vulnerabilities privately by email (see `SECURITY.md`), not in a public issue.

## License
MIT. Contributions are accepted under the same license.
