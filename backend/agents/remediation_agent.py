"""
Remediation Agent for providing script-based remediation recommendations.

This agent analyzes incidents and suggests actionable scripts that can help resolve issues.
"""

from typing import Dict, Any, List
from backend.utils.logger import get_logger, trace_async_execution
from backend.data import mock_data

logger = get_logger(__name__)


class RemediationAgent:
    """Agent responsible for providing remediation script recommendations."""
    
    def __init__(self):
        """Initialize Remediation agent."""
        self.name = "remediation_agent"
        logger.debug(f"Initialized {self.name}")
    
    @trace_async_execution
    async def query(self, incident_id: str, context: str) -> Dict[str, Any]:
        """
        Query remediations for the incident.
        
        Args:
            incident_id: The incident ID
            context: Additional context for the query
            
        Returns:
            Dictionary containing remediation script recommendations
        """
        logger.info(f"Remediation query for incident: {incident_id}")
        
        # Get incident details for context
        incident_data = self._get_incident_data(incident_id)
        
        # Generate remediation recommendations based on incident
        remediations = self._generate_remediations(incident_id, incident_data)
        
        result = {
            "source": "remediation_engine",
            "incident_id": incident_id,
            "remediations": remediations,
            "total_count": len(remediations)
        }
        
        logger.debug(f"Found {len(remediations)} remediation recommendations")
        return result
    
    def _get_incident_data(self, incident_id: str) -> Dict[str, Any]:
        """Retrieve incident data for context."""
        for inc in mock_data.MOCK_INCIDENTS:
            if inc["id"] == incident_id:
                return inc
        return {}
    
    def _generate_remediations(self, incident_id: str, incident_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate remediation script recommendations based on the incident."""
        
        severity = incident_data.get('severity', 'Medium').lower()
        title = incident_data.get('title', '').lower()
        description = incident_data.get('description', '').lower()
        affected_services = incident_data.get('affected_services', [])
        
        remediations = []
        
        # Helper function to check if a keyword matches affected services
        def matches_service(keyword: str) -> bool:
            """Check if keyword appears in any affected service."""
            keyword_lower = keyword.lower()
            return any(keyword_lower in service.lower() for service in affected_services)
        
        # Database-related remediations
        if 'database' in title or 'database' in description or matches_service('database'):
            remediations.extend([
                {
                    "id": "rem-db-001",
                    "title": "Restart Database Connection Pool",
                    "description": "Restarts the database connection pool to clear stale connections and re-establish healthy connections. This often resolves connection timeout issues.",
                    "script": "kubectl rollout restart deployment/db-connection-pool",
                    "risk_level": "low",
                    "estimated_duration": "2-3 minutes",
                    "prerequisites": ["Database backup completed", "Connection pool health check"],
                    "confidence_score": 0.85
                },
                {
                    "id": "rem-db-002",
                    "title": "Clear Database Query Cache",
                    "description": "Clears the query cache to remove potentially corrupted or stale cached queries. Useful for performance issues.",
                    "script": "mysql -e 'RESET QUERY CACHE;' -h db-primary -u admin -p",
                    "risk_level": "low",
                    "estimated_duration": "30 seconds",
                    "prerequisites": ["Read-only mode enabled"],
                    "confidence_score": 0.72
                }
            ])
        
        # API/Service-related remediations
        if 'api' in title or 'service' in title or matches_service('api') or matches_service('service'):
            remediations.extend([
                {
                    "id": "rem-svc-001",
                    "title": "Restart Affected Microservices",
                    "description": "Performs a rolling restart of the affected microservices to clear any memory leaks or stuck threads. Zero-downtime deployment.",
                    "script": "kubectl rollout restart deployment/api-gateway deployment/auth-service",
                    "risk_level": "low",
                    "estimated_duration": "5-7 minutes",
                    "prerequisites": ["Load balancer health check configured", "Auto-scaling enabled"],
                    "confidence_score": 0.78
                },
                {
                    "id": "rem-svc-002",
                    "title": "Scale Up Service Replicas",
                    "description": "Increases the number of service replicas to handle increased load and distribute traffic more effectively.",
                    "script": "kubectl scale deployment/api-gateway --replicas=6",
                    "risk_level": "low",
                    "estimated_duration": "2-4 minutes",
                    "prerequisites": ["Resource quotas available", "Auto-scaling limits checked"],
                    "confidence_score": 0.81
                }
            ])
        
        # Memory/Performance-related remediations
        if 'memory' in title or 'performance' in title or 'slow' in title:
            remediations.extend([
                {
                    "id": "rem-perf-001",
                    "title": "Clear Application Cache",
                    "description": "Flushes the application cache (Redis/Memcached) to remove stale or corrupted cached data that might be causing issues.",
                    "script": "redis-cli -h cache-primary FLUSHDB",
                    "risk_level": "medium",
                    "estimated_duration": "1 minute",
                    "prerequisites": ["Cache rebuild strategy in place", "Monitoring alerts configured"],
                    "confidence_score": 0.69
                },
                {
                    "id": "rem-perf-002",
                    "title": "Trigger Garbage Collection",
                    "description": "Forces garbage collection on application servers to free up memory and improve performance.",
                    "script": "./scripts/trigger-gc.sh --service=all",
                    "risk_level": "low",
                    "estimated_duration": "30 seconds",
                    "prerequisites": ["Application supports manual GC trigger"],
                    "confidence_score": 0.65
                }
            ])
        
        # Network/Connectivity remediations
        if 'timeout' in title or 'connection' in title or 'network' in title:
            remediations.extend([
                {
                    "id": "rem-net-001",
                    "title": "Reset Network Policy Rules",
                    "description": "Reapplies network policy rules to resolve potential configuration drift or rule conflicts affecting connectivity.",
                    "script": "kubectl apply -f ./k8s/network-policies/",
                    "risk_level": "medium",
                    "estimated_duration": "1-2 minutes",
                    "prerequisites": ["Network policy files validated", "Backup of current policies"],
                    "confidence_score": 0.74
                },
                {
                    "id": "rem-net-002",
                    "title": "Cycle Load Balancer Connection Pool",
                    "description": "Cycles the load balancer connection pool to clear stuck connections and rebalance traffic distribution.",
                    "script": "./scripts/lb-pool-cycle.sh --target=production",
                    "risk_level": "low",
                    "estimated_duration": "2 minutes",
                    "prerequisites": ["Multiple load balancer instances available"],
                    "confidence_score": 0.71
                }
            ])
        
        # Authentication remediations
        if 'auth' in title or 'login' in title or 'authentication' in description:
            remediations.extend([
                {
                    "id": "rem-auth-001",
                    "title": "Refresh Authentication Token Cache",
                    "description": "Clears and refreshes the authentication token cache to resolve stale token issues.",
                    "script": "kubectl exec -it deployment/auth-service -- /app/refresh-token-cache.sh",
                    "risk_level": "low",
                    "estimated_duration": "1 minute",
                    "prerequisites": ["Token refresh endpoint available"],
                    "confidence_score": 0.77
                },
                {
                    "id": "rem-auth-002",
                    "title": "Restart OAuth Provider Connection",
                    "description": "Restarts the connection to the OAuth provider to re-establish authentication flow.",
                    "script": "./scripts/restart-oauth.sh --provider=all",
                    "risk_level": "medium",
                    "estimated_duration": "3 minutes",
                    "prerequisites": ["OAuth provider health check", "Fallback authentication available"],
                    "confidence_score": 0.68
                }
            ])
        
        # If no specific remediations matched, provide generic ones
        if not remediations:
            remediations.extend([
                {
                    "id": "rem-gen-001",
                    "title": "Run Full System Health Check",
                    "description": "Executes a comprehensive health check across all system components to identify potential issues.",
                    "script": "./scripts/health-check.sh --full --verbose",
                    "risk_level": "low",
                    "estimated_duration": "3-5 minutes",
                    "prerequisites": ["Monitoring systems operational"],
                    "confidence_score": 0.60
                },
                {
                    "id": "rem-gen-002",
                    "title": "Review Recent Configuration Changes",
                    "description": "Retrieves and displays recent configuration changes that may have contributed to the incident.",
                    "script": "git log --since='24 hours ago' --pretty=format:'%h - %s' -- config/",
                    "risk_level": "low",
                    "estimated_duration": "1 minute",
                    "prerequisites": ["Access to configuration repository"],
                    "confidence_score": 0.55
                }
            ])
        
        # Sort by confidence score (highest first) and limit to top 5
        remediations.sort(key=lambda x: x.get('confidence_score', 0), reverse=True)
        return remediations[:5]
