#!/usr/bin/env python3
"""Utility functions for the socialmapper project.

This module provides various utility functions including census variable handling,
rate limiting, path security, and input validation.
"""

# Load environment variables from .env file as early as possible
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # dotenv not available - continue without it
    pass

# Import environment loading utilities
from .env_loader import ensure_environment_loaded, get_env_var, load_environment_variables
from .env_loader import get_census_api_key as _get_census_api_key

# Ensure environment is loaded
ensure_environment_loaded()

import asyncio
import logging
import os
import re
import sys
import time
from typing import Optional

import httpx

# Note: ratelimit import removed - not currently used
# Import modern census system for census utilities
from ..census import get_census_system

# Create a default system instance for utility functions
_census_system = None


def _get_census_system():
    """Get the census system instance."""
    global _census_system
    if _census_system is None:
        _census_system = get_census_system()
    return _census_system


# Census variable utilities - now using modern system
def census_code_to_name(census_code: str) -> str:
    """Convert a census variable code to its human-readable name."""
    return _get_census_system()._variable_service.code_to_name(census_code)


def census_name_to_code(name: str) -> str:
    """Convert a human-readable name to its census variable code."""
    return _get_census_system()._variable_service.name_to_code(name)


def normalize_census_variable(variable: str) -> str:
    """Normalize a census variable to its code form."""
    return _get_census_system()._variable_service.normalize_variable(variable)


def get_readable_census_variable(variable: str) -> str:
    """Get a human-readable representation of a census variable."""
    return _get_census_system()._variable_service.get_readable_variable(variable)


def get_readable_census_variables(variables: list[str]) -> list[str]:
    """Get human-readable representations for a list of census variables."""
    return _get_census_system()._variable_service.get_readable_variables(variables)


def validate_census_variable(variable: str) -> bool:
    """Validate a census variable code or name."""
    return _get_census_system()._variable_service.validate_variable(variable)


def get_census_api_key() -> str | None:
    """Get the Census API key from environment variable."""
    return _get_census_api_key()


# Legacy mappings for backward compatibility
CENSUS_VARIABLE_MAPPING = _get_census_system()._variable_service.VARIABLE_MAPPING
VARIABLE_COLORMAPS = _get_census_system()._variable_service.VARIABLE_COLORMAPS


# Add north arrow utility function
def add_north_arrow(ax, position="upper right", scale=0.1):
    """Add a north arrow to a map.

    Args:
        ax: Matplotlib axis to add arrow to
        position: Position on the plot ('upper right', 'upper left', 'lower right', 'lower left')
        scale: Size of the arrow relative to the axis

    Returns:
        The arrow annotation object
    """
    # Get axis limits
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    # Calculate position
    if position == "upper right":
        x = xlim[1] - (xlim[1] - xlim[0]) * 0.05
        y = ylim[1] - (ylim[1] - ylim[0]) * 0.05
    elif position == "upper left":
        x = xlim[0] + (xlim[1] - xlim[0]) * 0.05
        y = ylim[1] - (ylim[1] - ylim[0]) * 0.05
    elif position == "lower right":
        x = xlim[1] - (xlim[1] - xlim[0]) * 0.05
        y = ylim[0] + (ylim[1] - ylim[0]) * 0.05
    else:  # lower left
        x = xlim[0] + (xlim[1] - xlim[0]) * 0.05
        y = ylim[0] + (ylim[1] - ylim[0]) * 0.05

    # Scale the offset based on the scale parameter
    arrow_height = (ylim[1] - ylim[0]) * scale

    # Add the arrow
    arrow = ax.annotate(
        "N",
        xy=(x, y),
        xytext=(x, y - arrow_height),
        arrowprops={"facecolor": "black", "width": 3, "headwidth": 10},
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
    )

    return arrow


# Import utilities to expose at the module level
# Import input validation utilities
from .config_manager import (
    apply_preset,
    # Backward compatibility aliases
    get_config,
    get_config_summary,
    get_global_config,
    optimize_for_current_system,
    reset_config,
    reset_global_config,
    set_global_config,
    update_config,
    update_global_config,
    validate_config,
)
from .config_presets import (
    ConfigPresets,
    get_auto_config,
    get_config_for_environment,
    get_development_config,
    get_production_config,
)
from .input_validation import (
    InputValidationError,
    encode_for_url,
    sanitize_for_api,
    validate_address,
    validate_api_response,
    validate_census_variable,
    validate_coordinates,
    validate_poi_type,
    validate_state_name,
    validate_url,
)
from .input_validation import (
    sanitize_filename as sanitize_filename_input,
)

