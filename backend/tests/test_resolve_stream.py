"""Integration and unit tests for streaming resolution endpoint (SSE)."""
import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.agents.orchestrator import OrchestratorAgent


client = TestClient(app)


@pytest.mark.asyncio
async def test_orchestrator_resolve_stream_events():
    """Test that OrchestratorAgent.resolve_stream yields expected SSE events in order."""
    mock_llm = MagicMock()

    async def mock_stream(*args, **kwargs):
        chunks = ["Based on the analysis, ", "restart the ", "database service."]
        for chunk in chunks:
            mock_chunk = MagicMock()
            mock_chunk.content = chunk
            yield mock_chunk

    mock_llm.astream = mock_stream

    with patch("backend.agents.orchestrator.get_llm", return_value=mock_llm):
        orchestrator = OrchestratorAgent()
        orchestrator.llm = mock_llm

        events = []
        async for event in orchestrator.resolve_stream(incident_id="INC001", user_query="How to fix?"):
            events.append(event)

        # Check event types collected
        event_types = [e["event"] for e in events]
        assert "agent_start" in event_types
        assert "agent_complete" in event_types
        assert "synthesis_start" in event_types
        assert "llm_chunk" in event_types
        assert "complete" in event_types

        # Verify all agents ran
        agent_completes = [e["agent"] for e in events if e["event"] == "agent_complete"]
        expected_agents = ["servicenow", "confluence", "change", "logs", "events", "metrics", "remediation"]
        for agent in expected_agents:
            assert agent in agent_completes

        # Verify LLM chunks
        chunks = [e["content"] for e in events if e["event"] == "llm_chunk"]
        assert "".join(chunks) == "Based on the analysis, restart the database service."

        # Verify final complete event result
        complete_event = next(e for e in events if e["event"] == "complete")
        final_result = complete_event["result"]
        assert final_result["incident_id"] == "INC001"
        assert final_result["summary"] == "Based on the analysis, restart the database service."
        assert "resolution_steps" in final_result
        assert "confidence" in final_result


def test_resolve_stream_post_endpoint():
    """Test POST /api/v1/resolve/stream SSE endpoint."""
    response = client.post(
        "/api/v1/resolve/stream",
        json={"incident_id": "INC001", "user_query": "Test stream"}
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    lines = response.text.split("\n\n")
    data_lines = [line.replace("data: ", "").strip() for line in lines if line.startswith("data: ")]

    assert len(data_lines) > 0
    assert data_lines[-1] == "[DONE]"

    parsed_events = []
    for line in data_lines[:-1]:
        parsed_events.append(json.loads(line))

    event_names = [e["event"] for e in parsed_events]
    assert "agent_start" in event_names
    assert "agent_complete" in event_names
    assert "synthesis_start" in event_names
    assert "complete" in event_names


def test_resolve_stream_get_endpoint():
    """Test GET /api/v1/resolve/stream SSE endpoint."""
    response = client.get("/api/v1/resolve/stream?incident_id=INC001&user_query=Test")
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    lines = response.text.split("\n\n")
    data_lines = [line.replace("data: ", "").strip() for line in lines if line.startswith("data: ")]

    assert len(data_lines) > 0
    assert data_lines[-1] == "[DONE]"


def test_resolve_stream_not_found():
    """Test resolve/stream endpoint returns 404 for invalid incident ID."""
    response = client.post(
        "/api/v1/resolve/stream",
        json={"incident_id": "NONEXISTENT", "user_query": ""}
    )
    assert response.status_code == 404
