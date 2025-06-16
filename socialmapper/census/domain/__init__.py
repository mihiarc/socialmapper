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
    "BoundaryData",
    "CacheEntry",
    "CacheProvider",
    # Interfaces
    "CensusAPIClient",
    "CensusDataDependencies",
    "CensusDataPoint",
    "CensusRequest",
    "CensusVariable",
    "ConfigurationProvider",
    "DataRepository",
    "EventPublisher",
    "GeocodeProvider",
    "GeocodeResult",
    # Entities
    "GeographicUnit",
    "GeographyDependencies",
    "Logger",
    "NeighborDependencies",
    "NeighborRelationship",
    "RateLimiter",
]
