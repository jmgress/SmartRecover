"""Configuration management for SmartRecover LLM settings."""
import os
import yaml
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class OpenAIConfig(BaseModel):
    """OpenAI LLM configuration."""
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    api_key: Optional[str] = None


class GeminiConfig(BaseModel):
    """Google Gemini LLM configuration."""
    model: str = "gemini-pro"
    temperature: float = 0.7
    api_key: Optional[str] = None


class OllamaConfig(BaseModel):
    """Ollama LLM configuration."""
    model: str = "llama2"
    base_url: str = "http://localhost:11434"
    temperature: float = 0.7


class LLMConfig(BaseModel):
    """LLM provider configuration."""
    provider: str = Field(default="openai", pattern="^(openai|gemini|ollama)$")
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    gemini: GeminiConfig = Field(default_factory=GeminiConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)


class Config(BaseModel):
    """Main application configuration."""
    llm: LLMConfig = Field(default_factory=LLMConfig)


class ConfigManager:
    """Manages application configuration loading and access."""
    
    _instance: Optional['ConfigManager'] = None
    _config: Optional[Config] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._config = self._load_config()
    
    def _load_config(self) -> Config:
        """Load configuration from YAML file and environment variables."""
        logger.debug("Loading configuration")
        
        # Default configuration
        config_dict: Dict[str, Any] = {
            "llm": {
                "provider": "openai",
                "openai": {"model": "gpt-3.5-turbo", "temperature": 0.7},
                "gemini": {"model": "gemini-pro", "temperature": 0.7},
                "ollama": {"model": "llama2", "base_url": "http://localhost:11434", "temperature": 0.7}
            }
        }
        
        # Try to load from YAML file
        # Allow override via CONFIG_PATH environment variable
        config_path_str = os.getenv("CONFIG_PATH")
        if config_path_str:
            config_path = Path(config_path_str)
            logger.debug(f"Using config path from CONFIG_PATH: {config_path}")
        else:
            config_path = Path(__file__).parent / "config.yaml"
            logger.debug(f"Using default config path: {config_path}")
        
        if config_path.exists():
            logger.info(f"Loading configuration from {config_path}")
            with open(config_path, 'r') as f:
                yaml_config = yaml.safe_load(f)
                if yaml_config:
                    config_dict.update(yaml_config)
                    logger.debug("YAML configuration loaded successfully")
        else:
            logger.warning(f"Configuration file not found: {config_path}, using defaults")
        
        # Override with environment variables if present
        provider = os.getenv("LLM_PROVIDER")
        if provider:
            logger.info(f"Overriding LLM provider from environment: {provider}")
            config_dict["llm"]["provider"] = provider
        
        # OpenAI environment variables
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            config_dict["llm"]["openai"]["api_key"] = openai_api_key
            logger.debug("OpenAI API key loaded from environment")
        
        openai_model = os.getenv("OPENAI_MODEL")
        if openai_model:
            logger.info(f"Overriding OpenAI model from environment: {openai_model}")
            config_dict["llm"]["openai"]["model"] = openai_model
        
        # Gemini environment variables
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if google_api_key:
            config_dict["llm"]["gemini"]["api_key"] = google_api_key
            logger.debug("Google API key loaded from environment")
        
        gemini_model = os.getenv("GEMINI_MODEL")
        if gemini_model:
            logger.info(f"Overriding Gemini model from environment: {gemini_model}")
            config_dict["llm"]["gemini"]["model"] = gemini_model
        
        # Ollama environment variables
        ollama_base_url = os.getenv("OLLAMA_BASE_URL")
        if ollama_base_url:
            logger.info(f"Overriding Ollama base URL from environment: {ollama_base_url}")
            config_dict["llm"]["ollama"]["base_url"] = ollama_base_url
        
        ollama_model = os.getenv("OLLAMA_MODEL")
        if ollama_model:
            logger.info(f"Overriding Ollama model from environment: {ollama_model}")
            config_dict["llm"]["ollama"]["model"] = ollama_model
        
        config = Config(**config_dict)
        logger.info(f"Configuration loaded successfully, provider: {config.llm.provider}")
        return config
    
    @property
    def config(self) -> Config:
        """Get the current configuration."""
        return self._config
    
    def get_llm_config(self) -> LLMConfig:
        """Get LLM configuration."""
        return self._config.llm
    
    def reload(self):
        """Reload configuration from file and environment."""
        logger.info("Reloading configuration")
        self._config = self._load_config()
        logger.info("Configuration reloaded successfully")


# Singleton instance
config_manager = ConfigManager()


def get_config() -> Config:
    """Get the application configuration."""
    return config_manager.config
