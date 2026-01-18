from abc import ABC, abstractmethod
from typing import Dict, Any, List


class IncidentManagementConnector(ABC):
    """Base class for incident management tool connectors."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the connector with configuration.
        
        Args:
            config: Configuration dictionary with connector-specific settings
        """
        self.config = config
    
    @abstractmethod
    async def get_similar_incidents(self, incident_id: str, context: str) -> List[Dict[str, Any]]:
        """
        Retrieve similar historical incidents.
        
        Args:
            incident_id: The ID of the current incident
            context: Additional context about the incident
            
        Returns:
            List of similar incidents with their details
        """
        pass
    
    @abstractmethod
    async def get_related_changes(self, incident_id: str, context: str) -> List[Dict[str, Any]]:
        """
        Retrieve related changes/tickets.
        
        Args:
            incident_id: The ID of the current incident
            context: Additional context about the incident
            
        Returns:
            List of related changes/tickets
        """
        pass
    
    @abstractmethod
    async def get_resolutions(self, incident_id: str, context: str) -> List[str]:
        """
        Retrieve resolution information for similar incidents.
        
        Args:
            incident_id: The ID of the current incident
            context: Additional context about the incident
            
        Returns:
            List of resolution descriptions
        """
        pass
    
    @abstractmethod
    def get_connector_name(self) -> str:
        """
        Get the name of the connector.
        
        Returns:
            Name of the connector (e.g., 'servicenow', 'jira', 'mock')
        """
        pass
