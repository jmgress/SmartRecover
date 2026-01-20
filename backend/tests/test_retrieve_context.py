"""Tests for retrieve context endpoint."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.cache import get_agent_cache


client = TestClient(app)


def test_retrieve_context_success():
    """Test retrieving context for an existing incident."""
    # Clear cache to ensure fresh retrieval
    cache = get_agent_cache()
    cache.clear()
    
    # Use a known incident ID from mock data
    incident_id = "INC001"
    
    response = client.post(f"/api/v1/incidents/{incident_id}/retrieve-context")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify agent results structure
    assert "servicenow_results" in data
    assert "confluence_results" in data
    assert "change_results" in data
    
    # Verify data is cached
    cached_data = cache.get(incident_id)
    assert cached_data is not None


def test_retrieve_context_returns_cached_results():
    """Test that subsequent calls return cached results."""
    incident_id = "INC001"
    
    # First call
    response1 = client.post(f"/api/v1/incidents/{incident_id}/retrieve-context")
    assert response1.status_code == 200
    data1 = response1.json()
    
    # Second call should return cached data
    response2 = client.post(f"/api/v1/incidents/{incident_id}/retrieve-context")
    assert response2.status_code == 200
    data2 = response2.json()
    
    # Verify results are the same (cached)
    assert data1 == data2


def test_retrieve_context_incident_not_found():
    """Test retrieving context for non-existent incident returns 404."""
    response = client.post("/api/v1/incidents/NONEXISTENT/retrieve-context")
    
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_retrieve_context_updates_incident_details():
    """Test that retrieve context updates the incident details endpoint."""
    cache = get_agent_cache()
    cache.clear()
    
    incident_id = "INC002"
    
    # Get details before context retrieval
    response1 = client.get(f"/api/v1/incidents/{incident_id}/details")
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["agent_results"] is None
    
    # Retrieve context
    response2 = client.post(f"/api/v1/incidents/{incident_id}/retrieve-context")
    assert response2.status_code == 200
    
    # Get details after context retrieval
    response3 = client.get(f"/api/v1/incidents/{incident_id}/details")
    assert response3.status_code == 200
    data3 = response3.json()
    assert data3["agent_results"] is not None
    assert "servicenow_results" in data3["agent_results"]
