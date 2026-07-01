# Shared engineering conventions

Conventions the engineering skills (the nine, plus web-development and ui-ux-design) share. Ideas adopted
from open skill projects, with credit and no files copied. See ATTRIBUTION.md.

## Progressive disclosure (skill authoring)

A skill's YAML frontmatter (name plus a trigger-rich description) is what loads at startup; the body loads
only when the skill is triggered. So keep the description keyword-rich and specific, and keep the body
focused. This is the official Claude Skills guidance and the organizing pattern behind jeffallan/claude-skills
(MIT). Cambium's skills already follow it; new skills must too.

## Definition of done: the four-dimension scorecard

Before calling a non-trivial build done, review it on four dimensions and record pass or needs-work with a
one-line reason each:

- Security: input validated, secrets kept out of code, authz checked, dependencies scanned.
- Performance: no obvious N+1 or unbounded work; a budget where it matters (for web, Core Web Vitals).
- Test coverage: the risky logic has tests; coverage is a floor, not the goal.
- Documentation: how to run it, the key decisions, and the honest limits are written down.

This scorecard idea is adapted from the senior full-stack engineer skill (idea only, no license found, nothing
copied). It is a review stance, not a guarantee.

## Architecture first

For a non-trivial system, write a short Architecture Decision Record (context, decision, consequences) before
scaffolding. See skills/software-architecture. An ADR-before-build discipline is shared by the senior
full-stack and jeffallan skill sets.

## Pair the work with a reviewer and tests

Security and correctness work is done with a reviewer stance and tests, not single-shot. The security skill
pairs with software-testing-qa and a review pass, echoing the "security hardening chain" pattern.

## The honest boundary (all engineering skills)

Cambium advises and generates code that the human reviews and runs. It does not deploy to production, move
money, or hold secrets or credentials on the user's behalf, and its security guidance is not a security audit.

## Attribution

Ideas adopted, no files copied: jeffallan/claude-skills (MIT, progressive disclosure, lifecycle and
skill-combination patterns), nextlevelbuilder/ui-ux-pro-max-skill (MIT, brief-first design and a versioned
design-knowledge base), and the senior full-stack engineer suite (idea only, no license found: the
four-dimension scorecard and ADR-first stance). Verify each project's license before adapting any actual file.
