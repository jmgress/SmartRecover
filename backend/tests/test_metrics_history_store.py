"""Tests for durable metrics history storage."""

from datetime import datetime, timezone
from pathlib import Path
import threading

from backend.data.metrics_history_store import MetricsEventStore


def test_metrics_history_store_round_trip(tmp_path: Path):
    """Returned and excluded events survive a reload."""
    storage_path = tmp_path / "metrics_events.json"
    store = MetricsEventStore(storage_path=storage_path)
    timestamp = datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc)

    store.record_returned("incident", 4, timestamp=timestamp)
    store.record_excluded("incident", timestamp=timestamp)

    reloaded = MetricsEventStore(storage_path=storage_path)
    returned = reloaded.list_returned()
    excluded = reloaded.list_excluded()

    assert returned == [
        {
            "ts": timestamp.isoformat(),
            "source": "incident",
            "count": 4,
        }
    ]
    assert excluded == [
        {
            "ts": timestamp.isoformat(),
            "source": "incident",
        }
    ]


def test_metrics_history_store_recovers_from_corrupt_file(tmp_path: Path):
    """Corrupt metrics storage falls back to an empty event history."""
    storage_path = tmp_path / "metrics_events.json"
    storage_path.write_text("{bad json", encoding="utf-8")
    store = MetricsEventStore(storage_path=storage_path)

    store.record_returned("document", 2)

    assert len(store.list_returned()) == 1
    assert store.list_excluded() == []


def test_metrics_history_store_thread_safety(tmp_path: Path):
    """Concurrent writes do not corrupt the metrics event file."""
    storage_path = tmp_path / "metrics_events.json"
    store = MetricsEventStore(storage_path=storage_path)
    start = threading.Event()
    counts = [1, 2, 3, 4, 5]

    def write_returned(count: int):
        start.wait()
        store.record_returned("remediation", count)

    threads = [threading.Thread(target=write_returned, args=(count,)) for count in counts]
    for thread in threads:
        thread.start()

    start.set()

    for thread in threads:
        thread.join()

    reloaded = MetricsEventStore(storage_path=storage_path)
    returned_counts = sorted(event["count"] for event in reloaded.list_returned())
    assert returned_counts == counts
