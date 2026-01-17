from fastapi import APIRouter, HTTPException
from typing import List

from backend.models.incident import Incident, IncidentQuery, AgentResponse
from backend.agents.orchestrator import OrchestratorAgent
from backend.data.mock_data import MOCK_INCIDENTS
from backend.logging_config import get_logger, trace_execution

logger = get_logger(__name__)
router = APIRouter()
orchestrator = OrchestratorAgent()


@router.get("/incidents", response_model=List[Incident])
@trace_execution
async def list_incidents():
    """List all available incidents."""
    logger.info("Listing all incidents")
    incidents = [Incident(**inc) for inc in MOCK_INCIDENTS]
    logger.debug(f"Found {len(incidents)} incidents")
    return incidents


@router.get("/incidents/{incident_id}", response_model=Incident)
@trace_execution
async def get_incident(incident_id: str):
    """Get a specific incident by ID."""
    logger.info(f"Fetching incident: {incident_id}")
    for inc in MOCK_INCIDENTS:
        if inc["id"] == incident_id:
            logger.debug(f"Found incident: {incident_id}")
            return Incident(**inc)
    logger.warning(f"Incident not found: {incident_id}")
    raise HTTPException(status_code=404, detail="Incident not found")


@router.post("/resolve", response_model=AgentResponse)
@trace_execution
async def resolve_incident(query: IncidentQuery):
    """Resolve an incident using the agentic system."""
    logger.info(f"Resolving incident: {query.incident_id}")
    logger.debug(f"User query: {query.user_query}")
    
    incident_exists = any(inc["id"] == query.incident_id for inc in MOCK_INCIDENTS)
    if not incident_exists:
        logger.warning(f"Incident not found for resolution: {query.incident_id}")
        raise HTTPException(status_code=404, detail="Incident not found")
    
    try:
        response = await orchestrator.resolve(query.incident_id, query.user_query)
        logger.info(f"Successfully resolved incident: {query.incident_id} with confidence: {response.confidence}")
        return response
    except Exception as e:
        logger.error(f"Error resolving incident {query.incident_id}: {e}", exc_info=True)
        raise


@router.get("/health")
@trace_execution
async def health_check():
    """Health check endpoint."""
    logger.debug("Health check requested")
    return {"status": "healthy", "service": "incident-resolver"}
