"""Live connectors use mocked HTTP only; no external accounts are required."""

import json
from datetime import timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from backend.agents.incident_management_agent import IncidentManagementAgent
from backend.config import ConnectorConfig, JiraConfig, ServiceNowConfig, load_config_from_env
from backend.connectors.jira_connector import JiraServiceManagementConnector
from backend.connectors.live_incident import IncidentSourceError
from backend.connectors.servicenow_connector import ServiceNowConnector


def snow_row(number="INC100001", **updates):
    return {
        "number": number,
        "short_description": "Database connection failure",
        "description": "Database queries are failing",
        "priority": {"value": "2", "display_value": "2 - High"},
        "state": {"value": "2", "display_value": "In Progress"},
        "sys_created_on": "2026-10-17 10:00:00",
        "sys_updated_on": "2026-10-17 11:00:00",
        "category": {"value": "software", "display_value": "Software"},
        "subcategory": {"value": "database", "display_value": "Database"},
        "assignment_group": {"value": "opaque-id", "display_value": "Database Operations"},
        "business_service": {"value": "service-id", "display_value": "Checkout"},
        "close_notes": "",
        **updates,
    }


def jira_row(key="OPS-1", **updates):
    return {
        "key": key,
        "fields": {
            "project": {"key": "OPS"},
            "summary": "Database connection failure",
            "description": {
                "type": "doc", "version": 1,
                "content": [{"type": "paragraph", "content": [
                    {"type": "text", "text": "Database queries are failing"},
                ]}],
            },
            "priority": {"name": "High"},
            "status": {"statusCategory": {"key": "indeterminate"}},
            "created": "2026-10-17T10:00:00.000+0000",
            "updated": "2026-10-17T11:00:00.000+0000",
            "issuetype": {"name": "Incident"},
            "components": [{"name": "Database"}],
            "assignee": None,
            **updates,
        },
    }


@pytest.fixture
def transport(monkeypatch):
    original = httpx.AsyncClient

    def install(handler):
        def client(**kwargs):
            return original(**kwargs, transport=httpx.MockTransport(handler))
        monkeypatch.setattr(httpx, "AsyncClient", client)

    return install


@pytest.fixture(params=["servicenow", "jira"])
def connector(request):
    if request.param == "servicenow":
        return ServiceNowConnector({
            "instance_url": "https://snow.example.test",
            "username": "reader",
            "password": "test-only-password",
        })
    return JiraServiceManagementConnector({
        "url": "https://jira.example.test",
        "username": "reader",
        "api_token": "test-only-token",
        "project_key": "OPS",
    })


@pytest.mark.asyncio
async def test_paginated_reads_and_normalization(connector, transport):
    requests = []

    def handler(request):
        requests.append(request)
        assert request.method == "GET"
        assert request.headers["authorization"].startswith("Basic ")
        assert request.extensions["timeout"]["read"] == 30
        if connector.get_connector_name() == "servicenow":
            assert request.url.path == "/api/now/table/incident"
            assert "category,subcategory" in request.url.params["sysparm_fields"]
            offset = int(request.url.params["sysparm_offset"])
            rows = [snow_row(f"INC10000{offset + 1}")] if offset < 2 else []
            return httpx.Response(200, json={"result": rows})
        assert request.url.path == "/rest/api/3/search/jql"
        assert request.url.params["jql"] == 'project = "OPS" ORDER BY key ASC'
        if "nextPageToken" not in request.url.params:
            return httpx.Response(200, json={
                "issues": [jira_row()], "isLast": False, "nextPageToken": "next",
            })
        assert request.url.params["nextPageToken"] == "next"
        return httpx.Response(200, json={"issues": [jira_row("OPS-2")], "isLast": True})

    transport(handler)
    records = await connector.list_incidents()
    assert len(records) == 2
    assert len({record["id"] for record in records}) == 2
    for record in records:
        assert record["category"] == "Database"
        assert record["severity"] == "high"
        assert record["status"] == "investigating"
        assert record["description"] == "Database queries are failing"
        assert record["created_at"].tzinfo == timezone.utc
    assert len(requests) >= 2


