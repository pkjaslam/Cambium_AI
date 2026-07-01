---
name: software-testing-qa
description: >
  Designs and critiques test strategies across the full pyramid: unit, integration,
  end-to-end, contract, load, and accessibility. Use when a project needs a test plan,
  a specific test written, a flaky-test diagnosis, or a coverage conversation. Trigger on:
  "write tests", "test strategy", "flaky tests", "coverage report", "end-to-end testing",
  "contract test", "load test", "accessibility audit", "test pyramid", "mock vs fixture".
  Pairs well with software-architecture (test the seams you designed) and
  debugging-observability (tests are your first signal; traces explain the failure).
  Boundary: tests raise confidence in correctness; they do not prove the absence of bugs.
  A green suite is necessary, not sufficient.
---

# Test at the Right Level, Then Trust the Signal

The test pyramid exists because different test types give different feedback at different
costs. Write many fast unit tests, fewer integration tests, and a small number of
end-to-end tests. Invert the pyramid and you pay for it in slow, brittle CI.

---

## The Test Pyramid in Practice

| Layer | What it tests | Tools | Speed | Cost of failure |
|---|---|---|---|---|
| Unit | One function or class in isolation | Pytest, Vitest, Jest | Milliseconds | Cheap to fix |
| Integration | Two or more real components together | Pytest, Vitest | Seconds | Moderate |
| End-to-end (E2E) | Full user flow through a real browser | Playwright | Minutes | Expensive |
| Contract | API shape agreed between producer and consumer | Pact | Fast in CI | Prevents mismatches at deploy |
| Load / performance | System under realistic traffic | k6 | Long-running | Prevents incidents |
| Accessibility | UI against WCAG standards | axe-core, Playwright + axe | Seconds to minutes | Legal and usability risk |

---

## Fixtures vs. Mocks: Choose Deliberately

| Situation | Prefer | Reason |
|---|---|---|
| External HTTP service (unpredictable, slow, costs money) | Mock or recorded cassette | Tests stay deterministic |
| Your own database layer | Fixture (real DB in Docker) | Tests actual query behaviour |
| Time-dependent code | Mock `datetime.now` | Removes flakiness |
| File I/O in a unit test | Fixture (temp directory) | Fast and isolated |
| Message queue in integration test | Real broker (Docker Compose) | Tests real serialisation |

Over-mocking is the most common testing mistake. When you mock your own code you test the
mock, not the system. Favour real dependencies in integration tests; mock only at the true
boundary (network, time, randomness).

---

## Flaky-Test Hygiene

A flaky test is worse than no test. It trains the team to ignore red builds.

Causes and fixes:
- Shared mutable state between tests: use `setup`/`teardown` or test-scoped fixtures.
- Time-dependent assertions: freeze time; avoid `sleep()` in tests.
- Network calls in unit tests: mock at the boundary.
- Race conditions in async code: use explicit `await` or synchronisation primitives.
- Order-dependent tests: enforce random ordering in CI (`pytest-randomly`, `--random-order`).

When a test flakes more than twice, quarantine it immediately. Do not merge until fixed.

---

## Coverage as a Floor, Not a Goal

Coverage tells you which lines were executed during tests. It does not tell you whether the
tests were meaningful. Chasing 100% coverage produces tests that exercise code without
asserting anything useful.

Reasonable defaults:
```ini
# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
addopts = "--cov=src --cov-fail-under=80"
```

Use coverage to find untested critical paths, then write tests that assert behaviour. Stop
when the marginal test protects something real.

---

## Playwright End-to-End Snippet

```python
# tests/e2e/test_login.py  (Playwright + Pytest)
import pytest
from playwright.sync_api import Page, expect

def test_login_succeeds(page: Page):
    page.goto("http://localhost:3000/login")
    page.fill("[data-testid=email]", "user@example.com")
    page.fill("[data-testid=password]", "correct-password")
    page.click("[data-testid=submit]")
    expect(page.locator("h1")).to_have_text("Dashboard")
```

Target `data-testid` attributes, not CSS classes. Classes change with redesigns; test IDs
signal intent.

---

## Honest Guardrails

- Cambium writes tests and reviews strategies. The human runs them and owns the suite.
- A passing test suite does not mean the system is correct; it means the tested scenarios
  passed. Exploratory testing and user feedback surface what automated tests miss.
- Load tests measure the system as tested, not as deployed. Infrastructure differences
  (instance size, network topology, cold caches) can make results misleading.
- Cambium does not run tests against production systems or real user data.

---

## Attribution and Sources

- Playwright (~90k GitHub stars at time of writing, Microsoft). https://playwright.dev
- Pytest (Python). https://docs.pytest.org
- Vitest (Vite-native, fast). https://vitest.dev
- Jest (JavaScript, Meta). https://jestjs.io
- k6 load testing (Grafana Labs). https://k6.io/docs/
- Pact contract testing. https://docs.pact.io
- axe-core accessibility engine (Deque). https://github.com/dequelabs/axe-core
- Martin Fowler, "TestPyramid". https://martinfowler.com/bliki/TestPyramid.html
- WCAG 2.2 accessibility standard. https://www.w3.org/TR/WCAG22/
