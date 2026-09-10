"""Tests for the resolution agent's drafting and grading."""
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.agents.resolution_agent import ResolutionAgent
from backend.data import mock_data

INCIDENT_ID = mock_data.MOCK_INCIDENTS[0]["id"]


def _agent_without_llm() -> ResolutionAgent:
    """Agent whose LLM raises, forcing heuristic/fallback paths."""
    agent = ResolutionAgent()
    failing_llm = MagicMock()
    failing_llm.ainvoke = AsyncMock(side_effect=RuntimeError("no llm"))
    agent._llm = failing_llm
    return agent


def _agent_with_llm_response(content: str) -> ResolutionAgent:
    agent = ResolutionAgent()
    llm = MagicMock()
    llm.ainvoke = AsyncMock(return_value=MagicMock(content=content))
    agent._llm = llm
    return agent


def _descriptive_resolution() -> str:
    incident = mock_data.MOCK_INCIDENTS[0]
    service = (incident.get("affected_services") or ["the service"])[0]
    return (
        f"Root cause was a defect affecting {service} described in the incident "
        f"'{incident['title']}'. We applied a configuration rollback, restarted the "
        f"affected components, and verified recovery through health checks and monitoring dashboards."
    )


class TestHeuristicGrading:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("junk", ["resolved", "Fixed", "done", "it works now", "OK"])
    async def test_generic_phrases_are_rejected(self, junk):
        agent = _agent_without_llm()
        grade = await agent.grade_resolution(INCIDENT_ID, junk)
        assert grade.passed is False
        assert grade.score < grade.threshold
        assert grade.issues

    @pytest.mark.asyncio
    async def test_short_text_is_rejected(self):
        agent = _agent_without_llm()
        grade = await agent.grade_resolution(INCIDENT_ID, "rebooted box")
        assert grade.passed is False
        assert any("too short" in issue for issue in grade.issues)

    @pytest.mark.asyncio
    async def test_repetitive_text_is_rejected(self):
        agent = _agent_without_llm()
        grade = await agent.grade_resolution(INCIDENT_ID, "fix fix fix fix fix fix fix fix fix fix")
        assert grade.passed is False

    @pytest.mark.asyncio
    async def test_unrelated_text_is_rejected(self):
        agent = _agent_without_llm()
        grade = await agent.grade_resolution(
            INCIDENT_ID,
            "Watered plants weekly, painted fence, mowed lawn thoroughly yesterday afternoon outside.",
        )
        assert grade.passed is False

    @pytest.mark.asyncio
    async def test_descriptive_resolution_passes_without_llm(self):
        agent = _agent_without_llm()
        grade = await agent.grade_resolution(INCIDENT_ID, _descriptive_resolution())
        assert grade.passed is True
        assert grade.score >= grade.threshold


class TestLLMGrading:
    @pytest.mark.asyncio
    async def test_llm_score_and_feedback_are_used(self):
        payload = json.dumps(
            {"score": 0.9, "feedback": "Thorough resolution.", "issues": []}
        )
        agent = _agent_with_llm_response(payload)
        grade = await agent.grade_resolution(INCIDENT_ID, _descriptive_resolution())
        assert grade.passed is True
        assert grade.score == 0.9
        assert grade.feedback == "Thorough resolution."

    @pytest.mark.asyncio
    async def test_llm_can_fail_a_plausible_resolution(self):
        payload = json.dumps(
            {"score": 0.3, "feedback": "Does not match recorded data.", "issues": ["Wrong service"]}
        )
        agent = _agent_with_llm_response(payload)
        grade = await agent.grade_resolution(INCIDENT_ID, _descriptive_resolution())
        assert grade.passed is False
        assert grade.issues == ["Wrong service"]

    @pytest.mark.asyncio
    async def test_unparseable_llm_response_falls_back_to_heuristic(self):
        agent = _agent_with_llm_response("I think it is fine.")
        grade = await agent.grade_resolution(INCIDENT_ID, _descriptive_resolution())
        assert grade.passed is True  # heuristic pass


class TestDrafting:
    @pytest.mark.asyncio
    async def test_draft_uses_llm_output(self):
        agent = _agent_with_llm_response("Root cause was X; we fixed Y and verified Z.")
        draft = await agent.draft_resolution(INCIDENT_ID)
        assert draft == "Root cause was X; we fixed Y and verified Z."

    @pytest.mark.asyncio
    async def test_draft_falls_back_to_template_without_llm(self):
        agent = _agent_without_llm()
        draft = await agent.draft_resolution(INCIDENT_ID)
        assert "Root cause" in draft
        assert "Verification" in draft

    @pytest.mark.asyncio
    async def test_query_contract(self):
        agent = _agent_without_llm()
        result = await agent.query(INCIDENT_ID, "")
        assert result["source"] == "resolution_agent"
        assert result["incident_id"] == INCIDENT_ID
        assert result["draft"]
