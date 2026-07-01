---
name: backend-api-design
description: Design, build, and review servers and APIs that are correct, consistent, and operable: REST semantics, GraphQL trade-offs, the twelve-factor app, framework choices by language, error contracts, versioning, and security basics. Use when the user wants to build a backend service, design or review an API, choose a web framework, structure routes, handle auth, or set up a CI pipeline for a server. Trigger on "REST API", "GraphQL", "endpoint", "FastAPI", "Express", "NestJS", "Django", "HTTP verbs", "status codes", "idempotency", "pagination", "versioning", "twelve-factor", "backend", "server", "API design", "OpenAPI", "rate limiting", "middleware". Pairs with databases-and-data-modeling (for the data layer) and ai-application-engineering (when the API serves an AI feature). Honest: advises and generates code the human reviews and runs; the human is responsible for deployment, security hardening, and secrets management.
---

# Backend API design: boring, correct, and operable

A backend that is correct, consistent, and easy to operate is worth more than one that is clever. REST is
not fashionable, it is durable. Follow the semantics of HTTP, design for the client you actually have,
version early, and handle errors honestly.

Pick the simplest thing that works. A single FastAPI or Express service with a clear schema is almost always
the right starting point; reach for a microservice split or a framework layer only when a specific constraint
forces it. A popular framework is a signal (support, docs, hiring pool) but match to the job first.

## REST semantics: do not invent a new protocol

REST is a set of constraints on HTTP, not a religion. The four that matter most:

| Concern | Rule |
|---|---|
| Resources and URLs | Nouns, not verbs. `/users/42` not `/getUser?id=42`. Nest only when the child cannot exist without the parent. |
| HTTP verbs | GET reads (safe, cacheable), POST creates, PUT replaces, PATCH partial update, DELETE removes. Use them as specified in RFC 9110. |
| Status codes | 200 OK, 201 Created, 204 No Content, 400 Bad Request (client error), 401 Unauthenticated, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Unprocessable Entity (validation), 429 Too Many Requests, 500 Internal Server Error. Do not return 200 for errors. |
| Idempotency | GET, PUT, and DELETE must be idempotent. POST is not; add an idempotency key header for payment and retry-sensitive endpoints. |

## Error contracts

Return a consistent error shape; clients should never parse freeform strings to understand an error.

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "email must be a valid address",
    "field": "email",
    "request_id": "req_01j..."
  }
}
```

Log the `request_id` server-side; it is the link between the client complaint and the server trace.

## Pagination, filtering, and sorting

Prefer cursor-based pagination for large or frequently-updated datasets; offset pagination drifts when rows
are inserted or deleted mid-page. Return a `next_cursor` token and a `has_more` boolean. For small, stable
sets, limit-offset is fine. Always cap `limit` server-side (e.g., max 100).

## Versioning

Version in the URL path (`/v1/`, `/v2/`) rather than a header for REST APIs; it is obvious and cacheable.
Treat a breaking change (removed field, changed type, changed behavior) as a version bump. Support N-1 for
a documented deprecation window; do not break existing clients silently.

## Framework choices by language

| Language | Default choice | Stars (approx.) | When to look elsewhere |
|---|---|---|---|
| Python | FastAPI | ~98k | Django (~88k) when you want the ORM, admin, and auth batteries included; use Django REST Framework on top. |
| Node.js | Express | ~65k+ | NestJS (~75k) when the team prefers TypeScript decorators and a structured app architecture. |
| Go | Standard library `net/http` + chi or Echo | chi ~18k | Reach for a framework only when the stdlib routing becomes a bottleneck. |

FastAPI generates an OpenAPI schema automatically; commit the schema and use it to drive client generation
(openapi-generator) and contract tests.

## The twelve-factor app (the durable parts)

Not all twelve factors apply to every service, but four are non-negotiable for a Cambium-generated backend:

1. **Config**: all environment-specific config (database URL, API keys, flags) comes from environment variables, never from checked-in files.
2. **Logs**: write to stdout as structured JSON; let the platform route and store them.
3. **Processes**: be stateless; store session state in Redis or the database, not in-process memory.
4. **Dependencies**: declare and isolate them (`requirements.txt` + `pyproject.toml`, `package.json`, `go.mod`); never assume a system-installed library.

See 12factor.net for the full list.

## Security basics that belong in every API

- Validate and sanitize all inputs at the boundary (Pydantic, Zod, or equivalent); reject on the first validation failure, do not guess.
- Use HTTPS everywhere; never accept plaintext credentials.
- Authenticate before authorizing; prefer short-lived JWTs or opaque tokens over long-lived API keys.
- Rate-limit public endpoints; a missing rate limit is a denial-of-service waiting to happen.
- Set CORS headers deliberately; `Access-Control-Allow-Origin: *` is rarely correct.

## When GraphQL fits

GraphQL is the right choice when multiple clients need different shapes of the same data and over-fetching
is a real problem, not a hypothetical one. It adds schema maintenance, a resolver layer, and N+1 query risk
(mitigate with DataLoader). For a single client or a simple CRUD service, REST with a well-designed response
shape is simpler to build, test, and operate.

## Honest guardrails

- Cambium advises and generates; the human reviews, runs, and secures. Secrets management, certificate provisioning, and production hardening are on the human.
- Do not store credentials, connection strings, or API keys in generated code; use environment variable placeholders.
- OpenAPI schemas drift from implementation if not enforced in CI; add a schema-diff check to catch it early.
- The framework ecosystem moves: FastAPI minor releases can shift Pydantic v1 vs v2 behavior; pin and test.

## Attribution and sources

RFC 9110 HTTP Semantics (datatracker.ietf.org/doc/html/rfc9110), twelve-factor app (12factor.net),
FastAPI (fastapi.tiangolo.com), Django (djangoproject.com), Django REST Framework (django-rest-framework.org),
Express (expressjs.com), NestJS (nestjs.com), chi (github.com/go-chi/chi), OpenAPI Specification
(spec.openapis.org/oas/v3.1.0), openapi-generator (openapi-generator.tech), Pydantic (docs.pydantic.dev),
Zod (zod.dev), GraphQL (graphql.org), DataLoader (github.com/graphql/dataloader),
JWT best practices (datatracker.ietf.org/doc/html/rfc8725).
