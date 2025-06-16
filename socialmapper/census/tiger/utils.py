"""Utility functions for TIGER geometry operations."""

import logging

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from .client import TigerGeometryClient
from .models import GeographyLevel, GeometryQuery

logger = logging.getLogger(__name__)


def get_geography_hierarchy(
    point: Point | tuple[float, float],
    client: TigerGeometryClient | None = None,
) -> dict:
    """Get all geography levels that contain a given point.

    Args:
        point: Point geometry or (lon, lat) tuple
        client: TigerGeometryClient instance (creates new if None)

    Returns:
        Dictionary mapping geography levels to their GEOIDs and names
    """
    if client is None:
        client = TigerGeometryClient()

    # Convert tuple to Point if needed
    if isinstance(point, tuple):
        point = Point(point[0], point[1])

    hierarchy = {}

    # Define geography levels to check in hierarchical order
    levels_to_check = [
        GeographyLevel.STATE,
        GeographyLevel.COUNTY,
        GeographyLevel.TRACT,
        GeographyLevel.BLOCK_GROUP,
        GeographyLevel.ZCTA,
        GeographyLevel.PLACE,
        GeographyLevel.CONGRESSIONAL_DISTRICT,
    ]

    # Create a small buffer around the point for spatial query
    buffer = point.buffer(0.01)  # ~1km buffer
    bounds = buffer.bounds

    for level in levels_to_check:
        try:
            # For hierarchical levels, use previously found FIPS codes
            state_fips = hierarchy.get(GeographyLevel.STATE, {}).get("GEOID")
            county_fips = (
                hierarchy.get(GeographyLevel.COUNTY, {}).get("GEOID", "")[-3:]
                if GeographyLevel.COUNTY in hierarchy
                else None
            )

            # Build appropriate query
            if level in [GeographyLevel.STATE, GeographyLevel.ZCTA, GeographyLevel.PLACE]:
                # These don't require state/county filters
                query = GeometryQuery(geography_level=level)
            elif level in [GeographyLevel.COUNTY, GeographyLevel.CONGRESSIONAL_DISTRICT]:
                # These benefit from state filter
                query = GeometryQuery(
                    geography_level=level,
                    state_fips=state_fips,
                )
            else:
                # Block groups and tracts require state, benefit from county
                query = GeometryQuery(
                    geography_level=level,
                    state_fips=state_fips,
                    county_fips=county_fips,
                )

            # Fetch geometries
            result = client.fetch_geometries(query)

            # Find containing geometry
            containing = result.geodataframe[result.geodataframe.geometry.contains(point)]

            if not containing.empty:
                row = containing.iloc[0]
                hierarchy[level] = {
                    "GEOID": row["GEOID"],
                    "NAME": row.get("NAME", row["GEOID"]),
                }
        except Exception as e:
            logger.warning(f"Failed to fetch {level.value}: {e}")

    return hierarchy


def create_multi_level_geodataframe(
    geographies: list[tuple[GeographyLevel, GeometryQuery]],
    client: TigerGeometryClient | None = None,
) -> gpd.GeoDataFrame:
    """Create a GeoDataFrame with multiple geography levels.

    Args:
        geographies: List of (level, query) tuples
        client: TigerGeometryClient instance

    Returns:
        Combined GeoDataFrame with all geographies
    """
    if client is None:
        client = TigerGeometryClient()

    gdfs = []

    for level, query in geographies:
        try:
            result = client.fetch_geometries(query)
            gdf = result.geodataframe.copy()
            gdf["geography_level"] = level.value
            gdfs.append(gdf)
        except Exception as e:
            logger.error(f"Failed to fetch {level.value}: {e}")

    if not gdfs:
        return gpd.GeoDataFrame()

    # Combine all GeoDataFrames
    combined = pd.concat(gdfs, ignore_index=True)

    return combined


def get_neighboring_geographies(
    base_geoid: str,
    geography_level: GeographyLevel,
    client: TigerGeometryClient | None = None,
) -> gpd.GeoDataFrame:
    """Get all geographies that share a border with the given geography.

    Args:
        base_geoid: GEOID of the base geography
        geography_level: Geography level to fetch
        client: TigerGeometryClient instance

    Returns:
        GeoDataFrame of neighboring geographies
    """
    if client is None:
        client = TigerGeometryClient()

    # Extract state and county from GEOID if applicable
    state_fips = base_geoid[:2] if len(base_geoid) >= 2 else None
    county_fips = base_geoid[2:5] if len(base_geoid) >= 5 else None

    # Build query based on geography level
    query = GeometryQuery(
        geography_level=geography_level,
        state_fips=state_fips,
        county_fips=county_fips
        if geography_level in [GeographyLevel.BLOCK_GROUP, GeographyLevel.TRACT]
        else None,
    )

    # Fetch all geographies in the area
    result = client.fetch_geometries(query)

    # Find the base geography
    base_mask = result.geodataframe["GEOID"] == base_geoid
    if not base_mask.any():
        logger.warning(f"Base geography {base_geoid} not found")
        return gpd.GeoDataFrame()

    base_geometry = result.geodataframe[base_mask].iloc[0].geometry

    # Find neighbors (share a border)
    neighbors_mask = result.geodataframe.geometry.touches(base_geometry)
    neighbors = result.geodataframe[neighbors_mask].copy()

    # Add distance to centroid for sorting
    base_centroid = base_geometry.centroid
    neighbors["distance_to_base"] = neighbors.geometry.centroid.distance(base_centroid)
    neighbors = neighbors.sort_values("distance_to_base")

    return neighbors


