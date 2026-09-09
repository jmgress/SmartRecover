"""Tests for category-based auto-remediation gating."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from backend.agents.orchestrator import OrchestratorAgent
from backend.data.automation_store import AutomationStore
from backend.models.incident import AutomationConfig, CategoryAutomationRule


@pytest.fixture
def automation_store(tmp_path: Path) -> AutomationStore:
    return AutomationStore(storage_path=tmp_path / "automation_rules.json")


@pytest.fixture
def orchestrator(automation_store: AutomationStore) -> OrchestratorAgent:
    with patch("backend.agents.orchestrator.get_llm", return_value=MagicMock()):
        return OrchestratorAgent(automation_store=automation_store)


def test_automation_gate_approves_database_incident(orchestrator: OrchestratorAgent, automation_store: AutomationStore):
    automation_store.save_config(
        AutomationConfig(
            global_enabled=True,
            rules=[
                CategoryAutomationRule(
                    category="Database",
                    enabled=True,
                    threshold=0.6,
                    max_risk_level="low",
                    max_severity="medium",
                )
            ],
        )
    )

    decision = orchestrator._evaluate_automation_decision(
        "INC009",
        {
            "incident_id": "INC009",
            "summary": "Restart the connection pool",
            "resolution_steps": [],
            "related_knowledge": [],
            "correlated_changes": [],
            "confidence": 0.7,
            "suggested_fix": {
                "id": "rem-db-001",
                "title": "Restart Database Connection Pool",
                "description": "Restart the pool",
                "script": "kubectl rollout restart deployment/db-connection-pool",
                "risk_level": "low",
                "estimated_duration": "2 minutes",
                "prerequisites": [],
                "confidence_score": 0.85,
                "rationale": "Highest-confidence remediation",
                "source": "remediation_engine",
            },
        },
    )

    assert decision.automated is True
    assert decision.reason == "auto-remediation simulated and audited"
    assert decision.audit_record_id is not None
    assert len(automation_store.list_audit()) == 1


def test_automation_gate_honors_global_kill_switch(orchestrator: OrchestratorAgent, automation_store: AutomationStore):
    automation_store.save_config(
        AutomationConfig(
            global_enabled=False,
            rules=[
                CategoryAutomationRule(
                    category="Database",
                    enabled=True,
                    threshold=0.6,
                    max_risk_level="low",
                    max_severity="medium",
                )
            ],
        )
    )

    decision = orchestrator._evaluate_automation_decision(
        "INC009",
        {
            "incident_id": "INC009",
            "summary": "Restart the connection pool",
            "resolution_steps": [],
            "related_knowledge": [],
            "correlated_changes": [],
            "confidence": 0.7,
            "suggested_fix": {
                "id": "rem-db-001",
                "title": "Restart Database Connection Pool",
                "description": "Restart the pool",
                "script": "kubectl rollout restart deployment/db-connection-pool",
                "risk_level": "low",
                "estimated_duration": "2 minutes",
                "prerequisites": [],
                "confidence_score": 0.85,
                "rationale": "Highest-confidence remediation",
                "source": "remediation_engine",
            },
        },
    )

    assert decision.automated is False
    assert decision.reason == "global automation disabled"
    assert len(automation_store.list_audit()) == 1


def test_automation_gate_uses_safe_defaults_on_corrupt_rules_file(tmp_path: Path):
    storage_path = tmp_path / "automation_rules.json"
    storage_path.write_text("{invalid json", encoding="utf-8")

    with patch("backend.agents.orchestrator.get_llm", return_value=MagicMock()):
        orchestrator = OrchestratorAgent(
            automation_store=AutomationStore(storage_path=storage_path)
        )

    decision = orchestrator._evaluate_automation_decision(
        "INC009",
        {
            "incident_id": "INC009",
            "summary": "Restart the connection pool",
            "resolution_steps": [],
            "related_knowledge": [],
            "correlated_changes": [],
            "confidence": 0.7,
            "suggested_fix": {
                "id": "rem-db-001",
                "title": "Restart Database Connection Pool",
                "description": "Restart the pool",
                "script": "kubectl rollout restart deployment/db-connection-pool",
                "risk_level": "low",
                "estimated_duration": "2 minutes",
                "prerequisites": [],
                "confidence_score": 0.85,
                "rationale": "Highest-confidence remediation",
                "source": "remediation_engine",
            },
        },
    )

    assert decision.automated is False
    assert decision.reason == "global automation disabled"
