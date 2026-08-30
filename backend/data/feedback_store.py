"""Persistent storage for incident resolution feedback."""
import json
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.models.incident import FeedbackRecord, FeedbackRequest
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class FeedbackStore:
    """Store resolution feedback in a local JSON file."""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path(__file__).with_name("feedback.json")
        self._lock = threading.Lock()

    def save(self, feedback: FeedbackRequest) -> FeedbackRecord:
        """Persist a feedback record and return it."""
        record = FeedbackRecord(
            id=str(uuid.uuid4()),
            incident_id=feedback.incident_id,
            rating=feedback.rating,
            comment=feedback.comment,
            created_at=datetime.now(timezone.utc),
        )
        with self._lock:
            records = self._load()
            records.append(record.model_dump(mode="json"))
            self._write(records)
        logger.info("Stored resolution feedback for incident %s", feedback.incident_id)
        return record

    def get_for_incidents(self, incident_ids: List[str], limit: int = 3) -> List[FeedbackRecord]:
        """Return up to ``limit`` recent feedback records across the supplied incident IDs."""
        if not incident_ids:
            return []
        with self._lock:
            records = self._load()
        matching = [
            FeedbackRecord.model_validate(record)
            for record in records
            if record.get("incident_id") in incident_ids
        ]
        matching.sort(key=lambda record: record.created_at, reverse=True)
        return matching[:limit]

    def _load(self) -> List[Dict[str, Any]]:
        if not self.storage_path.exists():
            return []
        try:
            with self.storage_path.open(encoding="utf-8") as feedback_file:
                records = json.load(feedback_file)
        except (json.JSONDecodeError, OSError):
            logger.warning("Ignoring unreadable resolution feedback storage")
            return []
        if not isinstance(records, list):
            logger.warning("Ignoring invalid resolution feedback storage")
            return []
        return records

    def _write(self, records: List[Dict[str, Any]]) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=self.storage_path.parent,
            prefix=f"{self.storage_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as feedback_file:
            json.dump(records, feedback_file, indent=2)
            temporary_path = Path(feedback_file.name)
        temporary_path.replace(self.storage_path)