@pytest.mark.asyncio
async def test_detail_lookup_and_not_found(connector, transport):
    seen = []

    def handler(request):
        seen.append(request)
        if connector.get_connector_name() == "servicenow":
            query = request.url.params["sysparm_query"]
            assert query.startswith("number=INC")
            rows = [snow_row()] if query.startswith("number=INC100001^") and request.url.params["sysparm_offset"] == "0" else []
            return httpx.Response(200, json={"result": rows})
        jql = request.url.params["jql"]
        assert 'project = "OPS" AND key = ' in jql
        rows = [jira_row()] if 'key = "OPS-1"' in jql else []
        return httpx.Response(200, json={"issues": rows, "isLast": True})

    transport(handler)
    incident_id = "INC100001" if connector.get_connector_name() == "servicenow" else "OPS-1"
    assert (await connector.get_incident(incident_id))["id"] == incident_id
    assert await connector.get_incident(incident_id + "999") is None
    count = len(seen)
    assert await connector.get_incident('INC1^ORactive=true') is None
    assert await connector.get_incident('OPS-1" OR project != "OPS') is None
    assert await connector.get_incident("OTHER-1") is None
    assert len(seen) == count


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [401, 403, 429, 500, 302])
async def test_http_errors_are_explicit_and_sanitized(connector, transport, status, caplog):
    transport(lambda request: httpx.Response(
        status, text="private-upstream-response",
        headers={"Location": "https://other.example.test"},
    ))
    with pytest.raises(IncidentSourceError, match=f"HTTP {status}") as error:
        await connector.list_incidents()
    assert "private-upstream-response" not in str(error.value) + caplog.text
    assert connector.secret not in str(error.value) + caplog.text


@pytest.mark.asyncio
async def test_timeout_is_sanitized(connector, transport, caplog):
    def handler(request):
        raise httpx.ReadTimeout("private-upstream-response", request=request)
    transport(handler)
    with pytest.raises(IncidentSourceError, match="upstream request failed"):
        await connector.list_incidents()
    assert "private-upstream-response" not in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [[], {}, {"result": {}, "issues": {}}, {"result": [None], "issues": [None]}])
async def test_malformed_payload_fails_instead_of_returning_empty(connector, transport, payload):
    transport(lambda request: httpx.Response(200, json=payload))
    with pytest.raises(IncidentSourceError):
        await connector.list_incidents()


@pytest.mark.asyncio
async def test_malformed_json_is_explicit(connector, transport):
    transport(lambda request: httpx.Response(200, text="<html>not JSON</html>"))
    with pytest.raises(IncidentSourceError, match="invalid JSON"):
        await connector.list_incidents()


@pytest.mark.asyncio
async def test_invalid_required_fields_do_not_skip_records(connector, transport):
    transport(lambda request: httpx.Response(200, json={
        "result": [snow_row(sys_created_on="bad timestamp")],
        "issues": [jira_row(created="bad timestamp")], "isLast": True,
    }))
    with pytest.raises(IncidentSourceError, match="invalid incident fields"):
        await connector.list_incidents()


@pytest.mark.asyncio
async def test_repeated_pages_fail_without_partial_success(connector, transport):
    transport(lambda request: httpx.Response(200, json={
        "result": [snow_row()],
        "issues": [jira_row()], "isLast": False, "nextPageToken": "same-token",
    }))
    with pytest.raises(IncidentSourceError, match="pagination"):
        await connector.list_incidents()


@pytest.mark.asyncio
async def test_missing_continuation_token_is_an_error(transport):
    connector = JiraServiceManagementConnector({
        "url": "https://jira.example.test", "username": "reader",
        "api_token": "test-only-token", "project_key": "OPS",
    })
    transport(lambda request: httpx.Response(200, json={"issues": [], "isLast": False}))
    with pytest.raises(IncidentSourceError, match="pagination token"):
        await connector.list_incidents()


@pytest.mark.asyncio
@pytest.mark.parametrize("base_url", ["http://example.test", "https://user:pass@example.test", "https://example.test?token=value"])
async def test_unsafe_configuration_does_not_send_credentials(connector, transport, base_url):
    def handler(request):
        pytest.fail("Invalid configuration must not send any request")
    transport(handler)
    connector.base_url = base_url
    with pytest.raises(IncidentSourceError, match="HTTPS URL"):
        await connector.list_incidents()


