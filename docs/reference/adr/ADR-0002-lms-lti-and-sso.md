# ADR-0002: LMS/LTI integration and single sign-on

- **Status:** proposed (specced, not built) - 2026-07-02
- **Context:** Evaluations 03, 04, and 11 note there is no LMS/LTI 1.3 integration and no SSO
  (SAML or OAuth/OIDC). The Cambium Academy is self-contained HTML today. Building and, crucially,
  TESTING an LTI or SSO integration requires a real identity provider and a real learning management
  system to register with; those are external accounts and infrastructure this project does not have, so
  a build now could not be verified end to end.
- **Decision:** Do not build LTI or SSO yet. Record the intended shape so it is ready when an institution
  that wants to embed the Academy or gate access provides the identity provider to build and test against.
- **Design sketch (when built):**
  - SSO: add OIDC (OpenID Connect) as the first identity mechanism, since it is the simplest to test with
    common providers (university Google or Microsoft tenants). Map the verified identity to the existing
    `CAMBIUM_USER` stamp and the multi-PI approver roles (`MULTI_PI_ROLES.yml`) so gate approvals carry a
    verified identity rather than free text. SAML is a later option for institutions that require it.
  - LTI 1.3: expose the Academy as an LTI tool so a course can launch it; carry the LTI context (course,
    role) into a learner transcript (`tools/transcript.py`). Grade passback is out of scope for the first
    version; the Academy is formative, not graded.
  - Keep local-first working: SSO and LTI are optional layers; the plugin must still run with no identity
    provider for the solo researcher.
- **Alternatives considered:**
  - Plain OAuth without OIDC: gives a token but not a verified identity claim; rejected, OIDC is the right
    primitive for who-approved-this.
  - Building against a mock IdP only: would let code exist but not prove a real integration; the honest
    position is to wait for a real provider so the integration is verified, not asserted.
- **Consequences:** Until built, identity stays a signed approver token plus a `CAMBIUM_USER` stamp, which
  is honest and documented. When built, gate approvals and Academy access gain verified identity, at the
  cost of depending on an external identity provider and the accounts to test it.
- **Evidence pointer:** current identity handling is the approver token in `tools/gate_lock.py`,
  `MULTI_PI_ROLES.yml`, and `tools/roles_check.py`. This ADR records the deferral.
