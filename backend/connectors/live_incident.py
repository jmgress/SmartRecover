"""Shared read-only HTTP and normalization support for live incident sources."""

from datetime import timezone
from typing import Any
from urllib.parse import urlsplit

import httpx

from backend.connectors.base import IncidentManagementConnector
from backend.models.incident import Incident
from backend.utils.logger import get_logger
from backend.utils.similarity import find_similar_incidents

logger = get_logger(__name__)


class IncidentSourceError(RuntimeError):
    """A sanitized upstream/configuration failure safe to return to API clients."""


def source_error(source: str, reason: str) -> IncidentSourceError:
    logger.error("%s incident source: %s", source, reason)
    return IncidentSourceError(f"{source} incident source: {reason}")


def text(value: Any) -> str:
    """Normalize ServiceNow value/display objects without stringifying arbitrary data."""
    if isinstance(value, dict):
        value = value.get("display_value") or value.get("value")
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError("Expected a text field")
    return value.strip()


def raw_text(value: Any) -> str:
    return text(value.get("value") if isinstance(value, dict) else value)


def normalize_incident(record: dict[str, Any]) -> dict[str, Any]:
    incident = Incident.model_validate(record)
    for field in ("created_at", "updated_at", "resolved_at"):
        value = getattr(incident, field)
        if value is not None:
            setattr(incident, field, value.replace(tzinfo=timezone.utc) if value.tzinfo is None
                    else value.astimezone(timezone.utc))
    if not incident.id or not incident.title:
        raise ValueError("Missing incident identity")
    return {**record, **incident.model_dump()}


class LiveIncidentConnector(IncidentManagementConnector):
    base_url: str
    username: str
    secret: str
    page_size = 100
    max_pages = 1000

    def _client(self) -> httpx.AsyncClient:
        try:
            parsed = urlsplit(self.base_url)
            _ = parsed.port
        except ValueError:
            raise source_error(self.get_connector_name(), "invalid HTTPS URL") from None
        if (
            parsed.scheme != "https" or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment
            or not self.username or not self.secret
        ):
            raise source_error(self.get_connector_name(), "HTTPS URL and credentials are required")
        return httpx.AsyncClient(
            base_url=self.base_url.rstrip("/") + "/",
            auth=(self.username, self.secret),
            timeout=httpx.Timeout(30.0),
            follow_redirects=False,
            headers={"Accept": "application/json"},
        )

    async def _get(
        self, client: httpx.AsyncClient, path: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        source = self.get_connector_name()
        try:
            response = await client.get(path, params=params)
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise source_error(source, f"upstream returned HTTP {error.response.status_code}") from None
        except httpx.RequestError:
            raise source_error(source, "upstream request failed") from None
        try:
            payload = response.json()
        except ValueError:
            raise source_error(source, "invalid JSON response") from None
        if not isinstance(payload, dict):
            raise source_error(source, "invalid response shape")
        return payload

    async def get_similar_incidents(self, incident_id: str, context: str) -> list[dict[str, Any]]:
        incident = await self.get_incident(incident_id)
        if incident is None:
            raise source_error(self.get_connector_name(), "incident not found")
        history = await self.list_incidents()
        return [
            {
                **record,
                **Incident.model_validate(record).model_dump(mode="json"),
                "ticket_id": record["id"],
                "type": "similar_incident",
                "similarity_score": score,
                "source_incident_id": record["id"],
                "source_incident_title": record["title"],
            }
            for record, score in find_similar_incidents(
                incident, history, similarity_threshold=0.2, max_results=5
            )
        ]

    async def get_related_changes(self, incident_id: str, context: str) -> list[dict[str, Any]]:
        raise source_error(self.get_connector_name(), "live change retrieval is not supported")

    async def get_resolutions(self, incident_id: str, context: str) -> list[str]:
        incidents = await self.get_similar_incidents(incident_id, context)
        return [record["resolution"] for record in incidents if record.get("resolution")]
