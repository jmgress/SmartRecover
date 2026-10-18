import re
from typing import Any

from backend.config import ServiceNowConfig
from backend.connectors.live_incident import (
    LiveIncidentConnector, normalize_incident, raw_text, source_error, text,
)
from backend.utils.categorization import categorize_servicenow
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ServiceNowConnector(LiveIncidentConnector):
    """Read incidents through the ServiceNow Table API using basic authentication."""

    fields = (
        "number,short_description,description,priority,state,sys_created_on,"
        "sys_updated_on,resolved_at,category,subcategory,business_service,"
        "assignment_group,close_notes"
    )

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        settings = ServiceNowConfig.model_validate(config)
        self.base_url = settings.instance_url
        self.username = settings.username
        self.secret = settings.password

    def _normalize(self, row: dict[str, Any]) -> dict[str, Any]:
        number = text(row.get("number"))
        if not re.fullmatch(r"INC[0-9]+", number):
            raise ValueError("Invalid incident number")
        title = text(row.get("short_description"))
        description = text(row.get("description"))
        state = raw_text(row.get("state"))
        status = {"1": "open", "2": "investigating", "3": "investigating",
                  "6": "resolved", "7": "resolved", "8": "resolved"}.get(state)
        if status is None:
            logger.warning("Unmapped ServiceNow state; treating incident as investigating")
            status = "investigating"
        severity = {"1": "critical", "2": "high", "3": "medium", "4": "low", "5": "low"}.get(
            raw_text(row.get("priority")), "unknown"
        )
        if severity == "unknown":
            logger.warning("Unmapped ServiceNow priority; automation will fail closed")
        service = text(row.get("business_service"))
        return normalize_incident({
            "id": number,
            "title": title,
            "description": description,
            "severity": severity,
            "status": status,
            "created_at": raw_text(row.get("sys_created_on")),
            "updated_at": raw_text(row.get("sys_updated_on")) or None,
            "resolved_at": (raw_text(row.get("resolved_at")) or None) if status == "resolved" else None,
            "affected_services": [service] if service else [],
            "assignee": text(row.get("assignment_group")) or None,
            "resolved_by_team": text(row.get("assignment_group")) if status == "resolved" else "",
            "category": categorize_servicenow(
                raw_text(row.get("category")), raw_text(row.get("subcategory")), title, description
            ),
            "resolution": text(row.get("close_notes")),
        })

    async def _read(self, query: str) -> list[dict[str, Any]]:
        records = []
        seen = set()
        async with self._client() as client:
            offset = 0
            for _ in range(self.max_pages):
                payload = await self._get(client, "api/now/table/incident", {
                    "sysparm_query": query,
                    "sysparm_fields": self.fields,
                    "sysparm_display_value": "all",
                    "sysparm_exclude_reference_link": "true",
                    "sysparm_limit": self.page_size,
                    "sysparm_offset": offset,
                })
                rows = payload.get("result")
                if not isinstance(rows, list):
                    raise source_error("servicenow", "invalid incident response")
                if not rows:
                    return records
                try:
                    page = [self._normalize(row) for row in rows if isinstance(row, dict)]
                    if len(page) != len(rows):
                        raise ValueError("Invalid incident")
                except (ValueError, TypeError):
                    raise source_error("servicenow", "invalid incident fields") from None
                ids = {record["id"] for record in page}
                if len(ids) != len(page) or seen.intersection(ids):
                    raise source_error("servicenow", "inconsistent pagination; retry the request")
                records.extend(page)
                seen.update(ids)
                offset += len(rows)
            raise source_error("servicenow", "pagination limit exceeded")

    async def list_incidents(self) -> list[dict[str, Any]]:
        return await self._read("ORDERBYsys_id")

    async def get_incident(self, incident_id: str) -> dict[str, Any] | None:
        if not re.fullmatch(r"INC[0-9]+", incident_id):
            logger.warning("Rejected malformed ServiceNow incident number")
            return None
        records = await self._read(f"number={incident_id}^ORDERBYsys_id")
        return next((record for record in records if record["id"] == incident_id), None)

    def get_connector_name(self) -> str:
        return "servicenow"
