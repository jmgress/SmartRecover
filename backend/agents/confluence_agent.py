from typing import Dict, Any, List
from backend.data.mock_data import MOCK_CONFLUENCE_DOCS
from backend.logging_config import get_logger, trace_execution

logger = get_logger(__name__)


class ConfluenceAgent:
    """Agent responsible for querying Confluence for knowledge base articles."""
    
    def __init__(self):
        self.name = "confluence_agent"
        logger.debug(f"Initialized {self.name}")
    
    @trace_execution
    async def query(self, incident_id: str, context: str) -> Dict[str, Any]:
        """Query Confluence for relevant documentation and runbooks."""
        logger.info(f"Querying Confluence: incident_id={incident_id}")
        docs = MOCK_CONFLUENCE_DOCS.get(incident_id, [])
        logger.debug(f"Found {len(docs)} documents for incident {incident_id}")
        
        return {
            "source": "confluence",
            "incident_id": incident_id,
            "documents": docs,
            "knowledge_base_articles": [d.get("title", "") for d in docs],
            "content_summaries": [d.get("content", "") for d in docs]
        }
    
    def get_tool_description(self) -> str:
        return "Query Confluence for runbooks, troubleshooting guides, and knowledge base articles"
