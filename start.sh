#!/bin/bash

# SmartRecover Start Script
# This script starts the backend server for the SmartRecover application
# 
# Note: This is a Unix/Linux/macOS script. Windows users should use WSL or
# activate the virtual environment manually before running the server.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "====================================="
echo "  SmartRecover - Starting Backend"
echo "====================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    echo "Please install Python 3 and try again."
    exit 1
fi

echo -e "${GREEN}✓${NC} Python 3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}Error: pip3 is not installed.${NC}"
    echo "Please install pip3 and try again."
    exit 1
fi

echo -e "${GREEN}✓${NC} pip3 found"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed.${NC}"
    echo "Please install Node.js and try again."
    exit 1
fi

echo -e "${GREEN}✓${NC} Node.js found: $(node --version)"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm is not installed.${NC}"
    echo "Please install npm and try again."
    exit 1
fi

echo -e "${GREEN}✓${NC} npm found: $(npm --version)"

# =============================================================================
# Configuration File Validation
# =============================================================================

# Helper function to check if a value is a placeholder
is_placeholder() {
    local value="$1"
    # Check for common placeholder patterns
    if [[ -z "$value" ]] || \
       [[ "$value" =~ ^your-.*-here$ ]] || \
       [[ "$value" =~ ^your-.*-key$ ]] || \
       [[ "$value" == "xxx" ]] || \
       [[ "$value" == "XXX" ]] || \
       [[ "$value" == "your_"* ]] || \
       [[ "$value" =~ ^[xX]+$ ]]; then
        return 0  # Is a placeholder
    fi
    return 1  # Not a placeholder
}

# Helper function to read env variable from file
read_env_var() {
    local file="$1"
    local var_name="$2"
    if [ -f "$file" ]; then
        # Read variable, handling quotes and comments
        local value=$(grep -E "^${var_name}=" "$file" | head -n1 | cut -d= -f2- | sed -e 's/^["'"'"']//' -e 's/["'"'"']$//' -e 's/#.*//' | xargs)
        echo "$value"
    fi
}

# Check for .env files existence
check_env_files() {
    echo ""
    echo "Checking configuration files..."
    
    # Check backend/.env
    if [ ! -f "backend/.env" ]; then
        echo -e "${YELLOW}⚠${NC} Warning: backend/.env not found"
        echo "  → Copy from template: cp backend/.env.example backend/.env"
        echo "  → Then configure your LLM provider and API keys"
    else
        echo -e "${GREEN}✓${NC} backend/.env found"
    fi
    
    # Check frontend/.env
    if [ ! -f "frontend/.env" ]; then
        echo -e "${YELLOW}⚠${NC} Warning: frontend/.env not found"
        echo "  → Copy from template: cp frontend/.env.example frontend/.env"
    else
        echo -e "${GREEN}✓${NC} frontend/.env found"
    fi
    
    # Check root .env (optional)
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}⚠${NC} Note: Root .env not found (optional for incident connectors)"
        echo "  → Copy from template if needed: cp .env.example .env"
    else
        echo -e "${GREEN}✓${NC} .env found"
    fi
    
    # If critical files are missing, exit
    if [ ! -f "backend/.env" ] || [ ! -f "frontend/.env" ]; then
        echo ""
        echo -e "${RED}✗${NC} Error: Required .env files are missing"
        echo "Please create the missing configuration files and try again."
        exit 1
    fi
}

