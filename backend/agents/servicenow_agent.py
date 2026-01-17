from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage
from backend.data.mock_data import MOCK_SERVICENOW_TICKETS


class ServiceNowAgent:
    """Agent responsible for querying ServiceNow for related tickets and incidents."""
    
    def __init__(self):
        self.name = "servicenow_agent"
    
    async def query(self, incident_id: str, context: str) -> Dict[str, Any]:
        """Query ServiceNow for related tickets and historical incidents."""
        tickets = MOCK_SERVICENOW_TICKETS.get(incident_id, [])
        
        similar_incidents = [t for t in tickets if t.get("type") == "similar_incident"]
        related_changes = [t for t in tickets if t.get("type") == "related_change"]
        
        return {
            "source": "servicenow",
            "incident_id": incident_id,
            "similar_incidents": similar_incidents,
            "related_changes": related_changes,
            "resolutions": [t.get("resolution", "") for t in similar_incidents if t.get("resolution")]
        }
    
    def get_tool_description(self) -> str:
        return "Query ServiceNow for similar incidents, related tickets, and historical resolutions"
