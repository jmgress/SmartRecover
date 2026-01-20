"""Base class for knowledge base connectors."""

from abc import ABC, abstractmethod
from typing import Any


class KnowledgeBaseConnectorBase(ABC):
    """Abstract base class for knowledge base connectors."""

    @abstractmethod
    async def search(
        self, query: str, incident_id: str = None, max_results: int = 10
    ) -> list[dict[str, Any]]:
        """
        Search for relevant documentation.

        Args:
            query: Search query string
            incident_id: Optional incident ID to filter results
            max_results: Maximum number of results to return

        Returns:
            List of document dictionaries with keys:
                - doc_id: Unique document identifier
                - title: Document title
                - content: Document content/excerpt
        """
        pass

    @abstractmethod
    async def get_document(self, doc_id: str) -> dict[str, Any]:
        """
        Retrieve a specific document by ID.

        Args:
            doc_id: Unique document identifier

        Returns:
            Document dictionary with keys:
                - doc_id: Unique document identifier
                - title: Document title
                - content: Full document content
        """
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """
        Return the name of this knowledge source.

        Returns:
            Name of the knowledge base source (e.g., 'confluence', 'mock')
        """
        pass
