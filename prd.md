# Product Requirements Document — SmartRecover
> Version: 1.0.0 | Last updated: 2026-02-18

## 1. Overview

SmartRecover is an **agentic incident management system** that uses LangChain and LangGraph to automate incident investigation and resolution. When an operator selects an incident, SmartRecover's Orchestrator dispatches specialized AI agents to gather context from incident management platforms, knowledge bases, logs, events, and recent change records. An LLM then synthesizes all gathered data into a unified, actionable resolution recommendation. Operators can continue to interact with the system through a streaming chat interface for follow-up questions.

## 2. Goals & Success Metrics

| Goal | Success Metric |
|------|---------------|
| Reduce mean-time-to-resolution (MTTR) for incidents | Measured via accuracy metrics dashboard; target ≥ 80% relevance score |
| Provide actionable root-cause analysis automatically | Resolution response includes correlated changes, relevant runbooks, and log evidence |
| Support pluggable data sources and LLM providers | System operates with any combination of ServiceNow/Jira/mock connectors and OpenAI/Gemini/Ollama LLMs |
| Enable non-technical stakeholders to contribute mock data | CSV-based mock data system editable with spreadsheet tools |

## 3. User Personas

| Persona | Description | Key Needs |
|---------|-------------|-----------|
| **Incident Responder** | On-call engineer investigating production issues | Fast root-cause analysis, relevant runbooks, correlated changes |
| **Platform Engineer** | Maintains SmartRecover deployment and integrations | Easy configuration, pluggable connectors, reliable logging |
| **Team Lead / Manager** | Oversees incident response process | Accuracy metrics, resolution quality visibility |
| **Developer (Contributor)** | Extends SmartRecover with new agents or connectors | Clear agent API contract, testable architecture, mock data |

## 4. Functional Requirements

### 4.1 Core Features

- **FR-001 — Agentic Orchestration**: An Orchestrator Agent coordinates five specialized sub-agents via a LangGraph `StateGraph` workflow, running them sequentially and synthesizing their outputs with an LLM.
- **FR-002 — Incident Management Agent**: Queries incident management systems (ServiceNow, Jira Service Management, or mock data) for incident details and historical similar incidents.
- **FR-003 — Knowledge Base Agent**: Retrieves relevant runbooks and documentation from Confluence or local markdown/CSV files using keyword-based search.
- **FR-004 — Change Correlation Agent**: Correlates incidents with recent deployments and change records to identify potential root causes.
- **FR-005 — Logs Agent**: Retrieves and analyzes relevant log entries associated with the affected services.
- **FR-006 — Events Agent**: Retrieves application events and metrics (critical events, warnings) related to the incident.
- **FR-007 — Streaming Chat**: After initial resolution, users can ask follow-up questions via a streaming chat interface (`POST /chat/stream`). The chat receives full context from all five agents.
- **FR-008 — Incident Status Management**: Users can update incident status (open → investigating → resolved) via the UI, persisted to the backing data store.
- **FR-009 — Exclude Items**: Users can exclude irrelevant context items (tickets, docs, changes) from the resolution analysis per incident.
- **FR-010 — Dynamic Ticket Retrieval**: Context is retrieved dynamically per incident rather than pre-loaded, supporting on-demand data freshness.
- **FR-011 — Accuracy Metrics**: An admin dashboard exposes accuracy metrics per category to help evaluate resolution quality.
- **FR-012 — Quality Checker**: Responses are evaluated for quality before being returned to the user.

### 4.2 Integrations & Data Sources

| Integration | Connector | Status |
|-------------|-----------|--------|
| ServiceNow | `servicenow_connector.py` | Implemented |
| Jira Service Management | `jira_connector.py` | Implemented |
| Mock / CSV data | `mock_connector.py` | Implemented (default) |
| Confluence | `confluence_connector.py` | Implemented |
| Mock Knowledge Base | `knowledge_base/mock_connector.py` | Implemented (default) |
| OpenAI | LLM provider | Supported |
| Google Gemini | LLM provider | Supported |
| Ollama (local) | LLM provider | Supported (default) |

### 4.3 API Surface

