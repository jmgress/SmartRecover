import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict
from pydantic import BaseModel

from backend.models.incident import (
    Incident, IncidentQuery, AgentResponse, ChatRequest, 
    ExcludeItemRequest, ExcludedItem, AccuracyMetricsResponse, CategoryAccuracy
)
from backend.agents.orchestrator import OrchestratorAgent
from backend.data import mock_data
from backend.utils.logger import get_logger
from backend.llm.llm_manager import get_llm
from backend.cache import get_agent_cache

router = APIRouter()
orchestrator = OrchestratorAgent()
logger = get_logger(__name__)


@router.get("/incidents", response_model=List[Incident])
async def list_incidents():
    """List all available incidents."""
    logger.info("Listing all incidents")
    incidents = [Incident(**inc) for inc in mock_data.MOCK_INCIDENTS]
    logger.debug(f"Retrieved {len(incidents)} incidents")
    return incidents


@router.get("/incidents/{incident_id}", response_model=Incident)
async def get_incident(incident_id: str):
    """Get a specific incident by ID."""
    logger.info(f"Fetching incident: {incident_id}")
    for inc in mock_data.MOCK_INCIDENTS:
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
        success = mock_data.update_incident_status(incident_id, request.status)
        if not success:
            logger.warning(f"Incident not found for status update: {incident_id}")
            raise HTTPException(status_code=404, detail="Incident not found")
        
        # Return the updated incident
        for inc in mock_data.MOCK_INCIDENTS:
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
    for inc in mock_data.MOCK_INCIDENTS:
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
    incident_exists = any(inc["id"] == incident_id for inc in mock_data.MOCK_INCIDENTS)
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
    incident_exists = any(inc["id"] == query.incident_id for inc in mock_data.MOCK_INCIDENTS)
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
    log_file: Optional[str] = None


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
    level: Optional[str] = None
    enable_tracing: Optional[bool] = None


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
    incident_exists = any(inc["id"] == request.incident_id for inc in mock_data.MOCK_INCIDENTS)
    if not incident_exists:
        logger.warning(f"Incident not found for chat: {request.incident_id}")
        raise HTTPException(status_code=404, detail="Incident not found")
    
    async def generate_stream():
        """Generate SSE stream."""
        try:
            async for chunk in orchestrator.chat_stream(
                request.incident_id,
                request.message,
                request.conversation_history,
                request.excluded_items
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


class AgentPromptInfo(BaseModel):
    """Information about an agent's prompt."""
    current: str
    default: str
    is_custom: bool


class AgentPromptsResponse(BaseModel):
    """Response model for all agent prompts."""
    prompts: Dict[str, AgentPromptInfo]


@router.get("/admin/agent-prompts", response_model=AgentPromptsResponse)
async def get_agent_prompts():
    """Get all agent prompts with their current and default values."""
    logger.info("Fetching all agent prompts")
    
    from backend.prompts import get_prompt_manager
    prompt_manager = get_prompt_manager()
    
    prompts_data = prompt_manager.get_all_prompts()
    
    # Convert to response model format
    prompts = {
        agent_name: AgentPromptInfo(**prompt_info)
        for agent_name, prompt_info in prompts_data.items()
    }
    
    logger.info(f"Retrieved prompts for {len(prompts)} agents")
    return AgentPromptsResponse(prompts=prompts)


class UpdateAgentPromptRequest(BaseModel):
    """Request model for updating an agent prompt."""
    prompt: str


@router.put("/admin/agent-prompts/{agent_name}")
async def update_agent_prompt(agent_name: str, request: UpdateAgentPromptRequest):
    """Update the prompt for a specific agent."""
    logger.info(f"Updating prompt for agent: {agent_name}")
    
    from backend.prompts import get_prompt_manager
    prompt_manager = get_prompt_manager()
    
    # Validate agent name
    valid_agents = ["orchestrator", "servicenow", "knowledge_base", "change_correlation"]
    if agent_name not in valid_agents:
        logger.warning(f"Invalid agent name: {agent_name}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent name. Must be one of: {', '.join(valid_agents)}"
        )
    
    try:
        prompt_manager.set_prompt(agent_name, request.prompt)
        logger.info(f"Successfully updated prompt for agent: {agent_name}")
        
        # Return updated prompt info
        prompt_info = prompt_manager.get_all_prompts()[agent_name]
        return AgentPromptInfo(**prompt_info)
    except Exception as e:
        logger.error(f"Failed to update prompt for agent {agent_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update agent prompt: {str(e)}"
        )


@router.post("/admin/agent-prompts/reset")
async def reset_agent_prompts(agent_name: Optional[str] = None):
    """Reset agent prompts to their default values.
    
    Args:
        agent_name: Optional agent name to reset. If not provided, resets all agents.
    """
    from backend.prompts import get_prompt_manager
    prompt_manager = get_prompt_manager()
    
    if agent_name:
        logger.info(f"Resetting prompt for agent: {agent_name}")
        
        # Validate agent name
        valid_agents = ["orchestrator", "servicenow", "knowledge_base", "change_correlation"]
        if agent_name not in valid_agents:
            logger.warning(f"Invalid agent name for reset: {agent_name}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid agent name. Must be one of: {', '.join(valid_agents)}"
            )
        
        try:
            prompt_manager.reset_prompt(agent_name)
            logger.info(f"Successfully reset prompt for agent: {agent_name}")
            return {"message": f"Prompt reset successfully for {agent_name}"}
        except Exception as e:
            logger.error(f"Failed to reset prompt for agent {agent_name}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to reset agent prompt: {str(e)}"
            )
    else:
        logger.info("Resetting all agent prompts")
        try:
            prompt_manager.reset_all_prompts()
            logger.info("Successfully reset all agent prompts")
            return {"message": "All prompts reset successfully"}
        except Exception as e:
            logger.error(f"Failed to reset all prompts: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to reset prompts: {str(e)}"
            )


@router.get("/admin/accuracy-metrics", response_model=AccuracyMetricsResponse)
async def get_accuracy_metrics():
    """Get accuracy metrics for agent results based on user exclusions.
    
    This endpoint calculates accuracy scores for each category based on how many
    items users have excluded (deleted) from the results. The accuracy score
    represents the percentage of returned items that were NOT excluded.
    
    Returns:
        AccuracyMetricsResponse with per-category and overall accuracy metrics
    """
    logger.info("Fetching accuracy metrics")
    
    cache = get_agent_cache()
    
    # Get exclusion stats by source
    exclusion_stats = cache.get_exclusion_stats_by_source()
    
    # Get actual counts of items returned by each source from cached results
    items_by_source = cache.count_items_by_source()
    
    # Count total exclusions
    total_exclusions = sum(exclusion_stats.values())
    
    # Map sources to friendly category names
    source_to_category = {
        "servicenow": "Prior Incidents",
        "confluence": "Knowledge Base",
        "change_correlation": "Recent Changes",
        "logs": "System Logs",
        "events": "System Events",
        "remediation": "Remediations"
    }
    
    # Calculate metrics for each category
    categories = []
    total_items_returned = 0
    
    for source, category_name in source_to_category.items():
        exclusions = exclusion_stats.get(source, 0)
        items_count = items_by_source.get(source, 0)
        
        # Total items = actual items returned from cache
        total_items_returned += items_count
        
        # Calculate accuracy score (percentage of items that were NOT excluded)
        if items_count > 0:
            accuracy_score = ((items_count - exclusions) / items_count) * 100
        else:
            accuracy_score = 100.0  # No data means 100% accurate (no exclusions)
        
        categories.append(CategoryAccuracy(
            category=category_name,
            total_items_returned=items_count,
            total_items_excluded=exclusions,
            accuracy_score=round(accuracy_score, 2)
        ))
    
    # Calculate overall accuracy
    if total_items_returned > 0:
        overall_accuracy = ((total_items_returned - total_exclusions) / total_items_returned) * 100
    else:
        overall_accuracy = 100.0
    
    response = AccuracyMetricsResponse(
        categories=categories,
        overall_accuracy=round(overall_accuracy, 2),
        total_exclusions=total_exclusions,
        total_items_returned=total_items_returned
    )
    
    logger.info(f"Accuracy metrics calculated: {total_exclusions} exclusions, {total_items_returned} items returned, {overall_accuracy:.2f}% accuracy")
    return response


@router.post("/incidents/{incident_id}/exclude-item")
async def exclude_item(incident_id: str, request: ExcludeItemRequest):
    """Exclude an item from being included in chat context for this incident.
    
    Args:
        incident_id: The incident ID
        request: The item exclusion request
        
    Returns:
        Success message
    """
    logger.info(f"Excluding item {request.item_id} for incident {incident_id}")
    
    # Verify incident exists
    incident_exists = any(inc["id"] == incident_id for inc in mock_data.MOCK_INCIDENTS)
    if not incident_exists:
        logger.warning(f"Incident not found: {incident_id}")
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Create composite item ID (source:item_id)
    composite_id = f"{request.source}:{request.item_id}"
    
    # Add to cache with metadata
    cache = get_agent_cache()
    cache.add_excluded_item(
        incident_id, 
        composite_id,
        source=request.source,
        item_type=request.item_type,
        reason=request.reason or ""
    )
    
    logger.info(f"Successfully excluded item {composite_id} for incident {incident_id}")
    return {
        "message": "Item excluded successfully",
        "incident_id": incident_id,
        "excluded_item": composite_id
    }


@router.get("/incidents/{incident_id}/excluded-items", response_model=List[str])
async def get_excluded_items(incident_id: str):
    """Get all excluded items for an incident.
    
    Args:
        incident_id: The incident ID
        
    Returns:
        List of excluded item IDs
    """
    logger.info(f"Fetching excluded items for incident {incident_id}")
    
    # Verify incident exists
    incident_exists = any(inc["id"] == incident_id for inc in mock_data.MOCK_INCIDENTS)
    if not incident_exists:
        logger.warning(f"Incident not found: {incident_id}")
        raise HTTPException(status_code=404, detail="Incident not found")
    
    cache = get_agent_cache()
    excluded_items = cache.get_excluded_items(incident_id)
    
    logger.debug(f"Found {len(excluded_items)} excluded items for incident {incident_id}")
    return excluded_items


@router.delete("/incidents/{incident_id}/excluded-items/{item_id}")
async def unexclude_item(incident_id: str, item_id: str):
    """Remove an item from the exclusion list (undo exclude).
    
    Args:
        incident_id: The incident ID
        item_id: The composite item ID (source:item_id)
        
    Returns:
        Success message
    """
    logger.info(f"Un-excluding item {item_id} for incident {incident_id}")
    
    # Verify incident exists
    incident_exists = any(inc["id"] == incident_id for inc in mock_data.MOCK_INCIDENTS)
    if not incident_exists:
        logger.warning(f"Incident not found: {incident_id}")
        raise HTTPException(status_code=404, detail="Incident not found")
    
    cache = get_agent_cache()
    cache.remove_excluded_item(incident_id, item_id)
    
    logger.info(f"Successfully un-excluded item {item_id} for incident {incident_id}")
    return {
        "message": "Item un-excluded successfully",
        "incident_id": incident_id,
        "item_id": item_id
    }


@router.get("/admin/prompt-logs")
async def get_prompt_logs(incident_id: Optional[str] = None, limit: int = 100):
    """Get prompt logs, optionally filtered by incident ID.
    
    Args:
        incident_id: Optional incident ID to filter by
        limit: Maximum number of logs to return (default: 100, max: 500)
        
    Returns:
        List of prompt logs
    """
    logger.info(f"Fetching prompt logs (incident_id={incident_id}, limit={limit})")
    
    # Validate limit
    if limit > 500:
        limit = 500
    
    cache = get_agent_cache()
    logs = cache.get_prompt_logs(incident_id=incident_id, limit=limit)
    
    logger.debug(f"Retrieved {len(logs)} prompt logs")
    return {
        "logs": logs,
        "total_count": len(logs)
    }


@router.delete("/admin/prompt-logs")
async def clear_prompt_logs():
    """Clear all prompt logs.
    
    Returns:
        Success message
    """
    logger.info("Clearing all prompt logs")
    
    cache = get_agent_cache()
    cache.clear_prompt_logs()
    
    logger.info("Successfully cleared all prompt logs")
    return {"message": "All prompt logs cleared successfully"}
