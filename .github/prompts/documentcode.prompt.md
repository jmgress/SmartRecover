---
mode: agent
description: 'Add clear, maintainable documentation to the provided SmartRecover code.'
---

# Code Documentation Assistant

Document the provided code (or current selection) with clear, accurate, maintainable documentation that matches actual behavior.

## Inputs
- **Target**: ${input:TARGET:file, function, or component to document — leave blank for the current selection}

## Standards

### Python (backend / tests)
- **Docstrings**: Google-style for modules, classes, and functions.
- **Type hints**: annotate parameters and return values (agents follow `async def query(self, incident_id: str, context: str) -> Dict[str, Any]`).
- **Errors**: document expected exceptions and failure modes (e.g. external service/LLM errors in connectors).
- **Examples**: show usage for non-trivial functions and API endpoints.
- **Security**: note secret handling (env-var-only credentials) and any auth considerations.

### TypeScript / React (frontend)
- **TSDoc/JSDoc** for components and functions; document props with types and descriptions.
- Explain non-obvious state/data flow and event handlers.
- Note backend integration points (the `api` client in `frontend/src/services/api.ts`).

### Configuration
- Explain the file's role, key settings, environment-dependent behavior, and precedence (env vars > `config.yaml` > defaults). Flag sensitive values.

## SmartRecover context to reflect
- **Backend**: FastAPI (`/api/v1`), LangGraph `OrchestratorAgent` coordinating specialized agents, pluggable connectors via `from_config()` factories.
- **Logging**: `get_logger(__name__)` and the `@trace_async_execution` decorator.
- **Data**: mock-first sources under `backend/data/` (CSV + runbooks).

## Example
```python
async def query(self, incident_id: str, context: str) -> Dict[str, Any]:
    """Retrieve remediation suggestions for an incident.

    Args:
        incident_id: The incident identifier (e.g. "INC001").
        context: Optional free-text context to refine results.

    Returns:
        A dict including a ``source`` key identifying the agent and the
        agent-specific result payload.

    Raises:
        ConnectorError: If the underlying data source is unavailable.
    """
```

## Quality guidelines
- Write for developers new to the codebase; be complete but not verbose.
- Keep docs accurate to real behavior and close to the code they describe.
- Explain *why* where it isn't obvious, not just *what*. Do not restate the next line of code.
- Reference related components, API routes, and configuration where helpful.
