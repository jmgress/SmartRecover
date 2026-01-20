"""
Agent prompt management for SmartRecover.

This module stores and manages system prompts used by various agents
in the incident resolution system.
"""

from typing import Dict
from pathlib import Path
import json


# Default prompts for each agent
DEFAULT_PROMPTS = {
    "orchestrator": """You are an expert incident resolution assistant. 
Your task is to synthesize information from multiple data sources and provide a clear, 
actionable summary for resolving incidents. Be concise and focus on the most relevant information.

Consider:
- Similar historical incidents and their resolutions
- Relevant knowledge base articles and runbooks
- Recent changes that may have caused the incident
- Root cause analysis based on correlation scores

Provide clear, step-by-step resolution guidance.""",
    
    "servicenow": """You are a ServiceNow incident analysis expert.
Your task is to find similar historical incidents and extract relevant resolutions.

Focus on:
- Matching incident characteristics (severity, affected services, symptoms)
- High-quality resolutions from similar incidents
- Patterns in incident recurrence
- Proven resolution steps

Return the most relevant historical incidents with their resolutions.""",
    
    "knowledge_base": """You are a knowledge base retrieval expert.
Your task is to find relevant documentation, runbooks, and troubleshooting guides.

Focus on:
- Operational runbooks for affected services
- Troubleshooting guides for similar issues
- Architecture documentation
- Best practices and SLAs

Return the most relevant documentation with high relevance scores.""",
    
    "change_correlation": """You are a change correlation analysis expert.
Your task is to identify recent changes that may have caused or contributed to incidents.

Focus on:
- Temporal correlation between changes and incidents
- Changes to affected services
- High-risk changes (schema updates, config changes, deployments)
- Deployment timing and incident onset

Return correlated changes with confidence scores."""
}


class PromptManager:
    """Manages agent prompts with persistence and reset capabilities."""
    
    def __init__(self, storage_file: str = None):
        """
        Initialize prompt manager.
        
        Args:
            storage_file: Path to JSON file for storing custom prompts.
                         If None, uses backend/data/custom_prompts.json
        """
        if storage_file is None:
            storage_file = Path(__file__).parent / "data" / "custom_prompts.json"
        
        self.storage_file = Path(storage_file)
        self._custom_prompts = self._load_custom_prompts()
    
    def _load_custom_prompts(self) -> Dict[str, str]:
        """Load custom prompts from storage file."""
        if not self.storage_file.exists():
            return {}
        
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load custom prompts: {e}")
            return {}
    
    def _save_custom_prompts(self):
        """Save custom prompts to storage file."""
        # Ensure directory exists
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(self._custom_prompts, f, indent=2)
    
    def get_prompt(self, agent_name: str) -> str:
        """
        Get the prompt for a specific agent.
        
        Args:
            agent_name: Name of the agent (orchestrator, servicenow, knowledge_base, change_correlation)
            
        Returns:
            The current prompt for the agent (custom if set, otherwise default)
        """
        if agent_name in self._custom_prompts:
            return self._custom_prompts[agent_name]
        
        return DEFAULT_PROMPTS.get(agent_name, "")
    
    def set_prompt(self, agent_name: str, prompt: str):
        """
        Set a custom prompt for a specific agent.
        
        Args:
            agent_name: Name of the agent
            prompt: The custom prompt text
        """
        if agent_name not in DEFAULT_PROMPTS:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        self._custom_prompts[agent_name] = prompt
        self._save_custom_prompts()
    
    def reset_prompt(self, agent_name: str):
        """
        Reset an agent's prompt to its default value.
        
        Args:
            agent_name: Name of the agent
        """
        if agent_name in self._custom_prompts:
            del self._custom_prompts[agent_name]
            self._save_custom_prompts()
    
    def reset_all_prompts(self):
        """Reset all prompts to their default values."""
        self._custom_prompts = {}
        self._save_custom_prompts()
    
    def get_all_prompts(self) -> Dict[str, Dict[str, str]]:
        """
        Get all prompts with metadata.
        
        Returns:
            Dictionary mapping agent names to their prompt info:
            {
                "agent_name": {
                    "current": "current prompt text",
                    "default": "default prompt text",
                    "is_custom": bool
                }
            }
        """
        result = {}
        for agent_name in DEFAULT_PROMPTS:
            result[agent_name] = {
                "current": self.get_prompt(agent_name),
                "default": DEFAULT_PROMPTS[agent_name],
                "is_custom": agent_name in self._custom_prompts
            }
        return result


# Global prompt manager instance
_prompt_manager = None


def get_prompt_manager() -> PromptManager:
    """Get the global prompt manager instance."""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager
