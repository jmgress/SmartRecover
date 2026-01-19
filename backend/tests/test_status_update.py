"""
Tests for incident status update functionality with CSV persistence.
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from backend.data.mock_data import (
    update_incident_status,
    _save_incidents,
    _load_incidents,
    MockDataLoadError,
    MOCK_INCIDENTS
)


class TestStatusUpdateCSVPersistence:
    """Test suite for status update with CSV persistence."""
    
    @pytest.fixture
    def temp_csv_dir(self, monkeypatch):
        """Create a temporary CSV directory for testing."""
        temp_dir = tempfile.mkdtemp()
        csv_dir = Path(temp_dir) / "csv"
        csv_dir.mkdir()
        
        # Create a test incidents CSV
        csv_path = csv_dir / "incidents.csv"
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("id,title,description,severity,status,created_at,updated_at,affected_services,assignee\n")
            f.write("INC001,Test Incident,Test Description,high,open,2026-01-17T10:30:00,,service1|service2,ops-team\n")
            f.write("INC002,Another Incident,Another Description,medium,investigating,2026-01-17T12:00:00,,service3,\n")
        
        # Patch the _get_csv_dir function to use temp directory
        monkeypatch.setattr(
            "backend.data.mock_data._get_csv_dir",
            lambda: csv_dir
        )
        
        yield csv_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_save_incidents_creates_valid_csv(self, temp_csv_dir):
        """Test that _save_incidents creates a valid CSV file."""
        incidents = [
            {
                "id": "INC001",
                "title": "Test Incident",
                "description": "Test Description",
                "severity": "high",
                "status": "open",
                "created_at": datetime(2026, 1, 17, 10, 30, 0),
                "updated_at": None,
                "affected_services": ["service1", "service2"],
                "assignee": "ops-team"
            }
        ]
        
        _save_incidents(incidents)
        
        # Verify file exists
        csv_path = temp_csv_dir / "incidents.csv"
        assert csv_path.exists()
        
        # Verify content
        with open(csv_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 2  # Header + 1 row
            assert "id,title,description,severity,status,created_at,updated_at,affected_services,assignee" in lines[0]
            assert "INC001,Test Incident,Test Description,high,open," in lines[1]
            assert "service1|service2,ops-team" in lines[1]
    
    def test_save_incidents_with_updated_at(self, temp_csv_dir):
        """Test that _save_incidents properly saves updated_at field."""
        updated_time = datetime(2026, 1, 18, 15, 45, 0)
        incidents = [
            {
                "id": "INC001",
                "title": "Test Incident",
                "description": "Test Description",
                "severity": "high",
                "status": "resolved",
                "created_at": datetime(2026, 1, 17, 10, 30, 0),
                "updated_at": updated_time,
                "affected_services": ["service1"],
                "assignee": "ops-team"
            }
        ]
        
        _save_incidents(incidents)
        
        # Load and verify
        loaded = _load_incidents()
        assert len(loaded) == 1
        assert loaded[0]["status"] == "resolved"
        assert loaded[0]["updated_at"] == updated_time
    
    def test_update_incident_status_success(self, temp_csv_dir, monkeypatch):
        """Test successful status update."""
        # Load test data
        test_incidents = _load_incidents()
        monkeypatch.setattr("backend.data.mock_data.MOCK_INCIDENTS", test_incidents)
        
        # Update status
        success = update_incident_status("INC001", "resolved")
        assert success is True
        
        # Verify in-memory update
        incident = next(inc for inc in test_incidents if inc["id"] == "INC001")
        assert incident["status"] == "resolved"
        assert incident["updated_at"] is not None
        
        # Verify CSV persistence
        loaded = _load_incidents()
        loaded_incident = next(inc for inc in loaded if inc["id"] == "INC001")
        assert loaded_incident["status"] == "resolved"
        assert loaded_incident["updated_at"] is not None
    
    def test_update_incident_status_not_found(self, temp_csv_dir, monkeypatch):
        """Test status update for non-existent incident."""
        test_incidents = _load_incidents()
        monkeypatch.setattr("backend.data.mock_data.MOCK_INCIDENTS", test_incidents)
        
        success = update_incident_status("INC999", "resolved")
        assert success is False
    
    def test_update_incident_status_multiple_times(self, temp_csv_dir, monkeypatch):
        """Test updating status multiple times."""
        test_incidents = _load_incidents()
        monkeypatch.setattr("backend.data.mock_data.MOCK_INCIDENTS", test_incidents)
        
        # First update
        update_incident_status("INC001", "investigating")
        loaded1 = _load_incidents()
        incident1 = next(inc for inc in loaded1 if inc["id"] == "INC001")
        assert incident1["status"] == "investigating"
        first_update = incident1["updated_at"]
        
        # Second update (with a small delay to ensure different timestamps)
        import time
        time.sleep(0.01)
        update_incident_status("INC001", "resolved")
        loaded2 = _load_incidents()
        incident2 = next(inc for inc in loaded2 if inc["id"] == "INC001")
        assert incident2["status"] == "resolved"
        second_update = incident2["updated_at"]
        
        # Verify updated_at changed
        assert second_update != first_update
    
    def test_save_incidents_preserves_other_incidents(self, temp_csv_dir, monkeypatch):
        """Test that updating one incident doesn't affect others."""
        test_incidents = _load_incidents()
        monkeypatch.setattr("backend.data.mock_data.MOCK_INCIDENTS", test_incidents)
        
        # Store original state of INC002
        inc002_original = next(inc for inc in test_incidents if inc["id"] == "INC002").copy()
        
        # Update INC001
        update_incident_status("INC001", "resolved")
        
        # Verify INC002 unchanged
        loaded = _load_incidents()
        inc002_after = next(inc for inc in loaded if inc["id"] == "INC002")
        assert inc002_after["status"] == inc002_original["status"]
        assert inc002_after["title"] == inc002_original["title"]
    
    def test_backward_compatibility_without_updated_at_column(self, temp_csv_dir):
        """Test that CSV without updated_at column can still be loaded."""
        # Create CSV without updated_at column
        csv_path = temp_csv_dir / "incidents.csv"
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("id,title,description,severity,status,created_at,affected_services,assignee\n")
            f.write("INC001,Test,Desc,high,open,2026-01-17T10:30:00,service1,ops-team\n")
        
        # Should load without error
        incidents = _load_incidents()
        assert len(incidents) == 1
        assert incidents[0]["updated_at"] is None


