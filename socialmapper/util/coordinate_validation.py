#!/usr/bin/env python3
"""Coordinate Validation Module for SocialMapper.

This module provides Pydantic-based validation for all coordinate inputs
to ensure data quality and prevent issues with PyProj transformations.
"""

from typing import Any, Dict, List, Union

import geopandas as gpd
from pydantic import BaseModel, Field, ValidationError, field_validator
from shapely.geometry import Point

from ..constants import (
    MAX_LATITUDE,
    MAX_LONGITUDE,
    MIN_CLUSTER_POINTS,
    MIN_GEOJSON_COORDINATES,
    MIN_LATITUDE,
    MIN_LONGITUDE,
)
from ..ui.console import get_logger

logger = get_logger(__name__)


class Coordinate(BaseModel):
    """Validates a single coordinate pair (latitude, longitude)."""

    lat: float
    lon: float

    @field_validator("lat")
    @classmethod
    def validate_latitude(cls, v):
        """Validate latitude is within valid range."""
        if not isinstance(v, int | float):
            raise ValueError("Latitude must be a number")
        if not MIN_LATITUDE <= v <= MAX_LATITUDE:
            raise ValueError("Latitude must be between -90 and 90 degrees")
        return float(v)

    @field_validator("lon")
    @classmethod
    def validate_longitude(cls, v):
        """Validate longitude is within valid range."""
        if not isinstance(v, int | float):
            raise ValueError("Longitude must be a number")
        if not MIN_LONGITUDE <= v <= MAX_LONGITUDE:
            raise ValueError("Longitude must be between -180 and 180 degrees")
        return float(v)


class StrictCoordinate(BaseModel):
    """Stricter coordinate validation for high-precision use cases."""

    lat: float
    lon: float

    @field_validator("lat")
    @classmethod
    def validate_latitude(cls, v):
        """Validate latitude is within valid range with strict typing."""
        if not isinstance(v, int | float):
            raise ValueError("Latitude must be a number")
        if not MIN_LATITUDE <= v <= MAX_LATITUDE:
            raise ValueError("Latitude must be between -90 and 90 degrees")
        return float(v)

    @field_validator("lon")
    @classmethod
    def validate_longitude(cls, v):
        """Validate longitude is within valid range with strict typing."""
        if not isinstance(v, int | float):
            raise ValueError("Longitude must be a number")
        if not MIN_LONGITUDE <= v <= MAX_LONGITUDE:
            raise ValueError("Longitude must be between -180 and 180 degrees")
        return float(v)


class CoordinateCluster(BaseModel):
    """Validates a cluster of coordinates for distance calculations."""

    points: List[Coordinate]

    @field_validator("points")
    @classmethod
    def validate_minimum_points(cls, v):
        """Validate cluster has minimum number of points for meaningful analysis."""
        if len(v) < MIN_CLUSTER_POINTS:
            raise ValueError(
                "Coordinate clusters must contain at least 2 points for meaningful distance calculations"
            )
        return v


class ValidationResult(BaseModel):
    """Result of coordinate validation process."""

    valid_coordinates: list[Coordinate]
    invalid_coordinates: list[dict[str, Any]]
    validation_errors: list[str]
    total_input: int
    total_valid: int
    total_invalid: int

    @property
    def success_rate(self) -> float:
        """Calculate the percentage of successfully validated coordinates."""
        if self.total_input == 0:
            return 0.0
        return (self.total_valid / self.total_input) * 100


def validate_coordinate_point(
    lat: float, lon: float, context: str = "unknown"
) -> Coordinate | None:
    """Validate a single coordinate point using Pydantic.

    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
        context: Context for error reporting

    Returns:
        Coordinate if valid, None if invalid
    """
    try:
        return Coordinate(lat=lat, lon=lon)
    except ValidationError as e:
        logger.warning(f"Invalid coordinate in {context}: lat={lat}, lon={lon}. Errors: {e}")
        return None


