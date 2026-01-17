import logging
from typing import Dict, Any, List
from backend.data.mock_data import MOCK_CHANGE_CORRELATIONS

logger = logging.getLogger(__name__)


class ChangeCorrelationAgent:
    """Agent responsible for correlating incidents with recent changes."""
    
    def __init__(self):
        self.name = "change_correlation_agent"
        logger.debug(f"Initialized {self.name}")
    
    async def query(self, incident_id: str, context: str) -> Dict[str, Any]:
        """Query change correlation data to identify potentially related deployments."""
        logger.debug(f"Change correlation query started for incident: {incident_id}")
        correlations = MOCK_CHANGE_CORRELATIONS.get(incident_id, [])
        
        high_correlation = [c for c in correlations if c.get("correlation_score", 0) >= 0.8]
        medium_correlation = [c for c in correlations if 0.5 <= c.get("correlation_score", 0) < 0.8]
        
        top_suspect = high_correlation[0] if high_correlation else None
        
        logger.info(
            f"Change correlation query completed",
            extra={
                "extra_fields": {
                    "incident_id": incident_id,
                    "high_correlation_count": len(high_correlation),
                    "medium_correlation_count": len(medium_correlation),
                    "top_suspect_id": top_suspect.get("change_id") if top_suspect else None
                }
            }
        )
        
        return {
            "source": "change_correlation",
            "incident_id": incident_id,
            "high_correlation_changes": high_correlation,
            "medium_correlation_changes": medium_correlation,
            "all_correlations": correlations,
            "top_suspect": top_suspect
        }
    
    def get_tool_description(self) -> str:
        return "Correlate incidents with recent changes and deployments to identify potential causes"
