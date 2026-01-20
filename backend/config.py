"""Configuration management for SmartRecover LLM settings."""
import os
import yaml
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


# ============================================================================
# Connector Configuration Models
# ============================================================================

class ServiceNowConfig(BaseModel):
    """ServiceNow connector configuration."""
    instance_url: str = ""
    username: str = ""
    password: str = ""
    client_id: Optional[str] = None
    client_secret: Optional[str] = None


class JiraConfig(BaseModel):
    """Jira Service Management connector configuration."""
    url: str = ""
    username: str = ""
    api_token: str = ""
    project_key: str = ""


class MockConfig(BaseModel):
    """Mock connector configuration."""
    data_source: str = "mock"


class ConnectorConfig(BaseModel):
    """Connector configuration for incident management systems."""
    connector_type: Literal["servicenow", "jira", "mock"] = "mock"
    servicenow: Optional[ServiceNowConfig] = None
    jira: Optional[JiraConfig] = None
    mock: Optional[MockConfig] = Field(default_factory=MockConfig)


# ============================================================================
# Knowledge Base Configuration Models
# ============================================================================

class ConfluenceKBConfig(BaseModel):
    """Confluence knowledge base configuration."""
    base_url: str = ""
    username: str = ""
    api_token: str = ""
    space_keys: list = Field(default_factory=list)


class MockKBConfig(BaseModel):
    """Mock knowledge base configuration."""
    csv_path: str = "backend/data/csv/confluence_docs.csv"
    docs_folder: Optional[str] = None


class KnowledgeBaseConfig(BaseModel):
    """Knowledge base configuration."""
    source: Literal["mock", "confluence"] = "mock"
    confluence: Optional[ConfluenceKBConfig] = Field(default_factory=ConfluenceKBConfig)
    mock: Optional[MockKBConfig] = Field(default_factory=MockKBConfig)


def load_config_from_env() -> ConnectorConfig:
    """
    Load connector configuration from environment variables.
    
    Environment variables:
        CONNECTOR_TYPE: 'servicenow', 'jira', or 'mock' (default: 'mock')
        
        For ServiceNow:
            SERVICENOW_INSTANCE_URL
            SERVICENOW_USERNAME
            SERVICENOW_PASSWORD
            SERVICENOW_CLIENT_ID (optional)
            SERVICENOW_CLIENT_SECRET (optional)
        
        For Jira:
            JIRA_URL
            JIRA_USERNAME
            JIRA_API_TOKEN
            JIRA_PROJECT_KEY
        
        For Mock:
            MOCK_DATA_SOURCE (optional, default: 'mock')
    
    Returns:
        ConnectorConfig instance
    """
    connector_type = os.getenv("CONNECTOR_TYPE", "mock").lower()
    
    servicenow_config = None
    jira_config = None
    mock_config = MockConfig()
    
    if connector_type == "servicenow":
        servicenow_config = ServiceNowConfig(
            instance_url=os.getenv("SERVICENOW_INSTANCE_URL", ""),
            username=os.getenv("SERVICENOW_USERNAME", ""),
            password=os.getenv("SERVICENOW_PASSWORD", ""),
            client_id=os.getenv("SERVICENOW_CLIENT_ID"),
            client_secret=os.getenv("SERVICENOW_CLIENT_SECRET"),
        )
    elif connector_type == "jira":
        jira_config = JiraConfig(
            url=os.getenv("JIRA_URL", ""),
            username=os.getenv("JIRA_USERNAME", ""),
            api_token=os.getenv("JIRA_API_TOKEN", ""),
            project_key=os.getenv("JIRA_PROJECT_KEY", ""),
        )
    else:
        # Default to mock
        connector_type = "mock"
        mock_config = MockConfig(
            data_source=os.getenv("MOCK_DATA_SOURCE", "mock")
        )
    
    return ConnectorConfig(
        connector_type=connector_type,
        servicenow=servicenow_config,
        jira=jira_config,
        mock=mock_config,
    )


# ============================================================================
# LLM Configuration Models
# ============================================================================

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


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    enable_tracing: bool = False
    log_file: Optional[str] = None


