"""Tests for persisted resolution feedback."""
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.api import routes
from backend.data.feedback_store import FeedbackStore
from backend.main import app
from backend.models.incident import FeedbackRequest


def test_feedback_store_persists_and_filters_records(tmp_path):
    """Feedback is durable and limited to the requested incidents."""
    store = FeedbackStore(tmp_path / "feedback.json")
    store.save(FeedbackRequest(incident_id="INC001", rating="helpful", comment="Worked well"))
    store.save(FeedbackRequest(incident_id="INC002", rating="not_helpful"))

    records = store.get_for_incidents(["INC001"])

    assert len(records) == 1
    assert records[0].incident_id == "INC001"
    assert records[0].rating == "helpful"
    assert records[0].comment == "Worked well"


def test_submit_feedback_endpoint(monkeypatch, tmp_path):
    """The feedback endpoint validates and persists feedback."""
    store = FeedbackStore(tmp_path / "feedback.json")
    monkeypatch.setattr(routes, "feedback_store", store)
    client = TestClient(app)

    response = client.post(
        "/api/v1/feedback",
        json={"incident_id": "INC001", "rating": "helpful", "comment": "Resolved the issue"},
    )

    assert response.status_code == 201
    assert response.json()["rating"] == "helpful"
    assert store.get_for_incidents(["INC001"])[0].comment == "Resolved the issue"
    assert client.post("/api/v1/feedback", json={"incident_id": "INC001", "rating": "bad"}).status_code == 422


def test_feedback_is_added_to_future_resolution_context(tmp_path):
    """Feedback for similar incidents is made available to later resolutions."""
    from backend.agents.orchestrator import OrchestratorAgent

    store = FeedbackStore(tmp_path / "feedback.json")
    store.save(FeedbackRequest(incident_id="INC002", rating="helpful", comment="Restart fixed it"))
    orchestrator = OrchestratorAgent()
    orchestrator.feedback_store = store

    context = orchestrator._build_context_from_agent_data(
        "INC001",
        {"similar_incidents": [{"id": "INC002", "title": "Similar outage"}]},
        {},
        {},
        {},
        {},
        {},
    )

    assert "OPERATOR FEEDBACK FROM PRIOR RESOLUTIONS" in context
    assert "Rating: helpful; Comment: Restart fixed it" in context


@pytest.mark.asyncio
async def test_feedback_is_included_in_resolution_synthesis(tmp_path):
    """Synthesis includes feedback from a similar incident."""
    from backend.agents.orchestrator import OrchestratorAgent

    store = FeedbackStore(tmp_path / "feedback.json")
    store.save(FeedbackRequest(incident_id="INC002", rating="helpful", comment="Restart fixed it"))
    orchestrator = OrchestratorAgent()
    orchestrator.feedback_store = store
    orchestrator.llm = MagicMock()
    orchestrator.llm.ainvoke = AsyncMock(return_value=MagicMock(content="Summary"))

    await orchestrator._generate_summary_with_llm(
        "INC001",
        "How do I resolve this?",
        {"similar_incidents": [{"id": "INC002", "title": "Similar outage"}]},
        {},
        {},
        None,
    )

    prompt = orchestrator.llm.ainvoke.call_args.args[0][1].content
    assert "OPERATOR FEEDBACK FROM PRIOR RESOLUTIONS" in prompt
    assert "Rating: helpful; Comment: Restart fixed it" in prompt
