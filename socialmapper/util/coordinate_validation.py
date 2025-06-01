#!/usr/bin/env python3
"""
Coordinate Validation Module for SocialMapper.

This module provides Pydantic-based validation for all coordinate inputs
to ensure data quality and prevent issues with PyProj transformations.
"""

import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from pydantic import BaseModel, Field, validator, ValidationError
from shapely.geometry import Point
import geopandas as gpd
import pandas as pd

logger = logging.getLogger(__name__)


class CoordinatePoint(BaseModel):
    """
    Pydantic model for validating individual coordinate points.
    """
    lat: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    lon: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    
    @validator('lat')
    def validate_latitude(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError("Latitude must be a number")
        if not -90 <= v <= 90:
            raise ValueError("Latitude must be between -90 and 90 degrees")
        return float(v)
    
    @validator('lon')
    def validate_longitude(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError("Longitude must be a number")
        if not -180 <= v <= 180:
            raise ValueError("Longitude must be between -180 and 180 degrees")
        return float(v)
    
    def to_point(self) -> Point:
        """Convert to Shapely Point."""
        return Point(self.lon, self.lat)
    
    def to_tuple(self) -> Tuple[float, float]:
        """Convert to (lon, lat) tuple."""
        return (self.lon, self.lat)


class POICoordinate(BaseModel):
    """
    Pydantic model for validating POI coordinates with metadata.
    """
    id: Optional[Union[str, int]] = None
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    name: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None
    
    @validator('lat')
    def validate_latitude(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError("Latitude must be a number")
        if not -90 <= v <= 90:
            raise ValueError("Latitude must be between -90 and 90 degrees")
        return float(v)
    
    @validator('lon')
    def validate_longitude(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError("Longitude must be a number")
        if not -180 <= v <= 180:
            raise ValueError("Longitude must be between -180 and 180 degrees")
        return float(v)
    
    def to_point(self) -> Point:
        """Convert to Shapely Point."""
        return Point(self.lon, self.lat)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format expected by the rest of the system."""
        result = {
            'lat': self.lat,
            'lon': self.lon
        }
        if self.id is not None:
            result['id'] = self.id
        if self.name is not None:
            result['name'] = self.name
        if self.tags is not None:
            result['tags'] = self.tags
        return result


class CoordinateCluster(BaseModel):
    """
    Pydantic model for validating coordinate clusters.
    """
    points: List[CoordinatePoint] = Field(..., min_items=2, description="At least 2 points required for clustering")
    cluster_id: Optional[Union[str, int]] = None
    
    @validator('points')
    def validate_minimum_points(cls, v):
        if len(v) < 2:
            raise ValueError("Coordinate clusters must contain at least 2 points for meaningful distance calculations")
        return v
    
    def to_points_list(self) -> List[Point]:
        """Convert to list of Shapely Points."""
        return [point.to_point() for point in self.points]
    
    def get_centroid(self) -> CoordinatePoint:
        """Calculate the centroid of the cluster."""
        avg_lat = sum(p.lat for p in self.points) / len(self.points)
        avg_lon = sum(p.lon for p in self.points) / len(self.points)
        return CoordinatePoint(lat=avg_lat, lon=avg_lon)


class ValidationResult(BaseModel):
    """
    Result of coordinate validation process.
    """
    valid_coordinates: List[Union[CoordinatePoint, POICoordinate]]
    invalid_coordinates: List[Dict[str, Any]]
    validation_errors: List[str]
    total_input: int
    total_valid: int
    total_invalid: int
    
    @property
    def success_rate(self) -> float:
        """Calculate the percentage of successfully validated coordinates."""
        if self.total_input == 0:
            return 0.0
        return (self.total_valid / self.total_input) * 100


def validate_coordinate_point(lat: float, lon: float, context: str = "unknown") -> Optional[CoordinatePoint]:
    """
    Validate a single coordinate point using Pydantic.
    
    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
        context: Context for error reporting
        
    Returns:
        CoordinatePoint if valid, None if invalid
    """
    try:
        return CoordinatePoint(lat=lat, lon=lon)
    except ValidationError as e:
        logger.warning(f"Invalid coordinate in {context}: lat={lat}, lon={lon}. Errors: {e}")
        return None


def validate_poi_coordinates(poi_data: List[Dict[str, Any]]) -> ValidationResult:
    """
    Validate a list of POI coordinates using Pydantic.
    
    Args:
        poi_data: List of POI dictionaries
        
    Returns:
        ValidationResult with valid and invalid coordinates
    """
    valid_coordinates = []
    invalid_coordinates = []
    validation_errors = []
    
    for i, poi in enumerate(poi_data):
        try:
            # Try to extract coordinates from various possible formats
            lat = None
            lon = None
            
            # Direct lat/lon fields
            if 'lat' in poi and 'lon' in poi:
                lat, lon = poi['lat'], poi['lon']
            elif 'latitude' in poi and 'longitude' in poi:
                lat, lon = poi['latitude'], poi['longitude']
            elif 'lat' in poi and 'lng' in poi:
                lat, lon = poi['lat'], poi['lng']
            elif 'geometry' in poi and hasattr(poi['geometry'], 'x') and hasattr(poi['geometry'], 'y'):
                lat, lon = poi['geometry'].y, poi['geometry'].x
            elif 'coordinates' in poi and isinstance(poi['coordinates'], list) and len(poi['coordinates']) >= 2:
                lon, lat = poi['coordinates'][0], poi['coordinates'][1]  # GeoJSON format
            else:
                validation_errors.append(f"POI {i}: No valid coordinate fields found")
                invalid_coordinates.append({
                    'index': i,
                    'data': poi,
                    'error': 'No valid coordinate fields found'
                })
                continue
            
            # Validate using Pydantic
            validated_poi = POICoordinate(
                id=poi.get('id', i),
                lat=lat,
                lon=lon,
                name=poi.get('name'),
                tags=poi.get('tags')
            )
            valid_coordinates.append(validated_poi)
            
        except ValidationError as e:
            error_msg = f"POI {i}: {str(e)}"
            validation_errors.append(error_msg)
            invalid_coordinates.append({
                'index': i,
                'data': poi,
                'error': str(e)
            })
            logger.warning(error_msg)
        except Exception as e:
            error_msg = f"POI {i}: Unexpected error during validation: {str(e)}"
            validation_errors.append(error_msg)
            invalid_coordinates.append({
                'index': i,
                'data': poi,
                'error': str(e)
            })
            logger.error(error_msg)
    
    return ValidationResult(
        valid_coordinates=valid_coordinates,
        invalid_coordinates=invalid_coordinates,
        validation_errors=validation_errors,
        total_input=len(poi_data),
        total_valid=len(valid_coordinates),
        total_invalid=len(invalid_coordinates)
    )


def validate_coordinate_cluster(points: List[Dict[str, Any]], cluster_id: Optional[Union[str, int]] = None) -> Optional[CoordinateCluster]:
    """
    Validate a cluster of coordinates.
    
    Args:
        points: List of coordinate dictionaries
        cluster_id: Optional cluster identifier
        
    Returns:
        CoordinateCluster if valid, None if invalid
    """
    try:
        # Validate individual points first
        validated_points = []
        for point in points:
            coord_point = validate_coordinate_point(
                point.get('lat'), 
                point.get('lon'), 
                f"cluster_{cluster_id}"
            )
            if coord_point:
                validated_points.append(coord_point)
        
        if len(validated_points) < 2:
            logger.warning(f"Cluster {cluster_id}: Insufficient valid points ({len(validated_points)}) for clustering")
            return None
        
        return CoordinateCluster(points=validated_points, cluster_id=cluster_id)
        
    except ValidationError as e:
        logger.warning(f"Cluster {cluster_id} validation failed: {e}")
        return None


def validate_geodataframe_coordinates(gdf: gpd.GeoDataFrame) -> ValidationResult:
    """
    Validate coordinates in a GeoDataFrame.
    
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
                invalid_coordinates.append({
                    'index': idx,
                    'error': 'Empty or null geometry'
                })
                continue
            
            if geom.geom_type != 'Point':
                validation_errors.append(f"Row {idx}: Geometry is not a Point ({geom.geom_type})")
                invalid_coordinates.append({
                    'index': idx,
                    'error': f'Geometry is not a Point ({geom.geom_type})'
                })
                continue
            
            # Validate the point coordinates
            coord_point = validate_coordinate_point(geom.y, geom.x, f"gdf_row_{idx}")
            if coord_point:
                valid_coordinates.append(coord_point)
            else:
                invalid_coordinates.append({
                    'index': idx,
                    'error': 'Invalid coordinate values'
                })
                
        except Exception as e:
            error_msg = f"Row {idx}: Unexpected error: {str(e)}"
            validation_errors.append(error_msg)
            invalid_coordinates.append({
                'index': idx,
                'error': str(e)
            })
    
    return ValidationResult(
        valid_coordinates=valid_coordinates,
        invalid_coordinates=invalid_coordinates,
        validation_errors=validation_errors,
        total_input=len(gdf),
        total_valid=len(valid_coordinates),
        total_invalid=len(invalid_coordinates)
    )


def safe_coordinate_transform(points: List[Point], target_crs: str, source_crs: str = "EPSG:4326") -> Optional[gpd.GeoDataFrame]:
    """
    Safely transform coordinates with validation.
    
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
    
    if len(points) == 1:
        logger.warning("Single point transformations are not supported for distance calculations")
        return None
    
    try:
        # Create GeoDataFrame with multiple points
        gdf = gpd.GeoDataFrame(geometry=points, crs=source_crs)
        
        # Perform transformation
        transformed_gdf = gdf.to_crs(target_crs)
        
        return transformed_gdf
        
    except Exception as e:
        logger.error(f"Coordinate transformation failed: {e}")
        return None


def prevalidate_for_pyproj(data: Union[List[Dict], gpd.GeoDataFrame, List[Point]]) -> Tuple[bool, List[str]]:
    """
    Pre-validate data before it reaches PyProj to prevent warnings and errors.
    
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
            
            if len(data) == 1:
                errors.append("Single point data is not supported for distance calculations")
                return False, errors
            
            # Check if it's a list of dictionaries (POI data)
            if isinstance(data[0], dict):
                validation_result = validate_poi_coordinates(data)
                if validation_result.total_valid < 2:
                    errors.append(f"Insufficient valid coordinates: {validation_result.total_valid} valid out of {validation_result.total_input}")
                    errors.extend(validation_result.validation_errors)
                    return False, errors
            
            # Check if it's a list of Points
            elif isinstance(data[0], Point):
                for i, point in enumerate(data):
                    coord_point = validate_coordinate_point(point.y, point.x, f"point_{i}")
                    if not coord_point:
                        errors.append(f"Invalid point {i}: ({point.x}, {point.y})")
        
        elif isinstance(data, gpd.GeoDataFrame):
            validation_result = validate_geodataframe_coordinates(data)
            if validation_result.total_valid < 2:
                errors.append(f"Insufficient valid coordinates in GeoDataFrame: {validation_result.total_valid} valid out of {validation_result.total_input}")
                errors.extend(validation_result.validation_errors)
                return False, errors
        
        else:
            errors.append(f"Unsupported data type: {type(data)}")
            return False, errors
        
        return len(errors) == 0, errors
        
    except Exception as e:
        errors.append(f"Validation error: {str(e)}")
        return False, errors 