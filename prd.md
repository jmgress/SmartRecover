# Product Requirements Document — SmartRecover
> Version: 1.16.0 | Last updated: 2026-09-12

## 1. Overview

SmartRecover is an **agentic incident management system** that uses LangChain and LangGraph to automate incident investigation and resolution. When an operator selects an incident, SmartRecover's Orchestrator dispatches specialized AI agents to gather context from incident management platforms, knowledge bases, logs, events, and recent change records. An LLM then synthesizes all gathered data into a unified, actionable resolution recommendation. Operators can continue to interact with the system through a streaming chat interface for follow-up questions.

## 2. Goals & Success Metrics

| Goal | Success Metric |
|------|---------------|
| Reduce mean-time-to-resolution (MTTR) for incidents | Measured directly via the MTTR admin dashboard (mean of resolved-at − created-at across resolved incidents), with the accuracy metrics dashboard (target ≥ 80% relevance score) as a supporting quality signal |
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

- **FR-001 — Agentic Orchestration**: An Orchestrator Agent coordinates specialized sub-agents via a LangGraph `StateGraph` workflow that fans out independent agent queries in parallel, fans back in before synthesis, and isolates per-agent failures so one agent error does not block the final response.
- **FR-002 — Incident Management Agent**: Queries incident management systems (ServiceNow, Jira Service Management, or mock data) for incident details and historical similar incidents.
- **FR-003 — Knowledge Base Agent**: Retrieves relevant runbooks and documentation from Confluence or local markdown/CSV files. Local documents can use configurable top-k semantic search with embeddings from the configured OpenAI, Gemini, or Ollama provider, falling back to keyword search when embeddings are unavailable.
- **FR-004 — Change Correlation Agent**: Correlates incidents with recent deployments and change records to identify potential root causes.
- **FR-005 — Logs Agent**: Retrieves and analyzes relevant log entries associated with the affected services.
- **FR-006 — Events Agent**: Retrieves application events and metrics (critical events, warnings) related to the incident.
- **FR-007 — Streaming Chat**: After initial resolution, users can ask follow-up questions via a streaming chat interface (`POST /chat/stream`). The chat receives full context from all five agents and returns an evidence-based fallback summary when its LLM is unavailable.
- **FR-008 — Incident Status Management**: Users can update incident status (open → investigating → resolved) via the UI, persisted to the backing data store. Marking an incident resolved is gated by FR-022: it requires a recorded resolution that passed AI quality grading.
- **FR-009 — Exclude Items**: Users can exclude irrelevant context items (tickets, docs, changes) from the resolution analysis per incident.
- **FR-010 — Dynamic Ticket Retrieval**: Context is retrieved dynamically per incident rather than pre-loaded, supporting on-demand data freshness.
- **FR-011 — Accuracy Metrics**: An admin dashboard exposes accuracy metrics per category to help evaluate resolution quality.
- **FR-012 — Quality Checker**: Responses are evaluated for quality before being returned to the user.
- **FR-013 — LLM Prompt Logging**: All prompts sent to the LLM (including RAG context data) are logged with timestamps for debugging and transparency. Logs are accessible via the Admin panel.
- **FR-014 — Suggested Fix**: The orchestrator highlights the single most likely fix so responders don't have to digest all agent results. It selects the highest-confidence remediation recommendation, attaches a rationale built from correlated-change and similar-incident evidence, and surfaces the ready-to-run script (with risk level, duration, prerequisites, and copy/run actions) prominently in the resolution response and ticket details. Execution remains simulated (see Out of Scope).
- **FR-015 — Incident Timeline**: The Ticket Details Panel shows a chronological, keyboard-navigable timeline derived from the existing incident and agent-results payload: incident creation, status updates, correlated changes (from the Change Correlation Agent), notable events, and the suggested resolution.
- **FR-016 — Resolution Feedback Loop**: Responders can rate a resolution as helpful or not helpful and optionally add a comment. Feedback is persisted and included as historical evidence for resolutions of the same or similar incidents.
- **FR-017 — Streaming Resolution Progress**: Users can stream live resolution progress as agents run (`GET /resolve/stream` or `POST /resolve/stream`). The stream emits per-agent status updates and results as each agent completes, followed by real-time streaming of LLM synthesis tokens via SSE, providing immediate feedback before synthesis finishes. Non-streaming `POST /resolve` is retained for backward compatibility.
- **FR-018 — Metrics Observability**: A Metrics Agent correlates metric anomalies from mock data (default), Prometheus, or Datadog with an incident. Its results are included in resolution synthesis, streamed progress, and follow-up chat context.
- **FR-019 — Category-Based Auto-Remediation Gate**: Incidents include a backend category field using the canonical allowlist (Database, Application, Infrastructure, Network, Security, Storage, Monitoring, Cache, Payments, API). Mock incidents persist the category in CSV, and the backend derives the same canonical category from incident title/description when legacy rows or future connectors omit it. After synthesis, a pure deny-by-default automation gate evaluates eligibility for simulated auto-remediation using global enablement, category rule status, overall-confidence threshold, minimum fix confidence, max risk level, max severity, and suggested-fix presence; every blocking condition contributes a readable reason. `POST /resolve` includes this decision in `automation`, and streaming responses emit an `automation_decision` event (payload under `result`) before `complete`. Audit records are appended only for automated (`automated=true`) decisions.
- **FR-020 — Automation Admin Persistence**: The Admin automation tab must let operators update category-based auto-remediation guardrails, save them through the canonical rules API, reload the page, and observe the persisted rule state and audit history without manual data repair.
- **FR-021 — MTTR Tracking**: Incidents record a `resolved_at` timestamp when their status transitions to resolved (cleared if the incident is reopened; re-resolving stamps a new time). An admin MTTR dashboard reports the mean time to resolution (resolved-at − created-at) overall and broken down by severity and category, backed by `GET /admin/mttr-metrics`.
- **FR-022 — AI-Drafted & AI-Graded Resolutions**: Before an incident can be marked resolved, the responder must record a resolution. The system can generate an AI first draft from recorded incident data (details, related tickets, prior resolutions), which the responder edits. Submitted resolutions are graded by AI against the recorded data: deterministic checks reject low-effort text (e.g. "resolved", too-short or generic entries) without requiring an LLM, and LLM grading scores substance and consistency with what was recorded. Resolutions below the configurable quality threshold (default 0.7) are blocked with actionable feedback; passing resolutions are persisted and automatically set the incident status to resolved. The accepted resolution and its quality score are shown in the ticket details.
- **FR-023 — Recommended Teams to Involve**: The orchestrator derives which teams should be engaged beyond the assignee's own team, using three evidence sources: teams that resolved similar incident tickets (`resolved_by_team`), teams that own relevant knowledge base articles (`owning_team`), and teams that deployed highly correlated changes (`implementing_team`, root-cause suspects). Recommendations are deduplicated across sources with merged reasons, exclude the incident's current assignee team, and are surfaced in the `/resolve` response (`recommended_teams`), the retrieve-context payload, the chat resolution message, and a "Teams to Involve" section in the Ticket Details Panel. Mock CSV data carries the team ownership fields to drive this derivation.

