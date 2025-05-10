#!/usr/bin/env python3
"""
Convenience module for generating maps based on census variables.

This module re-exports the primary function for generating maps from the map_coordinator module.
"""

# Import and re-export the function
from .map_coordinator import generate_maps_for_variables

__all__ = ['generate_maps_for_variables'] 