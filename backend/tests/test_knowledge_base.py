"""
Tests for Knowledge Base Agent and connectors.
"""
import pytest
from pathlib import Path
from backend.agents.knowledge_base_agent import KnowledgeBaseAgent
from backend.connectors.knowledge_base import (
    MockKnowledgeBaseConnector,
    ConfluenceConnector,
    SemanticKnowledgeBaseConnector,
    KnowledgeBaseConnectorBase
)


class MockEmbeddings:
    """Deterministic embeddings for semantic connector tests."""

    def __init__(self):
        self.indexed_texts = []

    def embed_documents(self, texts):
        self.indexed_texts = texts
        return [
            [1.0, 0.0] if "Database Connection Troubleshooting" in text else [0.0, 1.0]
            for text in texts
        ]

    def embed_query(self, query):
        return [1.0, 0.0]


class UnavailableEmbeddings:
    """Embedding provider double that simulates an unavailable service."""

    def embed_documents(self, texts):
        raise ConnectionError("embedding service unavailable")


class TestSemanticKnowledgeBaseConnector:
    """Test suite for local semantic knowledge base retrieval."""

    @pytest.mark.asyncio
    async def test_indexes_csv_and_runbooks_and_returns_similar_documents(self):
        """Test local documents are embedded and ranked by similarity."""
        embeddings = MockEmbeddings()
        connector = SemanticKnowledgeBaseConnector({"top_k": 1}, embeddings)

        results = await connector.search("database connectivity problem")

        assert len(results) == 1
        assert results[0]["doc_id"] == "database_connection_troubleshooting"
        assert results[0]["relevance_score"] == 1.0
        assert any("Rabbitmq Troubleshooting Guide" in text for text in embeddings.indexed_texts)
        assert any("Database Connection Troubleshooting" in text for text in embeddings.indexed_texts)

    @pytest.mark.asyncio
    async def test_falls_back_to_keyword_search_when_embeddings_unavailable(self):
        """Test unavailable embeddings preserve mock connector retrieval."""
        connector = SemanticKnowledgeBaseConnector({}, UnavailableEmbeddings())

        results = await connector.search("database", incident_id="INC001")

        assert results
        assert results[0]["doc_id"] == "CONF001"

    def test_semantic_connector_get_source_name(self):
        """Test that the semantic connector identifies its source."""
        connector = SemanticKnowledgeBaseConnector({}, MockEmbeddings())

        assert connector.get_source_name() == "semantic"


class TestMockKnowledgeBaseConnector:
    """Test suite for MockKnowledgeBaseConnector."""
    
    @pytest.mark.asyncio
    async def test_mock_connector_loads_csv_data(self):
        """Test that mock connector loads data from CSV."""
        connector = MockKnowledgeBaseConnector({})
        
        # Search by incident_id
        results = await connector.search(
            query="database",
            incident_id="INC001",
            max_results=10
        )
        
        assert len(results) > 0
        assert all(isinstance(doc, dict) for doc in results)
        assert all("doc_id" in doc and "title" in doc and "content" in doc for doc in results)
    
    @pytest.mark.asyncio
    async def test_mock_connector_searches_by_incident_id(self):
        """Test searching by incident ID returns correct documents."""
        connector = MockKnowledgeBaseConnector({})
        
        # Search for INC001
        results = await connector.search(
            query="",
            incident_id="INC001",
            max_results=10
        )
        
        # Should return documents associated with INC001
        assert len(results) >= 1
        doc_ids = [doc["doc_id"] for doc in results]
        assert "CONF001" in doc_ids or "CONF002" in doc_ids
    
    @pytest.mark.asyncio
    async def test_mock_connector_loads_markdown_files(self):
        """Test that mock connector loads markdown files from docs folder."""
        # Point to the runbooks directory
        connector = MockKnowledgeBaseConnector({
            "docs_folder": "backend/data/runbooks"
        })
        
        # Search for content that's in the markdown files
        results = await connector.search(
            query="database",
            max_results=10
        )
        
        # Should find documents from both CSV and markdown files
        assert len(results) > 0
        
        # Check if markdown file was loaded
        titles = [doc["title"] for doc in results]
        assert any("database" in title.lower() for title in titles)
    
    @pytest.mark.asyncio
    async def test_mock_connector_get_document(self):
        """Test retrieving a specific document by ID."""
        connector = MockKnowledgeBaseConnector({})
        
        # Get a known document
        doc = await connector.get_document("CONF001")
        
        assert doc is not None
        assert doc["doc_id"] == "CONF001"
        assert "title" in doc
        assert "content" in doc
    
    @pytest.mark.asyncio
    async def test_mock_connector_get_document_not_found(self):
        """Test retrieving a non-existent document returns None."""
        connector = MockKnowledgeBaseConnector({})
        
        doc = await connector.get_document("NONEXISTENT")
        
        assert doc is None
    
    def test_mock_connector_get_source_name(self):
        """Test that mock connector returns correct source name."""
        connector = MockKnowledgeBaseConnector({})
        
        assert connector.get_source_name() == "mock"
    
    @pytest.mark.asyncio
    async def test_mock_connector_keyword_search(self):
        """Test keyword matching in documents."""
        connector = MockKnowledgeBaseConnector({
            "docs_folder": "backend/data/runbooks"
        })
        
        # Search for a specific keyword
        results = await connector.search(
            query="authentication",
            max_results=10
        )
        
        # Should find documents containing "authentication"
        assert len(results) > 0


