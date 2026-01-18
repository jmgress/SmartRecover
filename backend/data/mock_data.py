from datetime import datetime

MOCK_INCIDENTS = [
    {
        "id": "INC001",
        "title": "Database connection timeout",
        "description": "Production database experiencing intermittent connection timeouts affecting user login",
        "severity": "high",
        "status": "open",
        "created_at": datetime(2026, 1, 17, 10, 30),
        "affected_services": ["auth-service", "user-service"],
        "assignee": "ops-team"
    },
    {
        "id": "INC002",
        "title": "API response latency spike",
        "description": "Customer-facing API showing 5x increase in response times",
        "severity": "medium",
        "status": "investigating",
        "created_at": datetime(2026, 1, 17, 12, 0),
        "affected_services": ["api-gateway", "order-service"],
        "assignee": None
    }
]

MOCK_SERVICENOW_TICKETS = {
    "INC001": [
        {
            "ticket_id": "SNOW001",
            "type": "similar_incident",
            "resolution": "Increased connection pool size and added retry logic",
            "source": "servicenow"
        },
        {
            "ticket_id": "SNOW002",
            "type": "related_change",
            "description": "Database migration completed last week",
            "source": "servicenow"
        }
    ],
    "INC002": [
        {
            "ticket_id": "SNOW003",
            "type": "similar_incident",
            "resolution": "Identified memory leak in API gateway, restarted pods",
            "source": "servicenow"
        },
        {
            "ticket_id": "JIRA-123",
            "type": "similar_incident",
            "resolution": "Scaled up API gateway instances and optimized query performance",
            "source": "jira"
        },
        {
            "ticket_id": "JIRA-124",
            "type": "related_change",
            "description": "Deployed new API gateway version with performance improvements",
            "source": "jira"
        }
    ]
}

MOCK_CONFLUENCE_DOCS = {
    "INC001": [
        {"doc_id": "CONF001", "title": "Database Troubleshooting Guide", "content": "Steps: 1. Check connection pool stats 2. Verify network latency 3. Review recent schema changes"},
        {"doc_id": "CONF002", "title": "Auth Service Runbook", "content": "For connection issues, first check the database health dashboard"}
    ],
    "INC002": [
        {"doc_id": "CONF003", "title": "API Gateway Performance Tuning", "content": "Monitor memory usage, check for N+1 queries, review rate limiting settings"}
    ]
}

MOCK_CHANGE_CORRELATIONS = {
    "INC001": [
        {"change_id": "CHG001", "description": "Database schema update", "deployed_at": "2026-01-15T14:00:00Z", "correlation_score": 0.85},
        {"change_id": "CHG002", "description": "Auth service config update", "deployed_at": "2026-01-16T09:00:00Z", "correlation_score": 0.72}
    ],
    "INC002": [
        {"change_id": "CHG003", "description": "API gateway version upgrade", "deployed_at": "2026-01-17T08:00:00Z", "correlation_score": 0.91}
    ]
}
