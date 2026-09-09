"""Tests for MTTR (mean-time-to-resolution) metrics."""
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from backend.main import app
from backend.api.routes import _format_duration
from backend.data import mock_data


client = TestClient(app)


def test_get_mttr_metrics_structure():
    """Test MTTR metrics endpoint returns the documented structure."""
    response = client.get("/api/v1/admin/mttr-metrics")

    assert response.status_code == 200
    data = response.json()

    assert "overall_mean_seconds" in data
    assert "overall_mean_display" in data
    assert "resolved_count" in data
    assert "total_incidents" in data
    assert "by_severity" in data
    assert "by_category" in data

    assert data["total_incidents"] == len(mock_data.MOCK_INCIDENTS)
    assert data["resolved_count"] <= data["total_incidents"]

    for breakdown in data["by_severity"] + data["by_category"]:
        assert "label" in breakdown
        assert "resolved_count" in breakdown
        assert "mean_seconds" in breakdown
        assert "mean_display" in breakdown
        assert breakdown["mean_seconds"] >= 0


def test_get_mttr_metrics_seeded_data():
    """Seeded mock data includes resolved incidents, so MTTR is computed."""
    response = client.get("/api/v1/admin/mttr-metrics")

    assert response.status_code == 200
    data = response.json()

    assert data["resolved_count"] > 0
    assert data["overall_mean_seconds"] is not None
    assert data["overall_mean_seconds"] > 0
    assert data["overall_mean_display"]
    assert len(data["by_severity"]) > 0
    assert len(data["by_category"]) > 0


def test_mttr_calculation_matches_known_timestamps():
    """MTTR must equal the mean of (resolved_at - created_at) over resolved incidents."""
    expected_times = [
        (inc["resolved_at"] - inc["created_at"]).total_seconds()
        for inc in mock_data.MOCK_INCIDENTS
        if inc.get("resolved_at") and inc.get("created_at")
        and (inc["resolved_at"] - inc["created_at"]).total_seconds() >= 0
    ]

    response = client.get("/api/v1/admin/mttr-metrics")
    data = response.json()

    assert data["resolved_count"] == len(expected_times)
    expected_mean = sum(expected_times) / len(expected_times)
    assert abs(data["overall_mean_seconds"] - expected_mean) < 1.0


def test_resolving_incident_sets_resolved_at():
    """Marking an incident resolved stamps resolved_at."""
    incident = next(
        inc for inc in mock_data.MOCK_INCIDENTS if inc["status"] != "resolved"
    )
    incident_id = incident["id"]

    response = client.put(
        f"/api/v1/incidents/{incident_id}/status", json={"status": "resolved"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "resolved"
    assert data["resolved_at"] is not None
    resolved_at = datetime.fromisoformat(data["resolved_at"])
    assert resolved_at >= datetime.fromisoformat(data["created_at"])


def test_reopening_incident_clears_resolved_at():
    """Moving an incident away from resolved clears resolved_at."""
    incident = next(
        inc for inc in mock_data.MOCK_INCIDENTS if inc["status"] == "resolved"
    )
    incident_id = incident["id"]

    response = client.put(
        f"/api/v1/incidents/{incident_id}/status", json={"status": "investigating"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "investigating"
    assert data["resolved_at"] is None


def test_format_duration():
    """Duration formatting is human readable across magnitudes."""
    assert _format_duration(45) == "45s"
    assert _format_duration(5 * 60) == "5m"
    assert _format_duration(3 * 3600 + 12 * 60) == "3h 12m"
    assert (
        _format_duration(timedelta(days=2, hours=5).total_seconds()) == "2d 5h"
    )
