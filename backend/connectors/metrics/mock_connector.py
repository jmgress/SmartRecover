"""Mock metrics connector for local development and tests."""
from typing import Any, Dict, List

from backend.connectors.metrics.base import MetricsConnectorBase


class MockMetricsConnector(MetricsConnectorBase):
    """Return deterministic metric anomalies without an external service."""

    async def get_metric_anomalies(
        self, incident_id: str, context: str
    ) -> List[Dict[str, Any]]:
        return [
            {
                "id": f"METRIC-{incident_id}-latency",
                "metric_name": "http_request_duration_seconds",
                "service": "api-gateway",
                "current_value": 2.8,
                "baseline_value": 0.4,
                "unit": "seconds",
                "deviation_percent": 600.0,
                "severity": "CRITICAL",
            },
            {
                "id": f"METRIC-{incident_id}-errors",
                "metric_name": "http_requests_error_rate",
                "service": "api-gateway",
                "current_value": 12.5,
                "baseline_value": 0.8,
                "unit": "percent",
                "deviation_percent": 1462.5,
                "severity": "CRITICAL",
            },
        ]

    def get_source_name(self) -> str:
        return "mock"
