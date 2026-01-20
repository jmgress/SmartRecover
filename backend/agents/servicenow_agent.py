from typing import Any

from backend.data.mock_data import MOCK_INCIDENTS, MOCK_SERVICENOW_TICKETS
from backend.utils.logger import get_logger, trace_async_execution
from backend.utils.quality_checker import calculate_tickets_quality
from backend.utils.similarity import find_similar_incidents

logger = get_logger(__name__)


class ServiceNowAgent:
    """Agent responsible for querying ServiceNow for related tickets and incidents."""

    def __init__(self, similarity_threshold: float = 0.2, max_results: int = 5):
        """
        Initialize ServiceNow agent.

        Args:
            similarity_threshold: Minimum similarity score for matching incidents (0.0-1.0)
            max_results: Maximum number of similar incidents to return
        """
        self.name = "servicenow_agent"
        self.similarity_threshold = similarity_threshold
        self.max_results = max_results
        logger.debug(f"Initialized {self.name}")

    @trace_async_execution
    async def query(self, incident_id: str, context: str) -> dict[str, Any]:
        """
        Query ServiceNow for related tickets and historical incidents using dynamic similarity matching.

        This method finds similar resolved incidents at runtime by comparing incident characteristics,
        rather than using hardcoded relationships.
        """
        logger.info(f"ServiceNow query for incident: {incident_id}")

        # Find the current incident
        current_incident = None
        for incident in MOCK_INCIDENTS:
            if incident["id"] == incident_id:
                current_incident = incident
                break

        if not current_incident:
            logger.warning(f"Incident {incident_id} not found")
            return {
                "source": "servicenow",
                "incident_id": incident_id,
                "similar_incidents": [],
                "related_changes": [],
                "resolutions": [],
            }

        # Find similar resolved incidents dynamically
        similar = find_similar_incidents(
            current_incident,
            MOCK_INCIDENTS,
            similarity_threshold=self.similarity_threshold,
            max_results=self.max_results,
        )

        # Collect tickets from similar incidents
        similar_incidents = []
        for similar_incident, similarity_score in similar:
            similar_id = similar_incident["id"]
            tickets = MOCK_SERVICENOW_TICKETS.get(similar_id, [])

            # Add tickets from similar incidents
            for ticket in tickets:
                if ticket.get("type") == "similar_incident":
                    ticket_copy = ticket.copy()
                    ticket_copy["similarity_score"] = similarity_score
                    ticket_copy["source_incident_id"] = similar_id
                    ticket_copy["source_incident_title"] = similar_incident.get(
                        "title", ""
                    )
                    # Map fields for frontend compatibility
                    ticket_copy["id"] = ticket.get("ticket_id")
                    ticket_copy["title"] = similar_incident.get("title", "")
                    ticket_copy["severity"] = similar_incident.get("severity")
                    ticket_copy["status"] = similar_incident.get("status")
                    similar_incidents.append(ticket_copy)

        # Get related changes from current incident (not dynamically matched)
        related_changes = [
            t
            for t in MOCK_SERVICENOW_TICKETS.get(incident_id, [])
            if t.get("type") == "related_change"
        ]

        logger.debug(
            f"Found {len(similar_incidents)} similar incidents and {len(related_changes)} related changes"
        )

        # Calculate quality metrics for similar incidents
        quality_assessment = calculate_tickets_quality(similar_incidents)
        logger.debug(
            f"Quality assessment: level={quality_assessment['overall_level']}, "
            f"avg_score={quality_assessment['average_score']}"
        )

        return {
            "source": "servicenow",
            "incident_id": incident_id,
            "similar_incidents": similar_incidents,
            "related_changes": related_changes,
            "resolutions": [
                t.get("resolution", "")
                for t in similar_incidents
                if t.get("resolution")
            ],
            "quality_assessment": quality_assessment,
        }

    def get_tool_description(self) -> str:
        return "Query ServiceNow for similar incidents, related tickets, and historical resolutions"
