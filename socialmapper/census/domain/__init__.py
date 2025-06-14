"""
Domain layer for the modern census module.

This package contains the core business entities and interfaces
that define the census domain without any external dependencies.
"""

from .entities import (
    GeographicUnit,
    CensusVariable,
    CensusDataPoint,
    BoundaryData,
    NeighborRelationship,
    GeocodeResult,
    CensusRequest,
    CacheEntry
)

from .interfaces import (
    CensusAPIClient,
    GeocodeProvider,
    CacheProvider,
    DataRepository,
    ConfigurationProvider,
    RateLimiter,
    Logger,
    EventPublisher,
    CensusDataDependencies,
    GeographyDependencies,
    NeighborDependencies
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