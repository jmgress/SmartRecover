from typing import Dict, Any
import logging
from backend.connectors.base import IncidentManagementConnector
from backend.connectors.servicenow_connector import ServiceNowConnector
from backend.connectors.jira_connector import JiraServiceManagementConnector
from backend.connectors.mock_connector import MockConnector
from backend.config import ConnectorConfig, load_config_from_env

logger = logging.getLogger(__name__)


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
            
        Raises:
            ValueError: If configuration is invalid or missing required fields
        """
        try:
            if config.connector_type == "servicenow":
                if config.servicenow is None:
                    error_msg = (
                        "ServiceNow configuration is required when connector_type is 'servicenow'. "
                        "Please set SERVICENOW_INSTANCE_URL, SERVICENOW_USERNAME, and SERVICENOW_PASSWORD "
                        "environment variables."
                    )
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                return ServiceNowConnector(config.servicenow.model_dump())
            
            elif config.connector_type == "jira":
                if config.jira is None:
                    error_msg = (
                        "Jira configuration is required when connector_type is 'jira'. "
                        "Please set JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN, and JIRA_PROJECT_KEY "
                        "environment variables."
                    )
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                return JiraServiceManagementConnector(config.jira.model_dump())
            
            else:  # mock
                mock_config = config.mock.model_dump() if config.mock is not None else {}
                return MockConnector(mock_config)
        except Exception as e:
            logger.error(f"Failed to create connector for type '{config.connector_type}': {e}")
            raise
    
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