### 4.2 Integrations & Data Sources

| Integration | Connector | Status |
|-------------|-----------|--------|
| ServiceNow | `servicenow_connector.py` | Implemented |
| Jira Service Management | `jira_connector.py` | Implemented |
| Mock / CSV data | `mock_connector.py` | Implemented (default) |
| Confluence | `confluence_connector.py` | Implemented |
| Mock Knowledge Base | `knowledge_base/mock_connector.py` | Implemented (default) |
| Local Semantic Knowledge Base | `knowledge_base/semantic_connector.py` | Implemented |
| OpenAI | LLM provider | Supported |
| Google Gemini | LLM provider | Supported |
| Ollama (local) | LLM provider | Supported (default) |
| Prometheus | `metrics/prometheus_connector.py` | Supported |
| Datadog | `metrics/datadog_connector.py` | Supported |
| Mock Metrics | `metrics/mock_connector.py` | Implemented (default) |

### 4.3 API Surface

All endpoints are prefixed with `/api/v1`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/incidents` | List all incidents |
| `GET` | `/incidents/{id}` | Get a specific incident |
| `PUT` | `/incidents/{id}/status` | Update incident status (`resolved` requires a stored passing resolution; otherwise `400`) |
| `POST` | `/incidents/{id}/resolution/draft` | Generate an AI first-draft resolution from recorded incident data |
| `POST` | `/incidents/{id}/resolution` | Grade a submitted resolution; persist it and mark the incident resolved when it passes |
| `GET` | `/incidents/{id}/resolution` | Get the most recent accepted resolution |
| `GET` | `/incidents/{id}/details` | Get enriched incident details |
| `POST` | `/incidents/{id}/retrieve-context` | Trigger dynamic context retrieval |
| `POST` | `/resolve` | Run full agentic resolution for an incident |
| `GET` / `POST` | `/resolve/stream` | Stream live per-agent resolution status, results, and LLM synthesis tokens via SSE |
| `POST` | `/feedback` | Persist a helpful/not-helpful resolution rating and optional comment |
| `GET` | `/health` | Health check |
| `POST` | `/chat/stream` | Streaming follow-up chat |
| `POST` | `/admin/test-llm` | Test LLM connectivity |
| `GET` | `/admin/llm-config` | Get current LLM configuration |
| `GET` | `/admin/logging-config` | Get logging configuration |
| `PUT` | `/admin/logging-config` | Update logging configuration |
| `GET` | `/admin/automation-rules` | Get persisted canonical automation rules plus category list and default rule values |
| `PUT` | `/admin/automation-rules` | Validate and update persisted canonical automation rules (`400` on unknown category or out-of-range threshold) |
| `GET` | `/admin/automation-audit` | Get recent automation audit records (default `limit=50`) |
| `DELETE` | `/admin/automation-audit` | Clear all persisted automation audit records |
| `GET` | `/admin/automation-config` | Get persisted automation settings and recent audit entries |
| `PUT` | `/admin/automation-config` | Update persisted per-category automation settings |
| `GET` | `/admin/agent-prompts` | Get all agent prompts |
| `PUT` | `/admin/agent-prompts/{agent}` | Update a specific agent prompt |
| `POST` | `/admin/agent-prompts/reset` | Reset agent prompts to defaults |
| `GET` | `/admin/accuracy-metrics` | Get accuracy metrics |
| `GET` | `/admin/mttr-metrics` | Get MTTR metrics (overall mean time to resolution plus per-severity and per-category breakdowns) |
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
  - Backend category when present, with the existing keyword heuristic as fallback when the field is empty
  - Relative creation time (e.g., "2d ago")
  - Assigned team
  - Affected services count
  - **Hover tooltip** with full incident details: description, priority, category, assignee, open/updated timestamps, and all affected service tags
- **Ticket Details Panel**: Displays incident metadata and status dropdown, plus a highlighted **Suggested Fix card** (most likely remediation with rationale, risk/confidence badges, script, and Run/Copy actions) above the agent analysis tabs. For resolved incidents, a Resolution section shows the accepted resolution text, its AI quality score, and when it was recorded.
- **Resolution modal**: Selecting "Resolved" in the status dropdown opens a modal instead of updating status directly. Responders can generate an editable AI draft, then submit; a failed grade keeps the modal open and displays the score, feedback, and specific issues, while a passing grade records the resolution and marks the incident resolved.
- **Timeline Panel**: The right panel hosts a scrollable incident **Timeline** (creation/updates, correlated changes, events, and suggested resolution in chronological order), with an empty state when no incident is selected. (Replaces the former inline Timeline section in the Ticket Details Panel and the former right-panel Chat Panel.)
- **Incident automation state**: Ticket details show the incident category badge alongside severity/status metadata and expose whether the suggested fix was auto-remediated or blocked, including the backend-provided block reason for simulated automation.
- **Resolution feedback**: The resolution view lets responders submit a helpful/not-helpful rating and optional comment after agent analysis is available.
- **Chat Widget**: A floating chat button in the bottom-right corner (visible when an incident is selected) opens a floating overlay chat window with streaming responses. Chat retains full incident context and all retrieved agent content; the window closes and messages reset when switching incidents. (Replaces the former always-visible right-panel Chat Panel.)
- **Admin Page**: 
  - **Test LLM**: LLM configuration and connectivity testing
  - **Logging & Tracing**: System logging level and trace configuration
  - **Automation**: A dedicated Automation tab manages the global kill switch plus per-category enablement, confidence threshold, minimum fix confidence, max-risk/max-severity guardrails, and recent automation audit entries backed by the canonical `/admin/automation-rules` and `/admin/automation-audit` endpoints
  - **Agent Prompts**: View and edit prompts for all agents
  - **Accuracy Metrics**: Track relevance of agent results by category
  - **MTTR**: Track mean time to resolution overall and by severity/category, with resolved vs. total incident counts
  - **Prompt Logs**: View all prompts sent to LLM with RAG context for debugging
- **Resolution state badges**: Resolution views expose whether an incident was auto-remediated or blocked, along with the gate reason.
- **Personal theme selection**: Each user selects their own theme (Blue Enterprise, Purple, Dark, High Contrast, or Green / Teal) from the Settings submenu inside the profile menu in the header (not on the root menu). The selection is a per-user preference persisted locally in the browser and applied before the app renders; it is not a system-wide admin setting. All chat elements, including assistant message bubbles, follow the active theme.
- **Components**: Header, Sidebar, IncidentItem, FilterButtons, SeverityBadge, StatusDropdown, ChatContainer, ChatInput, ChatWidget, TimelinePanel, Message, QualityBadge, LoadingSpinner, Resizer, TicketDetailsPanel, IncidentTimeline, Admin

## 5. Non-Functional Requirements

### 5.1 Performance
- LLM responses are streamed to the client via `StreamingResponse` for perceived low-latency.
- Agent caching layer (`backend/cache/agent_cache.py`) avoids redundant external calls for the same incident.

### 5.2 Security
- Automated secret scanning prevents accidental credential exposure (see `docs/SECRET_SCANNING.md`).
- API keys are loaded from environment variables or config files, never hard-coded.
- Sensitive data must not appear in logs or error messages.
- Auto-remediation is simulated only: no subprocess, shell, or cluster command execution is allowed in the gating feature, and audit payloads must exclude secrets.

### 5.3 Scalability
- Pluggable connector architecture allows swapping data sources without code changes to agents.
- LLM provider is configurable at runtime via config file or environment variables.

### 5.4 Observability & Logging
- Structured logging via `backend/utils/logger.py` with configurable levels (DEBUG through CRITICAL).
- Optional function-level tracing (entry/exit, arguments, execution time, exceptions).
- Optional file-based logging.
- **LLM Prompt Logging**: All prompts sent to the LLM are logged with full context (system prompt, user message, RAG data summary, conversation history) for debugging and transparency. Logs are stored in-memory with a maximum of 1000 entries and are accessible via the Admin panel's "Prompt Logs" tab.
- **Automation Audit Trail**: Each automation gate decision records category, mode (`simulated`), confidence inputs, selected rule, fix metadata (including script text for audit only), outcome, and reasons in persisted local JSON audit storage.

### 5.5 Testing
- **Backend**: pytest with `@pytest.mark.asyncio` for async tests. Tests in `backend/tests/`.
- **Frontend**: Jest with React Testing Library.
- **Coverage**: Frontend generates coverage reports automatically.
- **Test runner**: Unified `./test.sh` script with `--backend`, `--frontend`, and `--e2e` flags.
- **Mock-first**: Tests use mock connectors by default, no external service dependencies.
- **End-to-end**: Python Playwright tests cover loading mock incidents, viewing incident details, submitting a resolution query, and the health endpoint. The `--e2e` runner starts a local headless mock-connector stack deterministically.

## 6. Architecture & Constraints

- **Orchestration pattern**: LangGraph `StateGraph` with parallel fan-out of independent agent queries, fan-in before synthesis, and post-synthesis automation evaluation.
- **Automation gate placement**: Category-based auto-remediation is enforced in a dedicated orchestrator node after synthesis, where both overall confidence and suggested-fix confidence are available.
- **Agent contract**: All agents implement `async query(incident_id: str, context: str) -> Dict[str, Any]`.
- **Connector pattern**: Abstract base classes (`IncidentManagementConnector`, `KnowledgeBaseConnectorBase`) with `from_config()` factory methods.
- **Configuration precedence**: Environment variables override `backend/config.yaml`.
- **All config models are Pydantic-based** (`backend/config.py`).
- **Backend framework**: FastAPI with Uvicorn.
- **Frontend framework**: React 18 + TypeScript, CRA with CRACO overrides.
- **Automation settings persistence**: Per-category automation rules are stored in `backend/data/automation_rules.json` and automation audit history is stored in `backend/data/automation_audit.json`, each using atomic temp-file replacement and a thread lock. Missing or corrupt files must fall back to safe defaults.

## 7. Configuration & Deployment

### LLM Configuration
Set via `backend/config.yaml` or environment variables (`LLM_PROVIDER`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`, etc.). Supported providers: OpenAI, Google Gemini, Ollama.

