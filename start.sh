#!/bin/bash

# SmartRecover Start Script
# This script starts the backend server for the SmartRecover application

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

# Check if requirements file exists
if [ ! -f "backend/requirements.txt" ]; then
    echo -e "${RED}Error: backend/requirements.txt not found.${NC}"
    echo "Please ensure you are running this script from the repository root."
    exit 1
fi

# Check if requirements are installed
echo ""
echo "Checking dependencies..."
if ! python3 -c "import fastapi, uvicorn, langchain" 2>/dev/null; then
    echo -e "${YELLOW}Dependencies not installed or incomplete.${NC}"
    echo "Installing dependencies from backend/requirements.txt..."
    pip3 install -r backend/requirements.txt
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
python3 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
