"""Focused route tests for canonical automation rule APIs."""

import pytest
from fastapi.testclient import TestClient

from backend.data.automation_store import AutomationStore
from backend.main import app
from backend.utils.categorization import CATEGORIES


client = TestClient(app)


@pytest.fixture
def temp_automation_store(tmp_path, monkeypatch):
    store = AutomationStore(storage_path=tmp_path / "automation_rules.json")
    monkeypatch.setattr("backend.api.routes.automation_store", store)
    monkeypatch.setattr("backend.api.routes.orchestrator.automation_store", store)
    return store


def test_automation_rules_get_put_round_trip(temp_automation_store):
    initial = client.get("/api/v1/admin/automation-rules")
    assert initial.status_code == 200
    assert set(initial.json()["categories"]) == set(CATEGORIES)

    payload = {
        "global_enabled": True,
        "rules": {
            "Database": {
                "enabled": True,
                "confidence_threshold": 0.6,
                "min_fix_confidence": 0.65,
                "max_risk_level": "low",
                "max_severity": "medium",
            }
        },
    }

    update = client.put("/api/v1/admin/automation-rules", json=payload)
    assert update.status_code == 200

    reloaded = client.get("/api/v1/admin/automation-rules")
    assert reloaded.status_code == 200
    data = reloaded.json()
    database_rule = data["rules"]["rules"]["Database"]
    assert data["rules"]["global_enabled"] is True
    assert database_rule["enabled"] is True
    assert database_rule["confidence_threshold"] == 0.6
    assert database_rule["min_fix_confidence"] == 0.65


def test_automation_rules_reject_unknown_category(temp_automation_store):
    response = client.put(
        "/api/v1/admin/automation-rules",
        json={
            "global_enabled": True,
            "rules": {"UnknownCategory": {"enabled": True}},
        },
    )
    assert response.status_code == 400
    assert "Unknown automation categories" in response.json()["detail"]


def test_automation_rules_reject_threshold_above_one(temp_automation_store):
    response = client.put(
        "/api/v1/admin/automation-rules",
        json={
            "global_enabled": True,
            "rules": {
                "Database": {
                    "enabled": True,
                    "confidence_threshold": 1.5,
                }
            },
        },
    )
    assert response.status_code == 400
    assert "less than or equal to 1" in response.json()["detail"]
