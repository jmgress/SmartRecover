"""
Pytest configuration and fixtures for tests.
"""
import pytest
import shutil
import tempfile
from pathlib import Path


# ---------------------------------------------------------------------------
# Agent result mock fixtures (used by test_chat_context.py and others)
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_incident_data():
    return {
        "id": "INC-TEST-001",
        "title": "Test incident",
        "description": "Test description",
        "severity": "High",
        "status": "Open",
        "affected_services": ["service-a", "service-b"],
    }


@pytest.fixture
def mock_logs_results():
    return {
        "source": "splunk",
        "logs": [
            {
                "timestamp": "2024-01-01T00:00:01Z",
                "service": "api-gateway",
                "level": "ERROR",
                "message": "Connection refused",
                "confidence_score": 0.9,
            },
            {
                "timestamp": "2024-01-01T00:00:02Z",
                "service": "auth-service",
                "level": "WARN",
                "message": "High latency detected",
                "confidence_score": 0.7,
            },
            {
                "timestamp": "2024-01-01T00:00:03Z",
                "service": "db-service",
                "level": "ERROR",
                "message": "Query timeout",
                "confidence_score": 0.85,
            },
        ],
        "error_count": 2,
        "warning_count": 1,
    }


@pytest.fixture
def mock_events_results():
    return {
        "source": "appdynamics",
        "events": [
            {
                "id": "evt-001",
                "severity": "CRITICAL",
                "application": "checkout-app",
                "type": "NodeDown",
                "message": "Node is unreachable",
                "confidence_score": 0.95,
            },
            {
                "id": "evt-002",
                "severity": "WARNING",
                "application": "payment-service",
                "type": "HighCPU",
                "message": "CPU usage above 90%",
                "confidence_score": 0.8,
            },
            {
                "id": "evt-003",
                "severity": "CRITICAL",
                "application": "order-service",
                "type": "SlowResponse",
                "message": "Response time exceeded SLA",
                "confidence_score": 0.88,
            },
        ],
        "critical_count": 2,
        "warning_count": 1,
    }


@pytest.fixture
def mock_servicenow_results():
    return {
        "similar_incidents": [
            {"id": "INC-001", "title": "Similar network outage"},
            {"id": "INC-002", "title": "Database connectivity issue"},
        ],
        "resolutions": [
            "Restart the affected service",
            "Roll back the recent deployment",
        ],
    }


@pytest.fixture
def mock_confluence_results():
    return {
        "documents": [
            {
                "title": "Network Troubleshooting Guide",
                "content": "Step 1: Check connectivity. Step 2: Verify DNS.",
            },
            {
                "title": "Database Recovery Runbook",
                "content": "Restart database cluster following these steps...",
            },
        ]
    }


@pytest.fixture
def mock_changes_results():
    return {
        "top_suspect": {
            "change_id": "CHG-100",
            "description": "Deployed new auth service version",
            "deployed_at": "2024-01-01T00:00:00Z",
            "correlation_score": 0.92,
        },
        "high_correlation_changes": [
            {
                "change_id": "CHG-101",
                "description": "Updated API gateway config",
                "correlation_score": 0.75,
            },
            {
                "change_id": "CHG-102",
                "description": "Database schema migration",
                "correlation_score": 0.60,
            },
        ],
    }


@pytest.fixture
def mock_remediations_results():
    return {
        "remediations": [
            {
                "id": "rem-001",
                "title": "Rollback deployment",
                "description": "Revert to previous stable version",
                "confidence_score": 0.9,
            },
            {
                "id": "rem-002",
                "title": "Restart services",
                "description": "Restart affected microservices in order",
                "confidence_score": 0.75,
            },
        ]
    }


# ---------------------------------------------------------------------------
# Session-scoped CSV backup fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def backup_csv_files():
    """Backup CSV files before all tests and restore after."""
    from backend.data.mock_data import _get_csv_dir
    
    csv_dir = _get_csv_dir()
    backup_dir = Path(tempfile.gettempdir()) / "smartrecover_csv_backup"
    backup_dir.mkdir(exist_ok=True)
    
    # Backup all CSV files
    for csv_file in csv_dir.glob("*.csv"):
        shutil.copy(csv_file, backup_dir / csv_file.name)
    
    yield
    
    # Restore all CSV files after all tests
    for csv_file in backup_dir.glob("*.csv"):
        shutil.copy(csv_file, csv_dir / csv_file.name)
    
    # Clean up backup directory
    shutil.rmtree(backup_dir, ignore_errors=True)


@pytest.fixture(scope="module", autouse=True)
def reload_mock_data_per_module():
    """Reload mock data before each test module to ensure fresh state."""
    from backend.data.mock_data import reload_mock_data
    
    # Reload at the start of each test module
    reload_mock_data()
    
    yield
    
    # Reload at the end of each test module
    reload_mock_data()
