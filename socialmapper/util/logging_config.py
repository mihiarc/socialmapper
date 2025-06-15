"""
Logging configuration for SocialMapper.

This module sets up the default logging configuration for the entire package.
"""

import logging
import os


def configure_logging(level=None):
    """
    Configure logging for SocialMapper.
    
    Args:
        level: Logging level (defaults to CRITICAL unless SOCIALMAPPER_LOG_LEVEL env var is set)
    """
    if level is None:
        # Check environment variable for logging level
        env_level = os.environ.get('SOCIALMAPPER_LOG_LEVEL', 'CRITICAL').upper()
        level = getattr(logging, env_level, logging.CRITICAL)
    
    # Configure root logger for socialmapper package
    logger = logging.getLogger('socialmapper')
    logger.setLevel(level)
    
    # Only add handler if none exists
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    # Also set urllib3 to warning or higher to reduce noise
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # Set other noisy libraries to warning
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('fiona').setLevel(logging.WARNING)
    logging.getLogger('rasterio').setLevel(logging.WARNING)
    logging.getLogger('pyproj').setLevel(logging.WARNING)


# Configure logging on import with CRITICAL level by default
configure_logging(logging.CRITICAL)