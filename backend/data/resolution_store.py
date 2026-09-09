"""Persistent storage for accepted incident resolutions."""
import json
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.models.incident import ResolutionGrade, ResolutionRecord
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ResolutionStore:
    """Store accepted incident resolutions in a local JSON file."""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path(__file__).with_name("resolutions.json")
        self._lock = threading.Lock()

    def save(self, incident_id: str, resolution_text: str, grade: ResolutionGrade) -> ResolutionRecord:
        """Persist an accepted resolution and return the stored record."""
        record = ResolutionRecord(
            id=str(uuid.uuid4()),
            incident_id=incident_id,
            resolution_text=resolution_text,
            grade=grade,
            created_at=datetime.now(timezone.utc),
        )
        with self._lock:
            records = self._load()
            records.append(record.model_dump(mode="json"))
            self._write(records)
        logger.info("Stored accepted resolution for incident %s", incident_id)
        return record

    def get_latest_for_incident(self, incident_id: str) -> Optional[ResolutionRecord]:
        """Return the most recent accepted resolution for an incident, if any."""
        with self._lock:
            records = self._load()
        matching = [
            ResolutionRecord.model_validate(record)
            for record in records
            if record.get("incident_id") == incident_id
        ]
        if not matching:
            return None
        matching.sort(key=lambda record: record.created_at, reverse=True)
        return matching[0]

    def has_passing_resolution(self, incident_id: str) -> bool:
        """Return True when the incident has a stored resolution that passed grading."""
        latest = self.get_latest_for_incident(incident_id)
        return bool(latest and latest.grade.passed)

    def _load(self) -> List[Dict[str, Any]]:
        if not self.storage_path.exists():
            return []
        try:
            with self.storage_path.open(encoding="utf-8") as resolution_file:
                records = json.load(resolution_file)
        except (json.JSONDecodeError, OSError):
            logger.warning("Ignoring unreadable resolution storage")
            return []
        if not isinstance(records, list):
            logger.warning("Ignoring invalid resolution storage")
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
            ) as resolution_file:
                temporary_path = Path(resolution_file.name)
                json.dump(records, resolution_file, indent=2)
            temporary_path.replace(self.storage_path)
        except Exception:
            if temporary_path:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass
            raise
