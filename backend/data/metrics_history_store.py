"""Persistent storage for historical metrics events."""

import json
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class MetricsEventStore:
    """Store accuracy metrics events in a local JSON file."""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path(__file__).with_name("metrics_events.json")
        self._lock = threading.Lock()

    def record_returned(
        self,
        source: str,
        count: int,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Persist a returned-items event for a source."""
        if count <= 0:
            return
        event = {
            "ts": (timestamp or datetime.now(timezone.utc)).isoformat(),
            "source": source,
            "count": count,
        }
        with self._lock:
            payload = self._load()
            payload["returned"].append(event)
            self._write(payload)
        logger.info("Stored metrics returned event for source %s (count=%s)", source, count)

    def record_excluded(
        self,
        source: str,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Persist an excluded-item event for a source."""
        event = {
            "ts": (timestamp or datetime.now(timezone.utc)).isoformat(),
            "source": source,
        }
        with self._lock:
            payload = self._load()
            payload["excluded"].append(event)
            self._write(payload)
        logger.info("Stored metrics excluded event for source %s", source)

    def list_returned(self) -> List[Dict[str, Any]]:
        """Return all stored returned-items events."""
        with self._lock:
            return list(self._load()["returned"])

    def list_excluded(self) -> List[Dict[str, Any]]:
        """Return all stored excluded-item events."""
        with self._lock:
            return list(self._load()["excluded"])

    def get_events(self) -> Dict[str, List[Dict[str, Any]]]:
        """Return all stored metrics events."""
        with self._lock:
            payload = self._load()
        return {
            "returned": list(payload["returned"]),
            "excluded": list(payload["excluded"]),
        }

    def _empty_payload(self) -> Dict[str, List[Dict[str, Any]]]:
        return {"returned": [], "excluded": []}

    def _load(self) -> Dict[str, List[Dict[str, Any]]]:
        if not self.storage_path.exists():
            return self._empty_payload()
        try:
            with self.storage_path.open(encoding="utf-8") as metrics_file:
                payload = json.load(metrics_file)
        except (json.JSONDecodeError, OSError):
            logger.warning("Ignoring unreadable metrics event storage")
            return self._empty_payload()
        if not isinstance(payload, dict):
            logger.warning("Ignoring invalid metrics event storage")
            return self._empty_payload()
        returned = payload.get("returned", [])
        excluded = payload.get("excluded", [])
        if not isinstance(returned, list) or not isinstance(excluded, list):
            logger.warning("Ignoring invalid metrics event storage structure")
            return self._empty_payload()
        return {
            "returned": returned,
            "excluded": excluded,
        }

    def _write(self, payload: Dict[str, List[Dict[str, Any]]]) -> None:
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
            ) as metrics_file:
                temporary_path = Path(metrics_file.name)
                json.dump(payload, metrics_file, indent=2)
            temporary_path.replace(self.storage_path)
        except Exception:
            if temporary_path:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass
            raise


_metrics_event_store: Optional[MetricsEventStore] = None
_metrics_store_lock = threading.Lock()


def get_metrics_event_store() -> MetricsEventStore:
    """Get the global metrics event store instance."""
    global _metrics_event_store
    with _metrics_store_lock:
        if _metrics_event_store is None:
            _metrics_event_store = MetricsEventStore()
        return _metrics_event_store
