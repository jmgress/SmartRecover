---
applyTo: 'backend/tests/**/*.py'
description: 'Rules for writing backend pytest tests in SmartRecover.'
---

# Backend Test Rules

- Discovery follows `backend/pytest.ini`: name files `test_*.py`, classes `Test*`, functions `test_*`. Place all tests under `backend/tests/`.
- Test async agents and connectors with `@pytest.mark.asyncio` and `await` the call, e.g.:
  ```python
  @pytest.mark.asyncio
  async def test_remediation_agent_query():
      agent = RemediationAgent()
      result = await agent.query("INC001", "")
      assert result["source"] == "remediation_engine"
  ```
- Be **mock-first**: use the mock connectors and mock data (`backend/data/mock_data.py`, `backend/data/csv/`, `backend/data/runbooks/`) by default. Do not call real external services (ServiceNow, Jira, Confluence, live LLMs) in tests.
- Reuse the shared fixtures in `backend/tests/conftest.py` (CSV backup/restore and per-module mock-data reload) for data isolation instead of mutating source data files directly.
- Assert on the documented result structure (e.g. `source`, and connector docs having `doc_id`, `title`, `content`) rather than incidental values.
- Run with `./test.sh --backend`, or a single file via `cd backend && python -m pytest tests/test_<name>.py -v`.
