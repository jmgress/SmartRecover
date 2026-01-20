"""
Tests for mock data CSV loading functionality.
"""
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from backend.data.mock_data import (
    MOCK_CHANGE_CORRELATIONS,
    MOCK_CONFLUENCE_DOCS,
    MOCK_INCIDENTS,
    MOCK_SERVICENOW_TICKETS,
    MockDataLoadError,
    _load_change_correlations,
    _load_confluence_docs,
    _load_incidents,
    _load_servicenow_tickets,
    reload_mock_data,
)


class TestMockDataLoading:
    """Test suite for CSV-based mock data loading."""

    def test_mock_incidents_loaded(self):
        """Test that mock incidents are loaded from CSV."""
        assert len(MOCK_INCIDENTS) > 0
        assert all(isinstance(inc, dict) for inc in MOCK_INCIDENTS)

        # Check first incident structure
        incident = MOCK_INCIDENTS[0]
        assert "id" in incident
        assert "title" in incident
        assert "description" in incident
        assert "severity" in incident
        assert "status" in incident
        assert "created_at" in incident
        assert "affected_services" in incident
        assert "assignee" in incident

        # Check data types
        assert isinstance(incident["id"], str)
        assert isinstance(incident["title"], str)
        assert isinstance(incident["created_at"], datetime)
        assert isinstance(incident["affected_services"], list)

    def test_mock_servicenow_tickets_loaded(self):
        """Test that ServiceNow tickets are loaded from CSV."""
        assert len(MOCK_SERVICENOW_TICKETS) > 0
        assert all(isinstance(v, list) for v in MOCK_SERVICENOW_TICKETS.values())

        # Check ticket structure
        for incident_id, tickets in MOCK_SERVICENOW_TICKETS.items():
            assert isinstance(incident_id, str)
            for ticket in tickets:
                assert "ticket_id" in ticket
                assert "type" in ticket
                assert "source" in ticket
                assert ticket["type"] in ["similar_incident", "related_change"]

    def test_mock_confluence_docs_loaded(self):
        """Test that Confluence docs are loaded from CSV."""
        assert len(MOCK_CONFLUENCE_DOCS) > 0
        assert all(isinstance(v, list) for v in MOCK_CONFLUENCE_DOCS.values())

        # Check document structure
        for incident_id, docs in MOCK_CONFLUENCE_DOCS.items():
            assert isinstance(incident_id, str)
            for doc in docs:
                assert "doc_id" in doc
                assert "title" in doc
                assert "content" in doc

    def test_mock_change_correlations_loaded(self):
        """Test that change correlations are loaded from CSV."""
        assert len(MOCK_CHANGE_CORRELATIONS) > 0
        assert all(isinstance(v, list) for v in MOCK_CHANGE_CORRELATIONS.values())

        # Check correlation structure
        for incident_id, correlations in MOCK_CHANGE_CORRELATIONS.items():
            assert isinstance(incident_id, str)
            for correlation in correlations:
                assert "change_id" in correlation
                assert "description" in correlation
                assert "deployed_at" in correlation
                assert "correlation_score" in correlation
                assert isinstance(correlation["correlation_score"], float)

    def test_incidents_csv_format(self):
        """Test that incidents CSV has correct format."""
        # Check specific known incident
        inc001 = next((inc for inc in MOCK_INCIDENTS if inc["id"] == "INC001"), None)
        assert inc001 is not None
        assert inc001["title"] == "Database connection timeout"
        assert inc001["severity"] == "high"
        assert "auth-service" in inc001["affected_services"]
        assert "user-service" in inc001["affected_services"]
        assert inc001["assignee"] == "ops-team"

    def test_servicenow_tickets_relationships(self):
        """Test that ServiceNow tickets are correctly linked to incidents."""
        # Check INC001 has tickets
        assert "INC001" in MOCK_SERVICENOW_TICKETS
        inc001_tickets = MOCK_SERVICENOW_TICKETS["INC001"]
        assert len(inc001_tickets) >= 2

        # Check ticket types
        similar_incidents = [t for t in inc001_tickets if t["type"] == "similar_incident"]
        related_changes = [t for t in inc001_tickets if t["type"] == "related_change"]
        assert len(similar_incidents) > 0
        assert len(related_changes) > 0

    def test_confluence_docs_relationships(self):
        """Test that Confluence docs are correctly linked to incidents."""
        # Check INC001 has docs
        assert "INC001" in MOCK_CONFLUENCE_DOCS
        inc001_docs = MOCK_CONFLUENCE_DOCS["INC001"]
        assert len(inc001_docs) >= 1

        # Check doc content
        doc = inc001_docs[0]
        assert len(doc["content"]) > 0

    def test_change_correlations_scores(self):
        """Test that change correlations have valid scores."""
        for _incident_id, correlations in MOCK_CHANGE_CORRELATIONS.items():
            for correlation in correlations:
                score = correlation["correlation_score"]
                assert 0.0 <= score <= 1.0, f"Correlation score {score} out of range"


