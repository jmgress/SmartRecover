---
mode: agent
description: 'Conduct a thorough, SmartRecover-aware code review with actionable, prioritized feedback.'
---

# Code Review Assistant

Review the provided code (or the current change) against SmartRecover's architecture and best practices. Give specific, actionable feedback with code examples.

## Inputs
- **Scope**: ${input:SCOPE:file, diff, or area to review — leave blank for the current selection/change}
- **Focus**: ${input:FOCUS:optional emphasis, e.g. security, performance, tests}

## Review principles
- **Clean code**: SOLID, DRY, KISS; clear, self-documenting names.
- **Maintainability**: modular design, proper separation of concerns.
- **Correctness & performance**: efficient async I/O, no blocking calls in async paths.
- **Testing**: adequate, meaningful coverage.

## Architecture alignment (SmartRecover)
- **Backend**: FastAPI routes under `/api/v1`, Pydantic models from `backend/models/incident.py`, the agent contract `async def query(self, incident_id, context) -> Dict[str, Any]`, LangGraph orchestrator wiring, and pluggable connectors selected via `from_config()` factories.
- **Frontend**: React 19 + TypeScript, all backend calls routed through `frontend/src/services/api.ts`, shared types in `frontend/src/types/`.
- **Config & logging**: env vars > `config.yaml` > defaults; `get_logger(__name__)` and `@trace_async_execution`; no `print`.

## Review areas
### 1. Security
- Input validation at API boundaries via Pydantic; injection/SSRF risks in connectors calling external systems.
- **Secrets**: credentials (`OPENAI_API_KEY`, `GOOGLE_API_KEY`, `SERVICENOW_*`) must come from env vars only — never hardcoded, committed to `config.yaml`, or logged.
- CORS configuration in `backend/main.py`; access controls on `/admin/...` routes.
- Dependency risks in `backend/requirements.txt` / `frontend/package.json`.

### 2. Backend (Python/FastAPI/LangGraph)
- Correct HTTP methods/status codes; Pydantic request/response validation.
- Proper `async`/`await` for I/O; error handling for external API/LLM failures with timeouts.
- Agents uphold the `query` contract and return a `source` key; new agents are wired into the orchestrator (`IncidentState`, graph node, `add_edge`).
- Connectors subclass the correct base and default to the mock connector.

Example to flag:
```python
# ❌ Blocking call inside an async agent
data = requests.get(url).json()
# ✅ Non-blocking I/O
data = (await client.get(url)).json()
```

### 3. Frontend (React/TypeScript)
- Single-responsibility components, typed props (no `any`), correct `useEffect` dependency arrays.
- Backend access via the `api` client, not scattered `fetch()` calls or hardcoded hosts.
- Accessibility (roles, labels, keyboard nav); loading/error states.

### 4. Tests
- Backend: `@pytest.mark.asyncio`, mock-first, reuse `conftest.py` fixtures, assert on documented result shapes.
- Frontend: Jest + React Testing Library with role-based queries.

## Output format
For each issue provide: **severity** (Critical/High/Medium/Low), **category** (Security/Performance/Maintainability/Bug/Style), **location**, **problem**, **risk**, and a **fix** with a code snippet. End with a prioritized list: immediate (security/critical bugs), short-term, long-term.
