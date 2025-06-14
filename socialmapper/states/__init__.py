#!/usr/bin/env python3
"""
Centralized state identifier management for the SocialMapper project.

This module provides tools for working with US states in different formats:
- Full state names (e.g., "California")
- Two-letter state abbreviations (e.g., "CA")
- FIPS codes (e.g., "06")

It also includes functions for state validation, neighboring states, and other state-related utilities.

Note: This module now uses the modern census system internally for better architecture
and maintainability while preserving the same API.
"""

# Import everything from the modern census system
from ..census_modern import get_census_system
from ..census_modern.services.geography_service import StateFormat

# Create a default geography service instance
_geography_service = None

def _get_geography_service():
    """Get the geography service instance."""
    global _geography_service
    if _geography_service is None:
        census_system = get_census_system()
        _geography_service = census_system._geography_service
    return _geography_service

# Re-export StateFormat for backward compatibility
__all__ = ["StateFormat"]

# Re-export all the functions with the same API
def is_fips_code(code):
    """Check if a string or number is a valid state FIPS code."""
    return _get_geography_service().is_fips_code(code)

def detect_state_format(state):
    """Detect the format of a state identifier."""
    return _get_geography_service().detect_state_format(state)

def normalize_state(state, to_format=StateFormat.ABBREVIATION):
    """Convert a state identifier to the requested format."""
    return _get_geography_service().normalize_state(state, to_format)

def state_name_to_abbreviation(state_name):
    """Convert a full state name to its two-letter abbreviation."""
    return normalize_state(state_name, to_format=StateFormat.ABBREVIATION)

def state_abbreviation_to_name(state_abbr):
    """Convert a state abbreviation to its full name."""
    return normalize_state(state_abbr, to_format=StateFormat.NAME)

def state_abbreviation_to_fips(state_abbr):
    """Convert a state abbreviation to its FIPS code."""
    return normalize_state(state_abbr, to_format=StateFormat.FIPS)

def state_fips_to_abbreviation(fips):
    """Convert a state FIPS code to its abbreviation."""
    return normalize_state(fips, to_format=StateFormat.ABBREVIATION)

def state_fips_to_name(fips):
    """Convert a state FIPS code to its full name."""
    return normalize_state(fips, to_format=StateFormat.NAME)

def state_name_to_fips(state_name):
    """Convert a state name to its FIPS code."""
    return normalize_state(state_name, to_format=StateFormat.FIPS)

def is_valid_state(state):
    """Check if a string is a valid state identifier in any format."""
    return _get_geography_service().is_valid_state(state)

def normalize_state_list(states, to_format=StateFormat.ABBREVIATION):
    """Normalize a list of state identifiers to a consistent format."""
    return _get_geography_service().normalize_state_list(states, to_format)

def get_all_states(format=StateFormat.ABBREVIATION):
    """Get a list of all US states in the requested format."""
    return _get_geography_service().get_all_states(format)

# Export all functions
__all__.extend([
    "is_fips_code",
    "detect_state_format", 
    "normalize_state",
    "state_name_to_abbreviation",
    "state_abbreviation_to_name",
    "state_abbreviation_to_fips",
    "state_fips_to_abbreviation",
    "state_fips_to_name",
    "state_name_to_fips",
    "is_valid_state",
    "normalize_state_list",
    "get_all_states",
])
