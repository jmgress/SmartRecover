#!/bin/bash

# SmartRecover Test Script
# Runs tests for both backend (Python/pytest) and frontend (React/Jest)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results tracking
BACKEND_EXIT_CODE=0
FRONTEND_EXIT_CODE=0
E2E_EXIT_CODE=0
BACKEND_SKIPPED=false
FRONTEND_SKIPPED=false
E2E_SKIPPED=false

# Print colored output
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Show usage information
show_usage() {
    echo "Usage: ./test.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --backend     Run only backend tests (Python/pytest)"
    echo "  --frontend    Run only frontend tests (React/Jest)"
    echo "  --e2e         Run end-to-end tests (Python/Playwright)"
    echo "  --all         Run all tests (default)"
    echo "  --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./test.sh              # Run all tests"
    echo "  ./test.sh --backend    # Run only backend tests"
    echo "  ./test.sh --frontend   # Run only frontend tests"
    echo "  ./test.sh --e2e        # Run only end-to-end tests"
}

# Parse command line arguments
RUN_BACKEND=false
RUN_FRONTEND=false
RUN_E2E=false

if [ $# -eq 0 ]; then
    # No arguments, run all tests
    RUN_BACKEND=true
    RUN_FRONTEND=true
    RUN_E2E=true
else
    while [ $# -gt 0 ]; do
        case "$1" in
            --backend)
                RUN_BACKEND=true
                shift
                ;;
            --frontend)
                RUN_FRONTEND=true
                shift
                ;;
            --e2e)
                RUN_E2E=true
                shift
                ;;
            --all)
                RUN_BACKEND=true
                RUN_FRONTEND=true
                RUN_E2E=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
fi

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_header "SmartRecover Test Suite"

# Run backend tests
if [ "$RUN_BACKEND" = true ]; then
    print_header "Running Backend Tests (Python/pytest)"
    
    cd "$SCRIPT_DIR/backend"
    
    # Check if pytest is installed
    if ! command -v pytest &> /dev/null; then
        print_warning "pytest not found. Attempting to install dependencies..."
        
        # Check if we're in a virtual environment
        if [ -z "$VIRTUAL_ENV" ]; then
            print_warning "No virtual environment detected. Creating one..."
            if [ ! -d "$SCRIPT_DIR/venv" ]; then
                python3 -m venv "$SCRIPT_DIR/venv"
            fi
            source "$SCRIPT_DIR/venv/bin/activate"
        fi
        
        print_info "Installing backend dependencies..."
        pip install -q -r requirements.txt
    fi
    
    # Run pytest (only tests in the tests/ directory)
    echo ""
    set +e  # Disable exit on error to capture exit code
    pytest tests/ -v --tb=short
    BACKEND_EXIT_CODE=$?
    set -e  # Re-enable exit on error
    
    if [ $BACKEND_EXIT_CODE -eq 0 ]; then
        print_success "Backend tests passed!"
    else
        print_error "Backend tests failed (exit code: $BACKEND_EXIT_CODE)"
    fi
    
    cd "$SCRIPT_DIR"
    echo ""
else
    BACKEND_SKIPPED=true
    print_info "Backend tests skipped"
    echo ""
fi

# Run frontend tests
if [ "$RUN_FRONTEND" = true ]; then
    print_header "Running Frontend Tests (React/Jest)"
    
    cd "$SCRIPT_DIR/frontend"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        print_warning "node_modules not found. Installing dependencies..."
        npm install
    fi
    
    # Run tests with CI flag to prevent watch mode
    echo ""
    set +e  # Disable exit on error to capture exit code
    CI=true npm test -- --coverage --watchAll=false
    FRONTEND_EXIT_CODE=$?
    set -e  # Re-enable exit on error
    
    if [ $FRONTEND_EXIT_CODE -eq 0 ]; then
        print_success "Frontend tests passed!"
    else
        print_error "Frontend tests failed (exit code: $FRONTEND_EXIT_CODE)"
    fi
    
    cd "$SCRIPT_DIR"
    echo ""
