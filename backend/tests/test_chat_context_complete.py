"""
End-to-end test to verify logs and events context is included in chat.

This test verifies that when an incident is queried via chat:
1. All 5 agents are executed
2. Logs and events data is collected
3. Context string includes logs and events
4. LLM receives complete context
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.agents.orchestrator import OrchestratorAgent
from backend.models.incident import ChatMessage


@pytest.mark.asyncio
async def test_chat_includes_logs_and_events_context():
    """Test that chat context includes logs and events from all agents."""
    
    # Create a mock LLM
    mock_llm = MagicMock()
    captured_context = None
    
    async def mock_stream(*args, **kwargs):
        nonlocal captured_context
        # Capture the system message which contains the context
        messages = args[0]
        if messages and len(messages) > 0:
            captured_context = messages[0].content
        yield MagicMock(content="Test response")
    
    mock_llm.astream = mock_stream
    
    with patch('backend.agents.orchestrator.get_llm', return_value=mock_llm):
        orchestrator = OrchestratorAgent()
        orchestrator.llm = mock_llm
        
        # Execute chat stream
        chunks = []
        async for chunk in orchestrator.chat_stream(
            incident_id="INC001",
            user_message="What's happening with this incident?",
            conversation_history=[]
        ):
            chunks.append(chunk)
        
        # Verify we got a response
        assert len(chunks) > 0
        
        # Verify context was captured
        assert captured_context is not None, "Context should be captured from system message"
        
        # Verify context includes logs section
        assert "RELEVANT LOG ENTRIES" in captured_context, \
            "Context should include logs section"
        assert "Errors:" in captured_context, \
            "Context should include error count from logs"
        assert "Warnings:" in captured_context, \
            "Context should include warning count from logs"
        
        # Verify context includes events section
        assert "RELEVANT EVENTS" in captured_context, \
            "Context should include events section"
        assert "Critical:" in captured_context, \
            "Context should include critical count from events"
        
        # Verify other sections still exist
        assert "TOP SUSPECT CHANGE" in captured_context or "SIMILAR HISTORICAL INCIDENTS" in captured_context, \
            "Context should still include other agent data"
        
        print("\n" + "="*80)
        print("CAPTURED CONTEXT FROM LLM CALL:")
        print("="*80)
        print(captured_context)
        print("="*80)


@pytest.mark.asyncio
async def test_chat_context_format_logs():
    """Test that logs are formatted correctly in context."""
    
    mock_llm = MagicMock()
    captured_context = None
    
    async def mock_stream(*args, **kwargs):
        nonlocal captured_context
        messages = args[0]
        if messages and len(messages) > 0:
            captured_context = messages[0].content
        yield MagicMock(content="Response")
    
    mock_llm.astream = mock_stream
    
    with patch('backend.agents.orchestrator.get_llm', return_value=mock_llm):
        orchestrator = OrchestratorAgent()
        orchestrator.llm = mock_llm
        
        chunks = []
        async for chunk in orchestrator.chat_stream(
            incident_id="INC001",
            user_message="Show me the logs",
            conversation_history=[]
        ):
            chunks.append(chunk)
        
        # Verify log entries have the expected format: [LEVEL] service: message (confidence: XX%)
        assert captured_context is not None
        
        # Look for log entry patterns
        has_error_logs = "[ERROR]" in captured_context or "[WARN]" in captured_context or "[INFO]" in captured_context
        has_confidence = "confidence:" in captured_context
        
        assert has_error_logs, "Context should include log level markers"
        assert has_confidence, "Context should include confidence scores"


@pytest.mark.asyncio
async def test_chat_context_format_events():
    """Test that events are formatted correctly in context."""
    
    mock_llm = MagicMock()
    captured_context = None
    
    async def mock_stream(*args, **kwargs):
        nonlocal captured_context
        messages = args[0]
        if messages and len(messages) > 0:
            captured_context = messages[0].content
        yield MagicMock(content="Response")
    
    mock_llm.astream = mock_stream
    
    with patch('backend.agents.orchestrator.get_llm', return_value=mock_llm):
        orchestrator = OrchestratorAgent()
        orchestrator.llm = mock_llm
        
        chunks = []
        async for chunk in orchestrator.chat_stream(
            incident_id="INC001",
            user_message="What events occurred?",
            conversation_history=[]
        ):
            chunks.append(chunk)
        
        # Verify event entries have the expected format: [SEVERITY] application: type - message
        assert captured_context is not None
        
        # Look for event patterns
        has_severity = "[CRITICAL]" in captured_context or "[WARNING]" in captured_context or "[INFO]" in captured_context
        has_confidence = "confidence:" in captured_context
        
        assert has_severity, "Context should include event severity markers"
        assert has_confidence, "Context should include confidence scores for events"
