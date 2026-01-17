import logging
from fastapi import APIRouter, HTTPException
from typing import List

from backend.models.incident import Incident, IncidentQuery, AgentResponse
from backend.agents.orchestrator import OrchestratorAgent
from backend.data.mock_data import MOCK_INCIDENTS

logger = logging.getLogger(__name__)

router = APIRouter()
orchestrator = OrchestratorAgent()


@router.get("/incidents", response_model=List[Incident])
async def list_incidents():
    """List all available incidents."""
    logger.info(f"Listing all incidents, count: {len(MOCK_INCIDENTS)}")
    return [Incident(**inc) for inc in MOCK_INCIDENTS]


@router.get("/incidents/{incident_id}", response_model=Incident)
async def get_incident(incident_id: str):
    """Get a specific incident by ID."""
    logger.debug(f"Fetching incident: {incident_id}")
    for inc in MOCK_INCIDENTS:
        if inc["id"] == incident_id:
            logger.info(f"Found incident: {incident_id}")
            return Incident(**inc)
    logger.warning(f"Incident not found: {incident_id}")
    raise HTTPException(status_code=404, detail="Incident not found")


@router.post("/resolve", response_model=AgentResponse)
async def resolve_incident(query: IncidentQuery):
    """Resolve an incident using the agentic system."""
    logger.info(
        f"Starting incident resolution",
        extra={
            "extra_fields": {
                "incident_id": query.incident_id,
                "user_query": query.user_query
            }
        }
    )
    
    incident_exists = any(inc["id"] == query.incident_id for inc in MOCK_INCIDENTS)
    if not incident_exists:
        logger.warning(f"Incident not found for resolution: {query.incident_id}")
        raise HTTPException(status_code=404, detail="Incident not found")
    
    try:
        response = await orchestrator.resolve(query.incident_id, query.user_query)
        logger.info(
            f"Incident resolution completed",
            extra={
                "extra_fields": {
                    "incident_id": query.incident_id,
                    "confidence": response.confidence
                }
            }
        )
        return response
    except Exception as e:
        logger.error(
            f"Error resolving incident: {str(e)}",
            extra={
                "extra_fields": {
                    "incident_id": query.incident_id
                }
            },
            exc_info=True
        )
        raise


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    logger.debug("Health check accessed")
    return {"status": "healthy", "service": "incident-resolver"}
