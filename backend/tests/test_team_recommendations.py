"""Tests for deriving recommended teams from ticket, KB, and change correlation data."""

import pytest

from backend.agents.orchestrator import OrchestratorAgent
from backend.models.incident import AgentResponse, TeamRecommendation


@pytest.fixture(scope="module")
def orchestrator():
    return OrchestratorAgent()


SERVICENOW = {
    "source": "servicenow",
    "incident_id": "INC001",
    "similar_incidents": [
        {
            "ticket_id": "SNOW100",
            "type": "similar_incident",
            "resolution": "Restarted pods",
            "resolved_by_team": "platform-team",
        },
        {
            "ticket_id": "SNOW101",
            "type": "similar_incident",
            "resolution": "Scaled consumers",
            "resolved_by_team": "dba-team",
        },
    ],
    "resolutions": ["Restarted pods", "Scaled consumers"],
}

CONFLUENCE = {
    "source": "confluence",
    "incident_id": "INC001",
    "documents": [
        {
            "doc_id": "CONF100",
            "title": "Cache Troubleshooting Guide",
            "content": "Check cache health",
            "owning_team": "platform-team",
        },
        {
            "doc_id": "CONF101",
            "title": "Auth Runbook",
            "content": "Check auth health",
            "owning_team": "identity-team",
        },
    ],
    "knowledge_base_articles": ["Cache Troubleshooting Guide", "Auth Runbook"],
}

CHANGES = {
    "source": "change_correlation",
    "incident_id": "INC001",
    "high_correlation_changes": [
        {
            "change_id": "CHG100",
            "description": "schema update",
            "correlation_score": 0.92,
            "implementing_team": "devops-team",
        }
    ],
    "medium_correlation_changes": [
        {
            "change_id": "CHG101",
            "description": "config tweak",
            "correlation_score": 0.6,
            "implementing_team": "ops-team",
        }
    ],
}


def _teams(recommendations):
    return {r["team"] for r in recommendations}


def test_derives_teams_from_all_sources(orchestrator):
    result = orchestrator._derive_recommended_teams(
        "INC001", SERVICENOW, CONFLUENCE, CHANGES
    )
    assert _teams(result) == {
        "platform-team",
        "dba-team",
        "identity-team",
        "devops-team",
    }


def test_merges_duplicate_teams_across_sources(orchestrator):
    result = orchestrator._derive_recommended_teams(
        "INC001", SERVICENOW, CONFLUENCE, CHANGES
    )
    platform = next(r for r in result if r["team"] == "platform-team")
    assert set(platform["sources"]) == {"servicenow", "knowledge_base"}
    assert len(platform["reasons"]) == 2


def test_only_high_correlation_changes_recommend_teams(orchestrator):
    result = orchestrator._derive_recommended_teams("INC001", {}, {}, CHANGES)
    assert _teams(result) == {"devops-team"}


def test_excludes_incident_assignee_team(orchestrator):
    # INC001's assignee in mock data is used for exclusion
    incident = orchestrator._get_incident_record("INC001")
    own_team = incident.get("assignee")
    assert own_team
    servicenow = {
        "similar_incidents": [
            {"ticket_id": "SNOW1", "resolved_by_team": own_team},
            {"ticket_id": "SNOW2", "resolved_by_team": "security-team"},
        ]
    }
    result = orchestrator._derive_recommended_teams("INC001", servicenow, {}, {})
    assert _teams(result) == {"security-team"}


def test_handles_empty_and_missing_team_data(orchestrator):
    servicenow = {"similar_incidents": [{"ticket_id": "SNOW1"}]}
    confluence = {"documents": [{"doc_id": "CONF1", "title": "Doc", "owning_team": ""}]}
    result = orchestrator._derive_recommended_teams(
        "INC001", servicenow, confluence, {}
    )
    assert result == []


def test_final_response_includes_recommended_teams(orchestrator):
    response = orchestrator._build_final_response(
        incident_id="INC001",
        servicenow=SERVICENOW,
        confluence=CONFLUENCE,
        changes=CHANGES,
        remediations={},
        summary="test summary",
    )
    assert "recommended_teams" in response
    assert _teams(response["recommended_teams"]) >= {"devops-team"}
    # Validate the response shape parses into the Pydantic model
    agent_response = AgentResponse(**{**response, "correlated_changes": []})
    assert all(
        isinstance(team, TeamRecommendation)
        for team in agent_response.recommended_teams
    )


def test_mock_data_carries_team_fields():
    from backend.data.mock_data import (
        MOCK_SERVICENOW_TICKETS,
        MOCK_CONFLUENCE_DOCS,
        MOCK_CHANGE_CORRELATIONS,
    )

    tickets = [t for ts in MOCK_SERVICENOW_TICKETS.values() for t in ts]
    docs = [d for ds in MOCK_CONFLUENCE_DOCS.values() for d in ds]
    changes = [c for cs in MOCK_CHANGE_CORRELATIONS.values() for c in cs]

    assert tickets and all(t.get("resolved_by_team") for t in tickets)
    assert docs and all(d.get("owning_team") for d in docs)
    assert changes and all(c.get("implementing_team") for c in changes)
