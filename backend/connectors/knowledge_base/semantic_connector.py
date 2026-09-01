"""Local semantic-search connector for mock knowledge base documents."""
import asyncio
import math
from typing import Any, Dict, List, Optional

from backend.config import get_config
from backend.connectors.knowledge_base.base import KnowledgeBaseConnectorBase
from backend.connectors.knowledge_base.mock_connector import MockKnowledgeBaseConnector
from backend.data.mock_data import MOCK_CONFLUENCE_DOCS
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class SemanticKnowledgeBaseConnector(KnowledgeBaseConnectorBase):
    """Search local CSV and runbook documents using configured LLM embeddings."""

    def __init__(
        self,
        config: Dict[str, Any],
        embeddings: Optional[Any] = None,
    ):
        self.config = config
        self.top_k = config.get("top_k", 5)
        self._embeddings = embeddings
        self._documents: List[Dict[str, Any]] = []
        self._vectors: List[List[float]] = []
        self._indexed = False
        self._fallback = MockKnowledgeBaseConnector({
            "csv_path": config.get("csv_path", "backend/data/csv/confluence_docs.csv"),
            "docs_folder": config.get("docs_folder", "backend/data/runbooks"),
        })

    def _get_embeddings(self) -> Any:
        """Create embeddings that match the configured LLM provider."""
        if self._embeddings is not None:
            return self._embeddings

        llm_config = get_config().llm
        if llm_config.provider == "openai":
            from langchain_openai import OpenAIEmbeddings

            self._embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=llm_config.openai.api_key,
            )
        elif llm_config.provider == "gemini":
            from langchain_google_genai import GoogleGenerativeAIEmbeddings

            self._embeddings = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                google_api_key=llm_config.gemini.api_key,
            )
        elif llm_config.provider == "ollama":
            from langchain_ollama import OllamaEmbeddings

            self._embeddings = OllamaEmbeddings(
                model=llm_config.ollama.model,
                base_url=llm_config.ollama.base_url,
            )
        else:
            raise ValueError(f"Unsupported embedding provider: {llm_config.provider}")
        return self._embeddings

    def _get_documents(self) -> List[Dict[str, Any]]:
        """Collect the CSV-backed documents and configured local runbooks."""
        documents = [
            document
            for document_list in MOCK_CONFLUENCE_DOCS.values()
            for document in document_list
        ]
        documents.extend(self._fallback.text_documents)

        seen_doc_ids = set()
        return [
            document
            for document in documents
            if not (
                document["doc_id"] in seen_doc_ids
                or seen_doc_ids.add(document["doc_id"])
            )
        ]

    async def _ensure_indexed(self) -> None:
        """Embed all local documents once for this connector instance."""
        if self._indexed:
            return

        self._documents = self._get_documents()
        texts = [
            f"{document['title']}\n{document['content']}"
            for document in self._documents
        ]
        self._vectors = await asyncio.to_thread(
            self._get_embeddings().embed_documents, texts
        )
        if len(self._vectors) != len(self._documents):
            raise ValueError("Embedding provider returned an unexpected vector count")
        self._indexed = True

    @staticmethod
    def _cosine_similarity(left: List[float], right: List[float]) -> float:
        if len(left) != len(right):
            raise ValueError("Embedding vectors have incompatible dimensions")
        denominator = math.sqrt(sum(value * value for value in left)) * math.sqrt(
            sum(value * value for value in right)
        )
        return sum(a * b for a, b in zip(left, right)) / denominator if denominator else 0.0

    async def search(
        self,
        query: str,
        incident_id: str = None,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """Return the most similar local documents, or keyword results on failure."""
        if not query:
            return await self._fallback.search(query, incident_id, max_results)

        try:
            await self._ensure_indexed()
            query_vector = await asyncio.to_thread(
                self._get_embeddings().embed_query, query
            )
            results = [
                {
                    **document,
                    "relevance_score": self._cosine_similarity(query_vector, vector),
                }
                for document, vector in zip(self._documents, self._vectors)
            ]
            return sorted(
                results, key=lambda document: document["relevance_score"], reverse=True
            )[:min(max_results, self.top_k)]
        except Exception as error:
            logger.warning(
                "Semantic knowledge base search unavailable; using keyword search: %s",
                error,
            )
            return await self._fallback.search(query, incident_id, max_results)

    async def get_document(self, doc_id: str) -> Dict[str, Any]:
        """Retrieve a local document by ID."""
        return await self._fallback.get_document(doc_id)

    def get_source_name(self) -> str:
        """Return the name of this knowledge source."""
        return "semantic"
