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

# Start the server
echo ""
echo "====================================="
echo "  Starting Backend Server"
echo "====================================="
echo ""
echo "Server will be available at:"
echo "  • http://localhost:8000"
echo "  • API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start uvicorn server from repository root
# This ensures proper Python module resolution for backend.* imports
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
