"""Tests for prompt logging functionality."""
import pytest
from datetime import datetime
from backend.cache.agent_cache import AgentCache
from backend.models.incident import PromptLog


def test_add_prompt_log():
    """Test adding a prompt log to the cache."""
    cache = AgentCache()
    
    log_id = cache.add_prompt_log(
        incident_id="INC001",
        prompt_type="synthesis",
        system_prompt="You are an expert assistant.",
        user_message="Help me resolve this incident.",
        context_summary="Test context"
    )
    
    assert log_id is not None
    assert len(log_id) > 0


def test_get_prompt_logs():
    """Test retrieving prompt logs from the cache."""
    cache = AgentCache()
    
    # Add multiple logs
    cache.add_prompt_log(
        incident_id="INC001",
        prompt_type="synthesis",
        system_prompt="System prompt 1",
        user_message="User message 1",
        context_summary="Context 1"
    )
    
    cache.add_prompt_log(
        incident_id="INC002",
        prompt_type="chat",
        system_prompt="System prompt 2",
        user_message="User message 2",
        context_summary="Context 2"
    )
    
    # Get all logs
    logs = cache.get_prompt_logs()
    assert len(logs) == 2
    assert logs[0]["incident_id"] in ["INC001", "INC002"]
    assert logs[0]["prompt_type"] in ["synthesis", "chat"]


def test_get_prompt_logs_filtered():
    """Test retrieving prompt logs filtered by incident ID."""
    cache = AgentCache()
    
    # Add logs for different incidents
    cache.add_prompt_log(
        incident_id="INC001",
        prompt_type="synthesis",
        system_prompt="System prompt 1",
        user_message="User message 1"
    )
    
    cache.add_prompt_log(
        incident_id="INC002",
        prompt_type="synthesis",
        system_prompt="System prompt 2",
        user_message="User message 2"
    )
    
    cache.add_prompt_log(
        incident_id="INC001",
        prompt_type="chat",
        system_prompt="System prompt 3",
        user_message="User message 3"
    )
    
    # Get logs for INC001 only
    logs = cache.get_prompt_logs(incident_id="INC001")
    assert len(logs) == 2
    for log in logs:
        assert log["incident_id"] == "INC001"


def test_get_prompt_logs_with_limit():
    """Test retrieving prompt logs with limit."""
    cache = AgentCache()
    
    # Add 5 logs
    for i in range(5):
        cache.add_prompt_log(
            incident_id=f"INC00{i}",
            prompt_type="synthesis",
            system_prompt=f"System prompt {i}",
            user_message=f"User message {i}"
        )
    
    # Get only 3 logs
    logs = cache.get_prompt_logs(limit=3)
    assert len(logs) == 3


def test_clear_prompt_logs():
    """Test clearing all prompt logs."""
    cache = AgentCache()
    
    # Add some logs
    cache.add_prompt_log(
        incident_id="INC001",
        prompt_type="synthesis",
        system_prompt="System prompt",
        user_message="User message"
    )
    
    cache.add_prompt_log(
        incident_id="INC002",
        prompt_type="chat",
        system_prompt="System prompt 2",
        user_message="User message 2"
    )
    
    # Verify logs exist
    logs = cache.get_prompt_logs()
    assert len(logs) == 2
    
    # Clear logs
    cache.clear_prompt_logs()
    
    # Verify logs are cleared
    logs = cache.get_prompt_logs()
    assert len(logs) == 0


def test_prompt_log_with_conversation_history():
    """Test adding a prompt log with conversation history."""
    cache = AgentCache()
    
    conversation_history = [
        {"role": "user", "content": "Previous question"},
        {"role": "assistant", "content": "Previous answer"}
    ]
    
    log_id = cache.add_prompt_log(
        incident_id="INC001",
        prompt_type="chat",
        system_prompt="System prompt",
        user_message="Current question",
        conversation_history=conversation_history,
        context_summary="Chat context"
    )
    
    # Retrieve the log
    logs = cache.get_prompt_logs()
    assert len(logs) == 1
    assert logs[0]["conversation_history"] == conversation_history
    assert logs[0]["context_summary"] == "Chat context"


def test_prompt_log_timestamp():
    """Test that prompt logs have timestamps."""
    cache = AgentCache()
    
    cache.add_prompt_log(
        incident_id="INC001",
        prompt_type="synthesis",
        system_prompt="System prompt",
        user_message="User message"
    )
    
    logs = cache.get_prompt_logs()
    assert len(logs) == 1
    assert "timestamp" in logs[0]
    
    # Verify timestamp is in ISO format
    timestamp_str = logs[0]["timestamp"]
    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    assert timestamp is not None


def test_prompt_log_max_size():
    """Test that prompt logs maintain a max size (1000 entries)."""
    cache = AgentCache()
    
    # Add 1050 logs
    for i in range(1050):
        cache.add_prompt_log(
            incident_id=f"INC{i:04d}",
            prompt_type="synthesis",
            system_prompt=f"System prompt {i}",
            user_message=f"User message {i}"
        )
    
    # Should only keep last 1000
    logs = cache.get_prompt_logs(limit=2000)  # Request more than exists
    assert len(logs) == 1000