@pytest.mark.asyncio
async def test_similar_incidents_are_serializable_and_preserve_categories(connector, transport):
    def handler(request):
        if connector.get_connector_name() == "servicenow":
            rows = [] if request.url.params["sysparm_offset"] != "0" else [
                snow_row(),
                snow_row("INC100002", state="6", close_notes="Restored database connectivity"),
            ]
            if request.url.params["sysparm_query"].startswith("number="):
                rows = rows[:1]
            return httpx.Response(200, json={"result": rows})
        rows = [jira_row(), jira_row("OPS-2", status={"statusCategory": {"key": "done"}})]
        if "AND key" in request.url.params["jql"]:
            rows = rows[:1]
        return httpx.Response(200, json={"issues": rows, "isLast": True})

    transport(handler)
    incident_id = "INC100001" if connector.get_connector_name() == "servicenow" else "OPS-1"
    records = await connector.get_similar_incidents(incident_id, "")
    assert len(records) == 1
    assert records[0]["category"] == "Database"
    assert records[0]["ticket_id"] != incident_id
    assert records[0]["similarity_score"] >= 0.2
    json.dumps(records)
    resolutions = await connector.get_resolutions(incident_id, "")
    assert resolutions == (["Restored database connectivity"] if connector.get_connector_name() == "servicenow" else [])
    with pytest.raises(IncidentSourceError, match="change retrieval is not supported"):
        await connector.get_related_changes(incident_id, "")


def test_source_normalizers_use_metadata_before_text():
    snow = ServiceNowConnector({})
    record = snow._normalize(snow_row(category="hardware", subcategory="network"))
    assert record["category"] == "Network"
    assert record["assignee"] == "Database Operations"
    assert record["affected_services"] == ["Checkout"]
    assert snow._normalize(snow_row(priority="custom"))["severity"] == "unknown"
    assert snow._normalize(snow_row(
        subcategory={"value": "network", "display_value": "Localized label"}
    ))["category"] == "Network"
    jira = JiraServiceManagementConnector({"project_key": "OPS"})
    record = jira._normalize(jira_row(
        issuetype={"name": "Incident"}, components=[{"name": "Security"}],
        status={"statusCategory": {"key": "done"}}, resolutiondate="2026-10-17T13:00:00Z",
    ))
    assert record["category"] == "Security"
    assert record["status"] == "resolved"
    assert record["resolved_at"].hour == 13
    assert jira._normalize(jira_row(priority=None))["severity"] == "unknown"


def test_connector_config_precedence_and_env_only_secrets(monkeypatch):
    monkeypatch.setenv("CONNECTOR_TYPE", "jira")
    monkeypatch.setenv("JIRA_PROJECT_KEY", "OPS")
    monkeypatch.setenv("JIRA_API_TOKEN", "test-env-token")
    monkeypatch.delenv("SERVICENOW_PASSWORD", raising=False)
    settings = load_config_from_env({
        "connector_type": "servicenow",
        "jira": {"url": "https://jira.example.test", "project_key": "OLD", "api_token": "ignored"},
        "servicenow": {"password": "ignored"},
    })
    assert settings.connector_type == "jira"
    assert settings.jira.url == "https://jira.example.test"
    assert settings.jira.project_key == "OPS"
    assert settings.jira.api_token == "test-env-token"
    assert settings.servicenow.password == ""
    assert "test-env-token" not in repr(settings)
    monkeypatch.setenv("CONNECTOR_TYPE", "typo")
    with pytest.raises(ValueError):
        load_config_from_env({})


def test_factory_preserves_mock_default_and_selects_live_sources():
    assert IncidentManagementAgent.from_config({}).connector.get_connector_name() == "mock"
    for source, settings in (("servicenow", ServiceNowConfig()), ("jira", JiraConfig())):
        config = ConnectorConfig(connector_type=source, **{source: settings})
        agent = IncidentManagementAgent.from_config(config.model_dump())
        assert agent.connector.get_connector_name() == source


