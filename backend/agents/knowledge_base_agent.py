"""Knowledge Base Agent with pluggable data sources."""
from typing import Dict, Any
from backend.connectors.knowledge_base import (
    KnowledgeBaseConnectorBase,
    MockKnowledgeBaseConnector,
    ConfluenceConnector
)
from backend.utils.logger import get_logger, trace_async_execution

logger = get_logger(__name__)


class KnowledgeBaseAgent:
    """
    Main knowledge base agent that coordinates access to documentation sources.
    
    This agent uses a pluggable connector architecture to support multiple
    knowledge base backends (Confluence, mock data, etc.).
    """
    
    def __init__(self, connector: KnowledgeBaseConnectorBase = None):
        """
        Initialize knowledge base agent.
        
        Args:
            connector: Knowledge base connector instance. If None, uses mock connector.
        """
        self.name = "knowledge_base_agent"
        
        if connector is None:
            # Default to mock connector for backward compatibility
            connector = MockKnowledgeBaseConnector({})
            logger.info("Using default MockKnowledgeBaseConnector")
        
        self.connector = connector
        logger.debug(f"Initialized {self.name} with {connector.get_source_name()} connector")
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'KnowledgeBaseAgent':
        """
        Create a KnowledgeBaseAgent from configuration.
        
        Args:
            config: Configuration dictionary with:
                - source: 'mock' or 'confluence'
                - mock: Mock configuration (csv_path, docs_folder)
                - confluence: Confluence configuration (base_url, username, api_token, space_keys)
        
        Returns:
            Configured KnowledgeBaseAgent instance
        """
        source = config.get("source", "mock")
        
        if source == "confluence":
            confluence_config = config.get("confluence", {})
            connector = ConfluenceConnector(confluence_config)
            logger.info("Created KnowledgeBaseAgent with ConfluenceConnector")
        else:
            # Default to mock
            mock_config = config.get("mock", {})
            connector = MockKnowledgeBaseConnector(mock_config)
            logger.info("Created KnowledgeBaseAgent with MockKnowledgeBaseConnector")
        
        return cls(connector=connector)
    
    @trace_async_execution
    async def query(self, incident_id: str, context: str) -> Dict[str, Any]:
        """
        Query knowledge base for relevant documentation and runbooks.
        
        This method maintains backward compatibility with the old ConfluenceAgent API.
        
        Args:
            incident_id: The incident ID to query for
            context: Additional context about the incident
            
        Returns:
            Dictionary with:
                - source: Name of the knowledge base source
                - incident_id: The incident ID
                - documents: List of relevant documents with relevance scores
                - knowledge_base_articles: List of article titles (deprecated, for backward compatibility)
        """
        logger.info(f"Knowledge base query for incident: {incident_id}")
        
        # Search for documents using both incident_id and context
        docs = await self.connector.search(
            query=context,
            incident_id=incident_id,
            max_results=10
        )
        
        logger.debug(f"Found {len(docs)} relevant documents")
        
        # Format response - removed content_summaries, kept documents with scores
        return {
            "source": self.connector.get_source_name(),
            "incident_id": incident_id,
            "documents": docs,
            "knowledge_base_articles": [d.get("title", "") for d in docs]
        }
    
    def get_tool_description(self) -> str:
        """Get description of this agent's capabilities."""
        return f"Query {self.connector.get_source_name()} knowledge base for runbooks, troubleshooting guides, and knowledge base articles"
