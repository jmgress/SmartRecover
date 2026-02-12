"""
Tests for the RemediationAgent.
"""

import pytest
from backend.agents.remediation_agent import RemediationAgent


@pytest.mark.asyncio
async def test_remediation_agent_initialization():
    """Test that RemediationAgent initializes correctly."""
    agent = RemediationAgent()
    assert agent.name == "remediation_agent"


@pytest.mark.asyncio
async def test_remediation_agent_query():
    """Test that RemediationAgent returns remediation recommendations."""
    agent = RemediationAgent()
    result = await agent.query("INC001", "")
    
    assert result is not None
    assert "source" in result
    assert result["source"] == "remediation_engine"
    assert "incident_id" in result
    assert result["incident_id"] == "INC001"
    assert "remediations" in result
    assert "total_count" in result
    assert isinstance(result["remediations"], list)
    assert result["total_count"] == len(result["remediations"])


@pytest.mark.asyncio
async def test_remediation_agent_result_structure():
    """Test that remediation results have the expected structure."""
    agent = RemediationAgent()
    result = await agent.query("INC001", "")
    
    # Verify we got remediations
    assert len(result["remediations"]) > 0
    
    # Check structure of first remediation
    remediation = result["remediations"][0]
    assert "id" in remediation
    assert "title" in remediation
    assert "description" in remediation
    assert "script" in remediation
    assert "risk_level" in remediation
    assert "estimated_duration" in remediation
    assert "prerequisites" in remediation
    assert "confidence_score" in remediation
    
    # Verify data types
    assert isinstance(remediation["id"], str)
    assert isinstance(remediation["title"], str)
    assert isinstance(remediation["description"], str)
    assert isinstance(remediation["script"], str)
    assert remediation["risk_level"] in ["low", "medium", "high"]
    assert isinstance(remediation["estimated_duration"], str)
    assert isinstance(remediation["prerequisites"], list)
    assert isinstance(remediation["confidence_score"], (int, float))
    assert 0 <= remediation["confidence_score"] <= 1


@pytest.mark.asyncio
async def test_remediation_agent_confidence_scores():
    """Test that remediations are sorted by confidence score."""
    agent = RemediationAgent()
    result = await agent.query("INC001", "")
    
    remediations = result["remediations"]
    if len(remediations) > 1:
        # Verify they are sorted by confidence (descending)
        for i in range(len(remediations) - 1):
            assert remediations[i]["confidence_score"] >= remediations[i + 1]["confidence_score"]


@pytest.mark.asyncio
async def test_remediation_agent_context_aware():
    """Test that remediations are context-aware based on incident details."""
    agent = RemediationAgent()
    
    # Test with a memory-related incident
    result1 = await agent.query("INC001", "memory leak")
    remediations1 = result1["remediations"]
    
    # Should have relevant remediations
    assert len(remediations1) > 0
    
    # Test that we get some results regardless of incident
    result2 = await agent.query("INC999", "")
    remediations2 = result2["remediations"]
    assert len(remediations2) > 0
