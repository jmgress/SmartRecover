"""Tests for admin API routes."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app


client = TestClient(app)


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
