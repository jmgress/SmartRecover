import httpx
import pytest
from fastapi.testclient import TestClient

from backend.agents.incident_management_agent import IncidentManagementAgent
from backend.connectors.splunk_connector import SplunkConnector
from backend.config import load_config_from_env
from backend.main import app


client = TestClient(app)


def _mock_async_client(monkeypatch, handler):
    transport = httpx.MockTransport(handler)
    real_async_client = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs["transport"] = transport
        return real_async_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)


@pytest.mark.asyncio
async def test_splunk_connector_normalizes_incidents(monkeypatch):
    """Splunk incidents are normalized to the shared incident schema."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/services/search/jobs/export"
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            json={
                "results": [
                    {
                        "incident_id": "SPL-1001",
                        "title": "API latency spike",
                        "description": "High latency detected in checkout API",
                        "severity": "high",
                        "status": "open",
                        "created_at": "2026-08-12T20:00:00Z",
                        "updated_at": "2026-08-12T20:15:00Z",
                        "affected_services": "checkout-api,payments-api",
                        "assignee": "sre-oncall",
                    }
                ]
            },
        )

    _mock_async_client(monkeypatch, handler)

    connector = SplunkConnector(
        {
            "base_url": "https://splunk.example.com:8089",
            "token": "test-token",
            "verify_ssl": False,
            "incidents_search": 'search index="{index}" | head 10',
        }
    )

    incidents = await connector.list_incidents()

    assert incidents == [
        {
            "id": "SPL-1001",
            "title": "API latency spike",
            "description": "High latency detected in checkout API",
            "severity": "high",
            "status": "open",
            "created_at": "2026-08-12T20:00:00Z",
            "updated_at": "2026-08-12T20:15:00Z",
            "affected_services": ["checkout-api", "payments-api"],
            "assignee": "sre-oncall",
            "source": "splunk",
        }
    ]


@pytest.mark.asyncio
async def test_splunk_connector_handles_auth_errors(monkeypatch):
    """Splunk auth failures degrade gracefully with a warning."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, headers={"content-type": "application/json"}, json={"messages": []})

    _mock_async_client(monkeypatch, handler)

    connector = SplunkConnector(
        {
            "base_url": "https://splunk.example.com:8089",
            "token": "bad-token",
            "verify_ssl": False,
            "incidents_search": 'search index="{index}" | head 10',
        }
    )

    incidents = await connector.list_incidents()

    assert incidents == []
    assert connector.get_last_warning() is not None
    assert "authenticate" in connector.get_last_warning().lower()


def test_incident_management_agent_selects_splunk_connector():
    """IncidentManagementAgent.from_config selects the Splunk connector."""
    agent = IncidentManagementAgent.from_config(
        {
            "connector": {
                "connector_type": "splunk",
                "splunk": {
                    "base_url": "https://splunk.example.com:8089",
                    "verify_ssl": False,
                },
            }
        }
    )

    assert isinstance(agent.connector, SplunkConnector)


def test_load_config_from_env_supports_splunk(monkeypatch):
    """Environment variables override connector config for Splunk."""
    monkeypatch.setenv("INCIDENT_CONNECTOR_TYPE", "splunk")
    monkeypatch.setenv("SPLUNK_BASE_URL", "https://splunk.example.com:8089")
    monkeypatch.setenv("SPLUNK_PORT", "8090")
    monkeypatch.setenv("SPLUNK_VERIFY_SSL", "false")
    monkeypatch.setenv("SPLUNK_INDEX", "itsi")

    config = load_config_from_env()

    assert config.connector_type == "splunk"
    assert config.splunk is not None
    assert config.splunk.base_url == "https://splunk.example.com:8089"
    assert config.splunk.port == 8090
    assert config.splunk.verify_ssl is False
    assert config.splunk.index == "itsi"


def test_list_incidents_route_returns_splunk_source(monkeypatch):
    """GET /incidents returns Splunk incidents with source attribution."""

    class FakeAgent:
        async def list_incidents(self):
            return [
                {
                    "id": "SPL-42",
                    "title": "Search head degraded",
                    "description": "Search head cluster latency increased",
                    "severity": "medium",
                    "status": "open",
                    "created_at": "2026-08-12T20:00:00Z",
                    "updated_at": "2026-08-12T20:05:00Z",
                    "affected_services": ["search-head"],
                    "assignee": "platform",
                    "source": "splunk",
                }
            ]

        def get_last_warning(self):
            return None

    monkeypatch.setattr("backend.api.routes._get_incident_management_agent", lambda: FakeAgent())

    response = client.get("/api/v1/incidents")

    assert response.status_code == 200
    assert response.json()[0]["source"] == "splunk"


def test_list_incidents_route_returns_warning_for_splunk_failure(monkeypatch):
    """GET /incidents surfaces Splunk failures cleanly for the frontend."""

    class FakeAgent:
        async def list_incidents(self):
            return []

        def get_last_warning(self):
            return "Unable to authenticate to Splunk with the configured credentials."

    monkeypatch.setattr("backend.api.routes._get_incident_management_agent", lambda: FakeAgent())

    response = client.get("/api/v1/incidents")

    assert response.status_code == 503
    assert "authenticate" in response.json()["detail"].lower()
