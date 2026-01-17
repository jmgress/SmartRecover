import logging
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextvars import ContextVar
from contextlib import asynccontextmanager

from backend.api.routes import router
from backend.logging_config import setup_logging

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Context variable for trace ID
trace_id_var: ContextVar[str] = ContextVar("trace_id", default=None)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("SmartRecover Incident Management Resolver starting up")
    yield
    # Shutdown (if needed in the future)
    logger.info("SmartRecover Incident Management Resolver shutting down")


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


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Middleware to add request logging and trace IDs."""
    # Generate or extract trace ID
    trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
    trace_id_var.set(trace_id)
    
    # Log request
    logger.info(
        f"Incoming request: {request.method} {request.url.path}",
        extra={
            "trace_id": trace_id,
            "extra_fields": {
                "method": request.method,
                "path": request.url.path,
                "client_host": request.client.host if request.client else None
            }
        }
    )
    
    # Process request
    response = await call_next(request)
    
    # Add trace ID to response headers
    response.headers["X-Trace-ID"] = trace_id
    
    # Log response
    logger.info(
        f"Response: {response.status_code}",
        extra={
            "trace_id": trace_id,
            "extra_fields": {
                "status_code": response.status_code,
                "method": request.method,
                "path": request.url.path
            }
        }
    )
    
    return response


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
    uvicorn.run(app, host="0.0.0.0", port=8000)
