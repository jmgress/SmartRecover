---
name: add-data-source-connector
description: 'End-to-end procedure to integrate a new external data source into SmartRecover as a pluggable connector. Use when: adding a new incident source (e.g. PagerDuty, Jira variant), adding a new knowledge base source (e.g. SharePoint, Notion), wiring a connector into an agent factory, or replacing mock data with a real integration.'
argument-hint: 'The data source name and which base it fits (incident management or knowledge base)'
---

# Add a Data Source Connector

Integrate a new external data source by implementing the correct abstract connector, exposing it through the agent's `from_config()` factory, and adding config + tests. This mirrors the existing mock/ServiceNow/Jira/Confluence connectors.

## 1. Pick the base class
- **Incident data** (similar incidents, related changes, resolutions) → subclass `IncidentManagementConnector` in `backend/connectors/base.py`. Implement: `get_similar_incidents`, `get_related_changes`, `get_resolutions`, `get_connector_name`.
- **Knowledge / docs / runbooks** → subclass `KnowledgeBaseConnectorBase` in `backend/connectors/knowledge_base/base.py`. Implement: `search`, `get_document`, `get_source_name`.

Read the base class and an existing concrete connector (e.g. `backend/connectors/servicenow_connector.py` or `backend/connectors/knowledge_base/confluence_connector.py`) before writing.

## 2. Implement the connector
- Create the file next to its siblings (`backend/connectors/` or `backend/connectors/knowledge_base/`).
- Keep all I/O `async`. Use `get_logger(__name__)`; never log secrets.
- Read credentials/URLs from environment variables (like `SERVICENOW_INSTANCE_URL`, `OPENAI_API_KEY`) — never hardcode them. Validate/normalize inputs at the boundary.
- Return the same result shapes the existing connectors return (e.g. knowledge docs with `doc_id`, `title`, `content`).

## 3. Add configuration
- In `backend/config.py`, add fields to the relevant Pydantic model (`KnowledgeBaseConfig` for KB sources) or add a new Pydantic model for the source's settings.
- Provide defaults in `backend/config.yaml`. Preserve precedence: env vars > `config.yaml` > defaults.

## 4. Register in the factory
- Add a branch in the owning agent's `from_config()` (e.g. `KnowledgeBaseAgent.from_config` selects on `config.get("source", ...)`), instantiating the new connector when its source name is configured. Keep the mock connector as the default fallback.

## 5. Test (mock-first)
- Add `backend/tests/test_<source>_connector.py` with `@pytest.mark.asyncio`.
- Exercise each implemented method against mocked responses (do not hit the live service). Assert on the documented result structure.
- Reuse fixtures from `backend/tests/conftest.py`.

## 6. Verify
- Run `cd backend && python -m pytest tests/test_<source>_connector.py -v`, then `./test.sh --backend`.
- Confirm no secrets are logged and the mock path still works when the new source is not configured.

Follow `backend-python.instructions.md` and `backend-tests.instructions.md` throughout.
