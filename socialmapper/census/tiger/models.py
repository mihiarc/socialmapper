"""Data models for TIGER geometry fetching."""

from dataclasses import dataclass
from enum import Enum
from typing import Any

import geopandas as gpd
from pydantic import BaseModel, Field, field_validator


class GeographyLevel(str, Enum):
    """Supported geography levels for TIGER API."""

    COUNTY = "county"
    BLOCK_GROUP = "block_group"
    BLOCK_GROUP_DETAILED = "block_group_detailed"  # Non-generalized version
    ZCTA = "zcta"
    TRACT = "tract"
    STATE = "state"
    PLACE = "place"
    CONGRESSIONAL_DISTRICT = "congressional_district"
    STATE_LEGISLATIVE_UPPER = "state_legislative_upper"
    STATE_LEGISLATIVE_LOWER = "state_legislative_lower"


class GeometryQuery(BaseModel):
    """Query parameters for fetching TIGER geometries."""

    geography_level: GeographyLevel = Field(..., description="The geographic level to fetch")
    state_fips: str | None = Field(None, description="State FIPS code (e.g., '06' for California)")
    county_fips: str | None = Field(
        None, description="County FIPS code (e.g., '001' for Alameda County)"
    )
    zcta_prefix: str | None = Field(
        None, description="ZCTA prefix for filtering (e.g., '945' for 94501-94599)"
    )
    geometry_ids: list[str] | None = Field(None, description="Specific geometry IDs to fetch")
    simplify_tolerance: float | None = Field(
        0.0001, description="Tolerance for geometry simplification (0 = no simplification)"
    )
    include_attributes: bool = Field(True, description="Whether to include demographic attributes")

    @field_validator("state_fips", "county_fips")
    @classmethod
    def validate_fips(cls, v: str | None) -> str | None:
        """Validate FIPS codes are properly formatted."""
        if v is not None:
            # Remove any non-numeric characters
            v = "".join(c for c in v if c.isdigit())
            # Pad with zeros if needed
            if len(v) == 1:
                v = "0" + v
        return v

    @field_validator("zcta_prefix")
    @classmethod
    def validate_zcta_prefix(cls, v: str | None) -> str | None:
        """Validate ZCTA prefix."""
        if v is not None:
            # Remove any non-numeric characters
            v = "".join(c for c in v if c.isdigit())
            if not (1 <= len(v) <= 5):
                raise ValueError("ZCTA prefix must be 1-5 digits")
        return v


@dataclass
class GeometryResult:
    """Result from TIGER geometry fetch operation."""

    geodataframe: gpd.GeoDataFrame
    geography_level: GeographyLevel
    query: GeometryQuery
    metadata: dict[str, Any]

    @property
    def geometry_count(self) -> int:
        """Number of geometries returned."""
        return len(self.geodataframe)

    @property
    def bounds(self) -> tuple:
        """Total bounds of all geometries."""
        return self.geodataframe.total_bounds

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "geography_level": self.geography_level.value,
            "geometry_count": self.geometry_count,
            "bounds": list(self.bounds),
            "metadata": self.metadata,
            "query": self.query.model_dump(),
        }


class TigerEndpoint(BaseModel):
    """Configuration for a TIGER REST API endpoint."""

    base_url: str = Field(..., description="Base URL for the service")
    layer_id: int = Field(..., description="Layer ID within the service")
    id_field: str = Field(..., description="Field name for geometry ID")
    name_field: str = Field(..., description="Field name for geometry name")
    state_field: str | None = Field(None, description="Field name for state FIPS")
    county_field: str | None = Field(None, description="Field name for county FIPS")

    def build_query_url(self) -> str:
        """Build the full query URL."""
        return f"{self.base_url}/{self.layer_id}/query"


# Endpoint configurations for each geography level
TIGER_ENDPOINTS: dict[GeographyLevel, TigerEndpoint] = {
    GeographyLevel.STATE: TigerEndpoint(
        base_url="https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer",
        layer_id=0,
        id_field="STATE",
        name_field="NAME",
    ),
    GeographyLevel.COUNTY: TigerEndpoint(
        # Using the generalized ACS2023 version
        base_url="https://tigerweb.geo.census.gov/arcgis/rest/services/Generalized_ACS2023/State_County/MapServer",
        layer_id=11,
        id_field="COUNTY",
        name_field="NAME",
        state_field="STATE",
    ),
    GeographyLevel.TRACT: TigerEndpoint(
        base_url="https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer",
        layer_id=0,
        id_field="TRACT",
        name_field="NAME",
        state_field="STATE",
        county_field="COUNTY",
    ),
    GeographyLevel.BLOCK_GROUP: TigerEndpoint(
        # Using the generalized 500k version for better performance
        base_url="https://tigerweb.geo.census.gov/arcgis/rest/services/Generalized_ACS2023/Tracts_Blocks/MapServer",
        layer_id=6,
        id_field="BLKGRP",
        name_field="BASENAME",
        state_field="STATE",
        county_field="COUNTY",
    ),
    GeographyLevel.BLOCK_GROUP_DETAILED: TigerEndpoint(
        # Detailed (non-generalized) version for precise boundaries
        base_url="https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer",
        layer_id=1,
        id_field="BLKGRP",
        name_field="BASENAME",
        state_field="STATE",
        county_field="COUNTY",
    ),
    GeographyLevel.ZCTA: TigerEndpoint(
        base_url="https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/PUMA_TAD_TAZ_UGA_ZCTA/MapServer",
        layer_id=7,
        id_field="ZCTA5",
        name_field="ZCTA5",
    ),
    GeographyLevel.PLACE: TigerEndpoint(
        base_url="https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Places_CouSub_ConCity_SubMCD/MapServer",
        layer_id=0,
        id_field="PLACE",
        name_field="NAME",
        state_field="STATE",
    ),
    GeographyLevel.CONGRESSIONAL_DISTRICT: TigerEndpoint(
        base_url="https://tigerweb.geo.census.gov/arcgis/rest/services/Legislative/CD118/MapServer",
        layer_id=0,
        id_field="CD118",
        name_field="BASENAME",
        state_field="STATE",
    ),
    GeographyLevel.STATE_LEGISLATIVE_UPPER: TigerEndpoint(
        base_url="https://tigerweb.geo.census.gov/arcgis/rest/services/Legislative/SLDU2022/MapServer",
        layer_id=0,
        id_field="SLDU",
        name_field="BASENAME",
        state_field="STATE",
    ),
    GeographyLevel.STATE_LEGISLATIVE_LOWER: TigerEndpoint(
        base_url="https://tigerweb.geo.census.gov/arcgis/rest/services/Legislative/SLDL2022/MapServer",
        layer_id=0,
        id_field="SLDL",
        name_field="BASENAME",
        state_field="STATE",
    ),
}
