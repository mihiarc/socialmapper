#!/usr/bin/env python3
"""
Module to calculate distances between POIs and block groups.
"""
import geopandas as gpd
from shapely.geometry import Point
from typing import Dict, List, Optional, Union
import pandas as pd
from socialmapper.progress import get_progress_bar

def calculate_distance(poi_point, block_group_centroid, crs="EPSG:5070"):
    """
    Calculate the distance between a POI and a block group centroid using Albers Equal Area projection.
    
    Args:
        poi_point: Point geometry of the POI
        block_group_centroid: Point geometry of the block group centroid
        crs: Projected CRS to use for distance calculation (default: EPSG:5070 - Albers Equal Area for US)
        
    Returns:
        Distance in kilometers
    """
    # Create GeoSeries for the two points
    points_gdf = gpd.GeoDataFrame(
        geometry=[poi_point, block_group_centroid],
        crs="EPSG:4326"  # Assuming points are in WGS84
    )
    
    # Project to Albers Equal Area
    points_gdf = points_gdf.to_crs(crs)
    
    # Calculate distance in meters and convert to kilometers
    distance_meters = points_gdf.iloc[0].geometry.distance(points_gdf.iloc[1].geometry)
    return distance_meters / 1000  # Convert to kilometers

def add_travel_distances(
    block_groups_gdf: gpd.GeoDataFrame,
    poi_data: Union[Dict, List[Dict]],
    output_path: Optional[str] = None
) -> gpd.GeoDataFrame:
    """
    Calculate and add travel distances from block groups to nearest POIs.
    
    Args:
        block_groups_gdf: GeoDataFrame with block group geometries
        poi_data: Dictionary with POI data or list of POIs
        output_path: Optional path to save the enhanced GeoDataFrame
        
    Returns:
        GeoDataFrame with travel distance information added
    """
    # Extract POIs from dictionary if needed
    pois = poi_data
    if isinstance(poi_data, dict) and 'pois' in poi_data:
        pois = poi_data['pois']
    if not isinstance(pois, list):
        pois = [pois]
    
    # Create a copy of the block groups data to avoid modifying the original
    df = block_groups_gdf.copy()
    
    # Add POI information
    poi_name = "unknown"
    poi_id = "unknown"
    travel_time_minutes = 15  # Default value
    
    # Try to extract the travel time and POI info from the first POI
    if pois and len(pois) > 0:
        first_poi = pois[0]
        poi_id = first_poi.get('id', poi_id)
        poi_name = first_poi.get('name', first_poi.get('tags', {}).get('name', poi_name))
        
        # Try to extract travel time from various possible sources
        if 'travel_time' in first_poi:
            travel_time_minutes = first_poi['travel_time']
        elif 'travel_time_minutes' in first_poi:
            travel_time_minutes = first_poi['travel_time_minutes']
        elif 'isochrone_minutes' in first_poi:
            travel_time_minutes = first_poi['isochrone_minutes']
    
    # Add POI information to the DataFrame
    df['poi_id'] = poi_id
    df['poi_name'] = poi_name
    df['travel_time_minutes'] = travel_time_minutes
    
    # Add average travel speed from isochrone calculation - standard value from the isochrone module
    # The default speed in the isochrone module is 50 km/h (31 mph) 
    df['avg_travel_speed_kmh'] = 50  # Default from isochrone.py
    df['avg_travel_speed_mph'] = 31  # Default from isochrone.py
    
    # Reproject to Albers Equal Area (EPSG:5070) for accurate centroid calculations
    df_projected = df.copy()
    if df_projected.crs is None:
        # If no CRS is set, assume WGS84
        df_projected.set_crs("EPSG:4326", inplace=True)
    
    # Reproject to a suitable projection for North America
    df_projected = df_projected.to_crs("EPSG:5070")
    
    # Calculate centroids of block groups in the projected CRS
    df['centroid'] = df_projected.geometry.centroid
    
    # Convert POIs to GeoDataFrame
    poi_points = []
    for poi in pois:
        if 'lon' in poi and 'lat' in poi:
            poi_points.append(Point(poi['lon'], poi['lat']))
    
    if poi_points:
        get_progress_bar().write("Calculating travel distances to POIs...")
        # For each block group, find the closest POI and calculate distance
        distances_km = []
        
        for _, row in df.iterrows():
            # Calculate distance to each POI and find the minimum
            min_distance = float('inf')
            for point in poi_points:
                distance = calculate_distance(point, row['centroid'])
                min_distance = min(min_distance, distance)
            distances_km.append(min_distance)
        
        # Add both km and miles
        df['travel_distance_km'] = distances_km
        df['travel_distance_miles'] = [d * 0.621371 for d in distances_km]  # Convert km to miles
    
    # Save enhanced GeoDataFrame if output path is provided
    if output_path:
        df.to_file(output_path, driver="GeoJSON")
        get_progress_bar().write(f"Saved block groups with travel distances to {output_path}")
    
    return df 