class TestMockDataErrorHandling:
    """Test error handling for CSV loading."""

    @pytest.fixture
    def temp_csv_dir(self, monkeypatch):
        """Create a temporary CSV directory for testing."""
        temp_dir = tempfile.mkdtemp()
        csv_dir = Path(temp_dir) / "csv"
        csv_dir.mkdir()

        # Patch the _get_csv_dir function to use temp directory
        monkeypatch.setattr(
            "backend.data.mock_data._get_csv_dir",
            lambda: csv_dir
        )

        yield csv_dir

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_missing_incidents_csv(self, temp_csv_dir):
        """Test error handling when incidents CSV is missing."""
        with pytest.raises(MockDataLoadError, match="Incidents CSV file not found"):
            _load_incidents()

    def test_missing_servicenow_tickets_csv(self, temp_csv_dir):
        """Test error handling when ServiceNow tickets CSV is missing."""
        with pytest.raises(MockDataLoadError, match="ServiceNow tickets CSV file not found"):
            _load_servicenow_tickets()

    def test_missing_confluence_docs_csv(self, temp_csv_dir):
        """Test error handling when Confluence docs CSV is missing."""
        with pytest.raises(MockDataLoadError, match="Confluence docs CSV file not found"):
            _load_confluence_docs()

    def test_missing_change_correlations_csv(self, temp_csv_dir):
        """Test error handling when change correlations CSV is missing."""
        with pytest.raises(MockDataLoadError, match="Change correlations CSV file not found"):
            _load_change_correlations()

    def test_malformed_incidents_csv(self, temp_csv_dir):
        """Test error handling with malformed incidents CSV."""
        csv_path = temp_csv_dir / "incidents.csv"
        with open(csv_path, 'w') as f:
            # Missing required columns
            f.write("id,title\n")
            f.write("INC001,Test\n")

        with pytest.raises(MockDataLoadError, match="Error loading incidents CSV"):
            _load_incidents()

    def test_malformed_datetime_in_incidents_csv(self, temp_csv_dir):
        """Test error handling with invalid datetime in incidents CSV."""
        csv_path = temp_csv_dir / "incidents.csv"
        with open(csv_path, 'w') as f:
            f.write("id,title,description,severity,status,created_at,affected_services,assignee\n")
            f.write("INC001,Test,Desc,high,open,INVALID_DATE,service1,ops-team\n")

        with pytest.raises(MockDataLoadError, match="Error loading incidents CSV"):
            _load_incidents()

    def test_malformed_correlation_score(self, temp_csv_dir):
        """Test error handling with invalid correlation score."""
        csv_path = temp_csv_dir / "change_correlations.csv"
        with open(csv_path, 'w') as f:
            f.write("incident_id,change_id,description,deployed_at,correlation_score\n")
            f.write("INC001,CHG001,Test,2026-01-15T14:00:00Z,INVALID_SCORE\n")

        with pytest.raises(MockDataLoadError, match="Error loading change correlations CSV"):
            _load_change_correlations()


class TestMockDataReload:
    """Test the reload_mock_data utility function."""

    def test_reload_function_exists(self):
        """Test that reload_mock_data function is available."""
        from backend.data.mock_data import reload_mock_data
        assert callable(reload_mock_data)

    def test_reload_preserves_data(self):
        """Test that reloading preserves the same data."""
        # Get current data
        original_incidents = len(MOCK_INCIDENTS)
        original_tickets = len(MOCK_SERVICENOW_TICKETS)

        # Reload
        reload_mock_data()

        # Check data is still present
        assert len(MOCK_INCIDENTS) == original_incidents
        assert len(MOCK_SERVICENOW_TICKETS) == original_tickets


class TestBackwardCompatibility:
    """Test that the refactored code maintains backward compatibility."""

    def test_mock_incidents_structure(self):
        """Test that MOCK_INCIDENTS maintains expected structure."""
        # Should be a list
        assert isinstance(MOCK_INCIDENTS, list)

        # Each incident should be a dict with expected keys
        for incident in MOCK_INCIDENTS:
            assert isinstance(incident, dict)
            assert all(key in incident for key in [
                "id", "title", "description", "severity", "status",
                "created_at", "affected_services", "assignee"
            ])

    def test_mock_servicenow_tickets_structure(self):
        """Test that MOCK_SERVICENOW_TICKETS maintains expected structure."""
        # Should be a dict
        assert isinstance(MOCK_SERVICENOW_TICKETS, dict)

        # Values should be lists of dicts
        for incident_id, tickets in MOCK_SERVICENOW_TICKETS.items():
            assert isinstance(incident_id, str)
            assert isinstance(tickets, list)
            for ticket in tickets:
                assert isinstance(ticket, dict)
                assert "ticket_id" in ticket
                assert "type" in ticket
                assert "source" in ticket

    def test_mock_confluence_docs_structure(self):
        """Test that MOCK_CONFLUENCE_DOCS maintains expected structure."""
        # Should be a dict
        assert isinstance(MOCK_CONFLUENCE_DOCS, dict)

        # Values should be lists of dicts
        for incident_id, docs in MOCK_CONFLUENCE_DOCS.items():
            assert isinstance(incident_id, str)
            assert isinstance(docs, list)
            for doc in docs:
                assert isinstance(doc, dict)
                assert "doc_id" in doc
                assert "title" in doc
                assert "content" in doc

    def test_mock_change_correlations_structure(self):
        """Test that MOCK_CHANGE_CORRELATIONS maintains expected structure."""
        # Should be a dict
        assert isinstance(MOCK_CHANGE_CORRELATIONS, dict)

        # Values should be lists of dicts
        for incident_id, correlations in MOCK_CHANGE_CORRELATIONS.items():
            assert isinstance(incident_id, str)
            assert isinstance(correlations, list)
            for correlation in correlations:
                assert isinstance(correlation, dict)
                assert "change_id" in correlation
                assert "description" in correlation
                assert "deployed_at" in correlation
                assert "correlation_score" in correlation
