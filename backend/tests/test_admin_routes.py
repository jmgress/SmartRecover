"""Tests for admin API routes."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.data.automation_store import AutomationStore


client = TestClient(app)


@pytest.fixture
def temp_automation_store(tmp_path, monkeypatch):
    store = AutomationStore(storage_path=tmp_path / "automation_rules.json")
    monkeypatch.setattr("backend.api.routes.automation_store", store)
    monkeypatch.setattr("backend.api.routes.orchestrator.automation_store", store)
    return store


def test_get_llm_config():
    """Test the LLM config endpoint returns configuration details."""
    response = client.get("/api/v1/admin/llm-config")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify required fields are present
    assert "provider" in data
    assert "model" in data
    assert "connection_details" in data
    assert "temperature" in data
    
    # Verify provider is one of the expected values
    assert data["provider"] in ["openai", "gemini", "ollama"]
    
    # Verify model is not empty
    assert data["model"]
    assert len(data["model"]) > 0
    
    # Verify temperature is a float
    assert isinstance(data["temperature"], (int, float))
    assert 0.0 <= data["temperature"] <= 2.0
    
    # Verify connection_details is a dict
    assert isinstance(data["connection_details"], dict)


def test_get_llm_config_ollama_details():
    """Test that Ollama configuration includes expected details."""
    response = client.get("/api/v1/admin/llm-config")
    
    assert response.status_code == 200
    data = response.json()
    
    # If provider is ollama, should have base_url and local flag
    if data["provider"] == "ollama":
        assert "base_url" in data["connection_details"]
        assert "local" in data["connection_details"]
        assert data["connection_details"]["local"] is True


def test_get_llm_config_cloud_provider_details():
    """Test that cloud providers include API key status."""
    response = client.get("/api/v1/admin/llm-config")
    
    assert response.status_code == 200
    data = response.json()
    
    # If provider is OpenAI or Gemini, should have api_key_configured and endpoint
    if data["provider"] in ["openai", "gemini"]:
        assert "api_key_configured" in data["connection_details"]
        assert "endpoint" in data["connection_details"]
        assert isinstance(data["connection_details"]["api_key_configured"], bool)


def test_get_logging_config():
    """Test the logging config endpoint returns configuration details."""
    response = client.get("/api/v1/admin/logging-config")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify required fields are present
    assert "level" in data
    assert "enable_tracing" in data
    assert "log_file" in data
    
    # Verify level is one of the expected values
    assert data["level"] in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    
    # Verify enable_tracing is a boolean
    assert isinstance(data["enable_tracing"], bool)


def test_update_logging_config_level():
    """Test updating the logging level."""
    # First get current config
    response = client.get("/api/v1/admin/logging-config")
    assert response.status_code == 200
    original_config = response.json()
    
    # Update to DEBUG level
    response = client.put("/api/v1/admin/logging-config", json={"level": "DEBUG"})
    assert response.status_code == 200
    data = response.json()
    assert data["level"] == "DEBUG"
    
    # Verify the change persisted
    response = client.get("/api/v1/admin/logging-config")
    assert response.status_code == 200
    data = response.json()
    assert data["level"] == "DEBUG"
    
    # Restore original level
    client.put("/api/v1/admin/logging-config", json={"level": original_config["level"]})


def test_update_logging_config_tracing():
    """Test enabling/disabling tracing."""
    # First get current config
    response = client.get("/api/v1/admin/logging-config")
    assert response.status_code == 200
    original_config = response.json()
    
    # Toggle tracing
    new_tracing = not original_config["enable_tracing"]
    response = client.put("/api/v1/admin/logging-config", json={"enable_tracing": new_tracing})
    assert response.status_code == 200
    data = response.json()
    assert data["enable_tracing"] == new_tracing
    
    # Verify the change persisted
    response = client.get("/api/v1/admin/logging-config")
    assert response.status_code == 200
    data = response.json()
    assert data["enable_tracing"] == new_tracing
    
    # Restore original setting
    client.put("/api/v1/admin/logging-config", json={"enable_tracing": original_config["enable_tracing"]})


def test_update_logging_config_invalid_level():
    """Test that invalid log levels are rejected."""
    response = client.put("/api/v1/admin/logging-config", json={"level": "INVALID"})
    assert response.status_code == 400
    data = response.json()
    assert "Invalid log level" in data["detail"]


def test_update_logging_config_both_params():
    """Test updating both level and tracing at once."""
    # First get current config
    response = client.get("/api/v1/admin/logging-config")
    assert response.status_code == 200
    original_config = response.json()
    
    # Update both parameters
    response = client.put("/api/v1/admin/logging-config", json={
        "level": "WARNING",
        "enable_tracing": True
    })
    assert response.status_code == 200
    data = response.json()
    assert data["level"] == "WARNING"
    assert data["enable_tracing"] is True
    
    # Restore original config
    client.put("/api/v1/admin/logging-config", json={
        "level": original_config["level"],
        "enable_tracing": original_config["enable_tracing"]
    })


def test_get_automation_config(temp_automation_store):
    """Test the automation config endpoint returns all category rules."""
    response = client.get("/api/v1/admin/automation-config")

    assert response.status_code == 200
    data = response.json()
    assert data["global_enabled"] is True
    assert len(data["rules"]) == 10
    assert any(rule["category"] == "Database" for rule in data["rules"])
    assert data["recent_audit"] == []


def test_update_automation_config_persists(temp_automation_store):
    """Test automation configuration updates persist across reads."""
    payload = {
        "global_enabled": True,
        "rules": [
            {
                "category": "Database",
                "enabled": True,
                "threshold": 0.6,
                "max_risk_level": "low",
                "max_severity": "medium",
            }
        ],
    }

    response = client.put("/api/v1/admin/automation-config", json=payload)
    assert response.status_code == 200
    data = response.json()
    database_rule = next(rule for rule in data["rules"] if rule["category"] == "Database")
    assert database_rule["enabled"] is True
    assert database_rule["threshold"] == 0.6

    reloaded = client.get("/api/v1/admin/automation-config")
    assert reloaded.status_code == 200
    reloaded_rule = next(
        rule for rule in reloaded.json()["rules"] if rule["category"] == "Database"
    )
    assert reloaded_rule["enabled"] is True
    assert reloaded_rule["threshold"] == 0.6
