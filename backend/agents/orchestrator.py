from typing import Dict, Any, TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

from backend.agents.incident_management_agent import IncidentManagementAgent
from backend.agents.servicenow_agent import ServiceNowAgent
from backend.agents.knowledge_base_agent import KnowledgeBaseAgent
from backend.agents.change_correlation_agent import ChangeCorrelationAgent
from backend.models.incident import AgentResponse
from backend.llm.llm_manager import get_llm
from backend.utils.logger import get_logger, trace_async_execution
from backend.config import config_manager

logger = get_logger(__name__)


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
        logger.info("Initializing OrchestratorAgent")
        self.servicenow_agent = ServiceNowAgent()
        
        # Initialize knowledge base agent from config
        kb_config = config_manager.get_knowledge_base_config()
        self.knowledge_base_agent = KnowledgeBaseAgent.from_config(kb_config.dict())
        
        self.change_agent = ChangeCorrelationAgent()
        self.llm = get_llm()
        logger.debug(f"LLM initialized: {type(self.llm).__name__}")
        self.graph = self._build_graph()
        logger.info("OrchestratorAgent initialized successfully")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        logger.debug("Building LangGraph workflow")
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
        
        logger.debug("LangGraph workflow built successfully")
        return workflow.compile()
    
    @trace_async_execution
    async def _query_servicenow(self, state: IncidentState) -> IncidentState:
        """Query ServiceNow agent."""
        logger.info(f"Querying ServiceNow for incident: {state['incident_id']}")
        results = await self.servicenow_agent.query(
            state["incident_id"],
            state["user_query"]
        )
        state["servicenow_results"] = results
        logger.debug(f"ServiceNow query complete: found {len(results.get('similar_incidents', []))} similar incidents")
        return state
    
    @trace_async_execution
    async def _query_confluence(self, state: IncidentState) -> IncidentState:
        """Query knowledge base agent."""
        logger.info(f"Querying knowledge base for incident: {state['incident_id']}")
        results = await self.knowledge_base_agent.query(
            state["incident_id"],
            state["user_query"]
        )
        state["confluence_results"] = results
        logger.debug(f"Knowledge base query complete: found {len(results.get('documents', []))} documents")
        return state
    
    @trace_async_execution
    async def _query_changes(self, state: IncidentState) -> IncidentState:
        """Query change correlation agent."""
        logger.info(f"Querying change correlation for incident: {state['incident_id']}")
        results = await self.change_agent.query(
            state["incident_id"],
            state["user_query"]
        )
        state["change_results"] = results
        logger.debug(f"Change correlation complete: found {len(results.get('high_correlation_changes', []))} high correlation changes")
        return state
    
    @trace_async_execution
    async def _synthesize_results(self, state: IncidentState) -> IncidentState:
        """Synthesize results from all agents into a coherent response."""
        logger.info(f"Synthesizing results for incident: {state['incident_id']}")
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
        logger.info(f"Synthesis complete for incident: {state['incident_id']}, confidence: {confidence:.2f}")
        return state
    
    @trace_async_execution
    async def _generate_summary_with_llm(
        self,
        incident_id: str,
        user_query: str,
        servicenow: Dict,
        confluence: Dict,
        changes: Dict,
        top_suspect: Optional[Dict]
    ) -> str:
        """Generate a summary using LLM for intelligent synthesis."""
        logger.debug(f"Generating LLM summary for incident: {incident_id}")
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
            # Note: All LangChain ChatModels support async operations via ainvoke
            logger.debug("Invoking LLM for summary generation")
            response = await self.llm.ainvoke([system_message, human_message])
            logger.debug("LLM summary generation successful")
            return response.content
        except Exception as e:
            # Fallback to basic summary if LLM fails (e.g., no API key, server down)
            logger.warning(f"LLM summary generation failed, using fallback: {e}")
            return self._generate_basic_summary(servicenow, confluence, changes, top_suspect)
    
    def _generate_basic_summary(
        self,
        incident_id: str,
        user_query: str,
        incident_mgmt: Dict,
        confluence: Dict,
        changes: Dict,
        top_suspect: Optional[Dict]
    ) -> str:
        """Generate a basic summary without LLM (fallback)."""
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
    
    @trace_async_execution
    async def resolve(self, incident_id: str, user_query: str) -> AgentResponse:
        """Main entry point for incident resolution."""
        logger.info(f"Starting incident resolution workflow for: {incident_id}")
        initial_state: IncidentState = {
            "incident_id": incident_id,
            "user_query": user_query,
            "incident_mgmt_results": {},
            "confluence_results": {},
            "change_results": {},
            "final_response": {}
        }
        
        result = await self.graph.ainvoke(initial_state)
        logger.info(f"Incident resolution workflow complete for: {incident_id}")
        
        return AgentResponse(**result["final_response"])
