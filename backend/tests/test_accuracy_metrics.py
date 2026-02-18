"""Tests for accuracy metrics endpoint."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.cache import get_agent_cache


client = TestClient(app)


def test_get_accuracy_metrics_no_exclusions():
    """Test accuracy metrics endpoint with no exclusions returns 100% accuracy."""
    # Clear cache to start fresh
    cache = get_agent_cache()
    cache.clear()
    
    response = client.get("/api/v1/admin/accuracy-metrics")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify structure
    assert "categories" in data
    assert "overall_accuracy" in data
    assert "total_exclusions" in data
    assert "total_items_returned" in data
    
    # With no exclusions, accuracy should be 100%
    assert data["overall_accuracy"] == 100.0
    assert data["total_exclusions"] == 0
    
    # Check categories exist
    assert len(data["categories"]) > 0
    for category in data["categories"]:
        assert "category" in category
        assert "total_items_returned" in category
        assert "total_items_excluded" in category
        assert "accuracy_score" in category


def test_get_accuracy_metrics_with_exclusions():
    """Test accuracy metrics calculation with exclusions."""
    # Clear cache to start fresh
    cache = get_agent_cache()
    cache.clear()
    
    # Cache some agent results first
    incident_id = "INC-001"
    agent_results = {
        "servicenow_results": {
            "similar_incidents": [
                {"id": "SNOW001", "title": "Similar issue 1"},
                {"id": "SNOW002", "title": "Similar issue 2"},
                {"id": "SNOW003", "title": "Similar issue 3"}
            ],
            "related_changes": []
        },
        "confluence_results": {
            "documents": [
                {"id": "DOC001", "title": "KB Article 1"},
                {"id": "DOC002", "title": "KB Article 2"}
            ]
        },
        "change_results": {"changes": []},
        "logs_results": {"logs": []},
        "events_results": {"events": []},
        "remediation_results": {"recommendations": []}
    }
    cache.set(incident_id, agent_results)
    
    # Add some exclusions
    cache.add_excluded_item(incident_id, "servicenow:SNOW001", source="servicenow", item_type="incident", reason="Not relevant")
    cache.add_excluded_item(incident_id, "servicenow:SNOW002", source="servicenow", item_type="incident", reason="Duplicate")
    cache.add_excluded_item(incident_id, "confluence:DOC001", source="confluence", item_type="document", reason="Outdated")
    
    response = client.get("/api/v1/admin/accuracy-metrics")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have 3 total exclusions
    assert data["total_exclusions"] == 3
    
    # Total items should be > 0 (we cached 5 items total: 3 servicenow + 2 confluence)
    assert data["total_items_returned"] == 5
    
    # Overall accuracy should be less than 100%
    assert data["overall_accuracy"] < 100.0
    assert data["overall_accuracy"] > 0.0
    
    # Find servicenow and confluence categories
    servicenow_category = next((c for c in data["categories"] if "Incidents" in c["category"]), None)
    confluence_category = next((c for c in data["categories"] if "Knowledge" in c["category"]), None)
    
    # ServiceNow should have 2 exclusions out of 3 items
    if servicenow_category:
        assert servicenow_category["total_items_returned"] == 3
        assert servicenow_category["total_items_excluded"] == 2
        assert servicenow_category["accuracy_score"] < 100.0
    
    # Confluence should have 1 exclusion out of 2 items
    if confluence_category:
        assert confluence_category["total_items_returned"] == 2
        assert confluence_category["total_items_excluded"] == 1
        assert confluence_category["accuracy_score"] < 100.0


def test_get_accuracy_metrics_multiple_incidents():
    """Test accuracy metrics with exclusions across multiple incidents."""
    # Clear cache to start fresh
    cache = get_agent_cache()
    cache.clear()
    
    # Cache agent results for multiple incidents
    for inc_id in ["INC-001", "INC-002", "INC-003"]:
        agent_results = {
            "servicenow_results": {
                "similar_incidents": [{"id": f"SNOW{inc_id}", "title": f"Issue from {inc_id}"}],
                "related_changes": []
            },
            "confluence_results": {
                "documents": [{"id": f"DOC{inc_id}", "title": f"Doc from {inc_id}"}]
            },
            "change_results": {"changes": []},
            "logs_results": {
                "logs": [{"id": f"LOG{inc_id}", "message": f"Log from {inc_id}"}]
            },
            "events_results": {
                "events": [{"id": f"EVT{inc_id}", "event": f"Event from {inc_id}"}]
            },
            "remediation_results": {"recommendations": []}
        }
        cache.set(inc_id, agent_results)
    
    # Add exclusions for multiple incidents
    cache.add_excluded_item("INC-001", "servicenow:SNOWINC-001", source="servicenow", item_type="incident")
    cache.add_excluded_item("INC-002", "servicenow:SNOWINC-002", source="servicenow", item_type="incident")
    cache.add_excluded_item("INC-003", "confluence:DOCINC-003", source="confluence", item_type="document")
    cache.add_excluded_item("INC-001", "logs:LOGINC-001", source="logs", item_type="log")
    cache.add_excluded_item("INC-002", "events:EVTINC-002", source="events", item_type="event")
    
    response = client.get("/api/v1/admin/accuracy-metrics")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have 5 total exclusions
    assert data["total_exclusions"] == 5
    
    # Check that different categories have exclusions
    categories_with_exclusions = [c for c in data["categories"] if c["total_items_excluded"] > 0]
    assert len(categories_with_exclusions) >= 4  # Should have at least 4 categories with exclusions


def test_accuracy_score_calculation():
    """Test that accuracy scores are calculated correctly."""
    # Clear cache to start fresh
    cache = get_agent_cache()
    cache.clear()
    
    # Cache some agent results first - 10 similar incidents
    incident_id = "INC-001"
    agent_results = {
        "servicenow_results": {
            "similar_incidents": [
                {"id": f"SNOW{i:03d}", "title": f"Similar issue {i}"} 
                for i in range(10)
            ],
            "related_changes": []
        },
        "confluence_results": {"documents": []},
        "change_results": {"changes": []},
        "logs_results": {"logs": []},
        "events_results": {"events": []},
        "remediation_results": {"recommendations": []}
    }
    cache.set(incident_id, agent_results)
    
    # Add exactly 5 exclusions for servicenow from same incident
    for i in range(5):
        cache.add_excluded_item(
            incident_id, 
            f"servicenow:SNOW{i:03d}", 
            source="servicenow", 
            item_type="incident"
        )
    
    response = client.get("/api/v1/admin/accuracy-metrics")
    
    assert response.status_code == 200
    data = response.json()
    
    # Find servicenow category
    servicenow_category = next((c for c in data["categories"] if "Incidents" in c["category"]), None)
    assert servicenow_category is not None
    
    # Should have 10 total items returned and 5 exclusions
    assert servicenow_category["total_items_returned"] == 10
    assert servicenow_category["total_items_excluded"] == 5
    
    # Accuracy should be (10 - 5) / 10 * 100 = 50%
    expected_accuracy = 50.0
    assert abs(servicenow_category["accuracy_score"] - expected_accuracy) < 0.01


def test_category_names():
    """Test that category names are user-friendly."""
    response = client.get("/api/v1/admin/accuracy-metrics")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check that we have expected categories
    category_names = [c["category"] for c in data["categories"]]
    
    # Should have user-friendly names, not source keys
    expected_categories = [
        "Prior Incidents",
        "Knowledge Base",
        "Recent Changes",
        "System Logs",
        "System Events",
        "Remediations"
    ]
    
    for expected in expected_categories:
        assert expected in category_names, f"Missing category: {expected}"


def test_exclusion_metadata_stored():
    """Test that exclusion metadata is properly stored."""
    # Clear cache to start fresh
    cache = get_agent_cache()
    cache.clear()
    
    # Add exclusion with metadata
    incident_id = "INC-001"
    item_id = "servicenow:SNOW001"
    reason = "Not relevant to current issue"
    
    cache.add_excluded_item(
        incident_id, 
        item_id,
        source="servicenow",
        item_type="incident",
        reason=reason
    )
    
    # Get metadata
    metadata = cache.get_all_exclusion_metadata()
    
    assert incident_id in metadata
    assert item_id in metadata[incident_id]
    assert metadata[incident_id][item_id]["source"] == "servicenow"
    assert metadata[incident_id][item_id]["item_type"] == "incident"
    assert metadata[incident_id][item_id]["reason"] == reason
    assert "excluded_at" in metadata[incident_id][item_id]


def test_exclusion_stats_by_source():
    """Test getting exclusion stats grouped by source."""
    # Clear cache to start fresh
    cache = get_agent_cache()
    cache.clear()
    
    # Add exclusions from different sources
    cache.add_excluded_item("INC-001", "servicenow:SNOW001", source="servicenow", item_type="incident")
    cache.add_excluded_item("INC-001", "servicenow:SNOW002", source="servicenow", item_type="incident")
    cache.add_excluded_item("INC-002", "confluence:DOC001", source="confluence", item_type="document")
    cache.add_excluded_item("INC-003", "logs:LOG001", source="logs", item_type="log")
    cache.add_excluded_item("INC-003", "logs:LOG002", source="logs", item_type="log")
    cache.add_excluded_item("INC-003", "logs:LOG003", source="logs", item_type="log")
    
    stats = cache.get_exclusion_stats_by_source()
    
    assert stats["servicenow"] == 2
    assert stats["confluence"] == 1
    assert stats["logs"] == 3
