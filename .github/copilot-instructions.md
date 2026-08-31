# SmartRecover - Copilot Instructions

## Architecture Overview

SmartRecover is an **agentic incident management system** using LangChain/LangGraph. The core pattern is a **LangGraph workflow** where an Orchestrator coordinates specialized agents:

```
OrchestratorAgent (backend/agents/orchestrator.py)
├── ServiceNowAgent → queries incident data (mock/ServiceNow/Jira)
├── KnowledgeBaseAgent → retrieves runbooks/docs (mock/Confluence)
└── ChangeCorrelationAgent → correlates with recent changes
```

The orchestrator runs agents **sequentially** via LangGraph's `StateGraph`, then uses an LLM to synthesize a unified response.

## Key Patterns

### Pluggable Connector Architecture
All external integrations use abstract base classes with swappable implementations:
- **Incident connectors**: `backend/connectors/base.py` → `IncidentManagementConnector`
- **Knowledge base connectors**: `backend/connectors/knowledge_base/base.py` → `KnowledgeBaseConnectorBase`

When adding a new data source, implement the abstract base class and register in `from_config()` factory method.

### Configuration Hierarchy
Configuration uses **env vars > config.yaml** precedence:
- Edit `backend/config.yaml` for defaults
- Use env vars (see `IMPLEMENTATION_NOTES.md`) to override
- All config models are Pydantic-based in `backend/config.py`

### Agent API Contract
All agents must implement: `async query(incident_id: str, context: str) -> Dict[str, Any]`

## Development Commands

```bash
# Start full stack (backend + frontend)
./start.sh

# Run all tests
./test.sh

# Backend only
./test.sh --backend

# Frontend only  
./test.sh --frontend

# Backend dev server manually
cd backend && python -m uvicorn backend.main:app --reload

# Run specific pytest file
cd backend && python -m pytest tests/test_knowledge_base.py -v
```

## Testing Patterns

- **Backend**: pytest with `@pytest.mark.asyncio` for async tests
- **Frontend**: Jest with React Testing Library
- Tests live in `backend/tests/` and use mock connectors by default
- Add new test files as `test_*.py` following existing patterns in [test_knowledge_base.py](backend/tests/test_knowledge_base.py)

## LLM Configuration

Set `LLM_PROVIDER` env var or edit `backend/config.yaml`:
- `openai`: Requires `OPENAI_API_KEY`
- `gemini`: Requires `GOOGLE_API_KEY`  
- `ollama`: Local LLM at `http://localhost:11434` (default)

## Adding New Features

### New Agent
1. Create agent in `backend/agents/` implementing `async query(incident_id, context)`
2. Add to orchestrator's `__init__` and create workflow node in `_build_graph()`
3. Wire into state flow with `workflow.add_edge()`

### New Connector/Data Source
1. Implement base class from `backend/connectors/knowledge_base/base.py`
2. Add config model to `backend/config.py`
3. Add `from_config()` factory case in the agent

### New API Endpoint
1. Add route in `backend/api/routes.py`
2. Use Pydantic models from `backend/models/incident.py`
3. Follow existing logging pattern with `get_logger(__name__)`

## Mock Data

Development uses mock data from:
- `backend/data/csv/` - CSV files for incidents/docs
- `backend/data/runbooks/` - Markdown runbook files with YAML frontmatter
- `backend/data/mock_data.py` - Python dict constants

## Frontend-Backend Communication

- API base: `http://localhost:8000/api/v1`
- Key endpoints: `GET /incidents`, `POST /resolve`, `GET /health`
- Frontend services: `frontend/src/services/api.ts`

## Autonomous Pull Request Work — Always Capture Screenshots

When you are working on a pull request on your own (Copilot coding agent / autonomous PR runs), you **must** capture screenshots as evidence and attach them to the PR:

- **Always take screenshots**, even for backend-only or non-visual changes. For non-UI changes, capture the relevant proof instead (e.g., test output, terminal results, API responses) and note that there was no visual change.
- **For any change that affects the UI** (`frontend/**`), start the app and capture before/after screenshots of the affected screens.
- **Prefer Playwright** for reproducible captures. Use the existing E2E setup in `tests/e2e/` and follow the `playwright-e2e-tests` skill. Save images to a predictable location (e.g., `tests/e2e/screenshots/`) and reference them in the PR description.
- **Suggested flow**: run `./start.sh` to bring up backend + frontend, then use Playwright's `page.screenshot()` (full page where useful) against `http://localhost:3000` for the relevant flows.
- **In the PR description**, embed or link the screenshots and briefly caption what each one demonstrates (the change, the state before/after, or the passing verification).
- If screenshots cannot be produced (e.g., the app fails to start), explicitly state why in the PR and include whatever alternative evidence is available.
