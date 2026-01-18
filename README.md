# Incident Management Resolver

An agentic incident management system using LangChain and LangGraph.

## Architecture

- **Orchestrator Agent**: Coordinates sub-agents and synthesizes responses
- **Incident Management Agent**: Queries incident management systems (ServiceNow, Jira Service Management, or mock data)
- **Confluence Agent**: Retrieves knowledge base articles and runbooks
- **Change Correlation Agent**: Correlates incidents with recent deployments

### Incident Management Connectors

The Incident Management Agent supports multiple backends:

1. **ServiceNow**: Connect to ServiceNow instance for real incident data
2. **Jira Service Management**: Connect to Jira for incident and change management
3. **Mock**: Use spreadsheet-like mock data for testing

## Configuration

The incident management connector can be configured using environment variables:

### Connector Type

Set the `INCIDENT_CONNECTOR_TYPE` environment variable to choose the connector:
- `mock` (default) - Use mock data for testing
- `servicenow` - Connect to ServiceNow
- `jira` - Connect to Jira Service Management

### ServiceNow Configuration

When using ServiceNow (`INCIDENT_CONNECTOR_TYPE=servicenow`), you must choose one authentication method:

**Option 1: Username/Password Authentication (Default)**
- `SERVICENOW_INSTANCE_URL` - Your ServiceNow instance URL
- `SERVICENOW_USERNAME` - ServiceNow username
- `SERVICENOW_PASSWORD` - ServiceNow password

**Option 2: OAuth Authentication (Advanced)**
- `SERVICENOW_INSTANCE_URL` - Your ServiceNow instance URL
- `SERVICENOW_CLIENT_ID` - OAuth client ID (use instead of username/password)
- `SERVICENOW_CLIENT_SECRET` - OAuth client secret (use instead of username/password)

Note: OAuth requires additional setup in your ServiceNow instance. For most users, username/password authentication is sufficient.

### Jira Service Management Configuration

When using Jira (`INCIDENT_CONNECTOR_TYPE=jira`), set:
- `JIRA_URL` - Your Jira instance URL (e.g., https://your-domain.atlassian.net)
- `JIRA_USERNAME` - Jira username/email
- `JIRA_API_TOKEN` - Jira API token (generate from https://id.atlassian.com/manage-profile/security/api-tokens)
- `JIRA_PROJECT_KEY` - Jira project key

### Mock Data Configuration

When using mock data (`INCIDENT_CONNECTOR_TYPE=mock`), optionally set:
- `MOCK_DATA_SOURCE` - Data source identifier (default: "mock")

### Example .env file

Copy `.env.example` to `.env` and configure your connector:

```bash
cp .env.example .env
# Edit .env with your configuration
```

Example configurations:

```bash
# Use mock data for testing
INCIDENT_CONNECTOR_TYPE=mock
MOCK_DATA_SOURCE=mock

# Or use ServiceNow
# INCIDENT_CONNECTOR_TYPE=servicenow
# SERVICENOW_INSTANCE_URL=https://your-instance.service-now.com
# SERVICENOW_USERNAME=your-username
# SERVICENOW_PASSWORD=your-password

# Or use Jira
# INCIDENT_CONNECTOR_TYPE=jira
# JIRA_URL=https://your-domain.atlassian.net
# JIRA_USERNAME=your-email@example.com
# JIRA_API_TOKEN=your-api-token
# JIRA_PROJECT_KEY=PROJ
```

## Setup

The easiest way to get started is to use the provided start script (see Quick Start below), which handles virtual environment setup automatically.

For manual setup:

```bash
# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt
```

## Running

### Quick Start

Use the provided start script to launch the application:

```bash
./start.sh
```

The script will:
- Check for Python 3 and pip
- Ensure a virtual environment is active (creates one if needed)
- Install dependencies if needed
- Start the backend server on http://localhost:8000

### Manual Start

Alternatively, you can start the backend manually:

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Start the backend
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Open frontend
open frontend/index.html
```

## API Endpoints

- `GET /api/v1/incidents` - List all incidents
- `GET /api/v1/incidents/{id}` - Get specific incident
- `POST /api/v1/resolve` - Resolve an incident with the agentic system
- `GET /api/v1/health` - Health check