# Import path security utilities
from .path_security import (
    PathSecurityError,
    get_safe_cache_path,
    safe_join_path,
    sanitize_path,
    validate_filename,
)
from .rate_limiter import (
    AsyncRateLimitedClient,
    RateLimitedClient,
    rate_limited,
    rate_limiter,
    with_retry,
)

# Import new utility modules
from .system_detection import (
    get_available_memory_gb,
    get_optimal_worker_count,
    get_performance_tier,
    get_system_capabilities,
    get_total_memory_gb,
    is_high_performance_system,
    is_memory_constrained,
    validate_system_requirements,
)

# Export these symbols at the package level
__all__ = [
    # Census variable utilities
    "CENSUS_VARIABLE_MAPPING",
    "VARIABLE_COLORMAPS",
    "AsyncRateLimitedClient",
    # Configuration preset utilities
    "ConfigPresets",
    "InputValidationError",
    "PathSecurityError",
    "RateLimitedClient",
    # Map utilities
    "add_north_arrow",
    "apply_preset",
    "census_code_to_name",
    "census_name_to_code",
    "encode_for_url",
    # Environment utilities
    "ensure_environment_loaded",
    "get_auto_config",
    "get_available_memory_gb",
    "get_census_api_key",
    # Backward compatibility aliases
    "get_config",
    "get_config_for_environment",
    "get_config_summary",
    "get_development_config",
    "get_env_var",
    # Configuration management utilities
    "get_global_config",
    "get_optimal_worker_count",
    "get_performance_tier",
    "get_production_config",
    "get_readable_census_variable",
    "get_readable_census_variables",
    "get_safe_cache_path",
    # System detection utilities
    "get_system_capabilities",
    "get_total_memory_gb",
    "is_high_performance_system",
    "is_memory_constrained",
    "load_environment_variables",
    "normalize_census_variable",
    "optimize_for_current_system",
    "rate_limited",
    # Rate limiter utilities
    "rate_limiter",
    "reset_config",
    "reset_global_config",
    "safe_join_path",
    "sanitize_filename_input",
    # Input validation utilities
    "sanitize_for_api",
    # Path security utilities
    "sanitize_path",
    "set_global_config",
    "update_config",
    "update_global_config",
    "validate_address",
    "validate_api_response",
    "validate_census_variable",
    "validate_config",
    "validate_coordinates",
    "validate_filename",
    "validate_poi_type",
    "validate_state_name",
    "validate_system_requirements",
    "validate_url",
    "with_retry",
]


# Create default rate limiter instance for backward compatibility
rate_limiter = RateLimitedClient()

# State name mapping utilities
STATE_NAMES_TO_ABBR = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
    "District of Columbia": "DC",
    "Puerto Rico": "PR",
}


def state_fips_to_abbreviation(fips_code):
    """Convert state FIPS code to state abbreviation."""
    fips_to_abbrev = {
        "01": "AL",
        "02": "AK",
        "04": "AZ",
        "05": "AR",
        "06": "CA",
        "08": "CO",
        "09": "CT",
        "10": "DE",
        "11": "DC",
        "12": "FL",
        "13": "GA",
        "15": "HI",
        "16": "ID",
        "17": "IL",
        "18": "IN",
        "19": "IA",
        "20": "KS",
        "21": "KY",
        "22": "LA",
        "23": "ME",
        "24": "MD",
        "25": "MA",
        "26": "MI",
        "27": "MN",
        "28": "MS",
        "29": "MO",
        "30": "MT",
        "31": "NE",
        "32": "NV",
        "33": "NH",
        "34": "NJ",
        "35": "NM",
        "36": "NY",
        "37": "NC",
        "38": "ND",
        "39": "OH",
        "40": "OK",
        "41": "OR",
        "42": "PA",
        "44": "RI",
        "45": "SC",
        "46": "SD",
        "47": "TN",
        "48": "TX",
        "49": "UT",
        "50": "VT",
        "51": "VA",
        "53": "WA",
        "54": "WV",
        "55": "WI",
        "56": "WY",
        "72": "PR",
    }
    return fips_to_abbrev.get(fips_code)



