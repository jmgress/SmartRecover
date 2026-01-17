# Incident Management Resolver

An agentic incident management system using LangChain and LangGraph.

## Architecture

- **Orchestrator Agent**: Coordinates sub-agents and synthesizes responses
- **ServiceNow Agent**: Queries historical incidents and tickets
- **Confluence Agent**: Retrieves knowledge base articles and runbooks
- **Change Correlation Agent**: Correlates incidents with recent deployments

## Setup

```bash
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
- Install dependencies if needed
- Start the backend server on http://localhost:8000

### Manual Start

Alternatively, you can start the backend manually:

```bash
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
