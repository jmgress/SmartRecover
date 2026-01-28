"""Integration tests for chat streaming functionality."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.agents.orchestrator import OrchestratorAgent
from backend.models.incident import ChatMessage


@pytest.mark.asyncio
async def test_chat_stream_with_mock_llm():
    """Test chat streaming with a mocked LLM."""
    
    # Create a mock LLM that returns chunks
    mock_llm = MagicMock()
    
    # Mock the astream method to return an async generator
    async def mock_stream(*args, **kwargs):
        chunks = ["Hello", " from", " the", " LLM", "!"]
        for chunk in chunks:
            mock_chunk = MagicMock()
            mock_chunk.content = chunk
            yield mock_chunk
    
    mock_llm.astream = mock_stream
    
    # Create orchestrator with mocked LLM
    with patch('backend.agents.orchestrator.get_llm', return_value=mock_llm):
        orchestrator = OrchestratorAgent()
        orchestrator.llm = mock_llm
        
        # Test the streaming
        result_chunks = []
        async for chunk in orchestrator.chat_stream(
            incident_id="INC001",
            user_message="What is the issue?",
            conversation_history=[]
        ):
            result_chunks.append(chunk)
        
        # Verify we got the chunks
        assert len(result_chunks) == 5
        assert "".join(result_chunks) == "Hello from the LLM!"


@pytest.mark.asyncio
async def test_chat_stream_uses_cache():
    """Test that chat streaming uses cached agent data."""
    
    mock_llm = MagicMock()
    
    async def mock_stream(*args, **kwargs):
        yield MagicMock(content="Response")
    
    mock_llm.astream = mock_stream
    
    with patch('backend.agents.orchestrator.get_llm', return_value=mock_llm):
        orchestrator = OrchestratorAgent()
        orchestrator.llm = mock_llm
        
        # First call - should populate cache
        chunks1 = []
        async for chunk in orchestrator.chat_stream(
            incident_id="INC001",
            user_message="First question",
            conversation_history=[]
        ):
            chunks1.append(chunk)
        
        # Check that cache was populated
        cached_data = orchestrator.cache.get("INC001")
        assert cached_data is not None
        assert "servicenow_results" in cached_data
        assert "confluence_results" in cached_data
        assert "change_results" in cached_data
        assert "logs_results" in cached_data
        
        # Second call - should use cache (we can verify by checking no agent calls)
        chunks2 = []
        async for chunk in orchestrator.chat_stream(
            incident_id="INC001",
            user_message="Second question",
            conversation_history=[]
        ):
            chunks2.append(chunk)
        
        # Both should have responses
        assert len(chunks1) > 0
        assert len(chunks2) > 0


@pytest.mark.asyncio
async def test_chat_stream_with_conversation_history():
    """Test that conversation history is properly included."""
    
    mock_llm = MagicMock()
    messages_received = []
    
    async def mock_stream(*args, **kwargs):
        # Capture the messages
        messages_received.extend(args[0])
        yield MagicMock(content="Response")
    
    mock_llm.astream = mock_stream
    
    with patch('backend.agents.orchestrator.get_llm', return_value=mock_llm):
        orchestrator = OrchestratorAgent()
        orchestrator.llm = mock_llm
        
        # Create conversation history
        history = [
            ChatMessage(role="user", content="First question"),
            ChatMessage(role="assistant", content="First answer"),
            ChatMessage(role="user", content="Second question"),
        ]
        
        chunks = []
        async for chunk in orchestrator.chat_stream(
            incident_id="INC001",
            user_message="Third question",
            conversation_history=history
        ):
            chunks.append(chunk)
        
        # Verify messages were passed to LLM
        assert len(messages_received) > 0
        # Should have: system message + 3 history messages + current message
        assert len(messages_received) >= 5


@pytest.mark.asyncio
async def test_chat_stream_context_includes_agent_data():
    """Test that the context includes data from all agents."""
    
    mock_llm = MagicMock()
    system_message_content = None
    
    async def mock_stream(*args, **kwargs):
        nonlocal system_message_content
        # Capture the system message
        messages = args[0]
        if messages and len(messages) > 0:
            system_message_content = messages[0].content
        yield MagicMock(content="Response")
    
    mock_llm.astream = mock_stream
    
    with patch('backend.agents.orchestrator.get_llm', return_value=mock_llm):
        orchestrator = OrchestratorAgent()
        orchestrator.llm = mock_llm
        
        chunks = []
        async for chunk in orchestrator.chat_stream(
            incident_id="INC001",
            user_message="What's the issue?",
            conversation_history=[]
        ):
            chunks.append(chunk)
        
        # Verify system message contains context
        assert system_message_content is not None
        # Should mention it's an assistant for the incident
        assert "INC001" in system_message_content
        assert "incident" in system_message_content.lower()


@pytest.mark.asyncio
async def test_chat_stream_context_includes_logs_data():
    """Test that the context includes logs data with error and warning prioritization."""
    
    mock_llm = MagicMock()
    system_message_content = None
    
    async def mock_stream(*args, **kwargs):
        nonlocal system_message_content
        # Capture the system message
        messages = args[0]
        if messages and len(messages) > 0:
            system_message_content = messages[0].content
        yield MagicMock(content="Response")
    
    mock_llm.astream = mock_stream
    
    # Mock logs data with errors and warnings
    mock_logs_data = {
        "source": "splunk",
        "incident_id": "INC001",
        "logs": [
            {
                "timestamp": "2026-01-27T10:32:15Z",
                "level": "ERROR",
                "service": "payment-service",
                "message": "Connection timeout to database after 30s",
                "confidence_score": 0.8
            },
            {
                "timestamp": "2026-01-27T10:30:00Z",
                "level": "WARN",
                "service": "payment-service",
                "message": "Connection pool running low",
                "confidence_score": 0.6
            }
        ],
        "total_count": 2,
        "error_count": 1,
        "warning_count": 1
    }
    
    with patch('backend.agents.orchestrator.get_llm', return_value=mock_llm):
        orchestrator = OrchestratorAgent()
        orchestrator.llm = mock_llm
        
        # Mock the _get_or_fetch_agent_data to return our mock logs data
        async def mock_get_agent_data(incident_id, user_query):
            return {
                "servicenow_results": {},
                "confluence_results": {},
                "change_results": {},
                "logs_results": mock_logs_data,
                "events_results": {}
            }
        
        orchestrator._get_or_fetch_agent_data = mock_get_agent_data
        
        chunks = []
        async for chunk in orchestrator.chat_stream(
            incident_id="INC001",
            user_message="What errors are in the logs?",
            conversation_history=[]
        ):
            chunks.append(chunk)
        
        # Verify system message contains logs context
        assert system_message_content is not None
        assert "RELEVANT LOGS" in system_message_content
        assert "Summary:" in system_message_content
        
        # Check for correct pluralization and counts
        assert "1 error" in system_message_content
        assert "1 warning" in system_message_content
        
        # Check that ERROR and WARN level logs are included
        assert "Recent Errors:" in system_message_content
        assert "Connection timeout to database after 30s" in system_message_content
        assert "Recent Warnings:" in system_message_content
        assert "Connection pool running low" in system_message_content


@pytest.mark.asyncio  
async def test_chat_stream_error_handling():
    """Test that errors in streaming are handled gracefully."""
    
    mock_llm = MagicMock()
    
    async def mock_stream_with_error(*args, **kwargs):
        yield MagicMock(content="Partial")
        raise Exception("LLM connection error")
    
    mock_llm.astream = mock_stream_with_error
    
    with patch('backend.agents.orchestrator.get_llm', return_value=mock_llm):
        orchestrator = OrchestratorAgent()
        orchestrator.llm = mock_llm
        
        chunks = []
        # Should not raise, but yield error message
        async for chunk in orchestrator.chat_stream(
            incident_id="INC001",
            user_message="Question",
            conversation_history=[]
        ):
            chunks.append(chunk)
        
        # Should have partial response and error
        assert len(chunks) >= 1
        combined = "".join(chunks)
        assert "Partial" in combined or "Error" in combined

