"""Tests for durable automation rule and audit JSON stores."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from backend.data.automation_store import AutomationAuditStore, AutomationStore
from backend.models.automation import (
    AutomationAuditRecord,
    AutomationRules,
    CategoryAutomationRule,
)
from backend.utils.categorization import CATEGORIES


def test_rules_round_trip_survives_restart(tmp_path: Path):
    storage_path = tmp_path / "automation_rules.json"
    store = AutomationStore(storage_path=storage_path)
    persisted = store.update_rules(
        AutomationRules(
            global_enabled=True,
            rules={
                "Database": CategoryAutomationRule(
                    enabled=True,
                    confidence_threshold=0.91,
                    min_fix_confidence=0.88,
                    max_risk_level="medium",
                    max_severity="high",
                )
            },
        )
    )

    assert persisted.global_enabled is True
    assert persisted.rules["Database"].enabled is True
    assert persisted.rules["Database"].confidence_threshold == 0.91
    assert persisted.rules["Database"].min_fix_confidence == 0.88

    reloaded = AutomationStore(storage_path=storage_path).get_rules()
    assert reloaded.global_enabled is True
    assert reloaded.rules["Database"].enabled is True
    assert reloaded.rules["Database"].confidence_threshold == 0.91
    assert set(reloaded.rules) == set(CATEGORIES)


def test_missing_or_corrupt_rules_file_returns_defaults(tmp_path: Path):
    storage_path = tmp_path / "automation_rules.json"
    store = AutomationStore(storage_path=storage_path)

    defaults = store.get_rules()
    assert defaults.global_enabled is False
    assert set(defaults.rules) == set(CATEGORIES)

    storage_path.write_text("{bad json", encoding="utf-8")
    recovered = store.get_rules()
    assert recovered.global_enabled is False
    assert set(recovered.rules) == set(CATEGORIES)


def test_unknown_category_rejected_before_write(tmp_path: Path):
    storage_path = tmp_path / "automation_rules.json"
    store = AutomationStore(storage_path=storage_path)
    rules = AutomationRules()
    rules.rules["NotARealCategory"] = CategoryAutomationRule(enabled=True)

    with pytest.raises(ValueError):
        store.update_rules(rules)

    assert store.get_rules().global_enabled is False


def test_automation_audit_store_append_list_and_clear(tmp_path: Path):
    storage_path = tmp_path / "automation_audit.json"
    audit_store = AutomationAuditStore(storage_path=storage_path)
    earlier = datetime.now(timezone.utc) - timedelta(minutes=2)
    later = datetime.now(timezone.utc)

    audit_store.append(
        AutomationAuditRecord(
            id="audit-1",
            incident_id="INC001",
            automated=False,
            category="Database",
            reasons=["global automation disabled"],
            overall_confidence=0.8,
            fix_confidence=0.8,
            evaluated_at=earlier,
            fix_id="fix-1",
            fix_title="Restart DB",
            script="echo safe",
        )
    )
    audit_store.append(
        AutomationAuditRecord(
            id="audit-2",
            incident_id="INC002",
            automated=True,
            category="Database",
            reasons=["all checks passed"],
            overall_confidence=0.95,
            fix_confidence=0.94,
            evaluated_at=later,
            fix_id="fix-2",
            fix_title="Roll service",
            script="echo safe-2",
        )
    )

    listed = audit_store.list(limit=1)
    assert len(listed) == 1
    assert listed[0].id == "audit-2"

    audit_store.clear()
    assert audit_store.list(limit=10) == []


def test_corrupt_audit_file_returns_empty_list(tmp_path: Path):
    storage_path = tmp_path / "automation_audit.json"
    storage_path.write_text("{bad json", encoding="utf-8")
    audit_store = AutomationAuditStore(storage_path=storage_path)
    assert audit_store.list(limit=5) == []
