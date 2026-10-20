# SmartRecover - Copilot Instructions

## Project and Architecture

SmartRecover is an agentic incident management system with a Python FastAPI/LangChain/LangGraph backend and a React 19 + TypeScript frontend using CRACO.

- `backend/agents/orchestrator.py`: `OrchestratorAgent` fans out independent incident, knowledge-base, change, logs, events, metrics, and remediation queries in parallel through a LangGraph `StateGraph`. Results fan in before LLM synthesis, followed by automation evaluation. Preserve per-agent failure isolation.
- `backend/connectors/`: pluggable incident, knowledge-base, and metrics integrations.
- `backend/api/routes.py` and `backend/models/`: `/api/v1` routes and Pydantic API models.
- `backend/config.py` and `backend/config.yaml`: typed settings and deployment defaults.
- `frontend/src/`: components, hooks, shared types, and the API client in `services/api.ts`.
- `backend/tests/`, colocated frontend tests, and `tests/e2e/`: backend, component, and browser coverage.
- [prd.md](../prd.md): product scope; [README](../README.md) and [implementation notes](../docs/IMPLEMENTATION_NOTES.md): setup and integration details.

## Scoped Rules and Skills

Read the applicable detailed instructions before editing; keep language-specific rules there rather than duplicating them here:

- [Backend Python](instructions/backend-python.instructions.md)
- [Backend tests](instructions/backend-tests.instructions.md)
- [Frontend React](instructions/frontend-react.instructions.md)
- [Documentation](instructions/documentation.instructions.md)
- [Product requirements maintenance](instructions/productreqdoc.instructions.md)

Use the matching project skill for [new data-source connectors](skills/add-data-source-connector/SKILL.md), [Playwright E2E tests](skills/playwright-e2e-tests/SKILL.md), or [threat analysis](skills/threat-analysis/SKILL.md).

## Implementation Patterns and Boundaries

- Agents expose `async query(incident_id: str, context: str) -> Dict[str, Any]`, returning a `source` identifier. Wire new agents into orchestrator initialization, `IncidentState`, graph nodes/edges, synthesis, and relevant streaming/chat context.
- Implement the appropriate connector base: `IncidentManagementConnector` in `backend/connectors/base.py`, `KnowledgeBaseConnectorBase` in `backend/connectors/knowledge_base/base.py`, or `MetricsConnectorBase` in `backend/connectors/metrics/base.py`. Register integrations through the owning agent's `from_config()` factory and typed configuration.
- Respect **environment variables > YAML > model defaults**. Use the Pydantic configuration in `backend/config.py`; keep secrets in environment variables, never source code or frontend bundles.
- `LLM_PROVIDER` selects `openai` (`OPENAI_API_KEY`), `gemini` (`GOOGLE_API_KEY`), or `ollama` (local, normally `http://localhost:11434`). The checked-in YAML selects Ollama.
- Incident sources default to mock/CSV; `CONNECTOR_TYPE` selects ServiceNow or Jira. Live ingestion is read-only: status updates and resolution drafting/recording remain unavailable, and mock-only evidence must not leak into live analysis. Report live-source failures explicitly rather than substituting mock or empty results.
- Remediation execution remains simulated. Preserve the deny-by-default automation gate, thresholds, kill switch, and audit trail.
- Add typed API routes under `/api/v1` using existing Pydantic models. Keep frontend requests in `frontend/src/services/api.ts` and shared request/response types in `frontend/src/types/`. The client uses `REACT_APP_API_BASE_URL`, defaulting to `http://localhost:8000/api/v1`.
- Use `get_logger(__name__)` and existing tracing helpers from `backend/utils/logger.py`; never log secrets or sensitive request data.
- Reuse existing helpers and patterns, keep changes focused, and add regression coverage for changed behavior.

## Development Commands

Run these scripts from the repository root in a compatible Bash environment. `test.sh` runs backend, frontend, and E2E tests by default; E2E setup installs dependencies and starts its own stack.

```bash
./start.sh
./test.sh
./test.sh --backend
./test.sh --frontend
./test.sh --e2e
```

Direct commands below work from the repository root, including in PowerShell, with dependencies already installed. Keep that working directory for backend commands so the `backend` package is importable.

```text
python -m uvicorn backend.main:app --reload --port 8000
python -m pytest backend/tests/test_knowledge_base.py -v
python -m pytest backend/tests -v
npm --prefix frontend start
npm --prefix frontend test -- --watchAll=false
npm --prefix frontend run build
```

The frontend runs at `http://localhost:3000`; backend health is `http://localhost:8000/api/v1/health`.

## Testing and Documentation

- Backend: pytest and `@pytest.mark.asyncio`; use mock connectors and mock external LLM/service calls. Reuse fixtures in `backend/tests/conftest.py` for CSV backup/restore and mock-data reload.
- Frontend: Jest + React Testing Library; prefer assertions on user-visible behavior. Browser tests use Python Playwright under `tests/e2e/`.
- Mock data lives in `backend/data/csv/`, YAML-frontmatter runbooks in `backend/data/runbooks/`, and `backend/data/mock_data.py`.
- Run the smallest relevant tests for a change; verify frontend builds when changing frontend code. Do not require live credentials or services for unit tests.
- Keep related docs aligned with implementation. For product behavior changes, update root `prd.md`, its version, and dated change log following the product-requirements instructions.

## Autonomous Pull Request Work — Always Capture Screenshots

When you are working on a pull request on your own (Copilot coding agent / autonomous PR runs), you **must** capture screenshots as evidence and attach them to the PR:

- **Always take screenshots**, even for backend-only or non-visual changes. For non-UI changes, capture the relevant proof instead (e.g., test output, terminal results, API responses) and note that there was no visual change.
- **For any change that affects the UI** (`frontend/**`), start the app and capture before/after screenshots of the affected screens.
- **Prefer Playwright** for reproducible captures. Use the existing E2E setup in `tests/e2e/` and follow the `playwright-e2e-tests` skill. Save images to a predictable location (e.g., `tests/e2e/screenshots/`) and reference them in the PR description.
- **Suggested flow**: run `./start.sh` to bring up backend + frontend, then use Playwright's `page.screenshot()` (full page where useful) against `http://localhost:3000` for the relevant flows.
- **In the PR description**, embed or link the screenshots and briefly caption what each one demonstrates (the change, the state before/after, or the passing verification).
- If screenshots cannot be produced (e.g., the app fails to start), explicitly state why in the PR and include whatever alternative evidence is available.
