from typing import Dict, Any, List
from backend.connectors.base import IncidentManagementConnector
from backend.data.mock_data import MOCK_SERVICENOW_TICKETS


class MockConnector(IncidentManagementConnector):
    """Mock connector for testing using spreadsheet-like data."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize mock connector.
        
        Args:
            config: Configuration with optional 'data_source' key
        """
        super().__init__(config)
        self.data_source = config.get("data_source", "mock")
    
    async def get_similar_incidents(self, incident_id: str, context: str) -> List[Dict[str, Any]]:
        """
        Get similar incidents from mock data.
        
        Args:
            incident_id: The ID of the current incident
            context: Additional context about the incident
            
        Returns:
            List of similar incidents
        """
        tickets = MOCK_SERVICENOW_TICKETS.get(incident_id, [])
        return [t for t in tickets if t.get("type") == "similar_incident"]
    
    async def get_related_changes(self, incident_id: str, context: str) -> List[Dict[str, Any]]:
        """
        Get related changes from mock data.
        
        Args:
            incident_id: The ID of the current incident
            context: Additional context about the incident
            
        Returns:
            List of related changes
        """
        tickets = MOCK_SERVICENOW_TICKETS.get(incident_id, [])
        return [t for t in tickets if t.get("type") == "related_change"]
    
    async def get_resolutions(self, incident_id: str, context: str) -> List[str]:
        """
        Get resolutions from mock data.
        
        Args:
            incident_id: The ID of the current incident
            context: Additional context about the incident
            
        Returns:
            List of resolution descriptions
        """
        similar_incidents = await self.get_similar_incidents(incident_id, context)
        return [t.get("resolution", "") for t in similar_incidents if t.get("resolution")]
    
    def get_connector_name(self) -> str:
        """Get connector name."""
        return "mock"
