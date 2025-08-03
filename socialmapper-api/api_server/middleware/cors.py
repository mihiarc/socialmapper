"""CORS configuration for the SocialMapper API.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config import get_settings

logger = logging.getLogger(__name__)


def setup_cors(app: FastAPI, settings=None):
    """Configure CORS middleware for the FastAPI application.
    
    Args:
        app: FastAPI application instance
        settings: Application settings (optional)
    """
    if settings is None:
        settings = get_settings()

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-API-Key",
            "X-Request-ID",
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Cache-Control",
        ],
        expose_headers=[
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
            "X-Request-ID",
            "Content-Language",
        ],
        max_age=86400,  # 24 hours
    )

    logger.info(f"CORS enabled for origins: {settings.cors_origins}")
