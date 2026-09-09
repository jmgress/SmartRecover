"""Persistent storage for automation configuration and audit records."""
import json
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.models.incident import (
    AutomationAuditRecord,
    AutomationConfig,
    AutomationDecision,
    CATEGORIES,
    CategoryAutomationRule,
)
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class AutomationStoreError(RuntimeError):
    """Raised when automation settings cannot be loaded or validated."""


class AutomationStore:
    """Store automation settings and audit history in a local JSON file."""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path(__file__).with_name("automation_rules.json")
        self._lock = threading.Lock()

    def get_config(self) -> AutomationConfig:
        """Return the persisted automation configuration."""
        with self._lock:
            data = self._load_data()
        config_data = data.get("config")
        return self._normalize_config(AutomationConfig.model_validate(config_data or {}))

    def save_config(self, config: AutomationConfig) -> AutomationConfig:
        """Persist automation configuration and return the normalized value."""
        normalized = self._normalize_config(config)
        with self._lock:
            data = self._load_data(allow_missing=True)
            data["config"] = normalized.model_dump(mode="json")
            data["audit_log"] = data.get("audit_log", [])
            self._write(data)
        logger.info("Stored automation configuration")
        return normalized

    def record_audit(self, incident_id: str, decision: AutomationDecision) -> AutomationAuditRecord:
        """Persist an automation decision audit record."""
        record = AutomationAuditRecord(
            id=str(uuid.uuid4()),
            incident_id=incident_id,
            automated=decision.automated,
            reason=decision.reason,
            category=decision.category,
            threshold=decision.threshold,
            incident_confidence=decision.incident_confidence,
            suggested_fix_confidence=decision.suggested_fix_confidence,
            risk_level=decision.risk_level,
            severity=decision.severity,
            suggested_fix_id=decision.suggested_fix_id,
            created_at=datetime.now(timezone.utc),
        )
        with self._lock:
            data = self._load_data(allow_missing=True)
            audit_log = data.get("audit_log", [])
            if not isinstance(audit_log, list):
                raise AutomationStoreError("Invalid automation audit log")
            audit_log.append(record.model_dump(mode="json"))
            data["config"] = self._normalize_config(
                AutomationConfig.model_validate(data.get("config") or {})
            ).model_dump(mode="json")
            data["audit_log"] = audit_log[-100:]
            self._write(data)
        logger.info("Stored automation audit for incident %s", incident_id)
        return record

    def list_audit(self, limit: int = 20) -> List[AutomationAuditRecord]:
        """Return recent automation audit records, newest first."""
        with self._lock:
            data = self._load_data(allow_missing=True)
        audit_log = data.get("audit_log", [])
        if not isinstance(audit_log, list):
            raise AutomationStoreError("Invalid automation audit log")
        records = [AutomationAuditRecord.model_validate(record) for record in audit_log]
        records.sort(key=lambda record: record.created_at, reverse=True)
        return records[:limit]

    def _load_data(self, allow_missing: bool = False) -> Dict[str, Any]:
        if not self.storage_path.exists():
            if allow_missing:
                return {}
            return {
                "config": self._default_config().model_dump(mode="json"),
                "audit_log": [],
            }
        try:
            with self.storage_path.open(encoding="utf-8") as storage_file:
                data = json.load(storage_file)
        except (json.JSONDecodeError, OSError) as error:
            raise AutomationStoreError("Failed to read automation storage") from error
        if not isinstance(data, dict):
            raise AutomationStoreError("Invalid automation storage format")
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
            ) as storage_file:
                temporary_path = Path(storage_file.name)
                json.dump(data, storage_file, indent=2)
            temporary_path.replace(self.storage_path)
        except Exception:
            if temporary_path:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass
            raise

    def _default_config(self) -> AutomationConfig:
        return AutomationConfig(
            global_enabled=True,
            rules=[
                CategoryAutomationRule(category=category)
                for category in CATEGORIES
            ],
        )

    def _normalize_config(self, config: AutomationConfig) -> AutomationConfig:
        rules_by_category = {rule.category: rule for rule in config.rules}
        normalized_rules = [
            rules_by_category.get(category, CategoryAutomationRule(category=category))
            for category in CATEGORIES
        ]
        return AutomationConfig(
            global_enabled=config.global_enabled,
            rules=normalized_rules,
        )
