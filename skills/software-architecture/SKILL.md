---
name: software-architecture
description: >
  Designs and critiques software systems at the structural level. Use when a project needs
  separation of concerns, a decision on monolith vs. services, API contracts, or a written
  Architecture Decision Record. Trigger on: "design the system", "should we split this into
  services", "API-first", "ADR", "coupling is too high", "how should this scale", "draw the
  architecture". Pairs well with software-testing-qa (validate the design) and
  debugging-observability (instrument what the architecture produces). Boundary: Cambium
  produces advice, diagrams, and ADR drafts; it does not guarantee the design scales under
  real load. Validate with load tests, code reviews, and staged rollouts before committing.
---

# Build the Simplest Structure That Carries the Load

Good architecture is about managing change, not predicting the future. Pick the design that
fits today's team and today's traffic, then make the next move cheap. Favour proven patterns
over custom ones; a boring CRUD monolith ships faster and fails more clearly than a distributed
mess nobody understands.

---

## Monolith vs. Services: Decide Before You Drift

| Signal | Stay monolithic | Consider services |
|---|---|---|
| Team size | Under 8 engineers | Multiple autonomous squads |
| Deployment cadence | Weekly or slower | Independent per-capability |
| Bounded contexts | Blurry, still evolving | Well-defined, stable |
| Data ownership | Single schema is fine | Each domain owns its store |
| Operational maturity | Basic infra, one on-call | Platform team, observability in place |
| Traffic pattern | Uniform | Wildly different per subsystem |

Start monolithic. Extract a service only when the seam hurts repeatedly and the team is
ready to own the operational overhead. A well-structured monolith beats a poorly operated
microservices cluster every time. See Martin Fowler's "Monolith First" pattern for the
reasoning behind this sequence.

---

## Coupling and Cohesion

High cohesion: code that changes together lives together. Low coupling: modules talk through
stable interfaces, not shared mutable state. The test: can you change module A without
reading module B? If not, coupling is too high.

Practical rules:
- Depend on abstractions (interfaces, protocols), not concrete implementations.
- Pass data, not behaviour, across module boundaries where possible.
- A package that imports half the codebase is a seam waiting to break.

---

## API-First Design

Define the contract before writing the implementation. This forces clarity on inputs,
outputs, and error cases, and lets frontend and backend teams work in parallel.

```yaml
# openapi: 3.1.0 stub (contract first, code second)
paths:
  /analyses/{id}:
    get:
      summary: Fetch a completed analysis
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        "200":
          description: Analysis result
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Analysis"
        "404":
          description: Not found
```

Use OpenAPI 3.1 (https://spec.openapis.org/oas/v3.1.0) for REST. Use AsyncAPI
(https://www.asyncapi.com) for event-driven contracts. Generate stubs and validators from
the spec, do not write them by hand.

---

## Architecture Decision Records (ADR)

An ADR is a short, permanent record of a consequential architectural choice. Write one
whenever a decision is hard to reverse or affects multiple teams. Store ADRs in
`docs/decisions/` and number them sequentially.

**ADR mini-template:**

```markdown
# ADR-NNN: <Title>

Date: YYYY-MM-DD
Status: Proposed | Accepted | Superseded by ADR-NNN

## Context
What is the situation forcing this decision? What constraints exist?

## Decision
What are we doing?

## Consequences
What becomes easier? What becomes harder or more expensive?

## Alternatives considered
What else was on the table and why was it rejected?
```

Keep ADRs short (one page). They are not design docs; they are decision logs.

---

## Honest Guardrails

- Cambium draws diagrams and writes ADR drafts. A human architect reviews and owns them.
- Architecture advice is based on stated context. Hidden constraints (org politics, legacy
  contracts, undocumented dependencies) can invalidate a recommendation completely.
- "Scales to X users" is never a guarantee from a diagram. Run load tests with realistic
  data and traffic shapes before trusting any scaling claim.
- Distributed systems trade latency, availability, and consistency in ways that are
  non-obvious. Read the CAP theorem literature before splitting data across services.

---

## Attribution and Sources

- Martin Fowler: patterns, monolith-first, strangler fig, event sourcing.
  https://martinfowler.com/architecture/
- roadmap.sh software architecture roadmap (community-maintained, up to date).
  https://roadmap.sh/software-architect
- Michael Nygard, "Documenting Architecture Decisions" (original ADR proposal).
  https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
- OpenAPI Specification 3.1. https://spec.openapis.org/oas/v3.1.0
- AsyncAPI 3.0. https://www.asyncapi.com/docs/reference/specification/v3.0.0
- "Building Microservices" (Sam Newman, O'Reilly, 2nd ed. 2021) for service decomposition.
