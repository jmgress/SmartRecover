# Logging and Tracing

SmartRecover includes comprehensive logging and distributed tracing capabilities to help monitor and debug the incident resolution system.

## Features

- **Structured Logging**: All log messages include consistent metadata
- **Request Tracing**: Unique trace IDs track requests across all components
- **JSON Format Support**: Optional JSON output for log aggregation systems
- **Configurable Log Levels**: Control verbosity from DEBUG to ERROR
- **Component-Specific Logging**: Each component (API, agents, LLM) has dedicated logging

## Configuration

### Environment Variables

Configure logging using environment variables:

```bash
# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
export LOG_LEVEL=INFO

# Enable JSON format (useful for log aggregation)
export LOG_JSON=true

# Optional: Write logs to a file
export LOG_FILE=/var/log/smartrecover.log
```

### Quick Start

The logging system is automatically initialized when the application starts. No additional setup is required.

Start the application with desired log level:

```bash
# Default logging (INFO level, text format)
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000

# Debug logging
LOG_LEVEL=DEBUG uvicorn main:app --host 0.0.0.0 --port 8000

# JSON logging for production
LOG_LEVEL=INFO LOG_JSON=true uvicorn main:app --host 0.0.0.0 --port 8000
```

## Log Output Examples

### Standard Text Format

```
2026-01-17 22:46:25 - backend.logging_config - INFO - Logging configured
2026-01-17 22:46:25 - backend.main - INFO - SmartRecover Incident Management Resolver starting up
2026-01-17 22:46:28 - backend.main - INFO - Incoming request: GET /api/v1/health
2026-01-17 22:46:28 - backend.api.routes - DEBUG - Health check accessed
2026-01-17 22:46:28 - backend.main - INFO - Response: 200
```

### JSON Format

```json
{"timestamp": "2026-01-17T22:46:25.123456Z", "level": "INFO", "logger": "backend.main", "message": "Incoming request: GET /api/v1/resolve", "trace_id": "abc-123-def-456", "method": "POST", "path": "/api/v1/resolve", "client_host": "127.0.0.1"}
{"timestamp": "2026-01-17T22:46:25.234567Z", "level": "INFO", "logger": "backend.agents.orchestrator", "message": "Starting incident resolution workflow", "trace_id": "abc-123-def-456", "incident_id": "INC001", "user_query": "What caused this issue?"}
{"timestamp": "2026-01-17T22:46:25.345678Z", "level": "INFO", "logger": "backend.agents.servicenow_agent", "message": "ServiceNow query completed", "trace_id": "abc-123-def-456", "incident_id": "INC001", "similar_incidents": 3, "related_changes": 1}
```

## Request Tracing

Each API request automatically receives a unique trace ID that is:

1. **Generated** automatically or extracted from `X-Trace-ID` header
2. **Propagated** through all components (orchestrator, agents, LLM)
3. **Returned** in the response via `X-Trace-ID` header
4. **Logged** with every log message related to that request

### Using Trace IDs

Send a request with a custom trace ID:

```bash
curl -H "X-Trace-ID: my-custom-trace-123" \
  http://localhost:8000/api/v1/incidents
```

The same trace ID will appear in all logs and be returned in the response:

```bash
X-Trace-ID: my-custom-trace-123
```

## Logged Events

### API Layer (`backend.api.routes`)

- Incoming requests with method, path, and client info
- Incident queries and resolution requests
- Response status codes
- Error conditions

### Orchestrator Agent (`backend.agents.orchestrator`)

- Workflow initialization and completion
- Graph node execution (ServiceNow, Confluence, Changes)
- LLM invocations and responses
- Result synthesis and confidence calculations

### Individual Agents

- **ServiceNow Agent**: Query execution, similar incidents found, related changes
- **Confluence Agent**: Document searches, articles found
- **Change Correlation Agent**: Correlation analysis, top suspects identified

### LLM Manager (`backend.llm.llm_manager`)

- Provider initialization (OpenAI, Gemini, Ollama)
- Model configuration
- Provider switching and reloading

### Configuration Manager (`backend.config`)

- Configuration file loading
- Environment variable overrides
- Provider and model settings

## Log Levels

- **DEBUG**: Detailed diagnostic information (configuration values, internal states)
- **INFO**: General informational messages (requests, agent queries, workflow steps)
- **WARNING**: Warning messages (missing config files, API fallbacks)
- **ERROR**: Error messages (failed requests, LLM errors, exceptions)

## Best Practices

### Development

```bash
# Use DEBUG level to see all internal operations
LOG_LEVEL=DEBUG uvicorn main:app --reload
```

### Production

```bash
# Use INFO level with JSON format for log aggregation
LOG_LEVEL=INFO LOG_JSON=true LOG_FILE=/var/log/smartrecover.log uvicorn main:app
```

### Troubleshooting

1. **Enable DEBUG logging** to see detailed execution flow
2. **Use trace IDs** to follow a specific request through the system
3. **Filter by logger name** to focus on specific components:
   - `backend.agents.*` - Agent execution
   - `backend.llm.*` - LLM operations
   - `backend.api.*` - API handling

## Integration with Log Aggregation Systems

The JSON format is designed to work with popular log aggregation tools:

### ELK Stack (Elasticsearch, Logstash, Kibana)

```bash
LOG_JSON=true LOG_LEVEL=INFO uvicorn main:app | logstash -f logstash.conf
```

### Splunk

```bash
LOG_JSON=true LOG_FILE=/var/log/smartrecover.log uvicorn main:app
# Configure Splunk to monitor /var/log/smartrecover.log
```

### CloudWatch / Datadog

```bash
# Use JSON format for structured log ingestion
LOG_JSON=true uvicorn main:app
```

## Programmatic Usage

If you're extending SmartRecover, use the logging system in your code:

```python
import logging
from backend.logging_config import get_logger

# Simple logger
logger = logging.getLogger(__name__)
logger.info("Simple message")

# Logger with trace ID support
trace_logger = get_logger(__name__, trace_id="trace-123")
trace_logger.info(
    "Message with extra fields",
    extra={
        "extra_fields": {
            "key": "value",
            "count": 42
        }
    }
)
```

## Disabling Noisy Logs

By default, some third-party library logs are suppressed to reduce noise:

- `httpx` - HTTP client (WARNING level)
- `httpcore` - HTTP core (WARNING level)
- `uvicorn.access` - Access logs (WARNING level)

You can adjust these in `backend/logging_config.py` if needed.
