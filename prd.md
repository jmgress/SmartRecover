# Product Requirements Document — SmartRecover
> Version: 1.2.2 | Last updated: 2026-08-30

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
- **FR-013 — LLM Prompt Logging**: All prompts sent to the LLM (including RAG context data) are logged with timestamps for debugging and transparency. Logs are accessible via the Admin panel.
- **FR-014 — Suggested Fix**: The orchestrator highlights the single most likely fix so responders don't have to digest all agent results. It selects the highest-confidence remediation recommendation, attaches a rationale built from correlated-change and similar-incident evidence, and surfaces the ready-to-run script (with risk level, duration, prerequisites, and copy/run actions) prominently in the resolution response and ticket details. Execution remains simulated (see Out of Scope).

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
| `GET` | `/admin/prompt-logs` | Get LLM prompt logs (with optional incident_id filter) |
| `DELETE` | `/admin/prompt-logs` | Clear all prompt logs |

### 4.4 Frontend / UI

- **Tech**: React with TypeScript
- **Sidebar**: Lists incidents with ServiceNow-style enriched cards and filter buttons (Open / Investigating / Closed). Each card displays:
  - Formatted incident number (7-digit ServiceNow style, e.g., `INC0000001`)
  - Status badge (Open / Investigating / Resolved)
  - Short title
  - Priority badge (P1 Critical / P2 High / P3 Moderate / P4 Low, derived from severity)
  - Severity badge
  - Derived category (Database, Application, Infrastructure, Network, Security, Storage, Monitoring, Cache, Payments, API)
  - Relative creation time (e.g., "2d ago")
  - Assigned team
  - Affected services count
  - **Hover tooltip** with full incident details: description, priority, category, assignee, open/updated timestamps, and all affected service tags
- **Ticket Details Panel**: Displays incident metadata and status dropdown, plus a highlighted **Suggested Fix card** (most likely remediation with rationale, risk/confidence badges, script, and Run/Copy actions) above the agent analysis tabs
- **Chat Panel**: Streaming chat container with input field for follow-up questions
- **Admin Page**: 
  - **Test LLM**: LLM configuration and connectivity testing
  - **Logging & Tracing**: System logging level and trace configuration
  - **Agent Prompts**: View and edit prompts for all agents
  - **Accuracy Metrics**: Track relevance of agent results by category
  - **Prompt Logs**: View all prompts sent to LLM with RAG context for debugging
- **Personal theme selection**: Each user selects their own theme (Blue Enterprise, Purple, Dark, High Contrast, or Green / Teal) from the profile menu in the header. The selection is a per-user preference persisted locally in the browser and applied before the app renders; it is not a system-wide admin setting. All chat elements, including assistant message bubbles, follow the active theme.
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
- **LLM Prompt Logging**: All prompts sent to the LLM are logged with full context (system prompt, user message, RAG data summary, conversation history) for debugging and transparency. Logs are stored in-memory with a maximum of 1000 entries and are accessible via the Admin panel's "Prompt Logs" tab.

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
| 2026-08-30 | Moved theme selector from the Admin panel (system-wide) to the personal profile dropdown in the header, making it a per-user preference | 4.4 |
| 2026-08-30 | Fixed assistant chat bubble staying purple regardless of theme — bubble colors now derive from theme CSS variables (with new on-primary text/shadow variables per theme) | 4.4 |
| 2026-08-30 | Added five selectable, persisted UI themes in the Admin panel: Blue Enterprise, Purple, Dark, High Contrast, and Green / Teal | 4.4 |
| 2026-08-30 | Added Suggested Fix (FR-014): orchestrator highlights the most likely remediation with rationale and ready-to-run script in `/resolve` and ticket details; new Suggested Fix card in Ticket Details Panel | 4.1, 4.3, 4.4 |
| 2026-03-11 | Fixed incident number mismatch: extracted `formatIncidentNumber` to shared utility and applied 7-digit ServiceNow-style formatting consistently in Sidebar, TicketDetailsPanel, and ChatContainer headers | 4.4 |
| 2026-03-10 | Enhanced sidebar incident cards to ServiceNow-style format: 7-digit number, priority badge, status badge, category, relative time, assignee, services count, and hover tooltip with full details | 4.4 |
| 2026-02-18 | Purple accent theme applied across UI for improved contrast — header gradient, sidebar accents, purple-tinted borders/tabs/scrollbars, updated CSS variables | 4.4 |
| 2026-02-18 | Added LLM Prompt Logging feature (FR-013) with Admin UI tab and API endpoints | 4.1, 4.3, 4.4, 5.4 |
| 2026-02-18 | Initial PRD created from existing codebase functionality | All |
