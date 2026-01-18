# Incident Management Resolver

An agentic incident management system using LangChain and LangGraph with configurable LLM providers.

## Architecture

- **Orchestrator Agent**: Coordinates sub-agents and synthesizes responses using LLM
- **Incident Management Agent**: Queries incident management systems (ServiceNow, Jira Service Management, or mock data)
- **Confluence Agent**: Retrieves knowledge base articles and runbooks
- **Change Correlation Agent**: Correlates incidents with recent deployments

### Incident Management Connectors

The Incident Management Agent supports multiple backends:

1. **ServiceNow**: Connect to ServiceNow instance for real incident data
2. **Jira Service Management**: Connect to Jira for incident and change management
3. **Mock**: Use spreadsheet-like mock data for testing

## Configuration

### Incident Management Connector Configuration

The incident management connector can be configured using environment variables:

#### Connector Type

Set the `INCIDENT_CONNECTOR_TYPE` environment variable to choose the connector:
- `mock` (default) - Use mock data for testing
- `servicenow` - Connect to ServiceNow
- `jira` - Connect to Jira Service Management

#### ServiceNow Configuration

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

#### Jira Service Management Configuration

When using Jira (`INCIDENT_CONNECTOR_TYPE=jira`), set:
- `JIRA_URL` - Your Jira instance URL (e.g., https://your-domain.atlassian.net)
- `JIRA_USERNAME` - Jira username/email
- `JIRA_API_TOKEN` - Jira API token (generate from https://id.atlassian.com/manage-profile/security/api-tokens)
- `JIRA_PROJECT_KEY` - Jira project key

#### Mock Data Configuration

When using mock data (`INCIDENT_CONNECTOR_TYPE=mock`), optionally set:
- `MOCK_DATA_SOURCE` - Data source identifier (default: "mock")

### LLM Configuration

The system supports three LLM providers: **OpenAI**, **Google Gemini**, and **Ollama**. You can configure the provider through either a configuration file or environment variables.

#### Configuration Options

**Option 1: Configuration File (Recommended)**

Edit `backend/config.yaml` to set your preferred LLM provider and settings:

```yaml
llm:
  provider: "openai"  # Options: "openai", "gemini", "ollama"
  
  openai:
    model: "gpt-3.5-turbo"
    temperature: 0.7
  
  gemini:
    model: "gemini-pro"
    temperature: 0.7
  
  ollama:
    model: "llama2"
    base_url: "http://localhost:11434"
    temperature: 0.7
```

**Option 2: Environment Variables**

Create a `.env` file in the `backend/` directory (see `.env.example` for a template):

```bash
# Incident Management Connector Configuration
INCIDENT_CONNECTOR_TYPE=mock  # Options: mock, servicenow, jira

# LLM Provider Selection
LLM_PROVIDER=openai  # Options: openai, gemini, ollama

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo

# Google Gemini Configuration
GOOGLE_API_KEY=your-google-api-key-here
GEMINI_MODEL=gemini-pro

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Optional: Custom config file path
# CONFIG_PATH=/path/to/custom/config.yaml
```

**Note:** Environment variables take precedence over the configuration file.

#### LLM Provider Details

**OpenAI**
- Requires an API key from [OpenAI Platform](https://platform.openai.com/)
- Supported models: `gpt-3.5-turbo`, `gpt-4`, `gpt-4-turbo-preview`, etc.
- Set `OPENAI_API_KEY` environment variable

**Google Gemini**
- Requires an API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- Supported models: `gemini-pro`, `gemini-pro-vision`
- Set `GOOGLE_API_KEY` environment variable

**Ollama (Local LLMs)**
- Runs locally, no API key required
- Requires [Ollama](https://ollama.ai/) to be installed and running
- Supported models: `llama2`, `mistral`, `codellama`, etc.
- Default endpoint: `http://localhost:11434`

### Logging Configuration

SmartRecover includes a comprehensive logging system with configurable verbosity and tracing capabilities.

#### Logging Options

Edit `backend/config.yaml` to configure logging:

```yaml
logging:
  level: "INFO"  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  enable_tracing: false  # Enable detailed function tracing
  # log_file: "logs/smartrecover.log"  # Optional: log to file
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
