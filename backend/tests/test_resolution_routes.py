"""Tests for the resolution API routes and the resolved-status quality gate."""
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from backend.api import routes
from backend.data import mock_data
from backend.data.resolution_store import ResolutionStore
from backend.main import app
from backend.models.incident import ResolutionGrade

client = TestClient(app)

INCIDENT_ID = mock_data.MOCK_INCIDENTS[0]["id"]


def _passing_grade() -> ResolutionGrade:
    return ResolutionGrade(
        score=0.9, passed=True, threshold=0.7, feedback="Good resolution.", issues=[]
    )


def _failing_grade() -> ResolutionGrade:
    return ResolutionGrade(
        score=0.1,
        passed=False,
        threshold=0.7,
        feedback="Too vague.",
        issues=["Generic phrase"],
    )


@pytest.fixture
def temp_resolution_store(tmp_path, monkeypatch):
    store = ResolutionStore(tmp_path / "resolutions.json")
    monkeypatch.setattr(routes, "resolution_store", store)
    return store


class TestResolutionStore:
    def test_save_and_get_latest(self, tmp_path):
        store = ResolutionStore(tmp_path / "resolutions.json")
        assert store.get_latest_for_incident("INC001") is None
        assert store.has_passing_resolution("INC001") is False

        store.save("INC001", "Detailed resolution text here.", _passing_grade())

        latest = store.get_latest_for_incident("INC001")
        assert latest is not None
        assert latest.resolution_text == "Detailed resolution text here."
        assert store.has_passing_resolution("INC001") is True
        assert store.get_latest_for_incident("INC999") is None

    def test_recovers_from_corrupt_data(self, tmp_path):
        storage_path = tmp_path / "resolutions.json"
        storage_path.write_text("{not valid JSON", encoding="utf-8")
        store = ResolutionStore(storage_path)
        store.save("INC001", "Detailed resolution text here.", _passing_grade())
        assert store.has_passing_resolution("INC001") is True


class TestDraftEndpoint:
    def test_draft_returns_agent_output(self, temp_resolution_store, monkeypatch):
        monkeypatch.setattr(
            routes.resolution_agent,
            "draft_resolution",
            AsyncMock(return_value="Drafted resolution."),
        )
        response = client.post(f"/api/v1/incidents/{INCIDENT_ID}/resolution/draft")
        assert response.status_code == 200
        body = response.json()
        assert body["incident_id"] == INCIDENT_ID
        assert body["draft"] == "Drafted resolution."
        assert body["source"] == "resolution_agent"

    def test_draft_unknown_incident_404(self, temp_resolution_store):
        assert client.post("/api/v1/incidents/NOPE/resolution/draft").status_code == 404


class TestSubmitEndpoint:
    def test_failing_grade_is_returned_without_saving(self, temp_resolution_store, monkeypatch):
        monkeypatch.setattr(
            routes.resolution_agent,
            "grade_resolution",
            AsyncMock(return_value=_failing_grade()),
        )
        response = client.post(
            f"/api/v1/incidents/{INCIDENT_ID}/resolution",
            json={"resolution_text": "resolved"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["grade"]["passed"] is False
        assert body["record"] is None
        assert temp_resolution_store.get_latest_for_incident(INCIDENT_ID) is None

    def test_passing_grade_saves_and_resolves(self, temp_resolution_store, monkeypatch):
        monkeypatch.setattr(
            routes.resolution_agent,
            "grade_resolution",
            AsyncMock(return_value=_passing_grade()),
        )
        status_calls = []
        monkeypatch.setattr(
            routes.mock_data,
            "update_incident_status",
            lambda incident_id, status: status_calls.append((incident_id, status)) or True,
        )
        response = client.post(
            f"/api/v1/incidents/{INCIDENT_ID}/resolution",
            json={"resolution_text": "Root cause was X; fixed via Y; verified with Z."},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["grade"]["passed"] is True
        assert body["record"]["incident_id"] == INCIDENT_ID
        assert status_calls == [(INCIDENT_ID, "resolved")]
        assert temp_resolution_store.has_passing_resolution(INCIDENT_ID) is True

    def test_empty_resolution_is_rejected_by_validation(self, temp_resolution_store):
        response = client.post(
            f"/api/v1/incidents/{INCIDENT_ID}/resolution",
            json={"resolution_text": ""},
        )
        assert response.status_code == 422

    def test_unknown_incident_404(self, temp_resolution_store):
        response = client.post(
            "/api/v1/incidents/NOPE/resolution",
            json={"resolution_text": "Something descriptive enough."},
        )
        assert response.status_code == 404


class TestGetResolutionEndpoint:
    def test_returns_latest_record(self, temp_resolution_store):
        temp_resolution_store.save(INCIDENT_ID, "Stored resolution text.", _passing_grade())
        response = client.get(f"/api/v1/incidents/{INCIDENT_ID}/resolution")
        assert response.status_code == 200
        assert response.json()["resolution_text"] == "Stored resolution text."

    def test_404_when_no_resolution(self, temp_resolution_store):
        assert client.get(f"/api/v1/incidents/{INCIDENT_ID}/resolution").status_code == 404


class TestResolvedStatusGate:
    def test_status_resolved_blocked_without_passing_resolution(self, temp_resolution_store):
        response = client.put(
            f"/api/v1/incidents/{INCIDENT_ID}/status",
            json={"status": "resolved"},
        )
        assert response.status_code == 400
        assert "resolution" in response.json()["detail"].lower()

    def test_status_resolved_allowed_with_passing_resolution(
        self, temp_resolution_store, monkeypatch
    ):
        temp_resolution_store.save(INCIDENT_ID, "Detailed resolution text.", _passing_grade())
        monkeypatch.setattr(
            routes.mock_data, "update_incident_status", lambda incident_id, status: True
        )
        response = client.put(
            f"/api/v1/incidents/{INCIDENT_ID}/status",
            json={"status": "resolved"},
        )
        assert response.status_code == 200

    def test_other_statuses_not_gated(self, temp_resolution_store, monkeypatch):
        monkeypatch.setattr(
            routes.mock_data, "update_incident_status", lambda incident_id, status: True
        )
        response = client.put(
            f"/api/v1/incidents/{INCIDENT_ID}/status",
            json={"status": "investigating"},
        )
        assert response.status_code == 200
