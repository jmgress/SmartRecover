"""
Events Agent for retrieving real-time application performance events.

This agent simulates integration with AppDynamics for event monitoring.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import random
from backend.utils.logger import get_logger, trace_async_execution

logger = get_logger(__name__)


class EventsAgent:
    """Agent responsible for querying real-time events from AppDynamics (mock implementation)."""
    
    def __init__(self):
        """Initialize Events agent."""
        self.name = "events_agent"
        logger.debug(f"Initialized {self.name}")
    
    @trace_async_execution
    async def query(self, incident_id: str, context: str) -> Dict[str, Any]:
        """
        Query real-time events for the incident.
        
        Args:
            incident_id: The incident ID
            context: Additional context for the query
            
        Returns:
            Dictionary containing event entries and summary statistics
        """
        logger.info(f"Events query for incident: {incident_id}")
        
        # Generate mock events
        events = self._generate_mock_events(incident_id)
        
        # Calculate statistics
        critical_count = sum(1 for event in events if event['severity'] == 'CRITICAL')
        warning_count = sum(1 for event in events if event['severity'] == 'WARNING')
        
        result = {
            "source": "appdynamics",
            "incident_id": incident_id,
            "events": events,
            "total_count": len(events),
            "critical_count": critical_count,
            "warning_count": warning_count
        }
        
        logger.debug(f"Found {len(events)} events ({critical_count} critical, {warning_count} warnings)")
        return result
    
    def _generate_mock_events(self, incident_id: str) -> List[Dict[str, Any]]:
        """Generate mock event entries for demonstration."""
        now = datetime.now()
        applications = ['Web-Application', 'Mobile-API', 'Payment-Gateway', 'User-Service', 'Analytics-Service']
        
        # Generate different event patterns based on incident_id for variety
        seed = sum(ord(c) for c in incident_id)
        random.seed(seed)
        
        events = []
        num_events = random.randint(6, 12)
        
        event_templates = [
            ("CRITICAL", "Slow Transaction", "Response time exceeded 5000ms"),
            ("CRITICAL", "Error Rate Spike", "Error rate increased to 15% in last 5 minutes"),
            ("WARNING", "Memory Threshold", "Heap memory usage at 80%"),
            ("CRITICAL", "Service Down", "Health check failing for 3 consecutive attempts"),
            ("WARNING", "CPU Spike", "CPU utilization at 85% for 2 minutes"),
            ("INFO", "Deployment Event", "New version deployed successfully"),
            ("WARNING", "Slow Database Query", "Query execution time: 4200ms"),
            ("CRITICAL", "Circuit Breaker Open", "External service circuit breaker tripped"),
            ("WARNING", "Cache Miss Rate High", "Cache miss rate at 60%"),
            ("INFO", "Scale Event", "Auto-scaling triggered: added 2 instances"),
        ]
        
        for i in range(num_events):
            severity, event_type, message = random.choice(event_templates)
            application = random.choice(applications)
            timestamp = now - timedelta(minutes=random.randint(2, 45))
            
            event_id = f"EVT-{abs(hash(f'{incident_id}-{i}')) % 100000:05d}"
            
            events.append({
                "id": event_id,
                "timestamp": timestamp.isoformat(),
                "type": event_type,
                "severity": severity,
                "application": application,
                "message": message,
                "details": f"Detected in {application} at {timestamp.strftime('%H:%M:%S')}"
            })
        
        # Sort by timestamp (most recent first)
        events.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return events