# Validate backend/.env configuration
validate_backend_env() {
    echo ""
    echo "Validating backend configuration..."
    
    local has_error=false
    local has_warning=false
    
    # Read LLM_PROVIDER
    local llm_provider=$(read_env_var "backend/.env" "LLM_PROVIDER")
    
    if [ -z "$llm_provider" ]; then
        echo -e "${RED}✗${NC} Error: LLM_PROVIDER not set in backend/.env"
        echo "  → Set LLM_PROVIDER to one of: openai, gemini, ollama"
        has_error=true
    elif [[ ! "$llm_provider" =~ ^(openai|gemini|ollama)$ ]]; then
        echo -e "${RED}✗${NC} Error: LLM_PROVIDER='$llm_provider' is not valid"
        echo "  → Valid values are: openai, gemini, ollama"
        has_error=true
    else
        echo -e "${GREEN}✓${NC} LLM_PROVIDER set to '$llm_provider'"
        
        # Validate provider-specific configuration
        case "$llm_provider" in
            openai)
                local openai_key=$(read_env_var "backend/.env" "OPENAI_API_KEY")
                if [ -z "$openai_key" ]; then
                    echo -e "${RED}✗${NC} Error: OPENAI_API_KEY not set"
                    echo "  → Set a valid OpenAI API key in backend/.env"
                    echo "  → Or switch to 'ollama' for local LLM: LLM_PROVIDER=ollama"
                    has_error=true
                elif is_placeholder "$openai_key"; then
                    echo -e "${YELLOW}⚠${NC} Warning: OPENAI_API_KEY appears to be a placeholder"
                    echo "  → Replace with your actual OpenAI API key from https://platform.openai.com/"
                    echo "  → Or switch to 'ollama' for local LLM: LLM_PROVIDER=ollama"
                    has_warning=true
                else
                    echo -e "${GREEN}✓${NC} OPENAI_API_KEY configured"
                fi
                ;;
            gemini)
                local google_key=$(read_env_var "backend/.env" "GOOGLE_API_KEY")
                if [ -z "$google_key" ]; then
                    echo -e "${RED}✗${NC} Error: GOOGLE_API_KEY not set"
                    echo "  → Set a valid Google API key in backend/.env"
                    echo "  → Or switch to 'ollama' for local LLM: LLM_PROVIDER=ollama"
                    has_error=true
                elif is_placeholder "$google_key"; then
                    echo -e "${YELLOW}⚠${NC} Warning: GOOGLE_API_KEY appears to be a placeholder"
                    echo "  → Replace with your actual Google API key from https://makersuite.google.com/"
                    echo "  → Or switch to 'ollama' for local LLM: LLM_PROVIDER=ollama"
                    has_warning=true
                else
                    echo -e "${GREEN}✓${NC} GOOGLE_API_KEY configured"
                fi
                ;;
            ollama)
                local ollama_url=$(read_env_var "backend/.env" "OLLAMA_BASE_URL")
                if [ -z "$ollama_url" ]; then
                    ollama_url="http://localhost:11434"
                    echo -e "${GREEN}✓${NC} OLLAMA_BASE_URL using default: $ollama_url"
                else
                    echo -e "${GREEN}✓${NC} OLLAMA_BASE_URL set to: $ollama_url"
                fi
                
                # Check if Ollama server is reachable (quick check)
                if command -v curl &> /dev/null; then
                    if curl -s -f -m 1 "$ollama_url/api/tags" > /dev/null 2>&1; then
                        echo -e "${GREEN}✓${NC} Ollama server is reachable"
                    else
                        echo -e "${YELLOW}⚠${NC} Warning: Cannot reach Ollama server at $ollama_url"
                        echo "  → Make sure Ollama is installed and running: ollama serve"
                        echo "  → Visit https://ollama.ai/ for installation instructions"
                        has_warning=true
                    fi
                fi
                ;;
        esac
    fi
    
    if [ "$has_error" = true ]; then
        echo ""
        echo -e "${RED}✗${NC} Backend configuration has errors. Please fix them and try again."
        exit 1
    fi
}

# Validate frontend/.env configuration
validate_frontend_env() {
    echo ""
    echo "Validating frontend configuration..."
    
    local api_url=$(read_env_var "frontend/.env" "REACT_APP_API_BASE_URL")
    
    if [ -z "$api_url" ]; then
        echo -e "${YELLOW}⚠${NC} Warning: REACT_APP_API_BASE_URL not set in frontend/.env"
        echo "  → Using default: http://localhost:8000/api/v1"
    else
        echo -e "${GREEN}✓${NC} REACT_APP_API_BASE_URL set to: $api_url"
        
        # Validate URL format (basic check)
        if [[ ! "$api_url" =~ ^https?:// ]]; then
            echo -e "${YELLOW}⚠${NC} Warning: REACT_APP_API_BASE_URL may not be a valid URL"
            echo "  → Expected format: http://localhost:8000/api/v1"
        fi
    fi
}

# Validate root .env connector configuration
validate_root_env() {
    # Root .env is optional, only validate if it exists
    if [ ! -f ".env" ]; then
        return 0
    fi
    
    echo ""
    echo "Validating incident connector configuration..."
    
    local connector_type=$(read_env_var ".env" "INCIDENT_CONNECTOR_TYPE")
    
    if [ -z "$connector_type" ]; then
        connector_type="mock"
    fi
    
    echo -e "${GREEN}✓${NC} INCIDENT_CONNECTOR_TYPE set to: $connector_type"
    
    case "$connector_type" in
        servicenow)
            local instance_url=$(read_env_var ".env" "SERVICENOW_INSTANCE_URL")
            local username=$(read_env_var ".env" "SERVICENOW_USERNAME")
            local password=$(read_env_var ".env" "SERVICENOW_PASSWORD")
            local client_id=$(read_env_var ".env" "SERVICENOW_CLIENT_ID")
            local client_secret=$(read_env_var ".env" "SERVICENOW_CLIENT_SECRET")
            
            if [ -z "$instance_url" ]; then
                echo -e "${YELLOW}⚠${NC} Warning: SERVICENOW_INSTANCE_URL not set"
            fi
            
            # Check if using basic auth or OAuth
            if [ -n "$client_id" ] && [ -n "$client_secret" ]; then
                echo -e "${GREEN}✓${NC} ServiceNow OAuth credentials configured"
            elif [ -n "$username" ] && [ -n "$password" ]; then
                echo -e "${GREEN}✓${NC} ServiceNow basic auth credentials configured"
            else
                echo -e "${YELLOW}⚠${NC} Warning: ServiceNow credentials not fully configured"
                echo "  → Set either username/password or client_id/client_secret in .env"
            fi
            ;;
        jira)
            local jira_url=$(read_env_var ".env" "JIRA_URL")
            local jira_username=$(read_env_var ".env" "JIRA_USERNAME")
            local jira_token=$(read_env_var ".env" "JIRA_API_TOKEN")
            
            if [ -z "$jira_url" ]; then
                echo -e "${YELLOW}⚠${NC} Warning: JIRA_URL not set"
            fi
            if [ -z "$jira_username" ]; then
                echo -e "${YELLOW}⚠${NC} Warning: JIRA_USERNAME not set"
            fi
            if [ -z "$jira_token" ]; then
                echo -e "${YELLOW}⚠${NC} Warning: JIRA_API_TOKEN not set"
            fi
            
            if [ -n "$jira_url" ] && [ -n "$jira_username" ] && [ -n "$jira_token" ]; then
                echo -e "${GREEN}✓${NC} Jira credentials configured"
            else
                echo -e "${YELLOW}⚠${NC} Warning: Jira credentials not fully configured in .env"
            fi
            ;;
        mock)
            echo -e "${GREEN}✓${NC} Using mock connector (no credentials required)"
            ;;
        *)
            echo -e "${YELLOW}⚠${NC} Warning: Unknown connector type '$connector_type', using mock"
            ;;
    esac
}

