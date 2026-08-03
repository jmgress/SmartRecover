---
name: playwright-e2e-tests
description: 'Author Playwright end-to-end tests (Python) for the SmartRecover React UI. Use when: the user asks to write E2E/browser/UI tests, generate Playwright tests, or add end-to-end coverage for a frontend flow. NOT for backend pytest unit tests (those follow backend-tests.instructions.md) or React component tests (Jest + React Testing Library).'
argument-hint: 'The user flow or page to cover (e.g. incident list, resolve flow)'
---

# Playwright E2E Tests (Python)

Write end-to-end tests that drive the SmartRecover React UI in a real browser using Playwright's Python sync API.

## Setup & structure
- Store E2E tests separately from backend unit tests, e.g. under a top-level `tests/e2e/` directory, named `test_<feature-or-page>.py`.
- Begin each file with `from playwright.sync_api import Page, expect`.
- Use the `page: Page` fixture; put `page.goto(...)` at the start of each test (a `scope="function", autouse=True` fixture is fine for shared navigation).
- The frontend talks to the backend at `/api/v1`; run both (`./start.sh`) or point tests at the running dev server's base URL.

## Code quality
- **Locators**: prefer user-facing, role-based locators — `get_by_role`, `get_by_label`, `get_by_text` — over CSS/XPath or test IDs.
- **Assertions**: use auto-retrying web-first `expect` assertions (`expect(page).to_have_url(...)`, `expect(locator).to_have_text(...)`, `expect(locator).to_have_count(...)`). Avoid `expect(locator).to_be_visible()` unless you're specifically testing a visibility change.
- **Waiting**: rely on Playwright auto-waiting; do not add hard-coded sleeps or inflate default timeouts.
- **Titles**: descriptive `def test_...():` names that state intent; comment only non-obvious logic.

## Example
```python
import re
from playwright.sync_api import Page, expect


def test_incident_list_loads(page: Page):
    page.goto("http://localhost:3000/")
    expect(page.get_by_role("heading", name=re.compile("Incidents", re.I))).to_be_visible()


def test_resolve_flow(page: Page):
    page.goto("http://localhost:3000/")
    page.get_by_role("button", name="Resolve").first.click()
    expect(page.get_by_text(re.compile("resolution", re.I))).to_be_visible()
```

## Running
- Execute from the terminal with `pytest tests/e2e/` (install via `pip install playwright pytest-playwright` and `playwright install` if not already present).
- Analyze failures to find root causes rather than loosening assertions.
