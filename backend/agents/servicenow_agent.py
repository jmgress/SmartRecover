from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage
from backend.data.mock_data import MOCK_SERVICENOW_TICKETS
from backend.logging_config import get_logger, trace_execution

logger = get_logger(__name__)


class ServiceNowAgent:
    """Agent responsible for querying ServiceNow for related tickets and incidents."""
    
    def __init__(self):
        self.name = "servicenow_agent"
        logger.debug(f"Initialized {self.name}")
    
    @trace_execution
    async def query(self, incident_id: str, context: str) -> Dict[str, Any]:
        """Query ServiceNow for related tickets and historical incidents."""
        logger.info(f"Querying ServiceNow: incident_id={incident_id}")
        tickets = MOCK_SERVICENOW_TICKETS.get(incident_id, [])
        logger.debug(f"Found {len(tickets)} tickets for incident {incident_id}")
        
        similar_incidents = [t for t in tickets if t.get("type") == "similar_incident"]
        related_changes = [t for t in tickets if t.get("type") == "related_change"]
        
        logger.debug(f"ServiceNow results: {len(similar_incidents)} similar incidents, {len(related_changes)} related changes")
        
        return {
            "source": "servicenow",
            "incident_id": incident_id,
            "similar_incidents": similar_incidents,
            "related_changes": related_changes,
            "resolutions": [t.get("resolution", "") for t in similar_incidents if t.get("resolution")]
        }
    
    def get_tool_description(self) -> str:
        return "Query ServiceNow for similar incidents, related tickets, and historical resolutions"
