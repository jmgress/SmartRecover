"""Tests for metrics connectors and MetricsAgent."""
import pytest

from backend.agents.metrics_agent import MetricsAgent
from backend.connectors.metrics import (
    DatadogConnector,
    MockMetricsConnector,
    PrometheusConnector,
)
from backend.config import Config, MetricsConfig


@pytest.mark.asyncio
async def test_mock_metrics_connector_returns_anomalies():
    """Mock connector supplies deterministic anomalies with documented fields."""
    anomalies = await MockMetricsConnector({}).get_metric_anomalies("INC001", "")

    assert anomalies
    assert all(
        {"id", "metric_name", "service", "current_value", "severity"} <= anomaly.keys()
        for anomaly in anomalies
    )


@pytest.mark.asyncio
async def test_metrics_agent_uses_mock_connector_by_default():
    """MetricsAgent defaults to the mock connector and returns its result shape."""
    agent = MetricsAgent()
    result = await agent.query("INC001", "database latency")

    assert isinstance(agent.connector, MockMetricsConnector)
    assert result["source"] == "mock"
    assert result["incident_id"] == "INC001"
    assert result["total_count"] == len(result["anomalies"])
    assert result["critical_count"] == len(result["anomalies"])


def test_metrics_agent_selects_configured_connector():
    """Factory selects Prometheus and Datadog connectors by source."""
    prometheus = MetricsAgent.from_config(
        {"source": "prometheus", "prometheus": {"base_url": "https://prom.example"}}
    )
    datadog = MetricsAgent.from_config({"source": "datadog"})

    assert isinstance(prometheus.connector, PrometheusConnector)
    assert isinstance(datadog.connector, DatadogConnector)


def test_metrics_config_defaults_to_mock_source():
    """Application configuration keeps the external-services-free default."""
    config = Config()

    assert isinstance(config.metrics, MetricsConfig)
    assert config.metrics.source == "mock"
