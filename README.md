# Incident Management Resolver

An agentic incident management system using LangChain and LangGraph with configurable LLM providers.

## Architecture

- **Orchestrator Agent**: Coordinates sub-agents and synthesizes responses using LLM
- **ServiceNow Agent**: Queries historical incidents and tickets
- **Confluence Agent**: Retrieves knowledge base articles and runbooks
- **Change Correlation Agent**: Correlates incidents with recent deployments

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

## Logging and Tracing

SmartRecover includes comprehensive logging and tracing capabilities to help with debugging and monitoring.

### Configuration Options

Logging can be configured through:

#### Option 1: Configuration File

Edit `backend/config.yaml`:

```yaml
logging:
  level: "INFO"  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
  verbose: false  # Enable verbose logging (overrides level to DEBUG)
  log_file: null  # Path to log file (null to disable file logging)
  log_to_console: true  # Enable console logging
  max_bytes: 10485760  # Maximum log file size before rotation (10 MB)
  backup_count: 5  # Number of backup log files to keep
```

#### Option 2: Environment Variables

Add to your `.env` file:

```bash
# Logging Configuration
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_VERBOSE=false  # Enable verbose logging
LOG_FILE=/path/to/logfile.log  # Optional log file path
```

#### Option 3: Command-Line Arguments

```bash
# Enable verbose mode (DEBUG level)
python backend/main.py --verbose

# Set specific log level
python backend/main.py --log-level DEBUG

# Enable file logging
python backend/main.py --log-file /tmp/smartrecover.log

# Combine options
python backend/main.py --verbose --log-file /tmp/smartrecover.log
```

Or with uvicorn:

```bash
# Start with verbose logging
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000 -- --verbose

# Start with specific log level and file output
uvicorn main:app --reload -- --log-level DEBUG --log-file /tmp/smartrecover.log
```

### Logging Features

- **Multiple Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Verbose Mode**: Enables DEBUG level logging with detailed execution traces
- **Function Tracing**: Automatic tracing of function entry/exit with timing information
- **Performance Monitoring**: Execution time tracking for traced functions
- **Sensitive Data Redaction**: Automatic redaction of passwords, API keys, and secrets
- **File Logging**: Optional file output with automatic rotation
- **Console Logging**: Formatted output to stdout/stderr

### Log Output Examples

**INFO level** (default):
```
2026-01-17 10:30:00,123 - backend.api.routes - INFO - Resolving incident: INC001
2026-01-17 10:30:00,456 - backend.agents.orchestrator - INFO - Starting incident resolution
```

**DEBUG/Verbose level**:
```
2026-01-17 10:30:00,123 - backend.api.routes - DEBUG - → Entering backend.api.routes.resolve_incident
2026-01-17 10:30:00,124 - backend.api.routes - DEBUG -   Arguments: args=(), kwargs={'query': <IncidentQuery object>}
2026-01-17 10:30:00,456 - backend.agents.orchestrator - INFO - Synthesizing results for incident INC001
2026-01-17 10:30:00,789 - backend.api.routes - DEBUG - ← Exiting backend.api.routes.resolve_incident (took 0.666s)
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

# Configure LLM (choose one method):
# Method 1: Copy and edit the config file
cp config.yaml config.yaml  # Edit as needed

# Method 2: Copy and edit the .env file
cp .env.example .env  # Add your API keys
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