def aggregate_to_higher_geography(
    gdf: gpd.GeoDataFrame,
    from_level: GeographyLevel,
    to_level: GeographyLevel,
    value_columns: list[str],
    aggregation: str | dict = "sum",
) -> gpd.GeoDataFrame:
    """Aggregate data from a lower geography level to a higher one.

    Args:
        gdf: GeoDataFrame with lower-level geographies
        from_level: Current geography level
        to_level: Target geography level
        value_columns: Columns to aggregate
        aggregation: Aggregation method ('sum', 'mean', etc.) or dict

    Returns:
        GeoDataFrame aggregated to higher geography level
    """
    # Validate geography hierarchy
    hierarchy = {
        GeographyLevel.BLOCK_GROUP: 4,
        GeographyLevel.BLOCK_GROUP_DETAILED: 4,
        GeographyLevel.TRACT: 3,
        GeographyLevel.COUNTY: 2,
        GeographyLevel.STATE: 1,
    }

    if from_level not in hierarchy or to_level not in hierarchy:
        raise ValueError("Aggregation only supported for hierarchical geographies")

    if hierarchy[from_level] <= hierarchy[to_level]:
        raise ValueError(f"Cannot aggregate from {from_level.value} to {to_level.value}")

    # Extract higher-level GEOID from lower-level GEOID
    if to_level == GeographyLevel.STATE:
        gdf["parent_geoid"] = gdf["GEOID"].str[:2]
    elif to_level == GeographyLevel.COUNTY:
        gdf["parent_geoid"] = gdf["GEOID"].str[:5]
    elif to_level == GeographyLevel.TRACT:
        gdf["parent_geoid"] = gdf["GEOID"].str[:11]

    # Prepare aggregation
    if isinstance(aggregation, str):
        agg_dict = dict.fromkeys(value_columns, aggregation)
    else:
        agg_dict = aggregation

    # Always include geometry in aggregation
    agg_dict["geometry"] = "first"  # Will be replaced with dissolved geometry

    # Aggregate data
    aggregated = gdf.groupby("parent_geoid").agg(agg_dict).reset_index()
    aggregated.rename(columns={"parent_geoid": "GEOID"}, inplace=True)

    # Dissolve geometries
    dissolved = gdf.dissolve(by="parent_geoid", as_index=False)
    aggregated["geometry"] = dissolved["geometry"]

    # Convert back to GeoDataFrame
    result = gpd.GeoDataFrame(aggregated, crs=gdf.crs)

    return result


def calculate_geography_statistics(gdf: gpd.GeoDataFrame) -> pd.DataFrame:
    """Calculate statistics about the geographies in a GeoDataFrame.

    Args:
        gdf: GeoDataFrame with geometries

    Returns:
        DataFrame with statistics
    """
    stats = {
        "count": len(gdf),
        "total_area_km2": gdf.to_crs("EPSG:3857").geometry.area.sum() / 1_000_000,
        "mean_area_km2": gdf.to_crs("EPSG:3857").geometry.area.mean() / 1_000_000,
        "min_area_km2": gdf.to_crs("EPSG:3857").geometry.area.min() / 1_000_000,
        "max_area_km2": gdf.to_crs("EPSG:3857").geometry.area.max() / 1_000_000,
        "total_bounds": gdf.total_bounds,
    }

    # Add geography level statistics if available
    if "geography_level" in gdf.columns:
        level_counts = gdf["geography_level"].value_counts().to_dict()
        stats["geography_levels"] = level_counts

    return pd.DataFrame([stats])


def validate_geoid_format(geoid: str, geography_level: GeographyLevel) -> bool:
    """Validate that a GEOID is properly formatted for the geography level.

    Args:
        geoid: GEOID to validate
        geography_level: Expected geography level

    Returns:
        True if valid, False otherwise
    """
    expected_lengths = {
        GeographyLevel.STATE: 2,
        GeographyLevel.COUNTY: 5,
        GeographyLevel.TRACT: 11,
        GeographyLevel.BLOCK_GROUP: 12,
        GeographyLevel.BLOCK_GROUP_DETAILED: 12,
        GeographyLevel.ZCTA: 5,
    }

    if geography_level not in expected_lengths:
        return True  # No validation for other levels

    expected_length = expected_lengths[geography_level]

    # Check length
    if len(geoid) != expected_length:
        return False

    # Check if numeric (except for some special cases)
    if not geoid.isdigit():
        return False

    return True


def clip_geometries_to_boundary(
    gdf: gpd.GeoDataFrame,
    boundary: gpd.GeoDataFrame | gpd.GeoSeries,
    keep_all: bool = False,
) -> gpd.GeoDataFrame:
    """Clip geometries to a boundary.

    Args:
        gdf: GeoDataFrame to clip
        boundary: Boundary to clip to
        keep_all: If True, keep geometries that don't intersect

    Returns:
        Clipped GeoDataFrame
    """
    # Ensure same CRS
    if hasattr(boundary, "crs") and boundary.crs != gdf.crs:
        boundary = boundary.to_crs(gdf.crs)

    # Get boundary geometry
    if isinstance(boundary, gpd.GeoDataFrame):
        boundary_geom = boundary.unary_union
    else:
        boundary_geom = boundary.unary_union if len(boundary) > 1 else boundary.iloc[0]

    # Clip geometries
    if keep_all:
        # Keep all records, but clip geometries that intersect
        clipped = gdf.copy()
        intersects = gdf.geometry.intersects(boundary_geom)
        clipped.loc[intersects, "geometry"] = gdf.loc[intersects].intersection(boundary_geom)
    else:
        # Only keep geometries that intersect
        intersects = gdf.geometry.intersects(boundary_geom)
        clipped = gdf[intersects].copy()
        clipped["geometry"] = clipped.intersection(boundary_geom)

    return clipped
