"""
Logs Agent for retrieving and analyzing log data.

This agent simulates integration with Splunk for log retrieval.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import random
from backend.utils.logger import get_logger, trace_async_execution

logger = get_logger(__name__)


class LogsAgent:
    """Agent responsible for querying logs from Splunk (mock implementation)."""
    
    def __init__(self):
        """Initialize Logs agent."""
        self.name = "logs_agent"
        logger.debug(f"Initialized {self.name}")
    
    @trace_async_execution
    async def query(self, incident_id: str, context: str) -> Dict[str, Any]:
        """
        Query logs for the incident.
        
        Args:
            incident_id: The incident ID
            context: Additional context for the query
            
        Returns:
            Dictionary containing log entries and summary statistics
        """
        logger.info(f"Logs query for incident: {incident_id}")
        
        # Generate mock log entries
        logs = self._generate_mock_logs(incident_id)
        
        # Calculate statistics
        error_count = sum(1 for log in logs if log['level'] == 'ERROR')
        warning_count = sum(1 for log in logs if log['level'] == 'WARN')
        
        result = {
            "source": "splunk",
            "incident_id": incident_id,
            "logs": logs,
            "total_count": len(logs),
            "error_count": error_count,
            "warning_count": warning_count
        }
        
        logger.debug(f"Found {len(logs)} log entries ({error_count} errors, {warning_count} warnings)")
        return result
    
    def _generate_mock_logs(self, incident_id: str) -> List[Dict[str, Any]]:
        """Generate mock log entries for demonstration."""
        now = datetime.now()
        services = ['api-gateway', 'auth-service', 'database', 'payment-service', 'user-service']
        
        # Generate different log patterns based on incident_id for variety
        seed = sum(ord(c) for c in incident_id)
        random.seed(seed)
        
        logs = []
        num_logs = random.randint(8, 15)
        
        log_messages = [
            ("ERROR", "Database connection timeout after 30s"),
            ("ERROR", "Failed to process payment transaction"),
            ("ERROR", "Authentication service unreachable"),
            ("WARN", "High memory usage detected: 85%"),
            ("WARN", "Response time exceeding threshold: 2500ms"),
            ("WARN", "Connection pool near capacity: 90%"),
            ("ERROR", "Null pointer exception in request handler"),
            ("INFO", "Service restart initiated"),
            ("ERROR", "Circuit breaker opened for external API"),
            ("WARN", "Disk space low: 15% remaining"),
            ("INFO", "Fallback cache activated"),
            ("ERROR", "Message queue connection lost"),
        ]
        
        for i in range(num_logs):
            level, message = random.choice(log_messages)
            service = random.choice(services)
            timestamp = now - timedelta(minutes=random.randint(5, 60))
            
            logs.append({
                "timestamp": timestamp.isoformat(),
                "level": level,
                "service": service,
                "message": message,
                "source": f"{service}.log"
            })
        
        # Sort by timestamp (most recent first)
        logs.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return logs