def validate_poi_coordinates(poi_data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> List[Coordinate]:
    """Validate POI coordinate data and return validated coordinates.
    
    Args:
        poi_data: POI data in various formats (single POI dict or list of POIs)
        
    Returns:
        List of validated Coordinate objects
        
    Raises:
        ValueError: If coordinate data is invalid or missing
    """
    if not poi_data:
        return []

    validated_coords = []

    # Handle single POI or list of POIs
    pois = poi_data if isinstance(poi_data, list) else [poi_data]

    for i, poi in enumerate(pois):
        try:
            # Multiple coordinate format possibilities
            coord = None

            # Format 1: Direct lat/lon fields
            if "lat" in poi and "lon" in poi:
                coord = Coordinate(lat=poi["lat"], lon=poi["lon"])

            # Format 2: latitude/longitude fields
            elif "latitude" in poi and "longitude" in poi:
                coord = Coordinate(lat=poi["latitude"], lon=poi["longitude"])

            # Format 3: GeoJSON coordinates array [lon, lat]
            elif (
                "coordinates" in poi
                and isinstance(poi["coordinates"], list)
                and len(poi["coordinates"]) >= MIN_GEOJSON_COORDINATES
            ):
                lon, lat = poi["coordinates"][0], poi["coordinates"][1]  # GeoJSON format
                coord = Coordinate(lat=lat, lon=lon)

            # Format 4: Nested geometry object
            elif "geometry" in poi and isinstance(poi["geometry"], dict):
                geom = poi["geometry"]
                if (
                    "coordinates" in geom
                    and isinstance(geom["coordinates"], list)
                    and len(geom["coordinates"]) >= MIN_GEOJSON_COORDINATES
                ):
                    lon, lat = geom["coordinates"][0], geom["coordinates"][1]
                    coord = Coordinate(lat=lat, lon=lon)

            if coord:
                validated_coords.append(coord)
            else:
                logger.warning(f"POI {i}: No valid coordinates found in format: {list(poi.keys())}")

        except Exception as e:
            logger.warning(f"POI {i}: Coordinate validation failed: {e}")
            continue

    return validated_coords


def validate_coordinate_cluster(coordinates: List[Dict[str, Any]], cluster_id: str = None) -> CoordinateCluster:
    """Validate a cluster of coordinates.
    
    Args:
        coordinates: List of coordinate dictionaries
        cluster_id: Optional identifier for the cluster (for logging)
        
    Returns:
        Validated CoordinateCluster object
        
    Raises:
        ValueError: If cluster validation fails
    """
    validated_points = []

    for i, coord_dict in enumerate(coordinates):
        try:
            # Try different coordinate formats
            if "lat" in coord_dict and "lon" in coord_dict:
                coord_point = Coordinate(lat=coord_dict["lat"], lon=coord_dict["lon"])
            elif "latitude" in coord_dict and "longitude" in coord_dict:
                coord_point = Coordinate(lat=coord_dict["latitude"], lon=coord_dict["longitude"])
            else:
                logger.warning(f"Coordinate {i}: Unknown format: {list(coord_dict.keys())}")
                continue

            validated_points.append(coord_point)

        except Exception as e:
            logger.warning(f"Coordinate {i}: Validation failed: {e}")
            continue

        if len(validated_points) < MIN_CLUSTER_POINTS:
            logger.warning(
                f"Cluster {cluster_id}: Insufficient valid points ({len(validated_points)}) for clustering"
            )

    return CoordinateCluster(points=validated_points)


def validate_geodataframe_coordinates(gdf: gpd.GeoDataFrame) -> ValidationResult:
    """Validate coordinates in a GeoDataFrame.

    Args:
        gdf: GeoDataFrame with geometry column

    Returns:
        ValidationResult with validation summary
    """
    valid_coordinates = []
    invalid_coordinates = []
    validation_errors = []

    for idx, row in gdf.iterrows():
        try:
            geom = row.geometry
            if geom is None or geom.is_empty:
                validation_errors.append(f"Row {idx}: Empty or null geometry")
                invalid_coordinates.append({"index": idx, "error": "Empty or null geometry"})
                continue

            if geom.geom_type != "Point":
                validation_errors.append(f"Row {idx}: Geometry is not a Point ({geom.geom_type})")
                invalid_coordinates.append(
                    {"index": idx, "error": f"Geometry is not a Point ({geom.geom_type})"}
                )
                continue

            # Validate the point coordinates
            coord_point = validate_coordinate_point(geom.y, geom.x, f"gdf_row_{idx}")
            if coord_point:
                valid_coordinates.append(coord_point)
            else:
                invalid_coordinates.append({"index": idx, "error": "Invalid coordinate values"})

        except Exception as e:
            error_msg = f"Row {idx}: Unexpected error: {e!s}"
            validation_errors.append(error_msg)
            invalid_coordinates.append({"index": idx, "error": str(e)})

    return ValidationResult(
        valid_coordinates=valid_coordinates,
        invalid_coordinates=invalid_coordinates,
        validation_errors=validation_errors,
        total_input=len(gdf),
        total_valid=len(valid_coordinates),
        total_invalid=len(invalid_coordinates),
    )


def safe_coordinate_transform(
    points: list[Point], target_crs: str, source_crs: str = "EPSG:4326"
) -> gpd.GeoDataFrame | None:
    """Safely transform coordinates with validation.

    Args:
        points: List of Shapely Point objects
        target_crs: Target CRS string
        source_crs: Source CRS string (default: EPSG:4326)

    Returns:
        Transformed GeoDataFrame or None if transformation fails
    """
    if len(points) == 0:
        logger.warning("No points provided for coordinate transformation")
        return None

    # Note: Single point transformations are actually fine for distance calculations
    # We can calculate distances from many centroids to 1 POI

    try:
        # Create GeoDataFrame with multiple points
        gdf = gpd.GeoDataFrame(geometry=points, crs=source_crs)

        # Perform transformation
        transformed_gdf = gdf.to_crs(target_crs)

        return transformed_gdf

    except Exception as e:
        logger.error(f"Coordinate transformation failed: {e}")
        return None


def prevalidate_for_pyproj(
    data: list[dict] | gpd.GeoDataFrame | list[Point],
) -> tuple[bool, list[str]]:
    """Pre-validate data before it reaches PyProj to prevent warnings and errors.

    Args:
        data: Input data in various formats

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    try:
        if isinstance(data, list):
            if len(data) == 0:
                errors.append("Empty data list provided")
                return False, errors

            # Note: Single POI is valid - we can calculate distances from many centroids to 1 POI
            # Only reject if we have zero POIs

            # Check if it's a list of dictionaries (POI data)
            if isinstance(data[0], dict):
                validation_result = validate_poi_coordinates(data)
                if len(validation_result) < 1:
                    errors.append(
                        f"No valid coordinates found: {len(validation_result)} valid out of {len(data)}"
                    )
                    errors.extend([f"Invalid coordinate: {coord}" for coord in validation_result])
                    return False, errors

            # Check if it's a list of Points
            elif isinstance(data[0], Point):
                for i, point in enumerate(data):
                    coord_point = validate_coordinate_point(point.y, point.x, f"point_{i}")
                    if not coord_point:
                        errors.append(f"Invalid point {i}: ({point.x}, {point.y})")

        elif isinstance(data, gpd.GeoDataFrame):
            validation_result = validate_geodataframe_coordinates(data)
            if validation_result.total_valid < 1:
                errors.append(
                    f"No valid coordinates found in GeoDataFrame: {validation_result.total_valid} valid out of {validation_result.total_input}"
                )
                errors.extend(validation_result.validation_errors)
                return False, errors

        else:
            errors.append(f"Unsupported data type: {type(data)}")
            return False, errors

        return len(errors) == 0, errors

    except Exception as e:
        errors.append(f"Validation error: {e!s}")
        return False, errors
