#!/usr/bin/env python3
"""Logging configuration for SocialMapper.

This module provides Rich-enhanced logging setup and utilities.
"""

import logging

from rich.logging import RichHandler

from .core import console

# Rich logging handler
rich_handler = RichHandler(
    console=console, show_time=True, show_path=False, markup=True, rich_tracebacks=True
)


def setup_rich_logging(level: str = "INFO", show_time: bool = True, show_path: bool = False):
    """Set up Rich-enhanced logging for SocialMapper.

    Args:
        level: Logging level (default: "INFO")
        show_time: Whether to show timestamps
        show_path: Whether to show file paths
    """
    # Convert string level to int
    if isinstance(level, str):
        level = getattr(logging, level.upper())

    # Configure root logger with Rich handler
    logging.basicConfig(level=level, format="%(message)s", datefmt="[%X]", handlers=[rich_handler])

    # Reduce noise from external libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a Rich-enabled logger.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
