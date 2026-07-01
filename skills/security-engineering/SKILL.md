---
name: security-engineering
description: Build more secure software by applying the OWASP Top 10 (2025), least privilege, secrets management, input validation, output encoding, authentication and authorization patterns (OAuth 2.0, OIDC, JWT), and dependency and supply-chain scanning. Use when the user wants to review code for security issues, set up secrets management, choose an auth pattern, scan dependencies, or understand a vulnerability class. Trigger on "security", "OWASP", "vulnerability", "injection", "XSS", "CSRF", "auth", "OAuth", "JWT", "OIDC", "secrets", "Vault", "Semgrep", "dependency scan", "supply chain", "least privilege", "input validation", "secure code review". Pairs with devops-cicd (which runs scanners in CI) and cloud-deployment (which owns IAM and network controls). Honest: this is security guidance, NOT a security audit or a penetration test. Following it does not make software secure. A qualified human must review. Cambium never handles real secrets or credentials.
---

# Security engineering: reduce attack surface, do not pretend it is gone

Security is not a checklist. It is a continuous practice of reducing attack surface, validating
assumptions, and failing safely. This skill encodes durable defensive patterns drawn from public
standards. It is not a penetration test, not a formal audit, and not a guarantee.

State this plainly every time: following this guidance reduces common risks. It does not make software
secure. A qualified security engineer must review anything that handles sensitive data, money, or
access to other systems. Cambium never holds real secrets, credentials, or keys.

## OWASP Top 10 (2025): the highest-priority classes to defend against

The current list at owasp.org/Top10 (verify there, as rankings shift):

| Rank | Category | Primary defense |
|---|---|---|
| A01 | Broken Access Control | Enforce authorization server-side on every request; deny by default |
| A02 | Cryptographic Failures | TLS everywhere; no MD5/SHA-1 for sensitive data; use libsodium or language stdlib crypto |
| A03 | Injection (SQL, NoSQL, OS, LDAP) | Parameterized queries only; never concatenate user input into a query or command |
| A04 | Insecure Design | Threat-model before building; the bug is in the design, not the code |
| A05 | Security Misconfiguration | Least privilege; disable defaults; review every open port and permission |
| A06 | Vulnerable and Outdated Components | Automated dependency scanning in CI (see below) |
| A07 | Identification and Authentication Failures | Use a proven auth library; MFA; rate-limit and lock accounts |
| A08 | Software and Data Integrity Failures | Verify signatures on packages and pipeline artifacts; pin dependencies |
| A09 | Security Logging and Monitoring Failures | Log auth events, access denials, and errors; alert on anomalies |
| A10 | Server-Side Request Forgery (SSRF) | Validate and allowlist URLs; block internal IP ranges at the network layer |

## Injection: the most important defensive pattern

Never build a query or command by concatenating user input. Use parameterized statements (prepared
statements) in every database driver. The same principle applies to OS commands, LDAP queries, XML
parsers, and template engines.

```python
# Wrong: concatenation opens SQL injection
cursor.execute("SELECT * FROM users WHERE email = '" + email + "'")

# Right: parameterized query (PostgreSQL example)
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
```

Output encoding is the injection defense for HTML: encode before inserting user content into HTML,
attributes, JavaScript contexts, or URLs. Use a library (`bleach` for Python, DOMPurify for browser JS)
rather than writing your own escaping logic.

## Authentication vs authorization: they are different problems

**Authentication** answers "who are you?" Use a proven identity layer, not a home-built one. For user
logins: OpenID Connect (OIDC) on top of OAuth 2.0. For machine-to-machine: OAuth 2.0 client credentials
flow or mTLS. Good libraries: Auth0, Keycloak, AWS Cognito, Supabase Auth.

**Authorization** answers "are you allowed to do this?" Enforce it server-side on every request, never
trust client-supplied role information. Common patterns: RBAC (role-based) for most apps, ABAC
(attribute-based) for fine-grained data access. Deny by default; grant explicitly.

