"""
Events Agent for retrieving real-time application performance events.

This agent simulates integration with AppDynamics for event monitoring.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import random
from backend.utils.logger import get_logger, trace_async_execution
from backend.data import mock_data

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
        
        # Get incident details for context
        incident_data = self._get_incident_data(incident_id)
        
        # Generate mock events with confidence scores
        events = self._generate_mock_events(incident_id, incident_data)
        
        # Filter events by confidence threshold (keep events with confidence >= 0.3)
        filtered_events = [event for event in events if event.get('confidence_score', 0) >= 0.3]
        
        # Sort by confidence score (highest first)
        filtered_events.sort(key=lambda x: x.get('confidence_score', 0), reverse=True)
        
        # Calculate statistics
        critical_count = sum(1 for event in filtered_events if event['severity'] == 'CRITICAL')
        warning_count = sum(1 for event in filtered_events if event['severity'] == 'WARNING')
        
        result = {
            "source": "appdynamics",
            "incident_id": incident_id,
            "events": filtered_events,
            "total_count": len(filtered_events),
            "critical_count": critical_count,
            "warning_count": warning_count
        }
        
        logger.debug(f"Found {len(filtered_events)} relevant events ({critical_count} critical, {warning_count} warnings)")
        return result
    
    def _get_incident_data(self, incident_id: str) -> Dict[str, Any]:
        """Retrieve incident data for context."""
        for inc in mock_data.MOCK_INCIDENTS:
            if inc["id"] == incident_id:
                return inc
        return {}
    
    def _calculate_confidence_score(
        self, 
        event_type: str,
        event_message: str, 
        event_application: str, 
        event_severity: str,
        incident_data: Dict[str, Any]
    ) -> float:
        """
        Calculate confidence score for how relevant an event is to the incident.
        
        Returns a score between 0.0 and 1.0, where:
        - 1.0 = highly relevant
        - 0.5 = moderately relevant
        - 0.0 = not relevant
        """
        score = 0.0
        
        # Base score by severity (critical events are more relevant)
        if event_severity == 'CRITICAL':
            score += 0.3
        elif event_severity == 'WARNING':
            score += 0.2
        elif event_severity == 'INFO':
            score += 0.1
        
        # Check if event application relates to affected services
        affected_services = incident_data.get('affected_services', [])
        if affected_services:
            # Check if any affected service is mentioned in the application name
            for service in affected_services:
                if service.lower() in event_application.lower():
                    score += 0.4
                    break
        
        # Check for keyword matches in event details and incident description
        incident_title = incident_data.get('title', '').lower()
        incident_desc = incident_data.get('description', '').lower()
        event_text = (event_type + ' ' + event_message).lower()
        
        # Extract important keywords from incident
        keywords = set()
        for word in (incident_title + ' ' + incident_desc).split():
            # Filter out common words and get meaningful keywords
            if len(word) > 4 and word not in ['about', 'with', 'from', 'that', 'this', 'production', 'environment', 'affecting']:
                keywords.add(word)
        
        # Check for keyword matches
        keyword_matches = sum(1 for keyword in keywords if keyword in event_text)
        if keyword_matches > 0:
            score += min(0.3, keyword_matches * 0.15)  # Up to 0.3 for keyword matches
        
        # Normalize score to be between 0 and 1
        return min(1.0, score)
    
    def _generate_mock_events(self, incident_id: str, incident_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate mock event entries for demonstration with confidence scores."""
        now = datetime.now()
        applications = ['Web-Application', 'Mobile-API', 'Payment-Gateway', 'User-Service', 
                       'Analytics-Service', 'Cache-Service', 'Search-Service', 'Notification-Service']
        
        # Include affected services from incident (convert to application names)
        affected_services = incident_data.get('affected_services', [])
        if affected_services:
            for service in affected_services:
                # Convert service names to application names (e.g., "auth-service" -> "Auth-Service")
                app_name = '-'.join(word.capitalize() for word in service.split('-'))
                if app_name not in applications:
                    applications.append(app_name)
        
        # Generate different event patterns based on incident_id for variety
        seed = sum(ord(c) for c in incident_id)
        random.seed(seed)
        
        events = []
        num_events = random.randint(12, 20)  # Generate more events to filter from
        
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
            ("CRITICAL", "Memory Leak Detected", "Memory leak in worker process"),
            ("WARNING", "API Latency Spike", "API response latency increased"),
            ("CRITICAL", "Cache Connection Failure", "Cache connection pool exhausted"),
            ("WARNING", "Log Pipeline Delay", "Log aggregation pipeline delayed"),
            ("CRITICAL", "Connection Pool Exhausted", "Redis connection failures detected"),
        ]
        
        for i in range(num_events):
            severity, event_type, message = random.choice(event_templates)
            application = random.choice(applications)
            timestamp = now - timedelta(minutes=random.randint(2, 45))
            
            event_id = f"EVT-{abs(hash(f'{incident_id}-{i}')) % 100000:05d}"
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                event_type,
                message,
                application,
                severity,
                incident_data
            )
            
            events.append({
                "id": event_id,
                "timestamp": timestamp.isoformat(),
                "type": event_type,
                "severity": severity,
                "application": application,
                "message": message,
                "details": f"Detected in {application} at {timestamp.strftime('%H:%M:%S')}",
                "confidence_score": round(confidence_score, 2)
            })
        
        # Sort by timestamp (most recent first)
        events.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return events
