#!/usr/bin/env python3
"""Simple script to run the SocialMapper API server.
"""

import uvicorn
from api_server.config import get_settings
from api_server.main import app

if __name__ == "__main__":
    settings = get_settings()

    print(f"Starting SocialMapper API server on {settings.host}:{settings.port}")
    print(f"API documentation available at: http://{settings.host}:{settings.port}/docs")
    print(f"CORS origins: {settings.cors_origins}")

    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info"
    )
