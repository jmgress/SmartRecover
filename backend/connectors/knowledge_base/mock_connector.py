"""Mock knowledge base connector for testing and development."""
import csv
from pathlib import Path
from typing import Dict, Any, List
from backend.connectors.knowledge_base.base import KnowledgeBaseConnectorBase
from backend.data.mock_data import MOCK_CONFLUENCE_DOCS
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class MockKnowledgeBaseConnector(KnowledgeBaseConnectorBase):
    """
    Mock knowledge base connector that loads data from CSV files and text files.
    
    Supports loading from:
    - CSV file (incident_id -> documents mapping)
    - Markdown/text files in a configured directory
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize mock knowledge base connector.
        
        Args:
            config: Configuration dictionary with:
                - csv_path: Path to CSV file with knowledge base data
                - docs_folder: Optional path to folder with .md/.txt files
        """
        self.config = config
        self.csv_path = config.get("csv_path", "backend/data/csv/confluence_docs.csv")
        self.docs_folder = config.get("docs_folder")
        self.text_documents = []
        
        # Load text documents if docs_folder is configured
        if self.docs_folder:
            self._load_text_documents()
        
        logger.debug(f"MockKnowledgeBaseConnector initialized with csv_path={self.csv_path}, docs_folder={self.docs_folder}")
    
    def _load_text_documents(self):
        """Load text documents from the configured docs folder."""
        if not self.docs_folder:
            return
        
        docs_path = Path(self.docs_folder)
        if not docs_path.exists():
            logger.warning(f"Docs folder does not exist: {docs_path}")
            return
        
        # Load .md and .txt files
        for file_path in docs_path.glob("**/*"):
            if file_path.suffix in [".md", ".txt"] and file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Use filename as doc_id and title
                    doc_id = file_path.stem
                    title = file_path.stem.replace("_", " ").replace("-", " ").title()
                    
                    # Try to extract frontmatter title if available
                    if content.startswith("---"):
                        lines = content.split("\n")
                        for line in lines[1:]:
                            if line.startswith("title:"):
                                title = line.split(":", 1)[1].strip().strip('"')
                                break
                            if line == "---":
                                break
                    
                    self.text_documents.append({
                        "doc_id": doc_id,
                        "title": title,
                        "content": content,
                        "file_path": str(file_path)
                    })
                    logger.debug(f"Loaded document: {doc_id} from {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to load document {file_path}: {e}")
        
        logger.info(f"Loaded {len(self.text_documents)} text documents from {docs_path}")
    
    async def search(
        self, 
        query: str, 
        incident_id: str = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documentation.
        
        First checks CSV data by incident_id, then searches text documents by keyword.
        
        Args:
            query: Search query string
            incident_id: Optional incident ID to filter results
            max_results: Maximum number of results to return
            
        Returns:
            List of document dictionaries
        """
        results = []
        
        # First, check incident-specific documents from CSV
        if incident_id and incident_id in MOCK_CONFLUENCE_DOCS:
            results.extend(MOCK_CONFLUENCE_DOCS[incident_id])
        
        # Then search text documents by keyword matching
        if self.text_documents and query:
            query_lower = query.lower()
            for doc in self.text_documents:
                # Simple keyword matching in title and content
                if (query_lower in doc["title"].lower() or 
                    query_lower in doc["content"].lower()):
                    results.append({
                        "doc_id": doc["doc_id"],
                        "title": doc["title"],
                        "content": doc["content"][:500]  # Truncate content for search results
                    })
        
        # Limit results
        return results[:max_results]
    
    async def get_document(self, doc_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific document by ID.
        
        Args:
            doc_id: Unique document identifier
            
        Returns:
            Document dictionary or None if not found
        """
        # Search in CSV data first
        for docs_list in MOCK_CONFLUENCE_DOCS.values():
            for doc in docs_list:
                if doc.get("doc_id") == doc_id:
                    return doc
        
        # Search in text documents
        for doc in self.text_documents:
            if doc["doc_id"] == doc_id:
                return doc
        
        logger.warning(f"Document not found: {doc_id}")
        return None
    
    def get_source_name(self) -> str:
        """Return the name of this knowledge source."""
        return "mock"
