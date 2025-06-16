"""Service layer for the modern census module.

This package contains the business logic services that coordinate
between the domain and infrastructure layers.
"""

from .census_service import CensusService

__all__ = [
    "CensusService",
]
