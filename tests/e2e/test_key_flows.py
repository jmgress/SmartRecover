import re

from playwright.sync_api import Page, expect


FRONTEND_URL = "http://localhost:3000"
API_URL = "http://localhost:8000/api/v1"
INCIDENT_NUMBER = "INC0000001"


def test_incident_list_loads(page: Page):
    page.goto(FRONTEND_URL)

    expect(page.get_by_role("heading", name="Incidents")).to_be_visible()
    expect(page.get_by_text(INCIDENT_NUMBER, exact=True)).to_be_visible()


def test_incident_detail_view_loads(page: Page):
    page.goto(FRONTEND_URL)
    page.get_by_text(INCIDENT_NUMBER, exact=True).click()

    expect(page.get_by_role("heading", name=INCIDENT_NUMBER, exact=True)).to_be_visible()
    expect(page.get_by_role("heading", name="Incident Details")).to_be_visible()
    expect(
        page.get_by_role("heading", level=3, name="Memory leak in auth service", exact=True)
    ).to_be_visible()


def test_resolution_is_triggered_from_chat(page: Page):
    page.goto(FRONTEND_URL)
    page.get_by_text(INCIDENT_NUMBER, exact=True).click()
    page.get_by_placeholder("Ask about this incident...").fill("What should I do?")
    page.get_by_role("button", name="Resolve").click()

    expect(page.get_by_text("What should I do?", exact=True)).to_be_visible()
    expect(page.get_by_text(re.compile(r"Found \d+ similar historical incidents"))).to_be_visible()


def test_health_check_is_healthy(page: Page):
    response = page.request.get(f"{API_URL}/health")

    assert response.ok
    assert response.json() == {"status": "healthy", "service": "incident-resolver"}
