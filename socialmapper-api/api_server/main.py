"""FastAPI application entry point for SocialMapper API server."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import get_settings
from .middleware import setup_api_key_auth, setup_cors, setup_error_handling, setup_rate_limiting
from .middleware.metrics import setup_metrics
from .middleware.compression import setup_compression
from .routers import analysis, health, metadata, results, feedback, websocket
from .services.cleanup_scheduler import get_cleanup_scheduler, init_cleanup_scheduler
from .services.enhanced_job_manager import EnhancedJobManager
from .services.result_storage import init_result_storage
from .services.feedback_service import init_feedback_service
from .services.cache_service import get_cache_service, CacheServiceSingleton
from .services.database_service import DatabaseServiceSingleton

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
        storage_path=settings.result_storage_path, ttl_hours=settings.result_ttl_hours
    )
    logger.info("Result storage initialized")

    # Initialize feedback service
    init_feedback_service(storage_path="feedback_data")
    logger.info("Feedback service initialized")
    
    # Initialize cache service
    if settings.cache_enabled:
        cache_service = get_cache_service()
        if cache_service.enabled:
            # Warm cache with demo data
            await cache_service.warm_demo_cache()
            logger.info("Cache service initialized and warmed")
    
    # Initialize database service if configured
    if settings.database_url or settings.db_password:
        try:
            db_service = await DatabaseServiceSingleton.get_instance()
            logger.info("Database service initialized with connection pooling")
        except Exception as e:
            logger.warning(f"Database service initialization failed: {e}")

    # Initialize and start cleanup scheduler
    init_cleanup_scheduler(settings.cleanup_interval_minutes)
    cleanup_scheduler = get_cleanup_scheduler()
    await cleanup_scheduler.start()
    logger.info("Cleanup scheduler started")

    # Initialize enhanced job manager
    job_manager = EnhancedJobManager()
    await job_manager.start()
    logger.info("Enhanced job manager started with prioritization")
    
    # Store job manager for access in routes
    app.state.job_manager = job_manager
    
    yield
    
    # Shutdown
    logger.info("Shutting down SocialMapper API server...")
    
    if hasattr(app.state, "job_manager"):
        await app.state.job_manager.stop()
        logger.info("Job manager stopped")

    await cleanup_scheduler.stop()
    logger.info("Cleanup scheduler stopped")
    
    # Close cache service
    await CacheServiceSingleton.close_instance()
    logger.info("Cache service closed")
    
    # Close database service
    await DatabaseServiceSingleton.close_instance()
    logger.info("Database service closed")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.api_title,
        description="REST API for SocialMapper community accessibility analysis",
        version=settings.api_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Configure middleware
    setup_error_handling(app)  # Set up error handling first
    setup_cors(app, settings)
    setup_rate_limiting(app, settings)
    setup_api_key_auth(app, settings)
    
    # Setup response compression for better performance
    if settings.enable_response_compression:
        setup_compression(app)
    
    # Setup comprehensive metrics collection
    setup_metrics(app)

    # Include routers
    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(analysis.router, prefix="/api/v1", tags=["analysis"])
    app.include_router(results.router, prefix="/api/v1", tags=["results"])
    app.include_router(metadata.router, prefix="/api/v1", tags=["metadata"])
    app.include_router(feedback.router, prefix="/api/v1", tags=["feedback"])
    
    # Include WebSocket router for real-time updates
    if settings.websocket_enabled:
        app.include_router(websocket.router, prefix="/api/v1", tags=["websocket"])

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "api_server.main:app", host=settings.host, port=settings.port, reload=True, log_level="info"
    )
