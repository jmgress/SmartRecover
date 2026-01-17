"""LLM Manager for creating and managing LLM instances based on configuration."""
from typing import Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

from backend.config import get_config, LLMConfig


class LLMManager:
    """Manages LLM instances based on configuration."""
    
    _instance: Optional['LLMManager'] = None
    _llm: Optional[BaseChatModel] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the LLM manager."""
        if self._llm is None:
            self._llm = self._create_llm()
    
    def _create_llm(self) -> BaseChatModel:
        """Create an LLM instance based on configuration."""
        config = get_config()
        llm_config = config.llm
        
        if llm_config.provider == "openai":
            return self._create_openai_llm(llm_config)
        elif llm_config.provider == "gemini":
            return self._create_gemini_llm(llm_config)
        elif llm_config.provider == "ollama":
            return self._create_ollama_llm(llm_config)
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_config.provider}")
    
    def _create_openai_llm(self, llm_config: LLMConfig) -> ChatOpenAI:
        """Create an OpenAI LLM instance."""
        openai_config = llm_config.openai
        
        kwargs = {
            "model": openai_config.model,
            "temperature": openai_config.temperature,
        }
        
        # API key is optional here - langchain-openai will use OPENAI_API_KEY env var
        if openai_config.api_key:
            kwargs["api_key"] = openai_config.api_key
        
        return ChatOpenAI(**kwargs)
    
    def _create_gemini_llm(self, llm_config: LLMConfig) -> ChatGoogleGenerativeAI:
        """Create a Google Gemini LLM instance."""
        gemini_config = llm_config.gemini
        
        kwargs = {
            "model": gemini_config.model,
            "temperature": gemini_config.temperature,
        }
        
        # API key is optional here - langchain-google-genai will use GOOGLE_API_KEY env var
        if gemini_config.api_key:
            kwargs["google_api_key"] = gemini_config.api_key
        
        return ChatGoogleGenerativeAI(**kwargs)
    
    def _create_ollama_llm(self, llm_config: LLMConfig) -> ChatOllama:
        """Create an Ollama LLM instance."""
        ollama_config = llm_config.ollama
        
        return ChatOllama(
            model=ollama_config.model,
            base_url=ollama_config.base_url,
            temperature=ollama_config.temperature,
        )
    
    def get_llm(self) -> BaseChatModel:
        """Get the configured LLM instance."""
        return self._llm
    
    def reload(self):
        """Reload the LLM instance with fresh configuration."""
        from backend.config import config_manager
        config_manager.reload()
        self._llm = self._create_llm()


# Singleton instance
llm_manager = LLMManager()


def get_llm() -> BaseChatModel:
    """Get the configured LLM instance."""
    return llm_manager.get_llm()
