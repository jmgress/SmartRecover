---
applyTo: 'backend/**/*.py'
description: 'Coding rules for the SmartRecover FastAPI/LangGraph backend (agents, connectors, config, logging).'
---

# Backend Python Rules

Apply these rules to all backend code except tests (see `backend-tests.instructions.md`).

## Agents
- Every agent exposes the async contract: `async def query(self, incident_id: str, context: str) -> Dict[str, Any]`.
- Return a dict that includes a `source` key identifying the agent (e.g. `"remediation_engine"`), matching existing agents in `backend/agents/`.
- Decorate async agent methods with `@trace_async_execution` from `backend/utils/logger.py` (use `@trace_execution` for sync functions).
- When an agent selects a connector, expose a `@classmethod from_config(cls, config: Dict[str, Any])` factory that reads `config.get("source", "mock")` and defaults to the mock connector — mirror `KnowledgeBaseAgent.from_config`.

## Orchestrator / LangGraph
- New agents are wired into `OrchestratorAgent` in `backend/agents/orchestrator.py`: add the result key to the `IncidentState` TypedDict, add a node in `_build_graph()`, and connect it with `workflow.add_edge()`.
- Keep the workflow sequential and feed agent outputs into `_synthesize_results` / `final_response`; do not add parallel branches unless explicitly requested.

## Connectors
- New external integrations subclass the abstract base: `IncidentManagementConnector` (`backend/connectors/base.py`) or `KnowledgeBaseConnectorBase` (`backend/connectors/knowledge_base/base.py`).
- Implement every abstract method and the name accessor (`get_connector_name()` / `get_source_name()`). Keep I/O async.
- Register the new connector in the agent's `from_config()` factory rather than instantiating it directly at call sites.

## Configuration
- All config is Pydantic-based in `backend/config.py`. Add new settings as fields on the existing models (`LLMConfig`, `LoggingConfig`, `KnowledgeBaseConfig`) or a new Pydantic model — never read raw dicts.
- Respect the precedence **env vars > `backend/config.yaml` > defaults**. Read secrets (API keys, ServiceNow credentials) from environment variables only; never hardcode them.

## Logging
- Get a logger with `logger = get_logger(__name__)` from `backend.utils.logger`. Do not call `logging.getLogger` directly or `print`.
- Never log secrets, API keys, credentials, or full request bodies that may contain sensitive data.

## API
- Add routes in `backend/api/routes.py` under the `/api/v1` prefix and type request/response with Pydantic models from `backend/models/incident.py`.
- Validate all input at the route boundary via Pydantic models.
