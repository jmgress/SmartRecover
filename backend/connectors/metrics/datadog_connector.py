"""Datadog metrics connector."""
from typing import Any, Dict, List

import httpx

from backend.connectors.metrics.base import MetricsConnectorBase
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class DatadogConnector(MetricsConnectorBase):
    """Query Datadog metrics API for configured anomaly queries."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.site = config.get("site", "datadoghq.com")
        self.query = config.get("query", "")
        self.api_key = config.get("api_key", "")
        self.app_key = config.get("app_key", "")

    async def get_metric_anomalies(
        self, incident_id: str, context: str
    ) -> List[Dict[str, Any]]:
        if not self.query or not self.api_key:
            logger.warning("Datadog metrics connector is not fully configured")
            return []
        headers = {"DD-API-KEY": self.api_key}
        if self.app_key:
            headers["DD-APPLICATION-KEY"] = self.app_key
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.{self.site}/api/v1/query",
                    params={"query": self.query},
                    headers=headers,
                    timeout=10.0,
                )
                response.raise_for_status()
            series = response.json().get("series", [])
        except (httpx.HTTPError, ValueError) as error:
            logger.warning(f"Datadog metrics query failed: {error}")
            return []
        return [
            {
                "id": f"METRIC-{incident_id}-{index}",
                "metric_name": item.get("metric", self.query),
                "service": item.get("scope", "unknown"),
                "current_value": item.get("pointlist", [[None, 0]])[-1][1],
                "unit": item.get("unit", [{}])[0].get("short_name", "value"),
                "severity": "WARNING",
            }
            for index, item in enumerate(series)
            if item.get("pointlist")
        ]

    def get_source_name(self) -> str:
        return "datadog"