All endpoints are prefixed with `/api/v1`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/incidents` | List all incidents |
| `GET` | `/incidents/{id}` | Get a specific incident |
| `PUT` | `/incidents/{id}/status` | Update incident status |
| `GET` | `/incidents/{id}/details` | Get enriched incident details |
| `POST` | `/incidents/{id}/retrieve-context` | Trigger dynamic context retrieval |
| `POST` | `/resolve` | Run full agentic resolution for an incident |
| `GET` | `/health` | Health check |
| `POST` | `/chat/stream` | Streaming follow-up chat |
| `POST` | `/admin/test-llm` | Test LLM connectivity |
| `GET` | `/admin/llm-config` | Get current LLM configuration |
| `GET` | `/admin/logging-config` | Get logging configuration |
| `PUT` | `/admin/logging-config` | Update logging configuration |
| `GET` | `/admin/agent-prompts` | Get all agent prompts |
| `PUT` | `/admin/agent-prompts/{agent}` | Update a specific agent prompt |
| `POST` | `/admin/agent-prompts/reset` | Reset agent prompts to defaults |
| `GET` | `/admin/accuracy-metrics` | Get accuracy metrics |
| `POST` | `/incidents/{id}/exclude-item` | Exclude an item from analysis |
| `GET` | `/incidents/{id}/excluded-items` | List excluded items |
| `DELETE` | `/incidents/{id}/excluded-items/{item_id}` | Remove an exclusion |

### 4.4 Frontend / UI

- **Tech**: React with TypeScript
- **Sidebar**: Lists incidents with severity badges and filter buttons
- **Ticket Details Panel**: Displays incident metadata and status dropdown
- **Chat Panel**: Streaming chat container with input field for follow-up questions
- **Admin Page**: LLM configuration, logging config, agent prompt editing, accuracy metrics
- **Components**: Header, Sidebar, IncidentItem, FilterButtons, SeverityBadge, StatusDropdown, ChatContainer, ChatInput, ChatPanel, Message, QualityBadge, LoadingSpinner, Resizer, TicketDetailsPanel, Admin

## 5. Non-Functional Requirements

### 5.1 Performance
- LLM responses are streamed to the client via `StreamingResponse` for perceived low-latency.
- Agent caching layer (`backend/cache/agent_cache.py`) avoids redundant external calls for the same incident.

### 5.2 Security
- Automated secret scanning prevents accidental credential exposure (see `docs/SECRET_SCANNING.md`).
- API keys are loaded from environment variables or config files, never hard-coded.
- Sensitive data must not appear in logs or error messages.

### 5.3 Scalability
- Pluggable connector architecture allows swapping data sources without code changes to agents.
- LLM provider is configurable at runtime via config file or environment variables.

### 5.4 Observability & Logging
- Structured logging via `backend/utils/logger.py` with configurable levels (DEBUG through CRITICAL).
- Optional function-level tracing (entry/exit, arguments, execution time, exceptions).
- Optional file-based logging.

### 5.5 Testing
- **Backend**: pytest with `@pytest.mark.asyncio` for async tests. Tests in `backend/tests/`.
- **Frontend**: Jest with React Testing Library.
- **Coverage**: Frontend generates coverage reports automatically.
- **Test runner**: Unified `./test.sh` script with `--backend` and `--frontend` flags.
- **Mock-first**: Tests use mock connectors by default, no external service dependencies.

## 6. Architecture & Constraints

- **Orchestration pattern**: LangGraph `StateGraph` with sequential agent execution and LLM synthesis.
- **Agent contract**: All agents implement `async query(incident_id: str, context: str) -> Dict[str, Any]`.
- **Connector pattern**: Abstract base classes (`IncidentManagementConnector`, `KnowledgeBaseConnectorBase`) with `from_config()` factory methods.
- **Configuration precedence**: Environment variables override `backend/config.yaml`.
- **All config models are Pydantic-based** (`backend/config.py`).
- **Backend framework**: FastAPI with Uvicorn.
- **Frontend framework**: React 18 + TypeScript, CRA with CRACO overrides.

## 7. Configuration & Deployment

### LLM Configuration
Set via `backend/config.yaml` or environment variables (`LLM_PROVIDER`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`, etc.). Supported providers: OpenAI, Google Gemini, Ollama.

### Knowledge Base Configuration
Set `knowledge_base.source` to `mock` or `confluence` in `config.yaml`. Mock mode reads from CSV and markdown runbook files.

### Logging Configuration
Set `logging.level`, `logging.enable_tracing`, and optionally `logging.log_file` in `config.yaml` or via `LOG_LEVEL`, `ENABLE_TRACING` environment variables.

### Running the System
- `./start.sh` — Start backend (auto-creates venv, installs deps)
- `cd frontend && npm start` — Start frontend on port 3000
- Backend runs on port 8000

## 8. Out of Scope

- Real-time alerting or pager integration (e.g., PagerDuty, OpsGenie).
- Multi-tenant / multi-user authentication and authorization.
- Persistent database (currently uses in-memory mock data and CSV files).
- Automated remediation execution (system recommends actions but does not execute them).
- Mobile-native application.

## 9. Open Questions

| # | Question | Status |
|---|----------|--------|
| OQ-1 | Should the system support parallel agent execution for faster resolution? | Open |
| OQ-2 | What is the strategy for persisting incident data beyond CSV/mock? | Open |
| OQ-3 | Should user authentication be added for multi-user deployments? | Open |

## 10. Change Log

| Date | Change | Section(s) |
|------|--------|------------|
| 2026-02-18 | Initial PRD created from existing codebase functionality | All |
