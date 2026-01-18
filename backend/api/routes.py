from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Optional
from pydantic import BaseModel

from backend.models.incident import Incident, IncidentQuery, AgentResponse, ChatRequest
from backend.agents.orchestrator import OrchestratorAgent
from backend.data.mock_data import MOCK_INCIDENTS
from backend.utils.logger import get_logger
from backend.llm.llm_manager import get_llm

router = APIRouter()
orchestrator = OrchestratorAgent()
logger = get_logger(__name__)


@router.get("/incidents", response_model=List[Incident])
async def list_incidents():
    """List all available incidents."""
    logger.info("Listing all incidents")
    incidents = [Incident(**inc) for inc in MOCK_INCIDENTS]
    logger.debug(f"Retrieved {len(incidents)} incidents")
    return incidents


@router.get("/incidents/{incident_id}", response_model=Incident)
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
async def resolve_incident(query: IncidentQuery):
    """Resolve an incident using the agentic system."""
    logger.info(f"Resolving incident: {query.incident_id} with query: {query.user_query}")
    incident_exists = any(inc["id"] == query.incident_id for inc in MOCK_INCIDENTS)
    if not incident_exists:
        logger.warning(f"Incident not found for resolution: {query.incident_id}")
        raise HTTPException(status_code=404, detail="Incident not found")
    
    logger.debug(f"Starting orchestrator for incident: {query.incident_id}")
    response = await orchestrator.resolve(query.incident_id, query.user_query)
    logger.info(f"Incident resolution complete: {query.incident_id}, confidence: {response.confidence}")
    return response


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    logger.debug("Health check requested")
    return {"status": "healthy", "service": "incident-resolver"}


class LLMTestRequest(BaseModel):
    message: Optional[str] = "Hello, are you working correctly?"


class LLMTestResponse(BaseModel):
    status: str
    provider: str
    model: str
    test_message: str
    llm_response: str
    error: Optional[str] = None


@router.post("/admin/test-llm", response_model=LLMTestResponse)
async def test_llm(request: LLMTestRequest):
    """Test LLM communication by sending a simple message."""
    logger.info(f"Testing LLM communication with message: {request.message}")
    
    from backend.config import get_config
    config = get_config()
    llm_config = config.llm
    
    try:
        # Get the LLM instance
        llm = get_llm()
        
        # Send a test message
        from langchain_core.messages import HumanMessage
        messages = [HumanMessage(content=request.message)]
        response = await llm.ainvoke(messages)
        
        logger.info(f"LLM test successful, received response")
        
        return LLMTestResponse(
            status="success",
            provider=llm_config.provider,
            model=_get_model_name(llm_config),
            test_message=request.message,
            llm_response=response.content
        )
    except Exception as e:
        logger.error(f"LLM test failed: {str(e)}")
        
        return LLMTestResponse(
            status="error",
            provider=llm_config.provider,
            model=_get_model_name(llm_config),
            test_message=request.message,
            llm_response="",
            error=str(e)
        )


def _get_model_name(llm_config):
    """Helper to get the model name based on provider."""
    if llm_config.provider == "openai":
        return llm_config.openai.model
    elif llm_config.provider == "gemini":
        return llm_config.gemini.model
    elif llm_config.provider == "ollama":
        return llm_config.ollama.model
    return "unknown"


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream an interactive chat response for an incident.
    
    This endpoint uses Server-Sent Events (SSE) to stream the response.
    Agent data is cached to avoid re-running expensive queries.
    """
    logger.info(f"Chat stream request for incident: {request.incident_id}")
    
    # Verify incident exists
    incident_exists = any(inc["id"] == request.incident_id for inc in MOCK_INCIDENTS)
    if not incident_exists:
        logger.warning(f"Incident not found for chat: {request.incident_id}")
        raise HTTPException(status_code=404, detail="Incident not found")
    
    async def generate_stream():
        """Generate SSE stream."""
        try:
            async for chunk in orchestrator.chat_stream(
                request.incident_id,
                request.message,
                request.conversation_history
            ):
                # Format as SSE event
                yield f"data: {chunk}\n\n"
            
            # Send done signal
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Error in chat stream: {e}")
            yield f"data: Error: {str(e)}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
        }
    )
