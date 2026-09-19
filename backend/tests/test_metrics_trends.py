"""Tests for the admin metrics trends endpoint."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from backend.api import routes
from backend.data.automation_store import AutomationStore
from backend.data.feedback_store import FeedbackStore
from backend.data.metrics_history_store import MetricsEventStore
from backend.data.resolution_store import ResolutionStore
from backend.main import app
from backend.models.automation import AutomationAuditRecord as StoredAutomationAuditRecord
from backend.models.incident import FeedbackRecord, ResolutionGrade, ResolutionRecord


client = TestClient(app)


@pytest.fixture
def temp_metrics_dependencies(tmp_path, monkeypatch):
    """Swap the admin metric stores with isolated temporary files."""
    feedback_store = FeedbackStore(tmp_path / "feedback.json")
    resolution_store = ResolutionStore(tmp_path / "resolutions.json")
    automation_store = AutomationStore(
        storage_path=tmp_path / "automation_rules.json",
        audit_storage_path=tmp_path / "automation_audit.json",
    )
    metrics_event_store = MetricsEventStore(tmp_path / "metrics_events.json")

    monkeypatch.setattr(routes, "feedback_store", feedback_store)
    monkeypatch.setattr(routes, "resolution_store", resolution_store)
    monkeypatch.setattr(routes, "automation_store", automation_store)
    monkeypatch.setattr(routes, "metrics_event_store", metrics_event_store)
    monkeypatch.setattr(routes.orchestrator, "feedback_store", feedback_store)
    monkeypatch.setattr(routes.orchestrator, "automation_store", automation_store)
    monkeypatch.setattr(routes.orchestrator, "metrics_event_store", metrics_event_store)

    return {
        "feedback_store": feedback_store,
        "resolution_store": resolution_store,
        "automation_store": automation_store,
        "metrics_event_store": metrics_event_store,
    }


def _series_points(series_list, key):
    series = next(series for series in series_list if series["key"] == key)
    return {point["date"]: point["value"] for point in series["points"]}


def test_metrics_trends_aggregates_daily_series(temp_metrics_dependencies, monkeypatch):
    """Metrics trends aggregate persisted data into daily series with gaps."""
    now = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
    today = now.date()
    yesterday = today - timedelta(days=1)
    two_days_ago = today - timedelta(days=2)

    monkeypatch.setattr(
        routes.mock_data,
        "MOCK_INCIDENTS",
        [
            {
                "id": "INC001",
                "title": "Database latency spike",
                "description": "Connections timing out",
                "severity": "high",
                "status": "resolved",
                "created_at": now - timedelta(days=1, hours=4),
                "updated_at": now - timedelta(days=1),
                "resolved_at": now - timedelta(days=1, hours=1),
                "affected_services": ["db-primary"],
                "assignee": "DB Team",
                "category": "Database",
            },
            {
                "id": "INC002",
                "title": "API gateway saturation",
                "description": "Traffic is slow",
                "severity": "medium",
                "status": "resolved",
                "created_at": now - timedelta(hours=5),
                "updated_at": now - timedelta(hours=1),
                "resolved_at": now - timedelta(hours=2),
                "affected_services": ["api-gateway"],
                "assignee": "Platform Team",
                "category": "Application",
            },
        ],
    )

    metrics_event_store = temp_metrics_dependencies["metrics_event_store"]
    metrics_event_store.record_returned(
        "incident",
        4,
        timestamp=datetime.combine(yesterday, datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=9),
    )
    metrics_event_store.record_excluded(
        "incident",
        timestamp=datetime.combine(yesterday, datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=10),
    )
    metrics_event_store.record_returned(
        "document",
        2,
        timestamp=datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=9),
    )

    feedback_store = temp_metrics_dependencies["feedback_store"]
    feedback_store._write(
        [
            FeedbackRecord(
                id="feedback-1",
                incident_id="INC001",
                rating="not_helpful",
                comment="Missing the root cause",
                created_at=datetime.combine(yesterday, datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=11),
            ).model_dump(mode="json"),
            FeedbackRecord(
                id="feedback-2",
                incident_id="INC002",
                rating="helpful",
                comment="Matched the fix",
                created_at=datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=11),
            ).model_dump(mode="json"),
        ]
    )

    resolution_store = temp_metrics_dependencies["resolution_store"]
    resolution_store._write(
        [
            ResolutionRecord(
                id="resolution-1",
                incident_id="INC001",
                resolution_text="Restarted the connection pool.",
                grade=ResolutionGrade(
                    score=0.8,
                    passed=True,
                    threshold=0.7,
                    feedback="Solid resolution",
                    issues=[],
                ),
                created_at=datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=13),
            ).model_dump(mode="json")
        ]
    )

    automation_store = temp_metrics_dependencies["automation_store"]
    automation_store._audit_store.append(
        StoredAutomationAuditRecord(
            id="audit-1",
            incident_id="INC001",
            automated=False,
            category="Database",
            mode="simulated",
            reasons=["confidence below threshold"],
            overall_confidence=0.7,
            fix_confidence=0.6,
            evaluated_at=datetime.combine(yesterday, datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=12),
            fix_id="rem-db-001",
            fix_title="Restart DB",
            script="echo safe",
        )
    )
    automation_store._audit_store.append(
        StoredAutomationAuditRecord(
            id="audit-2",
            incident_id="INC002",
            automated=True,
            category="Application",
            mode="simulated",
            reasons=["all checks passed"],
            overall_confidence=0.95,
            fix_confidence=0.93,
            evaluated_at=datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=12),
            fix_id="rem-app-001",
            fix_title="Restart API",
            script="echo safe-2",
        )
    )

    response = client.get("/api/v1/admin/metrics-trends?days=3")

    assert response.status_code == 200
    data = response.json()
    assert data["start_date"] == two_days_ago.isoformat()
    assert data["end_date"] == today.isoformat()

    overall_accuracy = _series_points(data["accuracy"], "overall")
    incident_accuracy = _series_points(data["accuracy"], "servicenow")
    document_accuracy = _series_points(data["accuracy"], "confluence")
    assert overall_accuracy[two_days_ago.isoformat()] is None
    assert incident_accuracy[yesterday.isoformat()] == 75.0
    assert document_accuracy[today.isoformat()] == 100.0

    mttr_overall = {point["date"]: point["value"] for point in data["mttr_overall"]["points"]}
    assert mttr_overall[yesterday.isoformat()] == 10800.0
    assert mttr_overall[today.isoformat()] == 10800.0
    severity_series = _series_points(data["mttr_by_severity"], "severity_high")
    assert severity_series[yesterday.isoformat()] == 10800.0

    helpful_rate = _series_points(data["feedback_rate"], "helpful_rate")
    not_helpful_rate = _series_points(data["feedback_rate"], "not_helpful_rate")
    assert helpful_rate[today.isoformat()] == 100.0
    assert not_helpful_rate[yesterday.isoformat()] == 100.0

    grade_points = {point["date"]: point["value"] for point in data["resolution_grade"]["points"]}
    assert grade_points[today.isoformat()] == 0.8

    automated_rate = _series_points(data["automation"], "automated_rate")
    blocked_rate = _series_points(data["automation"], "blocked_rate")
    assert automated_rate[today.isoformat()] == 100.0
    assert blocked_rate[yesterday.isoformat()] == 100.0


def test_metrics_trends_empty_window_returns_null_gaps(temp_metrics_dependencies, monkeypatch):
    """Empty windows preserve null points instead of inventing 100% values."""
    old_time = datetime.now(timezone.utc) - timedelta(days=10)
    monkeypatch.setattr(routes.mock_data, "MOCK_INCIDENTS", [])
    temp_metrics_dependencies["metrics_event_store"].record_returned(
        "incident",
        3,
        timestamp=old_time,
    )

    response = client.get("/api/v1/admin/metrics-trends?days=2")

    assert response.status_code == 200
    data = response.json()
    overall_accuracy = _series_points(data["accuracy"], "overall")
    assert list(overall_accuracy.values()) == [None, None]
    assert data["mttr_by_severity"] == []
    assert data["mttr_by_category"] == []
    assert all(point["value"] is None for point in data["mttr_overall"]["points"])
    assert all(point["value"] is None for point in data["resolution_grade"]["points"])
