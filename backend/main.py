from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.utils.logger import LoggerManager, get_logger

# Initialize logging as early as possible
LoggerManager.setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="Incident Management Resolver",
    description="Agentic system for incident resolution using LangChain and LangGraph",
    version="1.0.0"
)

logger.info("Starting Incident Management Resolver application")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("CORS middleware configured")

app.include_router(router, prefix="/api/v1")

logger.info("API routes registered")


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Application shutting down")


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
    logger.info("Starting uvicorn server on 0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
