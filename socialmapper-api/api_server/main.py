"""FastAPI application entry point for SocialMapper API server.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import get_settings
from .middleware import setup_api_key_auth, setup_cors, setup_error_handling, setup_rate_limiting
from .routers import analysis, health, metadata, results
from .services.cleanup_scheduler import get_cleanup_scheduler, init_cleanup_scheduler
from .services.job_manager import start_job_manager, stop_job_manager
from .services.result_storage import init_result_storage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting SocialMapper API server...")
    settings = get_settings()

    # Initialize result storage
    init_result_storage(
        storage_path=settings.result_storage_path,
        ttl_hours=settings.result_ttl_hours
    )
    logger.info("Result storage initialized")

    # Initialize and start cleanup scheduler
    init_cleanup_scheduler(settings.cleanup_interval_minutes)
    cleanup_scheduler = get_cleanup_scheduler()
    await cleanup_scheduler.start()
    logger.info("Cleanup scheduler started")

    await start_job_manager()
    logger.info("Job manager started")
    yield
    # Shutdown
    logger.info("Shutting down SocialMapper API server...")
    await stop_job_manager()
    logger.info("Job manager stopped")

    await cleanup_scheduler.stop()
    logger.info("Cleanup scheduler stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.api_title,
        description="REST API for SocialMapper community accessibility analysis",
        version=settings.api_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    # Configure middleware
    setup_error_handling(app)  # Set up error handling first
    setup_cors(app, settings)
    setup_rate_limiting(app, settings)
    setup_api_key_auth(app, settings)

    # Include routers
    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(analysis.router, prefix="/api/v1", tags=["analysis"])
    app.include_router(results.router, prefix="/api/v1", tags=["results"])
    app.include_router(metadata.router, prefix="/api/v1", tags=["metadata"])

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "api_server.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info"
    )
