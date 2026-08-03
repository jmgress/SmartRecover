---
name: threat-analysis
description: 'Perform a security threat analysis of SmartRecover code or a change. Use when: the user asks for a threat analysis, security review, or risk assessment; reviewing new connectors, agents, or API routes for vulnerabilities; auditing handling of secrets/credentials; or checking dependencies for known CVEs.'
argument-hint: 'The file, module, PR, or area to analyze (optional)'
---

# Threat Analysis

Produce a focused security assessment of the requested code or change. Ground every finding in the actual SmartRecover codebase — do not report theoretical issues that the code cannot exhibit.

## What to examine
1. **Threats & vulnerabilities** — Identify concrete risks in the code under review. Map findings to the OWASP Top 10 where applicable (injection, broken access control, security misconfiguration, SSRF, etc.).
2. **Secrets & sensitive data** — Confirm credentials, API keys, and tokens (e.g. `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `SERVICENOW_INSTANCE_URL`/`_USERNAME`/`_PASSWORD`) come **only** from environment variables and are never hardcoded, committed to `backend/config.yaml`, or written to logs. Verify `get_logger(__name__)` calls and `@trace_async_execution` traces don't leak secrets or full request bodies.
3. **Input validation** — Check that API routes in `backend/api/routes.py` validate input via Pydantic models from `backend/models/incident.py`, and that connectors validate/normalize external data at the boundary.
4. **AuthN / AuthZ** — Review access controls on sensitive routes (e.g. `/admin/...` config and prompt-log endpoints) and any CORS configuration in `backend/main.py`.
5. **External integrations** — For connectors (ServiceNow, Jira, Confluence, and new ones), review outbound requests for SSRF, injection into downstream queries, unsafe deserialization, and missing timeouts/error handling.
6. **Dependencies** — Review `backend/requirements.txt` and `frontend/package.json` for known-vulnerable versions; recommend patched versions or alternatives. Note the repo already runs `.github/workflows/secret-scan.yml` and `snyk-security.yml`.

## Output
For each finding report: **severity** (Critical/High/Medium/Low), **location** (file + line), **why it's exploitable**, and a **concrete mitigation** (with a code snippet when useful). End with a short prioritized remediation list. If no issues are found in an area, say so explicitly rather than padding.
