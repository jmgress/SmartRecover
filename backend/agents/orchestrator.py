from typing import Dict, Any, List, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from backend.agents.servicenow_agent import ServiceNowAgent
from backend.agents.confluence_agent import ConfluenceAgent
from backend.agents.change_correlation_agent import ChangeCorrelationAgent
from backend.models.incident import AgentResponse
from backend.llm.llm_manager import get_llm


class IncidentState(TypedDict):
    incident_id: str
    user_query: str
    servicenow_results: Dict[str, Any]
    confluence_results: Dict[str, Any]
    change_results: Dict[str, Any]
    final_response: Dict[str, Any]


class OrchestratorAgent:
    """Main orchestrator that coordinates the sub-agents for incident resolution."""
    
    def __init__(self):
        self.servicenow_agent = ServiceNowAgent()
        self.confluence_agent = ConfluenceAgent()
        self.change_agent = ChangeCorrelationAgent()
        self.llm = get_llm()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(IncidentState)
        
        workflow.add_node("query_servicenow", self._query_servicenow)
        workflow.add_node("query_confluence", self._query_confluence)
        workflow.add_node("query_changes", self._query_changes)
        workflow.add_node("synthesize", self._synthesize_results)
        
        workflow.set_entry_point("query_servicenow")
        workflow.add_edge("query_servicenow", "query_confluence")
        workflow.add_edge("query_confluence", "query_changes")
        workflow.add_edge("query_changes", "synthesize")
        workflow.add_edge("synthesize", END)
        
        return workflow.compile()
    
    async def _query_servicenow(self, state: IncidentState) -> IncidentState:
        """Query ServiceNow agent."""
        results = await self.servicenow_agent.query(
            state["incident_id"],
            state["user_query"]
        )
        state["servicenow_results"] = results
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
        servicenow = state.get("servicenow_results", {})
        confluence = state.get("confluence_results", {})
        changes = state.get("change_results", {})
        
        resolution_steps = []
        if servicenow.get("resolutions"):
            resolution_steps.extend(servicenow["resolutions"])
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
        summary = await self._generate_summary_with_llm(
            state["incident_id"],
            state["user_query"],
            servicenow,
            confluence,
            changes,
            top_suspect
        )
        
        confidence = self._calculate_confidence(servicenow, confluence, changes)
        
        state["final_response"] = {
            "incident_id": state["incident_id"],
            "resolution_steps": resolution_steps,
            "related_knowledge": related_knowledge,
            "correlated_changes": correlated_changes,
            "summary": summary,
            "confidence": confidence
        }
        return state
    
    async def _generate_summary_with_llm(
        self,
        incident_id: str,
        user_query: str,
        servicenow: Dict,
        confluence: Dict,
        changes: Dict,
        top_suspect: Dict | None
    ) -> str:
        """Generate a summary using LLM for intelligent synthesis."""
        # Build context for the LLM
        context_parts = []
        
        context_parts.append(f"Incident ID: {incident_id}")
        context_parts.append(f"User Query: {user_query}")
        
        if top_suspect:
            context_parts.append(
                f"\nTop Suspect Change:\n"
                f"- Change ID: {top_suspect.get('change_id', 'N/A')}\n"
                f"- Description: {top_suspect.get('description', 'N/A')}\n"
                f"- Deployed At: {top_suspect.get('deployed_at', 'N/A')}\n"
                f"- Correlation Score: {top_suspect.get('correlation_score', 0):.0%}"
            )
        
        if servicenow.get("similar_incidents"):
            context_parts.append(
                f"\nSimilar Historical Incidents: {len(servicenow['similar_incidents'])} found"
            )
            for incident in servicenow['similar_incidents'][:3]:  # Top 3
                context_parts.append(f"  - {incident.get('title', 'N/A')}")
        
        if servicenow.get("resolutions"):
            context_parts.append(f"\nPrevious Resolutions:")
            for resolution in servicenow['resolutions'][:3]:  # Top 3
                context_parts.append(f"  - {resolution}")
        
        if confluence.get("documents"):
            context_parts.append(
                f"\nRelevant Knowledge Base Articles: {len(confluence['documents'])} found"
            )
            for doc in confluence['documents'][:3]:  # Top 3
                context_parts.append(f"  - {doc.get('title', 'N/A')}")
        
        if changes.get("high_correlation_changes"):
            context_parts.append(
                f"\nHigh Correlation Changes: {len(changes['high_correlation_changes'])} found"
            )
        
        context = "\n".join(context_parts)
        
        # Create the prompt for the LLM
        system_message = SystemMessage(content="""You are an expert incident resolution assistant. 
Your task is to synthesize information from multiple data sources and provide a clear, 
actionable summary for resolving incidents. Be concise and focus on the most relevant information.""")
        
        human_message = HumanMessage(content=f"""Based on the following incident data, provide a concise summary 
of the incident, likely cause, and recommended resolution steps:

{context}

Provide a summary that:
1. Identifies the most likely cause of the incident
2. Suggests resolution steps based on historical data
3. Notes any relevant knowledge base articles or changes
4. Is clear and actionable for the incident responder""")
        
        try:
            response = await self.llm.ainvoke([system_message, human_message])
            return response.content
        except Exception as e:
            # Fallback to basic summary if LLM fails
            return self._generate_basic_summary(servicenow, confluence, changes, top_suspect)
    
    def _generate_basic_summary(
        self,
        servicenow: Dict,
        confluence: Dict,
        changes: Dict,
        top_suspect: Dict | None
    ) -> str:
        """Generate a basic summary without LLM (fallback)."""
        parts = []
        
        if top_suspect:
            parts.append(
                f"Likely cause: {top_suspect['description']} "
                f"(deployed at {top_suspect['deployed_at']}, correlation: {top_suspect['correlation_score']:.0%})"
            )
        
        if servicenow.get("similar_incidents"):
            parts.append(f"Found {len(servicenow['similar_incidents'])} similar historical incidents")
        
        if confluence.get("documents"):
            parts.append(f"Found {len(confluence['documents'])} relevant knowledge articles")
        
        return ". ".join(parts) if parts else "No significant findings from available data sources."
    
    def _calculate_confidence(
        self,
        servicenow: Dict,
        confluence: Dict,
        changes: Dict
    ) -> float:
        """Calculate confidence score based on data availability."""
        score = 0.0
        
        if servicenow.get("similar_incidents"):
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
            "servicenow_results": {},
            "confluence_results": {},
            "change_results": {},
            "final_response": {}
        }
        
        result = await self.graph.ainvoke(initial_state)
        
        return AgentResponse(**result["final_response"])
