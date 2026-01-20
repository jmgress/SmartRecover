from typing import Dict, Any, List
from backend.connectors.base import IncidentManagementConnector
from backend.data.mock_data import MOCK_SERVICENOW_TICKETS, MOCK_INCIDENTS
from backend.utils.similarity import find_similar_incidents


class MockConnector(IncidentManagementConnector):
    """Mock connector for testing using spreadsheet-like data with dynamic ticket retrieval."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize mock connector.
        
        Args:
            config: Configuration with optional 'data_source' key
        """
        super().__init__(config)
        self.data_source = config.get("data_source", "mock")
        self.similarity_threshold = config.get("similarity_threshold", 0.2)
        self.max_similar_incidents = config.get("max_similar_incidents", 5)
    
    async def get_similar_incidents(self, incident_id: str, context: str) -> List[Dict[str, Any]]:
        """
        Get similar incidents from mock data using dynamic similarity matching.
        
        This method finds similar resolved incidents at runtime by comparing:
        - Incident titles
        - Descriptions
        - Affected services
        
        Args:
            incident_id: The ID of the current incident
            context: Additional context about the incident
            
        Returns:
            List of similar incidents with their associated tickets
        """
        # Find the current incident
        current_incident = None
        for incident in MOCK_INCIDENTS:
            if incident['id'] == incident_id:
                current_incident = incident
                break
        
        if not current_incident:
            return []
        
        # Find similar resolved incidents using similarity algorithm
        similar = find_similar_incidents(
            current_incident,
            MOCK_INCIDENTS,
            similarity_threshold=self.similarity_threshold,
            max_results=self.max_similar_incidents
        )
        
        # For each similar incident, get its associated tickets
        results = []
        for similar_incident, similarity_score in similar:
            similar_id = similar_incident['id']
            tickets = MOCK_SERVICENOW_TICKETS.get(similar_id, [])
            
            # Only include tickets of type "similar_incident"
            for ticket in tickets:
                if ticket.get("type") == "similar_incident":
                    # Add the similarity score and source incident info
                    ticket_copy = ticket.copy()
                    ticket_copy['similarity_score'] = similarity_score
                    ticket_copy['source_incident_id'] = similar_id
                    ticket_copy['source_incident_title'] = similar_incident.get('title', '')
                    results.append(ticket_copy)
        
        return results
    
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
        Get resolutions from similar incidents using dynamic matching.
        
        Args:
            incident_id: The ID of the current incident
            context: Additional context about the incident
            
        Returns:
            List of resolution descriptions from similar incidents
        """
        similar_incidents = await self.get_similar_incidents(incident_id, context)
        return [t.get("resolution", "") for t in similar_incidents if t.get("resolution")]
    
    def get_connector_name(self) -> str:
        """Get connector name."""
        return "mock"