class TestConfluenceConnector:
    """Test suite for ConfluenceConnector."""
    
    @pytest.mark.asyncio
    async def test_confluence_connector_initialization(self):
        """Test that Confluence connector initializes with config."""
        config = {
            "base_url": "https://test.atlassian.net/wiki",
            "username": "test@example.com",
            "api_token": "test-token",
            "space_keys": ["DOCS", "KB"]
        }
        connector = ConfluenceConnector(config)
        
        assert connector.base_url == "https://test.atlassian.net/wiki"
        assert connector.username == "test@example.com"
        assert connector.api_token == "test-token"
        assert connector.space_keys == ["DOCS", "KB"]
    
    def test_confluence_connector_get_source_name(self):
        """Test that Confluence connector returns correct source name."""
        connector = ConfluenceConnector({})
        
        assert connector.get_source_name() == "confluence"
    
    @pytest.mark.asyncio
    async def test_confluence_connector_search_not_implemented(self):
        """Test that search returns empty list when not implemented."""
        connector = ConfluenceConnector({})
        
        results = await connector.search(
            query="test",
            incident_id="INC001",
            max_results=10
        )
        
        # Should return empty list since API is not implemented
        assert results == []
    
    @pytest.mark.asyncio
    async def test_confluence_connector_get_document_not_implemented(self):
        """Test that get_document returns None when not implemented."""
        connector = ConfluenceConnector({})
        
        doc = await connector.get_document("123")
        
        # Should return None since API is not implemented
        assert doc is None


class TestKnowledgeBaseAgent:
    """Test suite for KnowledgeBaseAgent."""
    
    @pytest.mark.asyncio
    async def test_knowledge_base_agent_default_connector(self):
        """Test that agent uses mock connector by default."""
        agent = KnowledgeBaseAgent()
        
        assert agent.name == "knowledge_base_agent"
        assert isinstance(agent.connector, MockKnowledgeBaseConnector)
    
    @pytest.mark.asyncio
    async def test_knowledge_base_agent_from_config_mock(self):
        """Test creating agent from config with mock source."""
        config = {
            "source": "mock",
            "mock": {
                "csv_path": "backend/data/csv/confluence_docs.csv"
            }
        }
        agent = KnowledgeBaseAgent.from_config(config)
        
        assert isinstance(agent.connector, MockKnowledgeBaseConnector)
        assert agent.connector.get_source_name() == "mock"
    
    @pytest.mark.asyncio
    async def test_knowledge_base_agent_from_config_confluence(self):
        """Test creating agent from config with Confluence source."""
        config = {
            "source": "confluence",
            "confluence": {
                "base_url": "https://test.atlassian.net/wiki",
                "username": "test@example.com",
                "api_token": "test-token"
            }
        }
        agent = KnowledgeBaseAgent.from_config(config)
        
        assert isinstance(agent.connector, ConfluenceConnector)
        assert agent.connector.get_source_name() == "confluence"

    @pytest.mark.asyncio
    async def test_knowledge_base_agent_from_config_semantic(self):
        """Test creating agent from config with semantic local search."""
        agent = KnowledgeBaseAgent.from_config({
            "source": "semantic",
            "semantic": {"top_k": 3},
        })

        assert isinstance(agent.connector, SemanticKnowledgeBaseConnector)
        assert agent.connector.top_k == 3
    
    @pytest.mark.asyncio
    async def test_knowledge_base_agent_query(self):
        """Test agent query returns correct format."""
        agent = KnowledgeBaseAgent()
        
        result = await agent.query(
            incident_id="INC001",
            context="database connection timeout"
        )
        
        # Check response format - content_summaries removed
        assert "source" in result
        assert "incident_id" in result
        assert "documents" in result
        assert "knowledge_base_articles" in result
        
        # Check values
        assert result["incident_id"] == "INC001"
        assert isinstance(result["documents"], list)
        assert isinstance(result["knowledge_base_articles"], list)
        
        # Check that documents have relevance scores
        if len(result["documents"]) > 0:
            assert "relevance_score" in result["documents"][0]
    
    @pytest.mark.asyncio
    async def test_knowledge_base_agent_query_finds_documents(self):
        """Test that query finds relevant documents."""
        agent = KnowledgeBaseAgent()
        
        result = await agent.query(
            incident_id="INC001",
            context="database"
        )
        
        # Should find documents for INC001
        assert len(result["documents"]) > 0
        assert len(result["knowledge_base_articles"]) > 0
    
    def test_knowledge_base_agent_get_tool_description(self):
        """Test agent tool description."""
        agent = KnowledgeBaseAgent()
        
        description = agent.get_tool_description()
        
        assert isinstance(description, str)
        assert len(description) > 0
        assert "knowledge base" in description.lower()


class TestBackwardCompatibility:
    """Test backward compatibility with ConfluenceAgent."""
    
    @pytest.mark.asyncio
    async def test_api_compatibility(self):
        """Test that KnowledgeBaseAgent maintains ConfluenceAgent API."""
        agent = KnowledgeBaseAgent()
        
        # Test the query method signature and response format
        result = await agent.query(
            incident_id="INC001",
            context="test context"
        )
        
        # Response should match updated API format (content_summaries removed)
        assert "source" in result
        assert "incident_id" in result
        assert "documents" in result
        assert "knowledge_base_articles" in result
        
        # Arrays should have same length
        assert len(result["knowledge_base_articles"]) == len(result["documents"])
        
        # Check that documents have relevance scores
        if len(result["documents"]) > 0:
            assert "relevance_score" in result["documents"][0]