# Validate backend/config.yaml
validate_config_yaml() {
    echo ""
    echo "Validating backend/config.yaml..."
    
    if [ ! -f "backend/config.yaml" ]; then
        echo -e "${RED}✗${NC} Error: backend/config.yaml not found"
        echo "  → This file is required for LLM configuration"
        exit 1
    fi
    
    echo -e "${GREEN}✓${NC} backend/config.yaml found"
    
    # Basic YAML syntax check and validation (done in single Python call for efficiency)
    if command -v python3 &> /dev/null; then
        local validation_result=$(python3 << 'PYEOF' 2>&1
import yaml
import sys

try:
    with open('backend/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Check for required sections
    has_llm = 'llm' in config
    has_logging = 'logging' in config
    llm_provider = config.get('llm', {}).get('provider', '') if has_llm else ''
    
    # Print results in format: has_llm|has_logging|provider
    print(f"{has_llm}|{has_logging}|{llm_provider}")
    sys.exit(0)
except yaml.YAMLError as e:
    print(f"YAML_ERROR:{e}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR:{e}")
    sys.exit(2)
PYEOF
)
        local exit_code=$?
        
        if [ $exit_code -eq 1 ]; then
            echo -e "${RED}✗${NC} Error: backend/config.yaml has invalid YAML syntax"
            echo "  → Check for proper indentation and syntax"
            echo "  → ${validation_result#YAML_ERROR:}"
            exit 1
        elif [ $exit_code -eq 2 ]; then
            echo -e "${RED}✗${NC} Error: Failed to validate config.yaml"
            echo "  → ${validation_result#ERROR:}"
            exit 1
        fi
        
        echo -e "${GREEN}✓${NC} YAML syntax is valid"
        
        # Parse validation results
        IFS='|' read -r has_llm has_logging yaml_provider <<< "$validation_result"
        
        if [ "$has_llm" != "True" ]; then
            echo -e "${RED}✗${NC} Error: 'llm' section missing in config.yaml"
            exit 1
        fi
        echo -e "${GREEN}✓${NC} 'llm' section found"
        
        if [ "$has_logging" != "True" ]; then
            echo -e "${YELLOW}⚠${NC} Warning: 'logging' section missing in config.yaml"
        else
            echo -e "${GREEN}✓${NC} 'logging' section found"
        fi
        
        # Validate llm.provider
        if [ -n "$yaml_provider" ]; then
            if [[ ! "$yaml_provider" =~ ^(openai|gemini|ollama)$ ]]; then
                echo -e "${YELLOW}⚠${NC} Warning: llm.provider='$yaml_provider' in config.yaml is not a standard value"
                echo "  → Valid values are: openai, gemini, ollama"
            else
                echo -e "${GREEN}✓${NC} llm.provider set to '$yaml_provider'"
            fi
        fi
    else
        echo -e "${YELLOW}⚠${NC} Note: Python not available for YAML validation"
    fi
}

# Run all validation checks
check_env_files
validate_backend_env
validate_frontend_env
validate_root_env
validate_config_yaml

echo ""
echo -e "${GREEN}✓${NC} Configuration validation complete"

# Check if a virtual environment is active
echo ""
echo "Checking virtual environment..."
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}No virtual environment is currently active.${NC}"
    
    # Check for existing virtual environment directories
    VENV_DIR=""
    if [ -d "venv" ]; then
        VENV_DIR="venv"
        echo "Found existing virtual environment at: venv/"
    elif [ -d ".venv" ]; then
        VENV_DIR=".venv"
        echo "Found existing virtual environment at: .venv/"
    fi
    
    if [ -n "$VENV_DIR" ]; then
        # Activate existing virtual environment
        echo "Activating virtual environment..."
        if [ ! -f "$VENV_DIR/bin/activate" ]; then
            echo -e "${RED}Error: Virtual environment activation script not found.${NC}"
            echo "The virtual environment at $VENV_DIR may be corrupted."
            echo "Please delete it and run this script again to recreate it."
            exit 1
        fi
        source "$VENV_DIR/bin/activate"
        if [ -z "$VIRTUAL_ENV" ]; then
            echo -e "${RED}Error: Failed to activate virtual environment.${NC}"
            exit 1
        fi
        echo -e "${GREEN}✓${NC} Virtual environment activated: $VIRTUAL_ENV"
    else
        # No virtual environment exists, create one
        echo "No virtual environment found. Creating a new one at: venv/"
        python3 -m venv venv
        if [ $? -ne 0 ]; then
            echo -e "${RED}Error: Failed to create virtual environment.${NC}"
            echo "Please ensure python3-venv is installed:"
            echo "  • Ubuntu/Debian: sudo apt install python3-venv"
            echo "  • macOS: It should be included with Python 3"
            exit 1
        fi
        
        # Activate the newly created virtual environment
        if [ ! -f "venv/bin/activate" ]; then
            echo -e "${RED}Error: Virtual environment creation incomplete.${NC}"
            echo "The activation script was not created properly."
            exit 1
        fi
        source venv/bin/activate
        if [ -z "$VIRTUAL_ENV" ]; then
            echo -e "${RED}Error: Failed to activate newly created virtual environment.${NC}"
            exit 1
        fi
        echo -e "${GREEN}✓${NC} Virtual environment created and activated: $VIRTUAL_ENV"
    fi
