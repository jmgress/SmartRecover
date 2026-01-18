from typing import Dict, Any, TypedDict, Optional
from langgraph.graph import StateGraph, END

from backend.agents.incident_management_agent import IncidentManagementAgent
from backend.agents.confluence_agent import ConfluenceAgent
from backend.agents.change_correlation_agent import ChangeCorrelationAgent
from backend.models.incident import AgentResponse


class IncidentState(TypedDict):
    incident_id: str
    user_query: str
    incident_mgmt_results: Dict[str, Any]
    confluence_results: Dict[str, Any]
    change_results: Dict[str, Any]
    final_response: Dict[str, Any]


class OrchestratorAgent:
    """Main orchestrator that coordinates the sub-agents for incident resolution."""
    
    def __init__(self):
        self.incident_mgmt_agent = IncidentManagementAgent()
        self.confluence_agent = ConfluenceAgent()
        self.change_agent = ChangeCorrelationAgent()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(IncidentState)
        
        workflow.add_node("query_incident_mgmt", self._query_incident_mgmt)
        workflow.add_node("query_confluence", self._query_confluence)
        workflow.add_node("query_changes", self._query_changes)
        workflow.add_node("synthesize", self._synthesize_results)
        
        workflow.set_entry_point("query_incident_mgmt")
        workflow.add_edge("query_incident_mgmt", "query_confluence")
        workflow.add_edge("query_confluence", "query_changes")
        workflow.add_edge("query_changes", "synthesize")
        workflow.add_edge("synthesize", END)
        
        return workflow.compile()
    
    async def _query_incident_mgmt(self, state: IncidentState) -> IncidentState:
        """Query incident management agent."""
        results = await self.incident_mgmt_agent.query(
            state["incident_id"],
            state["user_query"]
        )
        state["incident_mgmt_results"] = results
        return state
    
    async def _query_confluence(self, state: IncidentState) -> IncidentState:
        """Query Confluence agent."""
        results = await self.confluence_agent.query(
            state["incident_id"],
            state["user_query"]
        )
        state["confluence_results"] = results
        return state
    
    async def _query_changes(self, state: IncidentState) -> IncidentState:
        """Query change correlation agent."""
        results = await self.change_agent.query(
            state["incident_id"],
            state["user_query"]
        )
        state["change_results"] = results
        return state
    
    async def _synthesize_results(self, state: IncidentState) -> IncidentState:
        """Synthesize results from all agents into a coherent response."""
        incident_mgmt = state.get("incident_mgmt_results", {})
        confluence = state.get("confluence_results", {})
        changes = state.get("change_results", {})
        
        resolution_steps = []
        if incident_mgmt.get("resolutions"):
            resolution_steps.extend(incident_mgmt["resolutions"])
        if confluence.get("content_summaries"):
            resolution_steps.extend(confluence["content_summaries"])
        
        related_knowledge = confluence.get("knowledge_base_articles", [])
        
        correlated_changes = []
        if changes.get("high_correlation_changes"):
            correlated_changes = [
                f"{c['change_id']}: {c['description']} (score: {c['correlation_score']})"
                for c in changes["high_correlation_changes"]
            ]
        
        top_suspect = changes.get("top_suspect")
        summary = self._generate_summary(incident_mgmt, confluence, changes, top_suspect)
        
        confidence = self._calculate_confidence(incident_mgmt, confluence, changes)
        
        state["final_response"] = {
            "incident_id": state["incident_id"],
            "resolution_steps": resolution_steps,
            "related_knowledge": related_knowledge,
            "correlated_changes": correlated_changes,
            "summary": summary,
            "confidence": confidence
        }
        return state
    
    def _generate_summary(
        self,
        incident_mgmt: Dict,
        confluence: Dict,
        changes: Dict,
        top_suspect: Optional[Dict]
    ) -> str:
        """Generate a summary of findings."""
        parts = []
        
        if top_suspect:
            parts.append(
                f"Likely cause: {top_suspect['description']} "
                f"(deployed at {top_suspect['deployed_at']}, correlation: {top_suspect['correlation_score']:.0%})"
            )
        
        if incident_mgmt.get("similar_incidents"):
            parts.append(f"Found {len(incident_mgmt['similar_incidents'])} similar historical incidents")
        
        if confluence.get("documents"):
            parts.append(f"Found {len(confluence['documents'])} relevant knowledge articles")
        
        return ". ".join(parts) if parts else "No significant findings from available data sources."
    
    def _calculate_confidence(
        self,
        incident_mgmt: Dict,
        confluence: Dict,
        changes: Dict
    ) -> float:
        """Calculate confidence score based on data availability."""
        score = 0.0
        
        if incident_mgmt.get("similar_incidents"):
            score += 0.3
        if confluence.get("documents"):
            score += 0.2
        if changes.get("high_correlation_changes"):
            score += 0.4
        elif changes.get("medium_correlation_changes"):
            score += 0.2
        
        return min(score + 0.1, 1.0)
    
    async def resolve(self, incident_id: str, user_query: str) -> AgentResponse:
        """Main entry point for incident resolution."""
        initial_state: IncidentState = {
            "incident_id": incident_id,
            "user_query": user_query,
            "incident_mgmt_results": {},
            "confluence_results": {},
            "change_results": {},
            "final_response": {}
        }
        
        result = await self.graph.ainvoke(initial_state)
        
        return AgentResponse(**result["final_response"])