**JWT guidance**: JWTs are tokens, not sessions. Validate the signature on every request using a
library (`PyJWT`, `jsonwebtoken`, `go-jwt`). Set short expiry (15 minutes for access tokens,
days for refresh tokens). Never accept `alg: none`. Store tokens in memory or httpOnly cookies, not
localStorage (XSS reads localStorage).

## Secrets management: never in code, never in environment files committed to git

| Where secrets live | Risk level |
|---|---|
| Hardcoded in source | Critical: rotates never, leaks in git history forever |
| `.env` file committed to git | Critical: same as above |
| CI platform secrets store | Low: encrypted, audited, not in code |
| HashiCorp Vault | Low: dynamic secrets, fine-grained leases, audit log |
| AWS Secrets Manager / GCP Secret Manager | Low: managed, IAM-gated, auto-rotation available |

Use `git-secrets` or `trufflehog` as a pre-commit hook to block accidental commits of secrets.
If a secret is ever committed, treat the key as compromised and rotate it immediately, then scrub
git history (BFG Repo Cleaner or `git filter-repo`).

```bash
# Trufflehog: scan a repo for leaked secrets (run locally, review output before sharing)
trufflehog git https://github.com/your-org/your-repo --only-verified
```

## Dependency and supply-chain scanning

Every dependency is a trust decision. Pin exact versions in a lockfile. Scan for known vulnerabilities
in CI on every push:

- **Semgrep** (semgrep.dev): static analysis for security patterns; free OSS rules cover OWASP Top 10.
- **Trivy** (aquasecurity.github.io/trivy): scans container images, filesystems, and git repos.
- **Dependabot** (GitHub native) or **Renovate**: automated PRs to update vulnerable dependencies.
- **pip-audit** (Python), **npm audit** (Node), **cargo audit** (Rust): language-native vuln checks.

Verify the integrity of packages: use hash pinning in requirements files (`pip install --require-hashes`)
and check Sigstore signatures for packages that publish them (sigstore.dev).

## Input validation: validate early, encode on output

Validate all input at the boundary where it enters your system: type, length, format, and range. Reject
what does not conform. Do not rely on client-side validation alone; the client is user-controlled.
Encode on output in the context where the data will be used (HTML encoding for HTML, URL encoding for
URLs). These are two separate operations; doing one does not substitute for the other.

## Honest guardrails

- This skill is security guidance, not a security audit, and not a penetration test. It does not make
  software secure. A qualified, independent security engineer must review systems that handle PII,
  financial data, health data, or access to other systems.
- Cambium never handles real secrets, credentials, API keys, or private keys. Do not paste them into a
  conversation.
- Security requirements are jurisdiction-dependent. SOC 2, HIPAA, PCI-DSS, and GDPR impose specific
  technical controls beyond OWASP. Name the compliance context and engage a specialist.
- Cryptographic primitives age out. Check the current NIST recommendations before choosing an algorithm,
  especially for post-quantum migration (NIST FIPS 203, 204, 205 finalized in 2024).
- Fast-moving areas: supply-chain attacks (new vectors appear monthly), AI-generated code introducing
  novel injection surfaces, and browser security policies (CSP, COEP, COOP headers evolve).

## Attribution and sources

Guidance encoded from public standards and documentation, nothing invented here. OWASP Top 10
(owasp.org/Top10), OWASP Cheat Sheet Series (cheatsheetseries.owasp.org), OAuth 2.0 RFC 6749
(rfc-editor.org/rfc/rfc6749), OIDC spec (openid.net/connect), JWT RFC 7519
(rfc-editor.org/rfc/rfc7519), HashiCorp Vault (developer.hashicorp.com/vault), Semgrep
(semgrep.dev), Trivy (aquasecurity.github.io/trivy), TruffleHog (github.com/trufflesecurity/trufflehog),
DOMPurify (github.com/cure53/DOMPurify), Sigstore (sigstore.dev), NIST post-quantum standards
(csrc.nist.gov/projects/post-quantum-cryptography), git-secrets
(github.com/awslabs/git-secrets), BFG Repo Cleaner (rtyley.github.io/bfg-repo-cleaner).
