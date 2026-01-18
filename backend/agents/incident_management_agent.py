from typing import Dict, Any
from backend.connectors.base import IncidentManagementConnector
from backend.connectors.servicenow_connector import ServiceNowConnector
from backend.connectors.jira_connector import JiraServiceManagementConnector
from backend.connectors.mock_connector import MockConnector
from backend.config import ConnectorConfig, load_config_from_env


class IncidentManagementAgent:
    """
    Agent responsible for querying incident management systems.
    
    Supports multiple backends: ServiceNow, Jira Service Management, and mock data.
    """
    
    def __init__(self, config: ConnectorConfig = None):
        """
        Initialize the incident management agent.
        
        Args:
            config: Optional ConnectorConfig. If None, loads from environment variables.
        """
        self.name = "incident_management_agent"
        
        # Load config from environment if not provided
        if config is None:
            config = load_config_from_env()
        
        self.config = config
        self.connector = self._create_connector(config)
    
    def _create_connector(self, config: ConnectorConfig) -> IncidentManagementConnector:
        """
        Create the appropriate connector based on configuration.
        
        Args:
            config: ConnectorConfig instance
            
        Returns:
            Configured connector instance
        """
        if config.connector_type == "servicenow":
            if config.servicenow is None:
                raise ValueError("ServiceNow configuration is required when connector_type is 'servicenow'")
            return ServiceNowConnector(config.servicenow.model_dump())
        
        elif config.connector_type == "jira":
            if config.jira is None:
                raise ValueError("Jira configuration is required when connector_type is 'jira'")
            return JiraServiceManagementConnector(config.jira.model_dump())
        
        else:  # mock
            mock_config = config.mock if config.mock else {}
            return MockConnector(mock_config.model_dump() if hasattr(mock_config, 'model_dump') else {})
    
    async def query(self, incident_id: str, context: str) -> Dict[str, Any]:
        """
        Query the incident management system for related information.
        
        Args:
            incident_id: The ID of the current incident
            context: Additional context about the incident
            
        Returns:
            Dictionary containing similar incidents, related changes, and resolutions
        """
        # Get data from the connector
        similar_incidents = await self.connector.get_similar_incidents(incident_id, context)
        related_changes = await self.connector.get_related_changes(incident_id, context)
        resolutions = await self.connector.get_resolutions(incident_id, context)
        
        return {
            "source": self.connector.get_connector_name(),
            "incident_id": incident_id,
            "similar_incidents": similar_incidents,
            "related_changes": related_changes,
            "resolutions": resolutions
        }
    
    def get_tool_description(self) -> str:
        """Get description of the agent's capabilities."""
        connector_name = self.connector.get_connector_name()
        return f"Query {connector_name} for similar incidents, related tickets, and historical resolutions"