else
    echo -e "${GREEN}✓${NC} Virtual environment already active: $VIRTUAL_ENV"
fi

# Check if requirements file exists
if [ ! -f "backend/requirements.txt" ]; then
    echo -e "${RED}Error: backend/requirements.txt not found.${NC}"
    echo "Please ensure you are running this script from the repository root."
    exit 1
fi

# Check if requirements are installed
echo ""
echo "Checking dependencies..."
if ! python -c "import fastapi, uvicorn, langchain" 2>/dev/null; then
    echo -e "${YELLOW}Dependencies not installed or incomplete.${NC}"
    echo "Installing dependencies from backend/requirements.txt..."
    pip install -r backend/requirements.txt
    echo -e "${GREEN}✓${NC} Dependencies installed successfully"
else
    echo -e "${GREEN}✓${NC} Dependencies already installed"
fi

# Check and install frontend dependencies
echo ""
echo "Checking frontend dependencies..."
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}Frontend dependencies not installed.${NC}"
    echo "Installing frontend dependencies..."
    cd frontend && npm install && cd ..
    echo -e "${GREEN}✓${NC} Frontend dependencies installed successfully"
else
    echo -e "${GREEN}✓${NC} Frontend dependencies already installed"
fi

# Start the server
echo ""
echo "====================================="
echo "  Starting SmartRecover"
echo "====================================="
echo ""
echo "Services will be available at:"
echo "  • Frontend: http://localhost:3000"
echo "  • Backend API: http://localhost:8000"
echo "  • API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Start frontend server in background
echo "Starting frontend server..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
(cd "$SCRIPT_DIR/frontend" && npm start) &
FRONTEND_PID=$!
echo -e "${GREEN}✓${NC} Frontend server starting (PID: $FRONTEND_PID)"

# Trap to cleanup background processes on exit
cleanup() {
    echo ""
    echo "Shutting down servers..."
    # Kill frontend server
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    # Kill backend server (uvicorn process)
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    # Also cleanup any remaining uvicorn processes for this port
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

# Start uvicorn server from repository root
# This ensures proper Python module resolution for backend.* imports
echo "Starting backend server..."
cd "$SCRIPT_DIR"
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for background processes
wait
