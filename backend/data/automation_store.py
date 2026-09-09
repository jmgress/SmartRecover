"""Persistent storage for automation rules and audit records."""

import json
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from backend.models.automation import (
    AutomationAuditRecord as V2AutomationAuditRecord,
    AutomationRules,
    CategoryAutomationRule,
)
from backend.models.incident import (
    AutomationAuditRecord,
    AutomationConfig,
    AutomationDecision,
    CategoryAutomationRule as LegacyCategoryAutomationRule,
)
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class AutomationStoreError(RuntimeError):
    """Backward-compatible error type for automation storage."""


class AutomationStore:
    """Store automation rules in a local JSON file."""

    def __init__(self, storage_path: Optional[Path] = None, audit_storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path(__file__).with_name("automation_rules.json")
        default_audit_path = self.storage_path.with_name("automation_audit.json")
        self._audit_store = AutomationAuditStore(audit_storage_path or default_audit_path)
        self._lock = threading.Lock()

    def get_rules(self) -> AutomationRules:
        """Return the persisted automation rules."""
        with self._lock:
            data = self._load()
        return self._validate_rules_or_default(data)

    def update_rules(self, rules: AutomationRules) -> AutomationRules:
        """Persist automation rules and return the normalized value."""
        try:
            validated = AutomationRules.model_validate(rules.model_dump(mode="json"))
        except ValidationError as error:
            raise ValueError("Invalid automation rules") from error

        with self._lock:
            self._write(validated.model_dump(mode="json"))

        logger.info("Stored automation rules")
        return validated

    # Backward-compatible methods used by existing orchestrator/routes/tests.
    def get_config(self) -> AutomationConfig:
        rules = self.get_rules()
        return AutomationConfig(
            global_enabled=rules.global_enabled,
            rules=[
                LegacyCategoryAutomationRule(
                    category=category,
                    enabled=rule.enabled,
                    threshold=rule.confidence_threshold,
                    max_risk_level=rule.max_risk_level,
                    max_severity=rule.max_severity,
                )
                for category, rule in rules.rules.items()
            ],
        )

    def save_config(self, config: AutomationConfig) -> AutomationConfig:
        converted = AutomationRules(
            global_enabled=config.global_enabled,
            rules={
                rule.category: CategoryAutomationRule(
                    enabled=rule.enabled,
                    confidence_threshold=rule.threshold,
                    min_fix_confidence=rule.threshold,
                    max_risk_level=rule.max_risk_level,
                    max_severity=rule.max_severity,
                )
                for rule in config.rules
            },
        )
        self.update_rules(converted)
        return self.get_config()

    def record_audit(self, incident_id: str, decision: AutomationDecision) -> AutomationAuditRecord:
        rules = self.get_rules().rules
        category_rule = rules.get(decision.category) if decision.category else None
        record = V2AutomationAuditRecord(
            id=str(uuid.uuid4()),
            incident_id=incident_id,
            automated=decision.automated,
            category=decision.category,
            mode="simulated",
            reasons=[decision.reason],
            overall_confidence=decision.incident_confidence,
            fix_confidence=decision.suggested_fix_confidence,
            applied_rule=category_rule,
            evaluated_at=datetime.now(timezone.utc),
            fix_id=decision.suggested_fix_id,
            fix_title=None,
            script=None,
        )
        persisted = self._audit_store.append(record)
        return AutomationAuditRecord(
            id=persisted.id,
            incident_id=persisted.incident_id,
            automated=persisted.automated,
            reason=persisted.reasons[0] if persisted.reasons else "",
            category=persisted.category,
            threshold=(persisted.applied_rule.confidence_threshold if persisted.applied_rule else None),
            incident_confidence=persisted.overall_confidence,
            suggested_fix_confidence=persisted.fix_confidence,
            risk_level=(persisted.applied_rule.max_risk_level if persisted.applied_rule else None),
            severity=(persisted.applied_rule.max_severity if persisted.applied_rule else None),
            suggested_fix_id=persisted.fix_id,
            created_at=persisted.evaluated_at,
        )

    def list_audit(self, limit: int = 20) -> List[AutomationAuditRecord]:
        records = self._audit_store.list(limit=limit)
        return [
            AutomationAuditRecord(
                id=record.id,
                incident_id=record.incident_id,
                automated=record.automated,
                reason=record.reasons[0] if record.reasons else "",
                category=record.category,
                threshold=(record.applied_rule.confidence_threshold if record.applied_rule else None),
                incident_confidence=record.overall_confidence,
                suggested_fix_confidence=record.fix_confidence,
                risk_level=(record.applied_rule.max_risk_level if record.applied_rule else None),
                severity=(record.applied_rule.max_severity if record.applied_rule else None),
                suggested_fix_id=record.fix_id,
                created_at=record.evaluated_at,
            )
            for record in records
        ]

    def _validate_rules_or_default(self, data: Dict[str, Any]) -> AutomationRules:
        try:
            return AutomationRules.model_validate(data)
        except ValidationError:
            logger.warning("Ignoring invalid automation rules storage")
            return AutomationRules()

    def _load(self) -> Dict[str, Any]:
        if not self.storage_path.exists():
            return AutomationRules().model_dump(mode="json")
        try:
            with self.storage_path.open(encoding="utf-8") as rules_file:
                data = json.load(rules_file)
        except (json.JSONDecodeError, OSError):
            logger.warning("Ignoring unreadable automation rules storage")
            return AutomationRules().model_dump(mode="json")
        if not isinstance(data, dict):
            logger.warning("Ignoring invalid automation rules storage")
            return AutomationRules().model_dump(mode="json")
        return data

    def _write(self, data: Dict[str, Any]) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.storage_path.parent,
                prefix=f"{self.storage_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as rules_file:
                temporary_path = Path(rules_file.name)
                json.dump(data, rules_file, indent=2)
            temporary_path.replace(self.storage_path)
        except Exception:
            if temporary_path:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass
            raise


class AutomationAuditStore:
    """Store automation audit records in a local JSON file."""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path(__file__).with_name("automation_audit.json")
        self._lock = threading.Lock()

    def append(self, record: V2AutomationAuditRecord) -> V2AutomationAuditRecord:
        with self._lock:
            records = self._load()
            records.append(record.model_dump(mode="json"))
            self._write(records)
        logger.info("Stored automation audit for incident %s", record.incident_id)
        return record

    def list(self, limit: int = 20) -> List[V2AutomationAuditRecord]:
        limit = max(limit, 0)
        with self._lock:
            records = self._load()

        validated_records: List[V2AutomationAuditRecord] = []
        for record in records:
            try:
                validated_records.append(V2AutomationAuditRecord.model_validate(record))
            except ValidationError:
                logger.warning("Skipping invalid automation audit record")
        validated_records.sort(key=lambda record: record.evaluated_at, reverse=True)
        return validated_records[:limit]

    def clear(self) -> None:
        with self._lock:
            self._write([])

    def _load(self) -> List[Dict[str, Any]]:
        if not self.storage_path.exists():
            return []
        try:
            with self.storage_path.open(encoding="utf-8") as audit_file:
                records = json.load(audit_file)
        except (json.JSONDecodeError, OSError):
            logger.warning("Ignoring unreadable automation audit storage")
            return []
        if not isinstance(records, list):
            logger.warning("Ignoring invalid automation audit storage")
            return []
        return records

    def _write(self, records: List[Dict[str, Any]]) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.storage_path.parent,
                prefix=f"{self.storage_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as audit_file:
                temporary_path = Path(audit_file.name)
                json.dump(records, audit_file, indent=2)
            temporary_path.replace(self.storage_path)
        except Exception:
            if temporary_path:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass
            raise


_automation_store: Optional[AutomationStore] = None
_automation_audit_store: Optional[AutomationAuditStore] = None


def get_automation_store() -> AutomationStore:
    """Get the global automation rules store instance."""
    global _automation_store
    if _automation_store is None:
        _automation_store = AutomationStore()
    return _automation_store


def get_automation_audit_store() -> AutomationAuditStore:
    """Get the global automation audit store instance."""
    global _automation_audit_store
    if _automation_audit_store is None:
        _automation_audit_store = AutomationAuditStore()
    return _automation_audit_store
