"""Base interface for metrics and observability connectors."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class MetricsConnectorBase(ABC):
    """Base class for monitoring-system connectors."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    async def get_metric_anomalies(
        self, incident_id: str, context: str
    ) -> List[Dict[str, Any]]:
        """Return metric anomalies relevant to an incident."""

    @abstractmethod
    def get_source_name(self) -> str:
        """Return the connector's source name."""
