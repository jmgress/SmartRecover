"""Tests for the suggested fix selection in the orchestrator."""

import pytest

from backend.agents.orchestrator import OrchestratorAgent
from backend.models.incident import AgentResponse, SuggestedFix


@pytest.fixture(scope="module")
def orchestrator():
    return OrchestratorAgent()


REMEDIATIONS = {
    "source": "remediation_engine",
    "incident_id": "INC001",
    "remediations": [
        {
            "id": "rem-db-002",
            "title": "Clear Database Query Cache",
            "description": "Clears the query cache.",
            "script": "mysql -e 'RESET QUERY CACHE;'",
            "risk_level": "low",
            "estimated_duration": "30 seconds",
            "prerequisites": ["Read-only mode enabled"],
            "confidence_score": 0.72,
        },
        {
            "id": "rem-db-001",
            "title": "Restart Database Connection Pool",
            "description": "Restarts the pool.",
            "script": "kubectl rollout restart deployment/db-connection-pool",
            "risk_level": "low",
            "estimated_duration": "2-3 minutes",
            "prerequisites": ["Database backup completed"],
            "confidence_score": 0.85,
        },
    ],
    "total_count": 2,
}


def test_selects_highest_confidence_remediation(orchestrator):
    fix = orchestrator._select_suggested_fix(REMEDIATIONS, {}, {})
    assert fix is not None
    assert fix["id"] == "rem-db-001"
    assert fix["source"] == "remediation_engine"
    assert fix["script"] == "kubectl rollout restart deployment/db-connection-pool"
    assert "rationale" in fix


def test_rationale_includes_change_and_incident_evidence(orchestrator):
    changes = {
        "top_suspect": {
            "change_id": "CHG100",
            "description": "DB config change",
            "correlation_score": 0.9,
        }
    }
    servicenow = {"similar_incidents": [{"id": "INC000", "title": "Prior DB outage"}]}
    fix = orchestrator._select_suggested_fix(REMEDIATIONS, changes, servicenow)
    assert "CHG100" in fix["rationale"]
    assert "1 similar historical incident" in fix["rationale"]


def test_returns_none_without_remediations(orchestrator):
    assert orchestrator._select_suggested_fix({}, {}, {}) is None
    assert orchestrator._select_suggested_fix({"remediations": []}, {}, {}) is None


def test_suggested_fix_validates_against_model(orchestrator):
    fix = orchestrator._select_suggested_fix(REMEDIATIONS, {}, {})
    validated = SuggestedFix(**fix)
    assert validated.confidence_score == 0.85


def test_agent_response_accepts_optional_suggested_fix():
    response = AgentResponse(
        incident_id="INC001",
        resolution_steps=[],
        related_knowledge=[],
        correlated_changes=[],
        summary="test",
        confidence=0.5,
    )
    assert response.suggested_fix is None

    fix = SuggestedFix(
        id="rem-db-001",
        title="Restart Database Connection Pool",
        description="Restarts the pool.",
        script="kubectl rollout restart deployment/db-connection-pool",
        risk_level="low",
        confidence_score=0.85,
        rationale="Highest-confidence remediation",
    )
    response_with_fix = response.model_copy(update={"suggested_fix": fix})
    assert response_with_fix.suggested_fix.id == "rem-db-001"


@pytest.mark.asyncio
async def test_cached_agent_data_includes_suggested_fix(orchestrator):
    agent_data = await orchestrator._get_or_fetch_agent_data("INC001", "")
    assert "suggested_fix" in agent_data
    fix = agent_data["suggested_fix"]
    if fix is not None:
        assert fix["script"]
        assert fix["rationale"]
