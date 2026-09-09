from pathlib import Path

from playwright.sync_api import Page, expect


FRONTEND_URL = "http://localhost:3000"
SCREENSHOT_PATH = (
    Path(__file__).resolve().parent / "screenshots" / "automation-admin-persistence.png"
)


def test_automation_rule_persists_after_reload(page: Page):
    page.goto(FRONTEND_URL)
    page.get_by_role("button", name="Settings").click()
    expect(page.get_by_role("heading", name="Admin - System Configuration")).to_be_visible()
    page.get_by_role("button", name="Automation").click()

    application_toggle = page.get_by_role(
        "checkbox",
        name="Application automation enabled",
    )
    expect(application_toggle).not_to_be_checked()

    application_toggle.check()
    page.get_by_role("button", name="Update Automation Rules").click()
    expect(page.get_by_text("Automation settings saved successfully!")).to_have_count(1)

    SCREENSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(SCREENSHOT_PATH), full_page=True)

    page.reload()
    page.get_by_role("button", name="Settings").click()
    page.get_by_role("button", name="Automation").click()
    expect(
        page.get_by_role("checkbox", name="Application automation enabled")
    ).to_be_checked()
