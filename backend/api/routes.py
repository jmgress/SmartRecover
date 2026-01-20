import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.agents.orchestrator import OrchestratorAgent
from backend.data.mock_data import MOCK_INCIDENTS, update_incident_status
from backend.llm.llm_manager import get_llm
from backend.models.incident import AgentResponse, ChatRequest, Incident, IncidentQuery
from backend.utils.logger import get_logger

router = APIRouter()
orchestrator = OrchestratorAgent()
logger = get_logger(__name__)


@router.get("/incidents", response_model=list[Incident])
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


class UpdateStatusRequest(BaseModel):
    """Request model for updating incident status."""
    status: str


@router.put("/incidents/{incident_id}/status")
async def update_incident_status_endpoint(incident_id: str, request: UpdateStatusRequest):
    """Update the status of an incident and persist to CSV."""
    logger.info(f"Updating status for incident {incident_id} to: {request.status}")

    # Validate status value
    valid_statuses = ['open', 'investigating', 'resolved']
    if request.status not in valid_statuses:
        logger.warning(f"Invalid status value: {request.status}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )

    # Update the incident status
    try:
        success = update_incident_status(incident_id, request.status)
        if not success:
            logger.warning(f"Incident not found for status update: {incident_id}")
            raise HTTPException(status_code=404, detail="Incident not found")

        # Return the updated incident
        for inc in MOCK_INCIDENTS:
            if inc["id"] == incident_id:
                logger.info(f"Successfully updated incident {incident_id} status to {request.status}")
                return Incident(**inc)

        # This should not happen, but handle it just in case
        raise HTTPException(status_code=500, detail="Failed to retrieve updated incident")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating incident status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update incident status: {str(e)}")


@router.get("/incidents/{incident_id}/details")
async def get_incident_details(incident_id: str):
    """Get incident details with cached agent results.

    Returns the incident data along with any cached agent results
    (ServiceNow, Knowledge Base, Change Correlation).
    If no cached results exist, returns just the incident data.
    """
    logger.info(f"Fetching incident details: {incident_id}")

    # Get incident data
    incident_data = None
    for inc in MOCK_INCIDENTS:
        if inc["id"] == incident_id:
            incident_data = inc
            break

    if not incident_data:
        logger.warning(f"Incident not found: {incident_id}")
        raise HTTPException(status_code=404, detail="Incident not found")

    # Get cached agent results if available
    from backend.cache import get_agent_cache
    cache = get_agent_cache()
    agent_results = cache.get(incident_id)

    logger.debug(f"Found cached agent results: {agent_results is not None}")

    return {
        "incident": incident_data,
        "agent_results": agent_results
    }


@router.post("/incidents/{incident_id}/retrieve-context")
async def retrieve_incident_context(incident_id: str):
    """Retrieve agent context for an incident on demand.

    This endpoint triggers agent analysis to fetch similar incidents,
    knowledge base articles, and change correlations. Results are cached
    for subsequent requests.

    Returns:
        Agent results containing ServiceNow, Knowledge Base, and Change Correlation data

    Raises:
        404: If incident not found
        500: If agent analysis fails
    """
    logger.info(f"Retrieving context for incident: {incident_id}")

    # Verify incident exists
    incident_exists = any(inc["id"] == incident_id for inc in MOCK_INCIDENTS)
    if not incident_exists:
        logger.warning(f"Incident not found for context retrieval: {incident_id}")
        raise HTTPException(status_code=404, detail="Incident not found")

    try:
        # Use empty query for initial context retrieval
        agent_results = await orchestrator._get_or_fetch_agent_data(incident_id, "")
        logger.info(f"Context retrieval successful for incident: {incident_id}")
        return agent_results
    except Exception as e:
        logger.error(f"Failed to retrieve context for incident {incident_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve agent context: {str(e)}"
        )


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
    message: str | None = "Hello, are you working correctly?"


class LLMTestResponse(BaseModel):
    status: str
    llm_response: str
    error: str | None = None


@router.post("/admin/test-llm", response_model=LLMTestResponse)
async def test_llm(request: LLMTestRequest):
    """Test LLM communication by sending a simple message."""
    logger.info(f"Testing LLM communication with message: {request.message}")

    from backend.config import get_config
    get_config()

    try:
        # Get the LLM instance
        llm = get_llm()

        # Send a test message
        from langchain_core.messages import HumanMessage
        messages = [HumanMessage(content=request.message)]
        response = await llm.ainvoke(messages)

        logger.info("LLM test successful, received response")

        return LLMTestResponse(
            status="success",
            llm_response=response.content
        )
    except Exception as e:
        logger.error(f"LLM test failed: {str(e)}")

        return LLMTestResponse(
            status="error",
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


class LLMConfigResponse(BaseModel):
    """Response model for LLM configuration details."""
    provider: str
    model: str
    connection_details: dict
    temperature: float


@router.get("/admin/llm-config", response_model=LLMConfigResponse)
async def get_llm_config():
    """Get current LLM configuration details."""
    logger.info("Fetching LLM configuration details")

    from backend.config import get_config
    config = get_config()
    llm_config = config.llm

    # Build connection details based on provider
    connection_details = {}
    temperature = 0.7

    if llm_config.provider == "openai":
        model = llm_config.openai.model
        temperature = llm_config.openai.temperature
        connection_details = {
            "api_key_configured": bool(llm_config.openai.api_key or os.getenv("OPENAI_API_KEY")),
            "endpoint": "https://api.openai.com/v1"
        }
    elif llm_config.provider == "gemini":
        model = llm_config.gemini.model
        temperature = llm_config.gemini.temperature
        connection_details = {
            "api_key_configured": bool(llm_config.gemini.api_key or os.getenv("GOOGLE_API_KEY")),
            "endpoint": "https://generativelanguage.googleapis.com"
        }
    elif llm_config.provider == "ollama":
        model = llm_config.ollama.model
        temperature = llm_config.ollama.temperature
        connection_details = {
            "base_url": llm_config.ollama.base_url,
            "local": True
        }
    else:
        model = "unknown"
        connection_details = {"error": "Unknown provider"}

    logger.info(f"LLM configuration retrieved: provider={llm_config.provider}, model={model}")

    return LLMConfigResponse(
        provider=llm_config.provider,
        model=model,
        connection_details=connection_details,
        temperature=temperature
    )


class LoggingConfigResponse(BaseModel):
    """Response model for logging configuration details."""
    level: str
    enable_tracing: bool
    log_file: str | None = None


@router.get("/admin/logging-config", response_model=LoggingConfigResponse)
async def get_logging_config():
    """Get current logging configuration."""
    logger.info("Fetching logging configuration")

    from backend.config import get_config
    config = get_config()
    logging_config = config.logging

    return LoggingConfigResponse(
        level=logging_config.level,
        enable_tracing=logging_config.enable_tracing,
        log_file=logging_config.log_file
    )


class UpdateLoggingConfigRequest(BaseModel):
    """Request model for updating logging configuration."""
    level: str | None = None
    enable_tracing: bool | None = None


@router.put("/admin/logging-config", response_model=LoggingConfigResponse)
async def update_logging_config(request: UpdateLoggingConfigRequest):
    """Update logging configuration at runtime."""
    logger.info(f"Updating logging configuration: level={request.level}, enable_tracing={request.enable_tracing}")

    from backend.config import config_manager

    # Validate log level if provided
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if request.level and request.level not in valid_levels:
        logger.warning(f"Invalid log level: {request.level}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid log level. Must be one of: {', '.join(valid_levels)}"
        )

    try:
        # Update the configuration
        config_manager.update_logging_config(
            level=request.level,
            enable_tracing=request.enable_tracing
        )

        # Return updated configuration
        updated_config = config_manager.get_logging_config()
        logger.info(f"Logging configuration updated successfully: level={updated_config.level}, tracing={updated_config.enable_tracing}")

        return LoggingConfigResponse(
            level=updated_config.level,
            enable_tracing=updated_config.enable_tracing,
            log_file=updated_config.log_file
        )
    except Exception as e:
        logger.error(f"Failed to update logging configuration: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update logging configuration: {str(e)}"
        )


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