### Knowledge Base Configuration
Set `knowledge_base.source` to `mock`, `confluence`, or `semantic` in `config.yaml`. Semantic mode embeds the configured CSV and markdown runbook files locally and uses `knowledge_base.semantic.top_k` (or `KB_SEMANTIC_TOP_K`) to limit retrieval; it uses the configured LLM provider's embeddings and falls back to mock keyword search if unavailable.

### Logging Configuration
Set `logging.level`, `logging.enable_tracing`, and optionally `logging.log_file` in `config.yaml` or via `LOG_LEVEL`, `ENABLE_TRACING` environment variables.

### Automation Configuration
Admins manage the global kill switch plus per-category enablement, thresholds, and risk/severity guardrails through the persisted `/admin/automation-config` API. Unknown category keys are rejected before persistence, and missing/corrupt JSON store files fall back to safe defaults.
The canonical automation admin surface also exposes `/admin/automation-rules` (rules + canonical category/default metadata for UI rendering) and `/admin/automation-audit` (list/clear persisted audit records).

### Metrics Configuration
Set `metrics.source` to `mock`, `prometheus`, or `datadog`. Prometheus accepts `PROMETHEUS_BASE_URL`, `PROMETHEUS_QUERY`, and `PROMETHEUS_BEARER_TOKEN`; Datadog accepts `DATADOG_SITE`, `DATADOG_QUERY`, `DATADOG_API_KEY`, and `DATADOG_APP_KEY`.

