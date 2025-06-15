"""
Domain entities for census operations.

These are pure data structures with no external dependencies.
They represent the core concepts in the census domain.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Optional


@dataclass(frozen=True)
class GeographicUnit:
    """Represents a geographic unit (block group, tract, etc.)."""
    geoid: str
    name: Optional[str] = None
    state_fips: Optional[str] = None
    county_fips: Optional[str] = None
    tract_code: Optional[str] = None
    block_group_code: Optional[str] = None
    
    def __post_init__(self):
        if not self.geoid:
            raise ValueError("GEOID cannot be empty")


@dataclass(frozen=True)
class CensusVariable:
    """Census variable with human-readable mapping."""
    code: str
    name: str
    description: Optional[str] = None
    
    def __post_init__(self):
        if not self.code or not isinstance(self.code, str):
            raise ValueError("Census variable code must be a non-empty string")
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Census variable name must be a non-empty string")


@dataclass(frozen=True)
class CensusDataPoint:
    """A single census data point for a geographic unit."""
    geoid: str
    variable: CensusVariable
    value: Optional[float]
    margin_of_error: Optional[float] = None
    year: Optional[int] = None
    dataset: Optional[str] = None
    
    def __post_init__(self):
        if not self.geoid:
            raise ValueError("GEOID cannot be empty")


@dataclass(frozen=True)
class BoundaryData:
    """Geographic boundary information."""
    geoid: str
    geometry: Any  # GeoJSON or Shapely geometry
    area_land: Optional[float] = None
    area_water: Optional[float] = None
    
    def __post_init__(self):
        if not self.geoid:
            raise ValueError("GEOID cannot be empty")


@dataclass(frozen=True)
class NeighborRelationship:
    """Represents a neighbor relationship between geographic units."""
    source_geoid: str
    neighbor_geoid: str
    relationship_type: str  # 'adjacent', 'contains', etc.
    shared_boundary_length: Optional[float] = None
    
    def __post_init__(self):
        if not self.source_geoid or not self.neighbor_geoid:
            raise ValueError("Both GEOIDs must be provided")
        if self.source_geoid == self.neighbor_geoid:
            raise ValueError("A unit cannot be its own neighbor")


@dataclass(frozen=True)
class GeocodeResult:
    """Result of geocoding a point to geographic units."""
    latitude: float
    longitude: float
    state_fips: Optional[str] = None
    county_fips: Optional[str] = None
    tract_geoid: Optional[str] = None
    block_group_geoid: Optional[str] = None
    zcta_geoid: Optional[str] = None
    confidence: Optional[float] = None
    source: Optional[str] = None


@dataclass(frozen=True)
class CensusRequest:
    """Request for census data."""
    geographic_units: List[GeographicUnit]
    variables: List[CensusVariable]
    year: int = 2021
    dataset: str = "acs/acs5"
    
    def __post_init__(self):
        if not self.geographic_units:
            raise ValueError("At least one geographic unit must be specified")
        if not self.variables:
            raise ValueError("At least one variable must be specified")


@dataclass
class CacheEntry:
    """Represents a cached data entry."""
    key: str
    data: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    
    @property
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


@dataclass(frozen=True)
class StateInfo:
    """State information with all format conversions."""
    fips: str
    abbreviation: str
    name: str
    
    def __post_init__(self):
        if not self.fips or len(self.fips) != 2 or not self.fips.isdigit():
            raise ValueError("State FIPS must be a 2-digit string")
        if not self.abbreviation or len(self.abbreviation) != 2:
            raise ValueError("State abbreviation must be 2 characters")
        if not self.name:
            raise ValueError("State name cannot be empty")


@dataclass(frozen=True)
class CountyInfo:
    """County information with FIPS codes."""
    state_fips: str
    county_fips: str
    name: Optional[str] = None
    
    def __post_init__(self):
        if not self.state_fips or len(self.state_fips) != 2 or not self.state_fips.isdigit():
            raise ValueError("State FIPS must be a 2-digit string")
        if not self.county_fips or len(self.county_fips) != 3 or not self.county_fips.isdigit():
            raise ValueError("County FIPS must be a 3-digit string")
    
    @property
    def full_fips(self) -> str:
        """Get the full 5-digit county FIPS code."""
        return f"{self.state_fips}{self.county_fips}"


@dataclass(frozen=True)
class BlockGroupInfo:
    """Block group information with all geographic identifiers."""
    state_fips: str
    county_fips: str
    tract: str
    block_group: str
    geoid: Optional[str] = None
    
    def __post_init__(self):
        if not self.state_fips or len(self.state_fips) != 2 or not self.state_fips.isdigit():
            raise ValueError("State FIPS must be a 2-digit string")
        if not self.county_fips or len(self.county_fips) != 3 or not self.county_fips.isdigit():
            raise ValueError("County FIPS must be a 3-digit string")
        if not self.tract or len(self.tract) != 6 or not self.tract.isdigit():
            raise ValueError("Tract must be a 6-digit string")
        if not self.block_group or len(self.block_group) != 1 or not self.block_group.isdigit():
            raise ValueError("Block group must be a 1-digit string")
    
    @property
    def full_geoid(self) -> str:
        """Get the full 12-digit block group GEOID."""
        return f"{self.state_fips}{self.county_fips}{self.tract}{self.block_group}" 