else
    FRONTEND_SKIPPED=true
    print_info "Frontend tests skipped"
    echo ""
fi

# Run end-to-end tests
if [ "$RUN_E2E" = true ]; then
    print_header "Running E2E Tests (Python/Playwright)"

    if [ -z "$VIRTUAL_ENV" ]; then
        if [ ! -d "$SCRIPT_DIR/venv" ]; then
            python3 -m venv "$SCRIPT_DIR/venv"
        fi
        source "$SCRIPT_DIR/venv/bin/activate"
    fi

    python -m pip install -q -r "$SCRIPT_DIR/backend/requirements.txt" -r "$SCRIPT_DIR/tests/e2e/requirements.txt"
    python -m playwright install chromium
    if [ ! -d "$SCRIPT_DIR/frontend/node_modules" ]; then
        npm --prefix "$SCRIPT_DIR/frontend" install
    fi

    setsid env INCIDENT_CONNECTOR_TYPE=mock LLM_PROVIDER=ollama OLLAMA_BASE_URL=http://127.0.0.1:19999 \
        python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 > /tmp/smartrecover-e2e-backend.log 2>&1 &
    BACKEND_PID=$!
    setsid env REACT_APP_API_BASE_URL=http://localhost:8000/api/v1 \
        npm --prefix "$SCRIPT_DIR/frontend" start > /tmp/smartrecover-e2e-frontend.log 2>&1 &
    FRONTEND_PID=$!
    cleanup_e2e() {
        kill -- "-$BACKEND_PID" "-$FRONTEND_PID" 2>/dev/null || true
        wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
    }
    trap cleanup_e2e EXIT

    for _ in {1..30}; do
        if curl -fsS http://localhost:8000/api/v1/health >/dev/null &&
           curl -fsS http://localhost:3000 >/dev/null; then
            break
        fi
        sleep 1
    done

    if ! curl -fsS http://localhost:8000/api/v1/health >/dev/null ||
       ! curl -fsS http://localhost:3000 >/dev/null; then
        print_error "E2E stack did not start"
        E2E_EXIT_CODE=1
    else
        set +e
        CI=true python -m pytest "$SCRIPT_DIR/tests/e2e/" -v --tb=short --browser chromium
        E2E_EXIT_CODE=$?
        set -e
    fi
    cleanup_e2e
    trap - EXIT

    if [ $E2E_EXIT_CODE -eq 0 ]; then
        print_success "E2E tests passed!"
    else
        print_error "E2E tests failed (exit code: $E2E_EXIT_CODE)"
    fi
    echo ""
else
    E2E_SKIPPED=true
    print_info "E2E tests skipped"
    echo ""
fi

# Print summary
print_header "Test Summary"

if [ "$BACKEND_SKIPPED" = false ]; then
    if [ $BACKEND_EXIT_CODE -eq 0 ]; then
        print_success "Backend: PASSED"
    else
        print_error "Backend: FAILED (exit code: $BACKEND_EXIT_CODE)"
    fi
else
    print_info "Backend: SKIPPED"
fi

if [ "$FRONTEND_SKIPPED" = false ]; then
    if [ $FRONTEND_EXIT_CODE -eq 0 ]; then
        print_success "Frontend: PASSED"
    else
        print_error "Frontend: FAILED (exit code: $FRONTEND_EXIT_CODE)"
    fi
else
    print_info "Frontend: SKIPPED"
fi

if [ "$E2E_SKIPPED" = false ]; then
    if [ $E2E_EXIT_CODE -eq 0 ]; then
        print_success "E2E: PASSED"
    else
        print_error "E2E: FAILED (exit code: $E2E_EXIT_CODE)"
    fi
else
    print_info "E2E: SKIPPED"
fi

echo ""

# Determine overall exit code
if [ $BACKEND_EXIT_CODE -ne 0 ] || [ $FRONTEND_EXIT_CODE -ne 0 ] || [ $E2E_EXIT_CODE -ne 0 ]; then
    print_error "Some tests failed"
    exit 1
else
    print_success "All tests passed!"
    exit 0
fi
