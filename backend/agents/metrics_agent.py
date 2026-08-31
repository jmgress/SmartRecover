"""Metrics and observability agent with pluggable monitoring connectors."""
from typing import Any, Dict

from backend.connectors.metrics import (
    DatadogConnector,
    MetricsConnectorBase,
    MockMetricsConnector,
    PrometheusConnector,
)
from backend.utils.logger import get_logger, trace_async_execution

logger = get_logger(__name__)


class MetricsAgent:
    """Retrieve correlated metric anomalies for an incident."""

    def __init__(self, connector: MetricsConnectorBase = None):
        self.name = "metrics_agent"
        self.connector = connector or MockMetricsConnector({})
        logger.debug(
            f"Initialized {self.name} with {self.connector.get_source_name()} connector"
        )

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "MetricsAgent":
        """Create a metrics agent from source-specific configuration."""
        source = config.get("source", "mock")
        if source == "prometheus":
            connector = PrometheusConnector(config.get("prometheus", {}))
        elif source == "datadog":
            connector = DatadogConnector(config.get("datadog", {}))
        else:
            connector = MockMetricsConnector(config.get("mock", {}))
        return cls(connector=connector)

    @trace_async_execution
    async def query(self, incident_id: str, context: str) -> Dict[str, Any]:
        """Query the configured monitoring system for incident anomalies."""
        logger.info(f"Metrics query for incident: {incident_id}")
        anomalies = await self.connector.get_metric_anomalies(incident_id, context)
        critical_count = sum(
            anomaly.get("severity") == "CRITICAL" for anomaly in anomalies
        )
        return {
            "source": self.connector.get_source_name(),
            "incident_id": incident_id,
            "anomalies": anomalies,
            "total_count": len(anomalies),
            "critical_count": critical_count,
        }
