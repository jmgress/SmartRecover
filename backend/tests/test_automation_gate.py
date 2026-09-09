"""Tests for automation gate evaluation and orchestrator wiring behavior."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from backend.agents.automation_gate import evaluate_automation
from backend.agents.orchestrator import OrchestratorAgent
from backend.data.automation_store import AutomationStore
from backend.models.automation import AutomationRules, CategoryAutomationRule
from backend.models.incident import AutomationConfig, CategoryAutomationRule as LegacyRule


def _rules(**overrides) -> AutomationRules:
    rules = AutomationRules(
        global_enabled=True,
        rules={
            "Database": CategoryAutomationRule(
                enabled=True,
                confidence_threshold=0.8,
                min_fix_confidence=0.7,
                max_risk_level="medium",
                max_severity="high",
            )
        },
    )
    return rules.model_copy(update=overrides, deep=True)


@pytest.mark.parametrize(
    ("rules", "incident", "overall_confidence", "suggested_fix", "expected_reason"),
    [
        (
            _rules(),
            {"severity": "medium"},
            0.9,
            {"id": "fix-1", "confidence_score": 0.9, "risk_level": "low"},
            "incident category is unavailable",
        ),
        (
            _rules(global_enabled=False),
            {"category": "Database", "severity": "medium"},
            0.9,
            {"id": "fix-1", "confidence_score": 0.9, "risk_level": "low"},
            "global automation kill switch is off",
        ),
        (
            _rules(),
            {"category": "Database", "severity": "medium"},
            0.9,
            None,
            "no suggested fix present",
        ),
        (
            _rules(),
            {"category": "Payments", "severity": "medium"},
            0.9,
            {"id": "fix-1", "confidence_score": 0.9, "risk_level": "low"},
            "automation rule for category 'Payments' is disabled",
        ),
        (
            _rules(
                rules={
                    "Database": CategoryAutomationRule(
                        enabled=False,
                        confidence_threshold=0.8,
                        min_fix_confidence=0.7,
                        max_risk_level="medium",
                        max_severity="high",
                    )
                }
            ),
            {"category": "Database", "severity": "medium"},
            0.9,
            {"id": "fix-1", "confidence_score": 0.9, "risk_level": "low"},
            "automation rule for category 'Database' is disabled",
        ),
        (
            _rules(),
            {"category": "Database", "severity": "medium"},
            0.5,
            {"id": "fix-1", "confidence_score": 0.9, "risk_level": "low"},
            "overall confidence below threshold",
        ),
        (
            _rules(),
            {"category": "Database", "severity": "medium"},
            0.9,
            {"id": "fix-1", "confidence_score": 0.6, "risk_level": "low"},
            "fix confidence below minimum",
        ),
        (
            _rules(),
            {"category": "Database", "severity": "medium"},
            0.9,
            {"id": "fix-1", "confidence_score": 0.9, "risk_level": "high"},
            "fix risk level 'high' exceeds max 'medium'",
        ),
        (
            _rules(),
            {"category": "Database", "severity": "critical"},
            0.9,
            {"id": "fix-1", "confidence_score": 0.9, "risk_level": "low"},
            "incident severity 'critical' exceeds max 'high'",
        ),
        (
            _rules(),
            {"category": "Database"},
            0.9,
            {"id": "fix-1", "confidence_score": 0.9, "risk_level": "low"},
            "incident severity is unavailable",
        ),
        (
            _rules(),
            {"category": "Database", "severity": "medium"},
            0.9,
            {"id": "fix-1", "confidence_score": 0.9},
            "fix risk level is unavailable",
        ),
    ],
)
def test_evaluate_automation_blocks_with_distinct_reasons(
    rules: AutomationRules,
    incident: dict,
    overall_confidence: float,
    suggested_fix: dict,
    expected_reason: str,
):
    decision = evaluate_automation(
        incident=incident,
        overall_confidence=overall_confidence,
        suggested_fix=suggested_fix,
        rules=rules,
    )
    assert decision.automated is False
    assert expected_reason in decision.reason


def test_evaluate_automation_is_deny_by_default():
    decision = evaluate_automation(
        incident={"severity": "medium"},
        overall_confidence=None,
        suggested_fix=None,
        rules=AutomationRules(),
    )
    assert decision.automated is False
    assert "global automation kill switch is off" in decision.reason
    assert "incident category is unavailable" in decision.reason
    assert "no suggested fix present" in decision.reason


def test_evaluate_automation_accumulates_multiple_reasons():
    decision = evaluate_automation(
        incident={"category": "Database", "severity": "critical"},
        overall_confidence=0.1,
        suggested_fix=None,
        rules=_rules(global_enabled=False),
    )
    assert decision.automated is False
    assert "global automation kill switch is off" in decision.reason
    assert "no suggested fix present" in decision.reason
    assert "overall confidence below threshold" in decision.reason


def test_evaluate_automation_happy_path():
    decision = evaluate_automation(
        incident={"category": "Database", "severity": "medium"},
        overall_confidence=0.9,
        suggested_fix={
            "id": "fix-1",
            "confidence_score": 0.92,
            "risk_level": "low",
        },
        rules=_rules(),
    )
    assert decision.automated is True
    assert decision.reason == "auto-remediation simulated and audited"
    assert decision.category == "Database"
    assert decision.suggested_fix_id == "fix-1"


@pytest.fixture
def automation_store(tmp_path: Path) -> AutomationStore:
    return AutomationStore(storage_path=tmp_path / "automation_rules.json")


@pytest.fixture
def orchestrator(automation_store: AutomationStore) -> OrchestratorAgent:
    with patch("backend.agents.orchestrator.get_llm", return_value=MagicMock()):
        return OrchestratorAgent(automation_store=automation_store)


def test_orchestrator_automation_records_audit_only_on_automated(
    orchestrator: OrchestratorAgent,
    automation_store: AutomationStore,
):
    automation_store.save_config(
        AutomationConfig(
            global_enabled=True,
            rules=[
                LegacyRule(
                    category="Database",
                    enabled=True,
                    threshold=0.6,
                    max_risk_level="low",
                    max_severity="high",
                )
            ],
        )
    )
    with patch.object(
        orchestrator,
        "_get_incident_record",
        return_value={
            "id": "INCX",
            "title": "Database latency spike",
            "description": "Connection timeout for reads",
            "severity": "medium",
        },
    ):
        approved = orchestrator._evaluate_automation_decision(
            "INCX",
            {
                "confidence": 0.9,
                "suggested_fix": {
                    "id": "rem-db-001",
                    "confidence_score": 0.9,
                    "risk_level": "low",
                },
            },
        )
    assert approved.automated is True
    assert len(automation_store.list_audit()) == 1

    automation_store.save_config(
        AutomationConfig(
            global_enabled=False,
            rules=[
                LegacyRule(
                    category="Database",
                    enabled=True,
                    threshold=0.6,
                    max_risk_level="low",
                    max_severity="high",
                )
            ],
        )
    )
    denied = orchestrator._evaluate_automation_decision(
        "INCX",
        {
            "confidence": 0.9,
            "suggested_fix": {
                "id": "rem-db-001",
                "confidence_score": 0.9,
                "risk_level": "low",
            },
        },
    )
    assert denied.automated is False
    assert len(automation_store.list_audit()) == 1


def test_orchestrator_denies_when_rules_unavailable(orchestrator: OrchestratorAgent):
    with patch.object(orchestrator.automation_store, "get_rules", side_effect=RuntimeError("boom")):
        decision = orchestrator._evaluate_automation_decision(
            "INC001",
            {
                "confidence": 0.9,
                "suggested_fix": {
                    "id": "fix-1",
                    "confidence_score": 0.9,
                    "risk_level": "low",
                },
            },
        )
    assert decision.automated is False
    assert decision.reason == "automation rules unavailable"


@pytest.mark.asyncio
async def test_resolve_returns_automation_object(
    orchestrator: OrchestratorAgent,
    automation_store: AutomationStore,
):
    automation_store.save_config(
        AutomationConfig(
            global_enabled=True,
            rules=[
                LegacyRule(
                    category="Database",
                    enabled=True,
                    threshold=0.6,
                    max_risk_level="low",
                    max_severity="high",
                )
            ],
        )
    )
    response = await orchestrator.resolve("INC009", "How should we recover?")
    assert response.automation is not None
    assert response.automation_decision == response.automation