class Config(BaseModel):
    """Main application configuration."""
    llm: LLMConfig = Field(default_factory=LLMConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    knowledge_base: KnowledgeBaseConfig = Field(default_factory=KnowledgeBaseConfig)


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
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "enable_tracing": False,
                "log_file": None
            },
            "knowledge_base": {
                "source": "mock",
                "confluence": {
                    "base_url": "",
                    "username": "",
                    "api_token": "",
                    "space_keys": []
                },
                "mock": {
                    "csv_path": "backend/data/csv/confluence_docs.csv",
                    "docs_folder": None
                }
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
        
        # Logging environment variables
        log_level = os.getenv("LOG_LEVEL")
        if log_level:
            config_dict["logging"]["level"] = log_level
        
        log_format = os.getenv("LOG_FORMAT")
        if log_format:
            config_dict["logging"]["format"] = log_format
        
        enable_tracing = os.getenv("ENABLE_TRACING")
        if enable_tracing:
            config_dict["logging"]["enable_tracing"] = enable_tracing.lower() in ("true", "1", "yes")
        
        log_file = os.getenv("LOG_FILE")
        if log_file:
            config_dict["logging"]["log_file"] = log_file
        
        # Knowledge Base environment variables
        kb_source = os.getenv("KNOWLEDGE_BASE_SOURCE")
        if kb_source:
            config_dict["knowledge_base"]["source"] = kb_source
        
        # Confluence KB environment variables
        confluence_base_url = os.getenv("CONFLUENCE_BASE_URL")
        if confluence_base_url:
            config_dict["knowledge_base"]["confluence"]["base_url"] = confluence_base_url
        
        confluence_username = os.getenv("CONFLUENCE_USERNAME")
        if confluence_username:
            config_dict["knowledge_base"]["confluence"]["username"] = confluence_username
        
        confluence_api_token = os.getenv("CONFLUENCE_API_TOKEN")
        if confluence_api_token:
            config_dict["knowledge_base"]["confluence"]["api_token"] = confluence_api_token
        
        confluence_space_keys = os.getenv("CONFLUENCE_SPACE_KEYS")
        if confluence_space_keys:
            config_dict["knowledge_base"]["confluence"]["space_keys"] = confluence_space_keys.split(",")
        
        # Mock KB environment variables
        kb_csv_path = os.getenv("KB_CSV_PATH")
        if kb_csv_path:
            config_dict["knowledge_base"]["mock"]["csv_path"] = kb_csv_path
        
        kb_docs_folder = os.getenv("KB_DOCS_FOLDER")
        if kb_docs_folder:
            config_dict["knowledge_base"]["mock"]["docs_folder"] = kb_docs_folder
        
        return Config(**config_dict)
    
    @property
    def config(self) -> Config:
        """Get the current configuration."""
        return self._config
    
    def get_llm_config(self) -> LLMConfig:
        """Get LLM configuration."""
        return self._config.llm
    
    def get_logging_config(self) -> LoggingConfig:
        """Get logging configuration."""
        return self._config.logging
    
    def get_knowledge_base_config(self) -> KnowledgeBaseConfig:
        """Get knowledge base configuration."""
        return self._config.knowledge_base
    
    def update_logging_config(self, level: Optional[str] = None, enable_tracing: Optional[bool] = None):
        """Update logging configuration at runtime.
        
        Args:
            level: New logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            enable_tracing: Enable or disable function tracing
        """
        with self._lock:
            # Update the config
            if level is not None:
                self._config.logging.level = level
            if enable_tracing is not None:
                self._config.logging.enable_tracing = enable_tracing
            
            # Apply the changes to the logger (lazy import to avoid circular dependency)
            from backend.utils import logger as logger_module
            logger_module.LoggerManager.reset()
            logger_module.LoggerManager.setup_logging()
    
    def reload(self):
        """Reload configuration from file and environment."""
        self._config = self._load_config()


# Singleton instance
config_manager = ConfigManager()


def get_config() -> Config:
    """Get the application configuration."""
    return config_manager.config
