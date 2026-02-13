"""Tests for excluded items functionality."""
import pytest
from backend.cache.agent_cache import AgentCache


class TestExcludedItems:
    """Test excluded items in the agent cache."""
    
    def test_add_excluded_item(self):
        """Test adding an item to the exclusion list."""
        cache = AgentCache()
        incident_id = "INC-001"
        item_id = "incident:INC-123"
        
        cache.add_excluded_item(incident_id, item_id)
        
        assert cache.is_item_excluded(incident_id, item_id)
        excluded = cache.get_excluded_items(incident_id)
        assert item_id in excluded
    
    def test_remove_excluded_item(self):
        """Test removing an item from the exclusion list."""
        cache = AgentCache()
        incident_id = "INC-001"
        item_id = "incident:INC-123"
        
        cache.add_excluded_item(incident_id, item_id)
        cache.remove_excluded_item(incident_id, item_id)
        
        assert not cache.is_item_excluded(incident_id, item_id)
        excluded = cache.get_excluded_items(incident_id)
        assert item_id not in excluded
    
    def test_get_excluded_items_empty(self):
        """Test getting excluded items for an incident with none."""
        cache = AgentCache()
        incident_id = "INC-001"
        
        excluded = cache.get_excluded_items(incident_id)
        
        assert excluded == []
    
    def test_multiple_excluded_items(self):
        """Test multiple excluded items for the same incident."""
        cache = AgentCache()
        incident_id = "INC-001"
        items = ["incident:INC-123", "document:Doc1", "change:CHG-001"]
        
        for item in items:
            cache.add_excluded_item(incident_id, item)
        
        excluded = cache.get_excluded_items(incident_id)
        assert len(excluded) == 3
        for item in items:
            assert item in excluded
            assert cache.is_item_excluded(incident_id, item)
    
    def test_excluded_items_per_incident(self):
        """Test that excluded items are stored per incident."""
        cache = AgentCache()
        incident1 = "INC-001"
        incident2 = "INC-002"
        item1 = "incident:INC-123"
        item2 = "document:Doc1"
        
        cache.add_excluded_item(incident1, item1)
        cache.add_excluded_item(incident2, item2)
        
        assert cache.is_item_excluded(incident1, item1)
        assert not cache.is_item_excluded(incident1, item2)
        assert cache.is_item_excluded(incident2, item2)
        assert not cache.is_item_excluded(incident2, item1)


@pytest.mark.asyncio
async def test_context_filtering():
    """Test that excluded items are filtered from context."""
    from backend.agents.orchestrator import OrchestratorAgent
    
    orchestrator = OrchestratorAgent()
    
    # Mock data
    incident_id = "INC-001"
    servicenow = {
        "similar_incidents": [
            {"id": "INC-100", "title": "Test Incident 1"},
            {"id": "INC-101", "title": "Test Incident 2"},
        ]
    }
    confluence = {
        "documents": [
            {"title": "Doc1", "content": "Content 1"},
            {"title": "Doc2", "content": "Content 2"},
        ]
    }
    changes = {}
    logs = {}
    events = {}
    remediations = {}
    
    # Test without exclusions
    context = orchestrator._build_context_from_agent_data(
        incident_id, servicenow, confluence, changes, logs, events, remediations, []
    )
    assert "Test Incident 1" in context
    assert "Test Incident 2" in context
    assert "Doc1" in context
    assert "Doc2" in context
    
    # Test with exclusions
    excluded_items = ["incident:INC-100", "document:Doc1"]
    context = orchestrator._build_context_from_agent_data(
        incident_id, servicenow, confluence, changes, logs, events, remediations, excluded_items
    )
    assert "Test Incident 1" not in context
    assert "Test Incident 2" in context
    assert "Doc1" not in context
    assert "Doc2" in context
