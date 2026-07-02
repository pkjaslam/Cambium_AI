# Security & Responsible Use
- **Never paste secrets, credentials, embargoed, or restricted data** into agents (see AI_GOVERNANCE.md §7-8).
- Agents are **read-only on deliverables** and **cannot send/submit/publish** — humans do that.
- The `examples/demo-mid-project` ledger intentionally contains a leakage bug for the verify board to catch; it is fictional.
- Report a vulnerability or a governance concern by opening a private issue / emailing the maintainer at pkjaslamagrico@gmail.com. Please do not open a public issue for a security vulnerability; use email so it can be triaged privately first.
- Run `python3 governance/validate.py` before any release; an open P0 is a blocker.
