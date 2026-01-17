"""Configuration management for SmartRecover LLM settings."""
import os
import yaml
import threading
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


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
        else:
            config_path = Path(__file__).parent / "config.yaml"
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                yaml_config = yaml.safe_load(f)
                if yaml_config:
                    config_dict.update(yaml_config)
        
        # Override with environment variables if present
        provider = os.getenv("LLM_PROVIDER")
        if provider:
            config_dict["llm"]["provider"] = provider
        
        # OpenAI environment variables
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            config_dict["llm"]["openai"]["api_key"] = openai_api_key
        
        openai_model = os.getenv("OPENAI_MODEL")
        if openai_model:
            config_dict["llm"]["openai"]["model"] = openai_model
        
        # Gemini environment variables
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if google_api_key:
            config_dict["llm"]["gemini"]["api_key"] = google_api_key
        
        gemini_model = os.getenv("GEMINI_MODEL")
        if gemini_model:
            config_dict["llm"]["gemini"]["model"] = gemini_model
        
        # Ollama environment variables
        ollama_base_url = os.getenv("OLLAMA_BASE_URL")
        if ollama_base_url:
            config_dict["llm"]["ollama"]["base_url"] = ollama_base_url
        
        ollama_model = os.getenv("OLLAMA_MODEL")
        if ollama_model:
            config_dict["llm"]["ollama"]["model"] = ollama_model
        
        return Config(**config_dict)
    
    @property
    def config(self) -> Config:
        """Get the current configuration."""
        return self._config
    
    def get_llm_config(self) -> LLMConfig:
        """Get LLM configuration."""
        return self._config.llm
    
    def reload(self):
        """Reload configuration from file and environment."""
        self._config = self._load_config()


# Singleton instance
config_manager = ConfigManager()


def get_config() -> Config:
    """Get the application configuration."""
    return config_manager.config
