# SmartRecover - Incident Management Resolver

An agentic incident management system using LangChain and LangGraph with configurable LLM providers.

## Architecture

- **Orchestrator Agent**: Coordinates sub-agents and synthesizes responses using LLM
- **Incident Management Agent**: Queries incident management systems (ServiceNow, Jira Service Management, or mock data)
- **Knowledge Base Agent**: Retrieves knowledge base articles and runbooks from Confluence or local files (replaces Confluence Agent)
- **Change Correlation Agent**: Correlates incidents with recent deployments

### Tech Stack

- **Backend**: Python with FastAPI, LangChain, LangGraph
- **Frontend**: React with TypeScript
- **LLM Providers**: OpenAI, Google Gemini, or Ollama (local)

## LLM Configuration

The system supports three LLM providers: **OpenAI**, **Google Gemini**, and **Ollama**. You can configure the provider through either a configuration file or environment variables.

### Configuration Options

#### Option 1: Configuration File (Recommended)

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

#### Option 2: Environment Variables

Create a `.env` file in the `backend/` directory (see `.env.example` for a template):

```bash
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

### LLM Provider Details

#### OpenAI
- Requires an API key from [OpenAI Platform](https://platform.openai.com/)
- Supported models: `gpt-3.5-turbo`, `gpt-4`, `gpt-4-turbo-preview`, etc.
- Set `OPENAI_API_KEY` environment variable

#### Google Gemini
- Requires an API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- Supported models: `gemini-pro`, `gemini-pro-vision`
- Set `GOOGLE_API_KEY` environment variable

#### Ollama (Local LLMs)
- Runs locally, no API key required
- Requires [Ollama](https://ollama.ai/) to be installed and running
- Supported models: `llama2`, `mistral`, `codellama`, etc.
- Default endpoint: `http://localhost:11434`

## Logging Configuration

SmartRecover includes a comprehensive logging system with configurable verbosity and tracing capabilities.

### Configuration Options

#### Option 1: Configuration File (Recommended)

Edit `backend/config.yaml` to configure logging:

```yaml
logging:
  level: "INFO"  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  enable_tracing: false  # Enable detailed function tracing
  # log_file: "logs/smartrecover.log"  # Optional: log to file
```

#### Option 2: Environment Variables

Set logging options via environment variables in your `.env` file:

```bash
# Logging Configuration
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
ENABLE_TRACING=false  # Set to true for detailed function tracing
# LOG_FILE=logs/smartrecover.log  # Uncomment to enable file logging
```

**Note:** Environment variables take precedence over the configuration file.

### Logging Levels

- **DEBUG**: Detailed information for diagnosing problems (includes all tracing output)
- **INFO**: General informational messages about application operation
- **WARNING**: Warning messages for potentially harmful situations
- **ERROR**: Error messages for serious problems
- **CRITICAL**: Critical messages for very serious errors

### Tracing

When `enable_tracing` is set to `true`, the system logs:
- Function entry and exit
- Function arguments and execution time
- Exception details with stack traces

**Note:** Enable tracing with `LOG_LEVEL=DEBUG` for the most detailed output. Use tracing during development or troubleshooting, but disable it in production for better performance.

### Example Configuration

For verbose debugging during development:
```yaml
logging:
  level: "DEBUG"
  enable_tracing: true
  log_file: "logs/smartrecover.log"
```

For production use:
```yaml
logging:
  level: "INFO"
  enable_tracing: false
```

## Knowledge Base Configuration

The system supports multiple knowledge base sources for retrieving documentation and runbooks.

### Configuration Options

Configure in `backend/config.yaml`:

```yaml
knowledge_base:
  source: "mock"  # Options: "mock", "confluence"
  
  # Mock Configuration (for development/testing)
  mock:
    csv_path: "backend/data/csv/confluence_docs.csv"
    docs_folder: "backend/data/runbooks/"  # Optional: load markdown files
  
  # Confluence Configuration (for production)
  confluence:
    base_url: "https://your-domain.atlassian.net/wiki"
    username: "your-email@example.com"
    api_token: "your-api-token"
    space_keys: ["DOCS", "KB"]  # Optional: limit to specific spaces
```

Or via environment variables:

```bash
# Knowledge Base Source
KNOWLEDGE_BASE_SOURCE=mock  # or "confluence"

# Mock Configuration
KB_CSV_PATH=backend/data/csv/confluence_docs.csv
KB_DOCS_FOLDER=backend/data/runbooks/

# Confluence Configuration
CONFLUENCE_BASE_URL=https://your-domain.atlassian.net/wiki
CONFLUENCE_USERNAME=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token
CONFLUENCE_SPACE_KEYS=DOCS,KB
```

### Knowledge Base Sources

#### Mock (Default)
- **Use Case**: Development, testing, and demo purposes
- **Data Sources**: 
  - CSV file with incident-specific documentation
  - Markdown/text files in configured folder
