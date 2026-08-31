"""Prometheus metrics connector."""
from typing import Any, Dict, List

import httpx

from backend.connectors.metrics.base import MetricsConnectorBase
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class PrometheusConnector(MetricsConnectorBase):
    """Query Prometheus instant-query API for configured anomaly queries."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "").rstrip("/")
        self.query = config.get("query", "")
        self.bearer_token = config.get("bearer_token", "")

    async def get_metric_anomalies(
        self, incident_id: str, context: str
    ) -> List[Dict[str, Any]]:
        if not self.base_url or not self.query:
            logger.warning("Prometheus metrics connector is not fully configured")
            return []
        headers = (
            {"Authorization": f"******"}
            if self.bearer_token
            else {}
        )
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/query",
                    params={"query": self.query},
                    headers=headers,
                    timeout=10.0,
                )
                response.raise_for_status()
            results = response.json().get("data", {}).get("result", [])
        except (httpx.HTTPError, ValueError) as error:
            logger.warning(f"Prometheus metrics query failed: {error}")
            return []
        return [
            {
                "id": f"METRIC-{incident_id}-{index}",
                "metric_name": item.get("metric", {}).get("__name__", self.query),
                "service": item.get("metric", {}).get("service", "unknown"),
                "current_value": float(item.get("value", [None, 0])[1]),
                "unit": "value",
                "severity": "WARNING",
            }
            for index, item in enumerate(results)
        ]

    def get_source_name(self) -> str:
        return "prometheus"