class TestStatusUpdateAPI:
    """Test suite for status update API endpoint."""
    
    @pytest.fixture
    def test_client(self):
        """Create a test client for the API."""
        from fastapi.testclient import TestClient
        from backend.main import app
        return TestClient(app)
    
    def test_update_status_endpoint_success(self, test_client):
        """Test successful status update via API."""
        # Get initial incident state
        response = test_client.get("/api/v1/incidents/INC001")
        assert response.status_code == 200
        initial_status = response.json()["status"]
        
        # Update status
        new_status = "resolved" if initial_status != "resolved" else "open"
        response = test_client.put(
            "/api/v1/incidents/INC001/status",
            json={"status": new_status}
        )
        assert response.status_code == 200
        
        updated_incident = response.json()
        assert updated_incident["status"] == new_status
        assert updated_incident["updated_at"] is not None
        
        # Verify persistence
        response = test_client.get("/api/v1/incidents/INC001")
        assert response.status_code == 200
        assert response.json()["status"] == new_status
    
    def test_update_status_endpoint_invalid_status(self, test_client):
        """Test status update with invalid status value."""
        response = test_client.put(
            "/api/v1/incidents/INC001/status",
            json={"status": "invalid_status"}
        )
        assert response.status_code == 400
        assert "Invalid status" in response.json()["detail"]
    
    def test_update_status_endpoint_not_found(self, test_client):
        """Test status update for non-existent incident."""
        response = test_client.put(
            "/api/v1/incidents/INC999/status",
            json={"status": "resolved"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_update_status_endpoint_valid_statuses(self, test_client):
        """Test all valid status values."""
        valid_statuses = ["open", "investigating", "resolved"]
        
        for status in valid_statuses:
            response = test_client.put(
                "/api/v1/incidents/INC001/status",
                json={"status": status}
            )
            assert response.status_code == 200
            assert response.json()["status"] == status
