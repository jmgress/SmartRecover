import re
from typing import Any

from backend.config import JiraConfig
from backend.connectors.live_incident import LiveIncidentConnector, normalize_incident, source_error, text
from backend.utils.categorization import categorize_jira
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def _description(value: Any) -> str:
    """Extract readable text from Jira Cloud's Atlassian Document Format."""
    if value is None or isinstance(value, str):
        return text(value)
    if not isinstance(value, dict):
        raise ValueError("Invalid description")
    if value.get("type") == "text":
        return text(value.get("text"))
    if value.get("type") == "hardBreak":
        return "\n"
    children = value.get("content", [])
    if not isinstance(children, list):
        raise ValueError("Invalid description content")
    result = "".join(_description(child) for child in children)
    return result + "\n" if value.get("type") in ("paragraph", "heading", "listItem") else result


class JiraServiceManagementConnector(LiveIncidentConnector):
    """Read Jira Cloud issues with the enhanced JQL search API."""

    fields = "summary,description,priority,status,created,updated,resolutiondate,issuetype,components,assignee,resolution,project"

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        settings = JiraConfig.model_validate(config)
        self.base_url = settings.url
        self.username = settings.username
        self.secret = settings.api_token
        self.project_key = settings.project_key

    def _normalize(self, row: dict[str, Any]) -> dict[str, Any]:
        key = text(row.get("key"))
        if not re.fullmatch(rf"{re.escape(self.project_key)}-[0-9]+", key):
            raise ValueError("Invalid issue key")
        fields = row["fields"]
        if not isinstance(fields, dict):
            raise ValueError("Invalid fields")
        if text((fields.get("project") or {}).get("key")) != self.project_key:
            raise ValueError("Unexpected project")
        title = text(fields.get("summary"))
        description = _description(fields.get("description")).strip()
        components = [text(component.get("name")) for component in fields.get("components", [])]
        issue_type = text((fields.get("issuetype") or {}).get("name"))
        status_key = text(((fields.get("status") or {}).get("statusCategory") or {}).get("key"))
        status = {"new": "open", "indeterminate": "investigating", "done": "resolved"}.get(status_key)
        if status is None:
            logger.warning("Unmapped Jira status category; treating incident as investigating")
            status = "investigating"
        priority = text((fields.get("priority") or {}).get("name")).lower()
        severity = {"highest": "critical", "critical": "critical", "blocker": "critical",
                    "high": "high", "medium": "medium", "low": "low", "lowest": "low"}.get(
                        priority, "unknown"
                    )
        if severity == "unknown":
            logger.warning("Unmapped Jira priority; automation will fail closed")
        return normalize_incident({
            "id": key,
            "title": title,
            "description": description,
            "severity": severity,
            "status": status,
            "created_at": text(fields.get("created")),
            "updated_at": text(fields.get("updated")) or None,
            "resolved_at": (text(fields.get("resolutiondate")) or None) if status == "resolved" else None,
            "affected_services": components,
            "assignee": text((fields.get("assignee") or {}).get("displayName")) or None,
            "category": categorize_jira(issue_type, components, title, description),
            # Jira's resolution label (e.g. "Done") is not a remediation procedure.
            "resolution": "",
        })

    async def _read(self, clause: str = "") -> list[dict[str, Any]]:
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", self.project_key):
            raise source_error("jira", "a valid project key is required")
        records = []
        seen_ids = set()
        seen_tokens = set()
        params = {
            "jql": f'project = "{self.project_key}"{clause} ORDER BY key ASC',
            "fields": self.fields,
            "maxResults": self.page_size,
        }
        async with self._client() as client:
            for _ in range(self.max_pages):
                payload = await self._get(client, "rest/api/3/search/jql", params)
                rows = payload.get("issues")
                if not isinstance(rows, list):
                    raise source_error("jira", "invalid issue response")
                try:
                    page = [self._normalize(row) for row in rows if isinstance(row, dict)]
                    if len(page) != len(rows):
                        raise ValueError("Invalid issue")
                except (ValueError, TypeError, KeyError, AttributeError):
                    raise source_error("jira", "invalid incident fields") from None
                ids = {record["id"] for record in page}
                if len(ids) != len(page) or seen_ids.intersection(ids):
                    raise source_error("jira", "inconsistent pagination; retry the request")
                records.extend(page)
                seen_ids.update(ids)
                token = payload.get("nextPageToken")
                if payload.get("isLast") is True:
                    return records
                if not token and payload.get("isLast") is not False:
                    return records
                if not isinstance(token, str) or not token or token in seen_tokens:
                    raise source_error("jira", "invalid pagination token")
                seen_tokens.add(token)
                params["nextPageToken"] = token
            raise source_error("jira", "pagination limit exceeded")

    async def list_incidents(self) -> list[dict[str, Any]]:
        return await self._read()

    async def get_incident(self, incident_id: str) -> dict[str, Any] | None:
        if not re.fullmatch(rf"{re.escape(self.project_key)}-[0-9]+", incident_id):
            logger.warning("Rejected malformed or out-of-project Jira issue key")
            return None
        records = await self._read(f' AND key = "{incident_id}"')
        return next((record for record in records if record["id"] == incident_id), None)

    def get_connector_name(self) -> str:
        return "jira"
