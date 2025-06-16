"""Domain layer for the modern census module.

This package contains the core business entities and interfaces
that define the census domain without any external dependencies.
"""

from .entities import (
    BoundaryData,
    CacheEntry,
    CensusDataPoint,
    CensusRequest,
    CensusVariable,
    GeocodeResult,
    GeographicUnit,
    NeighborRelationship,
)
from .interfaces import (
    CacheProvider,
    CensusAPIClient,
    CensusDataDependencies,
    ConfigurationProvider,
    DataRepository,
    EventPublisher,
    GeocodeProvider,
    GeographyDependencies,
    Logger,
    NeighborDependencies,
    RateLimiter,
)

__all__ = [
    # Entities
    "GeographicUnit",
    "CensusVariable",
    "CensusDataPoint",
    "BoundaryData",
    "NeighborRelationship",
    "GeocodeResult",
    "CensusRequest",
    "CacheEntry",
    # Interfaces
    "CensusAPIClient",
    "GeocodeProvider",
    "CacheProvider",
    "DataRepository",
    "ConfigurationProvider",
    "RateLimiter",
    "Logger",
    "EventPublisher",
    "CensusDataDependencies",
    "GeographyDependencies",
    "NeighborDependencies",
]
