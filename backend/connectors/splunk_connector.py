import json
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

import httpx

from backend.connectors.base import IncidentManagementConnector
from backend.connectors.utils import extract_secret_value
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class SplunkConnector(IncidentManagementConnector):
    """Connector for Splunk incident and notable event searches."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = (config.get("base_url") or "").rstrip("/")
        self.host = config.get("host", "localhost")
        self.port = int(config.get("port", 8089))
        self.token = extract_secret_value(config.get("token"))
        self.username = config.get("username", "")
        self.password = extract_secret_value(config.get("password"))
        self.index = config.get("index", "main")
        self.incidents_search = config.get("incidents_search", "")
        self.incident_lookup_search = config.get("incident_lookup_search", self.incidents_search)
        self.similar_incidents_search = config.get("similar_incidents_search", "")
        self.related_changes_search = config.get("related_changes_search", "")
        self.resolutions_search = config.get("resolutions_search", "")
        self.verify_ssl = config.get("verify_ssl", True)
        self.last_warning: Optional[str] = None

    def reset_warning(self) -> None:
        self.last_warning = None

    def get_last_warning(self) -> Optional[str]:
        return self.last_warning

    def _set_warning(self, message: str) -> None:
        self.last_warning = message
        logger.warning(message)

    def _get_api_base_url(self) -> str:
        if self.base_url:
            return self.base_url
        return f"https://{self.host}:{self.port}"

    def _build_search(self, template: str, incident_id: str = "", context: str = "") -> str:
        query = template or ""
        safe_context = re.sub(r"[^\w\s\-.:/]", " ", context or "").strip()
        return query.format(
            index=self.index,
            incident_id=incident_id,
            context=safe_context,
        )

    async def _run_search(self, search: str) -> List[Dict[str, Any]]:
        if not search:
            self._set_warning("Splunk search is not configured.")
            return []

        url = f"{self._get_api_base_url()}/services/search/jobs/export"
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Splunk {self.token}"

        auth = None
        if not self.token and self.username and self.password:
            auth = (self.username, self.password)

        try:
            async with httpx.AsyncClient(
                verify=self.verify_ssl,
                timeout=15.0,
                headers=headers,
                auth=auth,
            ) as client:
                response = await client.post(
                    url,
                    data={
                        "search": search,
                        "output_mode": "json",
                        "exec_mode": "oneshot",
                    },
                )
                if response.status_code in (401, 403):
                    self._set_warning("Unable to authenticate to Splunk with the configured credentials.")
                    return []

                response.raise_for_status()
                return self._parse_search_response(response)
        except httpx.HTTPStatusError:
            self._set_warning("Splunk returned an unexpected error while searching incident data.")
            return []
        except httpx.HTTPError as exc:
            self._set_warning(f"Failed to query Splunk incident data: {type(exc).__name__}")
            return []

    def _parse_search_response(self, response: httpx.Response) -> List[Dict[str, Any]]:
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            payload = response.json()
            if isinstance(payload, list):
                return [item for item in payload if isinstance(item, dict)]
            if isinstance(payload, dict):
                if isinstance(payload.get("results"), list):
                    return [item for item in payload["results"] if isinstance(item, dict)]
                if isinstance(payload.get("result"), dict):
                    return [payload["result"]]

        results: List[Dict[str, Any]] = []
        for line in response.text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict) and isinstance(parsed.get("result"), dict):
                results.append(parsed["result"])
            elif isinstance(parsed, dict):
                results.append(parsed)
        return results

    def _normalize_services(self, services: Any) -> List[str]:
        if isinstance(services, list):
            normalized_services = []
            for service in services:
                if service is None:
                    continue
                normalized = str(service).strip()
                if normalized:
                    normalized_services.append(normalized)
            return normalized_services
        if isinstance(services, str):
            normalized = services.replace("|", ",")
            return [service.strip() for service in normalized.split(",") if service.strip()]
        return []

    def _normalize_datetime(self, value: Any) -> str:
        if not value:
            return datetime.now(timezone.utc).isoformat()
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()
        text = str(value).strip()
        if not text:
            return datetime.now(timezone.utc).isoformat()
        if text.endswith("Z"):
            return text
        try:
            return datetime.fromisoformat(text).isoformat()
        except ValueError:
            try:
                return datetime.fromtimestamp(float(text), tz=timezone.utc).isoformat()
            except ValueError:
                return datetime.now(timezone.utc).isoformat()

    def _normalize_incident(self, result: Dict[str, Any]) -> Dict[str, Any]:
        incident_id = (
            result.get("incident_id")
            or result.get("id")
            or result.get("event_id")
            or result.get("notable_id")
            or result.get("_cd")
            or "SPLUNK-UNKNOWN"
        )
        return {
            "id": str(incident_id),
            "title": str(result.get("title") or result.get("name") or result.get("rule_name") or "Splunk Incident"),
            "description": str(result.get("description") or result.get("message") or result.get("_raw") or ""),
            "severity": str(result.get("severity") or result.get("priority") or "medium"),
            "status": str(result.get("status") or result.get("state") or "open"),
            "created_at": self._normalize_datetime(result.get("created_at") or result.get("_time")),
            "updated_at": self._normalize_datetime(result.get("updated_at") or result.get("last_time") or result.get("_time")),
            "affected_services": self._normalize_services(
                result.get("affected_services") or result.get("service") or result.get("services")
            ),
            "assignee": result.get("assignee") or result.get("owner"),
            "source": "splunk",
        }

    async def list_incidents(self) -> List[Dict[str, Any]]:
        self.reset_warning()
        results = await self._run_search(self._build_search(self.incidents_search))
        incidents = [self._normalize_incident(result) for result in results]
        if not incidents and not self.last_warning:
            logger.warning("No incidents were returned from Splunk.")
        return incidents

    async def get_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        self.reset_warning()
        search = self._build_search(self.incident_lookup_search, incident_id=incident_id)
        results = await self._run_search(search)
        for result in results:
            incident = self._normalize_incident(result)
            if incident["id"] == incident_id:
                return incident
        return None

    async def get_similar_incidents(self, incident_id: str, context: str) -> List[Dict[str, Any]]:
        search = self._build_search(self.similar_incidents_search, incident_id=incident_id, context=context)
        results = await self._run_search(search)
        return [
            {
                "id": str(result.get("incident_id") or result.get("id") or result.get("event_id") or ""),
                "title": str(result.get("title") or result.get("name") or "Splunk Incident"),
                "description": str(result.get("description") or result.get("message") or ""),
                "resolution": result.get("resolution") or result.get("close_notes"),
                "severity": result.get("severity") or result.get("priority"),
                "status": result.get("status") or result.get("state"),
                "similarity_score": float(result.get("similarity_score") or result.get("score") or 0),
            }
            for result in results
        ]

    async def get_related_changes(self, incident_id: str, context: str) -> List[Dict[str, Any]]:
        search = self._build_search(self.related_changes_search, incident_id=incident_id, context=context)
        results = await self._run_search(search)
        return [
            {
                "change_id": str(result.get("change_id") or result.get("id") or ""),
                "description": str(result.get("description") or result.get("title") or ""),
                "deployed_at": self._normalize_datetime(result.get("deployed_at") or result.get("_time")),
                "correlation_score": float(result.get("correlation_score") or result.get("score") or 0),
                "service": result.get("service"),
            }
            for result in results
        ]

    async def get_resolutions(self, incident_id: str, context: str) -> List[str]:
        search = self._build_search(self.resolutions_search, incident_id=incident_id, context=context)
        results = await self._run_search(search)
        resolutions = []
        for result in results:
            resolution = result.get("resolution") or result.get("close_notes")
            if resolution:
                resolutions.append(str(resolution))
        return resolutions

    def get_connector_name(self) -> str:
        return "splunk"
