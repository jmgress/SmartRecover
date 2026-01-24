"""
Logs Agent for retrieving and analyzing log data.

This agent simulates integration with Splunk for log retrieval.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import random
from backend.utils.logger import get_logger, trace_async_execution
from backend.data import mock_data

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
        
        # Get incident details for context
        incident_data = self._get_incident_data(incident_id)
        
        # Generate mock log entries with confidence scores
        logs = self._generate_mock_logs(incident_id, incident_data)
        
        # Filter logs by confidence threshold (keep logs with confidence >= 0.3)
        filtered_logs = [log for log in logs if log.get('confidence_score', 0) >= 0.3]
        
        # Sort by confidence score (highest first)
        filtered_logs.sort(key=lambda x: x.get('confidence_score', 0), reverse=True)
        
        # Calculate statistics
        error_count = sum(1 for log in filtered_logs if log['level'] == 'ERROR')
        warning_count = sum(1 for log in filtered_logs if log['level'] == 'WARN')
        
        result = {
            "source": "splunk",
            "incident_id": incident_id,
            "logs": filtered_logs,
            "total_count": len(filtered_logs),
            "error_count": error_count,
            "warning_count": warning_count
        }
        
        logger.debug(f"Found {len(filtered_logs)} relevant log entries ({error_count} errors, {warning_count} warnings)")
        return result
    
    def _get_incident_data(self, incident_id: str) -> Dict[str, Any]:
        """Retrieve incident data for context."""
        for inc in mock_data.MOCK_INCIDENTS:
            if inc["id"] == incident_id:
                return inc
        return {}
    
    def _calculate_confidence_score(
        self, 
        log_message: str, 
        log_service: str, 
        log_level: str,
        incident_data: Dict[str, Any]
    ) -> float:
        """
        Calculate confidence score for how relevant a log is to the incident.
        
        Returns a score between 0.0 and 1.0, where:
        - 1.0 = highly relevant
        - 0.5 = moderately relevant
        - 0.0 = not relevant
        """
        score = 0.0
        
        # Base score by log level (errors and warnings are more relevant)
        if log_level == 'ERROR':
            score += 0.3
        elif log_level == 'WARN':
            score += 0.2
        elif log_level == 'INFO':
            score += 0.1
        
        # Check if log service matches affected services
        affected_services = incident_data.get('affected_services', [])
        if affected_services and log_service in affected_services:
            score += 0.4
        
        # Check for keyword matches in log message and incident description
        incident_title = incident_data.get('title', '').lower()
        incident_desc = incident_data.get('description', '').lower()
        log_message_lower = log_message.lower()
        
        # Extract important keywords from incident
        keywords = set()
        for word in (incident_title + ' ' + incident_desc).split():
            # Filter out common words and get meaningful keywords
            if len(word) > 4 and word not in ['about', 'with', 'from', 'that', 'this', 'production', 'environment', 'affecting']:
                keywords.add(word)
        
        # Check for keyword matches
        keyword_matches = sum(1 for keyword in keywords if keyword in log_message_lower)
        if keyword_matches > 0:
            score += min(0.3, keyword_matches * 0.15)  # Up to 0.3 for keyword matches
        
        # Normalize score to be between 0 and 1
        return min(1.0, score)
    
    def _generate_mock_logs(self, incident_id: str, incident_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate mock log entries for demonstration with confidence scores."""
        now = datetime.now()
        services = ['api-gateway', 'auth-service', 'database', 'payment-service', 'user-service', 
                   'cache-service', 'search-service', 'notification-service', 'reporting-service']
        
        # Include affected services from incident
        affected_services = incident_data.get('affected_services', [])
        if affected_services:
            services = list(set(services + affected_services))
        
        # Generate different log patterns based on incident_id for variety
        seed = sum(ord(c) for c in incident_id)
        random.seed(seed)
        
        logs = []
        num_logs = random.randint(15, 25)  # Generate more logs to filter from
        
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
            ("ERROR", "Memory leak detected in worker process"),
            ("WARN", "API response latency spike detected"),
            ("ERROR", "Cache connection failure"),
            ("WARN", "Log aggregation pipeline delayed"),
            ("ERROR", "Redis connection pool exhausted"),
            ("INFO", "Health check passed"),
        ]
        
        for i in range(num_logs):
            level, message = random.choice(log_messages)
            service = random.choice(services)
            timestamp = now - timedelta(minutes=random.randint(5, 60))
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                message, 
                service, 
                level, 
                incident_data
            )
            
            logs.append({
                "timestamp": timestamp.isoformat(),
                "level": level,
                "service": service,
                "message": message,
                "source": f"{service}.log",
                "confidence_score": round(confidence_score, 2)
            })
        
        # Sort by timestamp (most recent first)
        logs.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return logs
