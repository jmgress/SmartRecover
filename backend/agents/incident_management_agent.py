from typing import Dict, Any, List, Optional

from backend.config import ConnectorConfig, load_config_from_env
from backend.connectors.base import IncidentManagementConnector
from backend.connectors.jira_connector import JiraServiceManagementConnector
from backend.connectors.mock_connector import MockConnector
from backend.connectors.servicenow_connector import ServiceNowConnector
from backend.connectors.splunk_connector import SplunkConnector
from backend.data import mock_data
from backend.utils.logger import get_logger, trace_async_execution

logger = get_logger(__name__)


class IncidentManagementAgent:
    """
    Agent responsible for querying incident management systems.

    Supports multiple backends: ServiceNow, Jira Service Management, Splunk, and mock data.
    """

    def __init__(self, config: Optional[ConnectorConfig] = None):
        self.name = "incident_management_agent"

        if config is None:
            config = load_config_from_env()

        self.config = config
        self.connector = self._create_connector(config)

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "IncidentManagementAgent":
        """Create an incident management agent from application config."""
        connector_config = config.get("connector", config)
        if isinstance(connector_config, ConnectorConfig):
            return cls(connector_config)
        return cls(ConnectorConfig(**connector_config))

    def _create_connector(self, config: ConnectorConfig) -> IncidentManagementConnector:
        try:
            if config.connector_type == "servicenow":
                if config.servicenow is None:
                    error_msg = (
                        "ServiceNow configuration is required when connector_type is 'servicenow'. "
                        "Please configure the ServiceNow connector settings."
                    )
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                return ServiceNowConnector(config.servicenow.model_dump())

            if config.connector_type == "jira":
                if config.jira is None:
                    error_msg = (
                        "Jira configuration is required when connector_type is 'jira'. "
                        "Please configure the Jira connector settings."
                    )
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                return JiraServiceManagementConnector(config.jira.model_dump())

            if config.connector_type == "splunk":
                if config.splunk is None:
                    error_msg = (
                        "Splunk configuration is required when connector_type is 'splunk'. "
                        "Please configure the Splunk connector settings."
                    )
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                return SplunkConnector(config.splunk.model_dump())

            mock_config = config.mock.model_dump() if config.mock is not None else {}
            return MockConnector(mock_config)
        except Exception as exc:
            logger.error(f"Failed to create connector for type '{config.connector_type}': {exc}")
            raise

    def _reset_connector_warning(self) -> None:
        reset_warning = getattr(self.connector, "reset_warning", None)
        if callable(reset_warning):
            reset_warning()

    def get_last_warning(self) -> Optional[str]:
        get_warning = getattr(self.connector, "get_last_warning", None)
        if callable(get_warning):
            return get_warning()
        return None

    def _normalize_incident(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        incident_copy = incident.copy()
        incident_copy.setdefault("source", self.connector.get_connector_name())
        return incident_copy

    async def list_incidents(self) -> List[Dict[str, Any]]:
        self._reset_connector_warning()
        list_method = getattr(self.connector, "list_incidents", None)
        if callable(list_method):
            try:
                incidents = await list_method()
                return [self._normalize_incident(incident) for incident in incidents]
            except Exception as exc:
                logger.warning(f"Failed to list incidents from {self.connector.get_connector_name()}: {exc}")
                return []

        return [self._normalize_incident(incident) for incident in mock_data.MOCK_INCIDENTS]

    async def get_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        self._reset_connector_warning()
        get_method = getattr(self.connector, "get_incident", None)
        if callable(get_method):
            try:
                incident = await get_method(incident_id)
                return self._normalize_incident(incident) if incident else None
            except Exception as exc:
                logger.warning(
                    f"Failed to fetch incident {incident_id} from {self.connector.get_connector_name()}: {exc}"
                )
                return None

        for incident in mock_data.MOCK_INCIDENTS:
            if incident["id"] == incident_id:
                return self._normalize_incident(incident)
        return None

    @trace_async_execution
    async def query(self, incident_id: str, context: str) -> Dict[str, Any]:
        self._reset_connector_warning()
        similar_incidents: List[Dict[str, Any]] = []
        related_changes: List[Dict[str, Any]] = []
        resolutions: List[str] = []

        try:
            similar_incidents = await self.connector.get_similar_incidents(incident_id, context)
            related_changes = await self.connector.get_related_changes(incident_id, context)
            resolutions = await self.connector.get_resolutions(incident_id, context)
        except Exception as exc:
            logger.warning(f"Incident source query failed for {incident_id}: {exc}")

        result = {
            "source": self.connector.get_connector_name(),
            "incident_id": incident_id,
            "similar_incidents": similar_incidents,
            "related_changes": related_changes,
            "resolutions": resolutions,
        }

        warning = self.get_last_warning()
        if warning:
            result["warning"] = warning

        return result

    def get_tool_description(self) -> str:
        connector_name = self.connector.get_connector_name()
        return f"Query {connector_name} for similar incidents, related tickets, and historical resolutions"