@pytest.fixture
def live_app(connector, transport, monkeypatch, tmp_path):
    from backend.agents.orchestrator import OrchestratorAgent
    from backend.api import routes
    from backend.cache.agent_cache import AgentCache
    from backend.data.automation_store import AutomationStore
    from backend.data.feedback_store import FeedbackStore
    from backend.data.metrics_history_store import MetricsEventStore
    from backend.data.resolution_store import ResolutionStore
    from backend.main import app
    from fastapi.testclient import TestClient

    source = connector.get_connector_name()
    incident_id = "INC001" if source == "servicenow" else "OPS-1"

    def handler(request):
        assert request.method == "GET"
        if source == "servicenow":
            query = request.url.params["sysparm_query"]
            rows = [
                snow_row("INC001", subcategory="Security"),
                snow_row(
                    "INC002", subcategory="Security", state="6",
                    resolved_at="2026-10-17 12:00:00",
                    close_notes="Restored certificate trust",
                ),
            ]
            if query.startswith("number="):
                requested = query.split("^")[0].split("=")[1]
                rows = [row for row in rows if row["number"] == requested]
            if request.url.params["sysparm_offset"] != "0":
                rows = []
            return httpx.Response(200, json={"result": rows})
        rows = [
            jira_row(components=[{"name": "Security"}]),
            jira_row(
                "OPS-2", components=[{"name": "Security"}],
                status={"statusCategory": {"key": "done"}},
                resolutiondate="2026-10-17T12:00:00Z",
            ),
        ]
        if "AND key" in request.url.params["jql"]:
            rows = [row for row in rows if f'key = "{row["key"]}"' in request.url.params["jql"]]
        return httpx.Response(200, json={"issues": rows, "isLast": True})

    transport(handler)
    config = ConnectorConfig(
        connector_type=source,
        **{source: ServiceNowConfig() if source == "servicenow" else JiraConfig()},
    )
    agent = IncidentManagementAgent(config)
    agent.connector = connector
    llm = MagicMock()
    llm.ainvoke = AsyncMock(return_value=SimpleNamespace(content="Mapped incident summary"))

    async def stream(*args, **kwargs):
        yield SimpleNamespace(content="Mapped incident summary")

    llm.astream = stream
    monkeypatch.setattr("backend.agents.orchestrator.get_llm", lambda: llm)
    orchestrator = OrchestratorAgent(
        incident_agent=agent,
        automation_store=AutomationStore(storage_path=tmp_path / "rules.json"),
        feedback_store=FeedbackStore(storage_path=tmp_path / "feedback.json"),
        metrics_event_store=MetricsEventStore(storage_path=tmp_path / "metrics.json"),
    )
    orchestrator.cache = AgentCache()
    monkeypatch.setattr(routes, "orchestrator", orchestrator)
    monkeypatch.setattr(routes, "feedback_store", orchestrator.feedback_store)
    monkeypatch.setattr(routes, "automation_store", orchestrator.automation_store)
    monkeypatch.setattr(routes, "metrics_event_store", orchestrator.metrics_event_store)
    monkeypatch.setattr(routes, "resolution_store", ResolutionStore(storage_path=tmp_path / "resolutions.json"))
    monkeypatch.setattr("backend.cache.get_agent_cache", lambda: orchestrator.cache)
    return TestClient(app), orchestrator, incident_id


def test_live_api_reads_categories_and_uses_source_for_metrics(live_app):
    client, orchestrator, incident_id = live_app
    response = client.get("/api/v1/incidents")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert all(row["category"] == "Security" for row in response.json())
    record = client.get(f"/api/v1/incidents/{incident_id}")
    assert record.status_code == 200
    assert record.json()["category"] == "Security"
    details = client.get(f"/api/v1/incidents/{incident_id}/details")
    assert details.status_code == 200
    assert details.json()["incident"]["category"] == "Security"
    assert client.get(f"/api/v1/incidents/{incident_id}9999").status_code == 404
    metrics = client.get("/api/v1/admin/mttr-metrics")
    assert metrics.status_code == 200
    assert metrics.json()["total_incidents"] == 2
    assert metrics.json()["resolved_count"] == 1
    assert metrics.json()["overall_mean_seconds"] == 7200
    assert client.get("/api/v1/admin/metrics-trends?days=7").status_code == 200