### Resolution Grading Configuration
Set `resolution.quality_threshold` (default `0.7`) and `resolution.min_length` (default `30`) in `config.yaml`, or override with `RESOLUTION_QUALITY_THRESHOLD` and `RESOLUTION_MIN_LENGTH` environment variables. Accepted resolutions are persisted to a local JSON store.

### Running the System
- `./start.sh` — Start backend (auto-creates venv, installs deps)
- `cd frontend && npm start` — Start frontend on port 3000
- Backend runs on port 8000

## 8. Out of Scope

- Real-time alerting or pager integration (e.g., PagerDuty, OpsGenie).
- Multi-tenant / multi-user authentication and authorization.
- Persistent database (currently uses in-memory mock data and CSV files).
- Automated remediation execution (system recommends actions but does not execute them).
- Admin-managed dynamic incident taxonomy.
- Live incident-category ingestion from ServiceNow or Jira (future mapping from ServiceNow category/subcategory and Jira issue type/components remains unimplemented).
- Automated rollback for an auto-remediation decision.
- Mobile-native application.

## 9. Open Questions

| # | Question | Status |
|---|----------|--------|
| OQ-1 | Should the system support parallel agent execution for faster resolution? | Resolved (implemented) |
| OQ-2 | What is the strategy for persisting incident data beyond CSV/mock? | Open |
| OQ-3 | Should user authentication be added for multi-user deployments? | Open |

