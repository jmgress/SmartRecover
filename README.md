# SmartRecover - Incident Management Resolver

An agentic incident management system using LangChain and LangGraph with configurable LLM providers.

## Architecture

- **Orchestrator Agent**: Coordinates sub-agents and synthesizes responses using LLM
- **Incident Management Agent**: Queries incident management systems (ServiceNow, Jira Service Management, or mock data)
- **Confluence Agent**: Retrieves knowledge base articles and runbooks
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
│   ├── data/             # Mock data for development
│   ├── llm/              # LLM configuration and manager
│   ├── models/           # Pydantic models
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
└── README.md
```

## License

See [LICENSE](LICENSE) for details.
