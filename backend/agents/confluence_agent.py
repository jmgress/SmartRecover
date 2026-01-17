from typing import Dict, Any, List
from backend.data.mock_data import MOCK_CONFLUENCE_DOCS


class ConfluenceAgent:
    """Agent responsible for querying Confluence for knowledge base articles."""
    
    def __init__(self):
        self.name = "confluence_agent"
    
    async def query(self, incident_id: str, context: str) -> Dict[str, Any]:
        """Query Confluence for relevant documentation and runbooks."""
        docs = MOCK_CONFLUENCE_DOCS.get(incident_id, [])
        
        return {
            "source": "confluence",
            "incident_id": incident_id,
            "documents": docs,
            "knowledge_base_articles": [d.get("title", "") for d in docs],
            "content_summaries": [d.get("content", "") for d in docs]
        }
    
    def get_tool_description(self) -> str:
        return "Query Confluence for runbooks, troubleshooting guides, and knowledge base articles"