## 10. Change Log

| Date | Change | Section(s) |
|------|--------|------------|
| 2026-09-12 | Added Recommended Teams to Involve (FR-023): orchestrator derives teams from similar-incident resolvers, KB article owners, and correlated-change deployers; new `recommended_teams` in resolve/context responses; "Teams to Involve" sections in the chat resolution message and Ticket Details Panel; mock CSVs gained `resolved_by_team`, `owning_team`, and `implementing_team` columns | 4.1, 4.3, 4.4 |
| 2026-09-09 | Added AI-drafted & AI-graded resolutions (FR-022): resolution required (and quality-gated) to mark incidents resolved, AI first-draft generation, deterministic + LLM grading with configurable threshold, new resolution endpoints, resolution modal in the UI, and recorded resolution display in ticket details | 4.1, 4.3, 4.4, 7 |
| 2026-09-09 | Added MTTR tracking: incidents record `resolved_at` on resolution (cleared on reopen), new `GET /admin/mttr-metrics` endpoint, and an Admin MTTR dashboard with overall/severity/category breakdowns; MTTR goal now measured directly | 2, 4.1, 4.3, 4.4 |
| 2026-09-09 | Moved the incident Timeline to a scrollable right panel (replacing the Chat Panel) and replaced the always-visible chat with a floating chat button opening an overlay chat window with full incident/retrieved context | 4.4 |
| 2026-09-09 | Updated orchestrator requirements to run independent agent queries in parallel with fan-out/fan-in flow and per-agent failure isolation | 4.1, 6, 9 |
| 2026-09-09 | Added explicit automation-admin persistence requirement so category-based auto-remediation settings must survive save/reload and remain visible in admin audit tooling | 4.1 |
| 2026-09-09 | Added dedicated Automation admin tab wiring for canonical rules/audit endpoints plus incident category and automation-state badges in incident views | 4.4 |
| 2026-09-09 | Added dedicated admin automation rules/audit endpoints with canonical category/default metadata, 400 validation for unknown categories and out-of-range thresholds, and audit log clear support | 4.3, 7 |
| 2026-09-09 | Added a pure deny-by-default automation gate function and aligned graph + streaming orchestration so responses always include `automation` and streaming emits `automation_decision.result` before completion | 4.1, 4.3, 5.2, 6 |
| 2026-09-09 | Split automation persistence into dedicated rules/audit JSON stores, added explicit automation rule/decision/audit models, and made missing/corrupt store files default safely while rejecting unknown categories on write | 4.1, 5.4, 6, 7 |
| 2026-09-09 | Clarified that incident categories are persisted in mock CSV data, backfilled by a shared backend categorizer, and still not ingested from ServiceNow or Jira connectors | 4.1, 8 |
| 2026-09-09 | Added persisted per-category auto-remediation controls, a post-synthesis automation gate, incident category field support, and audit-tracked automation decisions surfaced in the admin UI and resolution views | 4.1, 4.3, 4.4, 5.2, 5.4, 6, 7, 8 |
| 2026-08-31 | Added local semantic knowledge-base retrieval over CSV documents and runbooks, using the configured LLM provider's embeddings, configurable top-k, and keyword fallback | 4.1, 4.2, 7 |
| 2026-08-31 | Added a mock-first Metrics Agent with pluggable Prometheus and Datadog connectors; correlated anomalies now inform synthesis, streaming progress, and follow-up chat | 4.1, 4.2, 6, 7 |
| 2026-08-31 | Added Streaming Resolution Progress (FR-017) via SSE endpoint `/resolve/stream` emitting per-agent status and streaming LLM synthesis tokens | 4.1, 4.3 |
| 2026-08-30 | Added persisted resolution feedback (FR-016), including helpful/not-helpful ratings, optional comments, a feedback API, UI control, and historical feedback context for future resolutions | 4.1, 4.3, 4.4 |
| 2026-08-30 | Added Incident Timeline (FR-015): new `IncidentTimeline` component derives a chronological, keyboard-navigable timeline of incident creation/updates, correlated changes, events, and the suggested resolution from the existing `/incidents/{id}/details` payload | 4.1, 4.4 |
| 2026-08-30 | Made streaming chat return an evidence-based fallback summary when the configured LLM is unavailable | 4.1 |
| 2026-08-30 | Added deterministic, headless Python Playwright coverage for incident list, detail, resolution, and health flows, runnable through `./test.sh --e2e` against the mock-connector stack | 5.5, 7 |
| 2026-08-30 | Nested the theme picker under the profile menu's Settings submenu instead of the dropdown root | 4.4 |
| 2026-08-30 | Moved theme selector from the Admin panel (system-wide) to the personal profile dropdown in the header, making it a per-user preference | 4.4 |
| 2026-08-30 | Fixed assistant chat bubble staying purple regardless of theme — bubble colors now derive from theme CSS variables (with new on-primary text/shadow variables per theme) | 4.4 |
| 2026-08-30 | Added five selectable, persisted UI themes in the Admin panel: Blue Enterprise, Purple, Dark, High Contrast, and Green / Teal | 4.4 |
| 2026-08-30 | Added Suggested Fix (FR-014): orchestrator highlights the most likely remediation with rationale and ready-to-run script in `/resolve` and ticket details; new Suggested Fix card in Ticket Details Panel | 4.1, 4.3, 4.4 |
| 2026-03-11 | Fixed incident number mismatch: extracted `formatIncidentNumber` to shared utility and applied 7-digit ServiceNow-style formatting consistently in Sidebar, TicketDetailsPanel, and ChatContainer headers | 4.4 |
| 2026-03-10 | Enhanced sidebar incident cards to ServiceNow-style format: 7-digit number, priority badge, status badge, category, relative time, assignee, services count, and hover tooltip with full details | 4.4 |
| 2026-02-18 | Purple accent theme applied across UI for improved contrast — header gradient, sidebar accents, purple-tinted borders/tabs/scrollbars, updated CSS variables | 4.4 |
| 2026-02-18 | Added LLM Prompt Logging feature (FR-013) with Admin UI tab and API endpoints | 4.1, 4.3, 4.4, 5.4 |
| 2026-02-18 | Initial PRD created from existing codebase functionality | All |
