"""Logging configuration for SocialMapper using Rich.

This module sets up Rich-enhanced logging for the entire package.
"""

import logging
import os

from ..ui.console import setup_rich_logging


def configure_logging(level=None):
    """Configure Rich logging for SocialMapper.

    Args:
        level: Logging level (defaults to CRITICAL unless SOCIALMAPPER_LOG_LEVEL env var is set)
    """
    if level is None:
        # Check environment variable for logging level
        env_level = os.environ.get("SOCIALMAPPER_LOG_LEVEL", "CRITICAL").upper()
        level = env_level

    # Use Rich logging setup
    setup_rich_logging(level=level, show_time=False, show_path=False)

    # Set socialmapper logger level
    logger = logging.getLogger("socialmapper")
    logger.setLevel(getattr(logging, level, logging.CRITICAL))

    # Also set urllib3 to warning or higher to reduce noise
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # Set other noisy libraries to warning
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("fiona").setLevel(logging.WARNING)
    logging.getLogger("rasterio").setLevel(logging.WARNING)
    logging.getLogger("pyproj").setLevel(logging.WARNING)
    logging.getLogger("shapely").setLevel(logging.WARNING)
    logging.getLogger("geopandas").setLevel(logging.WARNING)
    logging.getLogger("osmnx").setLevel(logging.WARNING)


# Configure logging on import with CRITICAL level by default
configure_logging("CRITICAL")
