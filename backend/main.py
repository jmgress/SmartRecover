import argparse
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.config import get_config
from backend.logging_config import configure_logging, get_logger

# Parse command line arguments
parser = argparse.ArgumentParser(description='SmartRecover Incident Management Resolver')
parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging (DEBUG level)')
parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                    help='Set the logging level')
parser.add_argument('--log-file', type=str, help='Path to log file')

# Parse known args to allow uvicorn arguments to pass through
args, unknown = parser.parse_known_args()

# Initialize logging configuration
config = get_config()
logging_config = config.logging

# Override with command-line arguments
if args.verbose:
    logging_config.verbose = True
if args.log_level:
    logging_config.level = args.log_level
if args.log_file:
    logging_config.log_file = args.log_file

# Configure logging
configure_logging(
    log_level=logging_config.level,
    verbose=logging_config.verbose,
    log_file=logging_config.log_file,
    log_to_console=logging_config.log_to_console,
    max_bytes=logging_config.max_bytes,
    backup_count=logging_config.backup_count
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan event handler."""
    # Startup
    logger.info("Starting SmartRecover Incident Management Resolver")
    logger.info(f"LLM Provider: {config.llm.provider}")
    logger.debug(f"Configuration: {config.model_dump()}")
    logger.info("Application startup complete")
    logger.info("API documentation available at: /docs")
    yield
    # Shutdown
    logger.info("Application shutting down")


app = FastAPI(
    title="Incident Management Resolver",
    description="Agentic system for incident resolution using LangChain and LangGraph",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    logger.debug("Root endpoint accessed")
    return {
        "message": "Incident Management Resolver API",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting uvicorn server on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