def test_live_resolution_and_stream_use_mapped_category_without_mock_evidence(live_app):
    client, orchestrator, incident_id = live_app
    response = client.post("/api/v1/resolve", json={"incident_id": incident_id, "user_query": "Investigate"})
    assert response.status_code == 200, response.text
    assert response.json()["automation"]["category"] == "Security"
    assert response.json()["automation"]["automated"] is False
    response = client.post("/api/v1/resolve/stream", json={"incident_id": incident_id, "user_query": "Investigate"})
    assert response.status_code == 200
    events = [
        json.loads(line[6:]) for line in response.text.splitlines()
        if line.startswith("data: ") and line != "data: [DONE]"
    ]
    assert not any(event["event"] == "error" for event in events), response.text
    automation = next(event for event in events if event["event"] == "automation_decision")
    complete = next(event for event in events if event["event"] == "complete")
    assert automation["result"]["category"] == "Security"
    assert complete["result"]["automation"] == automation["result"]
    incident_event = next(
        event for event in events if event["event"] == "agent_complete" and event["agent"] == "servicenow"
    )
    assert incident_event["result"]["incident"]["category"] == "Security"
    assert len(orchestrator.automation_store.list_audit()) == 2
    assert all(row.category == "Security" for row in orchestrator.automation_store.list_audit())
    data = orchestrator.cache.get(incident_id)
    assert data["logs_results"]["error"]
    assert data["remediation_results"]["error"]
    assert data["change_results"]["error"]
    assert not data["suggested_fix"]


def test_live_context_chat_and_exclusions_accept_external_ids(live_app):
    client, orchestrator, incident_id = live_app
    response = client.post(f"/api/v1/incidents/{incident_id}/retrieve-context")
    assert response.status_code == 200, response.text
    assert response.json()["servicenow_results"]["incident"]["category"] == "Security"
    assert client.get(f"/api/v1/incidents/{incident_id}/excluded-items").status_code == 200
    response = client.post("/api/v1/chat/stream", json={
        "incident_id": incident_id, "message": "Explain this category", "conversation_history": [],
    })
    assert response.status_code == 200
    assert "Mapped incident summary" in response.text
    context = orchestrator._build_context_from_agent_data(
        incident_id, orchestrator.cache.get(incident_id)["servicenow_results"], {}, {}, {}, {}, {},
    )
    assert "Current incident: Database connection failure" in context
    assert "Category: Security" in context


@pytest.mark.parametrize(("path", "method", "payload"), [
    ("status", "put", {"status": "resolved"}),
    ("resolution", "post", {"resolution_text": "Restored certificate trust and confirmed queries recovered"}),
    ("resolution/draft", "post", None),
])
def test_live_writes_are_rejected_before_touching_mock_data(live_app, monkeypatch, path, method, payload):
    from backend.data import mock_data

    def forbidden(*args, **kwargs):
        pytest.fail("Live incident operations must not mutate mock CSV")

    monkeypatch.setattr(mock_data, "update_incident_status", forbidden)
    client, _, incident_id = live_app
    response = client.request(method, f"/api/v1/incidents/{incident_id}/{path}", json=payload)
    assert response.status_code == 405
    assert "read-only" in response.json()["detail"]


def test_live_api_upstream_failure_is_not_mock_success(live_app, transport):
    client, _, incident_id = live_app
    transport(lambda request: httpx.Response(401, text="upstream-private-detail"))
    for path in ("/incidents", f"/incidents/{incident_id}", f"/incidents/{incident_id}/details", "/admin/mttr-metrics"):
        response = client.get(f"/api/v1{path}")
        assert response.status_code == 502
        assert "HTTP 401" in response.json()["detail"]
        assert "upstream-private-detail" not in response.text


def test_live_unknown_severity_blocks_automation_without_breaking_response(live_app):
    from backend.models.automation import AutomationRules, CategoryAutomationRule

    _, orchestrator, incident_id = live_app
    orchestrator.automation_store.update_rules(AutomationRules(
        global_enabled=True,
        rules={"Security": CategoryAutomationRule(enabled=True, max_severity="critical")},
    ))
    decision = orchestrator._evaluate_automation_decision(
        incident_id,
        {"confidence": 1.0, "suggested_fix": {
            "id": "example-fix", "confidence_score": 1.0, "risk_level": "low",
        }},
        {"id": incident_id, "category": "Security", "severity": "unknown"},
    )
    assert decision.automated is False
    assert "severity 'unknown'" in decision.reason
    assert decision.severity is None
    assert decision.audit_record_id
