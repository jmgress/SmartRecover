import asyncio
import time
from unittest.mock import MagicMock, patch

import pytest

from backend.agents.orchestrator import OrchestratorAgent


def _delayed_query(result, delay_seconds: float = 0.15):
    async def _query(*args, **kwargs):
        await asyncio.sleep(delay_seconds)
        return result

    return _query


@pytest.mark.asyncio
async def test_resolve_runs_subagents_in_parallel():
    with patch("backend.agents.orchestrator.get_llm", return_value=MagicMock()):
        orchestrator = OrchestratorAgent()

    async def _summary(*args, **kwargs):
        return "parallel summary"

    orchestrator._generate_summary_with_llm = _summary

    orchestrator.servicenow_agent.query = _delayed_query(
        {"source": "servicenow", "similar_incidents": [{"id": "INC002"}], "resolutions": ["Restart DB"]}
    )
    orchestrator.knowledge_base_agent.query = _delayed_query(
        {"source": "confluence", "documents": [{"title": "KB"}], "knowledge_base_articles": ["KB article"]}
    )
    orchestrator.change_agent.query = _delayed_query({"source": "change_correlation", "high_correlation_changes": []})
    orchestrator.logs_agent.query = _delayed_query({"source": "logs", "logs": []})
    orchestrator.events_agent.query = _delayed_query({"source": "events", "events": []})
    orchestrator.metrics_agent.query = _delayed_query({"source": "metrics", "anomalies": []})
    orchestrator.remediation_agent.query = _delayed_query({"source": "remediation", "remediations": []})

    started_at = time.perf_counter()
    response = await orchestrator.resolve("INC_PARALLEL_001", "How do we fix this?")
    elapsed = time.perf_counter() - started_at

    assert response.summary == "parallel summary"
    assert elapsed < 0.75


@pytest.mark.asyncio
async def test_resolve_isolates_agent_failures():
    with patch("backend.agents.orchestrator.get_llm", return_value=MagicMock()):
        orchestrator = OrchestratorAgent()

    async def _summary(*args, **kwargs):
        return "summary despite failure"

    async def _failing_kb_query(*args, **kwargs):
        raise RuntimeError("kb unavailable")

    orchestrator._generate_summary_with_llm = _summary
    orchestrator.servicenow_agent.query = _delayed_query(
        {"source": "servicenow", "similar_incidents": [{"id": "INC002"}], "resolutions": ["Retry request"]},
        delay_seconds=0.01,
    )
    orchestrator.knowledge_base_agent.query = _failing_kb_query
    orchestrator.change_agent.query = _delayed_query({"source": "change_correlation", "high_correlation_changes": []}, 0.01)
    orchestrator.logs_agent.query = _delayed_query({"source": "logs", "logs": []}, 0.01)
    orchestrator.events_agent.query = _delayed_query({"source": "events", "events": []}, 0.01)
    orchestrator.metrics_agent.query = _delayed_query({"source": "metrics", "anomalies": []}, 0.01)
    orchestrator.remediation_agent.query = _delayed_query({"source": "remediation", "remediations": []}, 0.01)

    response = await orchestrator.resolve("INC_PARALLEL_FAIL", "Investigate")
    cached_data = orchestrator.cache.get("INC_PARALLEL_FAIL")

    assert response.summary == "summary despite failure"
    assert response.resolution_steps == ["Retry request"]
    assert cached_data["confluence_results"]["error"] == "kb unavailable"
