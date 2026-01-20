"""
Pytest tests for backend configuration management.
"""

import pytest

from backend.config import (
    Config,
    GeminiConfig,
    LLMConfig,
    LoggingConfig,
    OllamaConfig,
    OpenAIConfig,
)


def test_default_config_creation():
    """Test that default configuration can be created."""
    config = Config()
    assert config.llm.provider in ["openai", "gemini", "ollama"]
    assert config.logging.level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def test_llm_config_defaults():
    """Test LLM configuration defaults."""
    llm_config = LLMConfig()
    assert llm_config.provider == "openai"
    assert isinstance(llm_config.openai, OpenAIConfig)
    assert isinstance(llm_config.gemini, GeminiConfig)
    assert isinstance(llm_config.ollama, OllamaConfig)


def test_openai_config():
    """Test OpenAI configuration."""
    config = OpenAIConfig(model="gpt-4", temperature=0.8)
    assert config.model == "gpt-4"
    assert config.temperature == 0.8


def test_gemini_config():
    """Test Gemini configuration."""
    config = GeminiConfig(model="gemini-pro", temperature=0.5)
    assert config.model == "gemini-pro"
    assert config.temperature == 0.5


def test_ollama_config():
    """Test Ollama configuration."""
    config = OllamaConfig(model="llama2", base_url="http://localhost:11434")
    assert config.model == "llama2"
    assert config.base_url == "http://localhost:11434"


def test_logging_config():
    """Test logging configuration."""
    logging_config = LoggingConfig(level="DEBUG", enable_tracing=True)
    assert logging_config.level == "DEBUG"
    assert logging_config.enable_tracing is True


def test_invalid_provider():
    """Test that invalid provider raises validation error."""
    with pytest.raises(Exception):  # Pydantic ValidationError
        LLMConfig(provider="invalid")


def test_invalid_log_level():
    """Test that invalid log level raises validation error."""
    with pytest.raises(Exception):  # Pydantic ValidationError
        LoggingConfig(level="INVALID")


def test_complete_config():
    """Test complete configuration with all settings."""
    config = Config(
        llm=LLMConfig(
            provider="openai", openai=OpenAIConfig(model="gpt-4", temperature=0.9)
        ),
        logging=LoggingConfig(level="INFO", enable_tracing=False),
    )
    assert config.llm.provider == "openai"
    assert config.llm.openai.model == "gpt-4"
    assert config.logging.level == "INFO"
