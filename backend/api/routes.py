from fastapi import APIRouter, HTTPException
from typing import List

from backend.models.incident import Incident, IncidentQuery, AgentResponse
from backend.agents.orchestrator import OrchestratorAgent
from backend.data.mock_data import MOCK_INCIDENTS

router = APIRouter()
orchestrator = OrchestratorAgent()


@router.get("/incidents", response_model=List[Incident])
async def list_incidents():
    """List all available incidents."""
    return [Incident(**inc) for inc in MOCK_INCIDENTS]


@router.get("/incidents/{incident_id}", response_model=Incident)
async def get_incident(incident_id: str):
    """Get a specific incident by ID."""
    for inc in MOCK_INCIDENTS:
        if inc["id"] == incident_id:
            return Incident(**inc)
    raise HTTPException(status_code=404, detail="Incident not found")


@router.post("/resolve", response_model=AgentResponse)
async def resolve_incident(query: IncidentQuery):
    """Resolve an incident using the agentic system."""
    incident_exists = any(inc["id"] == query.incident_id for inc in MOCK_INCIDENTS)
    if not incident_exists:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    response = await orchestrator.resolve(query.incident_id, query.user_query)
    return response


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "incident-resolver"}