- **Setup**: No additional configuration needed
- **Features**:
  - Fast, no external dependencies
  - Supports markdown files with YAML frontmatter
  - Keyword-based search

#### Confluence
- **Use Case**: Production environments with Confluence
- **Requirements**: Confluence Cloud or Server instance
- **Authentication**: API token (recommended) or password
- **Setup**: Configure base URL, credentials, and space keys
- **Features** (when implemented):
  - Search across Confluence spaces
  - Retrieve full page content
  - Support for attachments and comments

### Adding Custom Runbooks

To add your own runbooks for mock mode:

1. Create markdown files in `backend/data/runbooks/`
2. Optionally add YAML frontmatter:
   ```markdown
   ---
   title: My Runbook Title
   ---
   
   # Runbook Content
   Your troubleshooting steps here...
   ```
3. Configure `docs_folder` in config.yaml or set `KB_DOCS_FOLDER` environment variable
4. The Knowledge Base Agent will automatically load and index your files

## Setup

The easiest way to get started is to use the provided start script (see Quick Start below), which handles virtual environment setup automatically.

### Backend Setup

```bash
# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Configure LLM (choose one method):
# Method 1: Edit the config file
# Edit backend/config.yaml as needed

# Method 2: Copy and edit the .env file
cp .env.example .env  # Add your API keys
```

### Frontend Setup

```bash
cd frontend
npm install
```

## Running

### Quick Start

Use the provided start script to launch the backend:

```bash
./start.sh
```

The script will:
- Check for Python 3 and pip
- Ensure a virtual environment is active (creates one if needed)
- Install dependencies if needed
- Start the backend server on http://localhost:8000

### Manual Start

#### Backend

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Start the backend
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend
npm start
```

The frontend will start on http://localhost:3000 and proxy API requests to the backend.

## Testing

SmartRecover includes comprehensive test coverage for both backend and frontend components.

### Quick Testing

Run all tests with a single command:

```bash
./test.sh
```

### Test Options

The test script supports the following flags:

```bash
# Run all tests (backend + frontend)
./test.sh

# Run only backend tests (Python/pytest)
./test.sh --backend

# Run only frontend tests (React/Jest)
./test.sh --frontend

# Show help
./test.sh --help
```

### Backend Tests

Backend tests use pytest and are located in `backend/tests/`:
- Configuration management tests
- LLM provider configuration tests
- Logging system tests

To run backend tests manually:

```bash
cd backend
pytest tests/ -v
```

### Frontend Tests

Frontend tests use Jest and React Testing Library:
- Component tests (Message, SeverityBadge, etc.)
- Hook tests (useIncidents, useResolveIncident)
- Service tests (API layer)

To run frontend tests manually:

```bash
cd frontend
npm test
```

### Coverage Reports

The frontend test runner automatically generates coverage reports. Coverage summary is displayed after test execution.

## Mock Data

SmartRecover uses CSV files to store mock data for testing and development. This provides several benefits:
- **Easy editing**: Modify test scenarios using spreadsheet applications or text editors
- **Non-technical accessibility**: Team members can contribute without Python knowledge
- **Version control friendly**: CSV changes are easy to review
- **Flexibility**: Quick dataset swapping for different testing scenarios

Mock data files are located in `backend/data/csv/`:
- `incidents.csv` - Mock incident records
- `servicenow_tickets.csv` - ServiceNow tickets and related records
- `confluence_docs.csv` - Confluence documentation and runbooks
- `change_correlations.csv` - Change records correlated with incidents

See [backend/data/csv/README.md](backend/data/csv/README.md) for detailed CSV format documentation.

## API Endpoints

- `GET /api/v1/incidents` - List all incidents
- `GET /api/v1/incidents/{id}` - Get specific incident
- `POST /api/v1/resolve` - Resolve an incident with the agentic system
- `GET /api/v1/health` - Health check

## Project Structure

```
SmartRecover/
├── backend/
│   ├── agents/           # LangGraph agents (orchestrator, incident, confluence, change)
│   ├── api/              # FastAPI routes
│   ├── connectors/       # Incident management system connectors
│   ├── data/             # Mock data for development (CSV files)
│   │   └── csv/          # CSV data files (incidents, tickets, docs, changes)
│   ├── llm/              # LLM configuration and manager
│   ├── models/           # Pydantic models
│   ├── tests/            # Backend pytest tests
│   ├── utils/            # Logging utilities
│   ├── config.yaml       # Main configuration file
│   └── main.py           # FastAPI application entry point
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── hooks/        # Custom React hooks
│   │   ├── services/     # API service layer
│   │   └── types/        # TypeScript type definitions
│   └── package.json
├── start.sh              # Backend start script
├── test.sh               # Unified test script
└── README.md
```

## License

See [LICENSE](LICENSE) for details.
