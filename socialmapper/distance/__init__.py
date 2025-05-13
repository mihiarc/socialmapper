#!/usr/bin/env python3
"""
Module to calculate distances between POIs and block groups.
"""
import geopandas as gpd
from shapely.geometry import Point
from typing import Dict, List, Optional, Union
import pandas as pd
from socialmapper.progress import get_progress_bar
import logging
import json
import time

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

def preprocess_poi_data(pois):
    """
    Preprocess POI data to ensure coordinates are at the top level
    
    Args:
        pois: List of POI dictionaries
        
    Returns:
        List of POI dictionaries with coordinates at the top level
    """
    processed_pois = []
    
    for poi in pois:
        poi_copy = dict(poi)  # Create a copy to avoid modifying original
        
        # Check if coordinates are in properties
        if 'properties' in poi and 'lon' not in poi:
            props = poi['properties']
            if isinstance(props, dict):
                if 'lon' in props and 'lat' in props:
                    poi_copy['lon'] = props['lon']
                    poi_copy['lat'] = props['lat']
                elif 'longitude' in props and 'latitude' in props:
                    poi_copy['lon'] = props['longitude']
                    poi_copy['lat'] = props['latitude']
                elif 'lng' in props and 'lat' in props:
                    poi_copy['lon'] = props['lng']
                    poi_copy['lat'] = props['lat']
        
        # Check if coordinates are in geometry
        elif 'geometry' in poi and 'lon' not in poi and isinstance(poi['geometry'], Point):
            geom = poi['geometry']
            if hasattr(geom, 'x') and hasattr(geom, 'y'):
                poi_copy['lon'] = geom.x
                poi_copy['lat'] = geom.y
        
        processed_pois.append(poi_copy)
    
    return processed_pois

def add_travel_distances(
    block_groups_gdf: gpd.GeoDataFrame,
    poi_data: Union[Dict, List[Dict]],
    output_path: Optional[str] = None,
    verbose: bool = False
) -> gpd.GeoDataFrame:
    """
    Calculate and add travel distances from block groups to nearest POIs.
    
    Args:
        block_groups_gdf: GeoDataFrame with block group geometries
        poi_data: Dictionary with POI data or list of POIs
        output_path: Optional path (no longer used - kept for backwards compatibility)
        verbose: If True, print detailed debug information
        
    Returns:
        GeoDataFrame with travel distance information added
    """
    # Extract POIs from dictionary if needed
    pois = poi_data
    if isinstance(poi_data, dict) and 'pois' in poi_data:
        pois = poi_data['pois']
    if not isinstance(pois, list):
        pois = [pois]
    
    # Preprocess POIs to ensure coordinates are available
    pois = preprocess_poi_data(pois)
    
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
    
    # Calculate centroids properly by first projecting to a projected CRS for accuracy
    # then converting back to WGS84 for compatibility with POI coordinates
    if df.crs is None:
        # If no CRS is set, assume WGS84
        df.set_crs("EPSG:4326", inplace=True)
    
    # Project to Albers Equal Area, calculate centroids, then convert back to WGS84
    df_projected = df.to_crs("EPSG:5070")
    centroids_projected = df_projected.geometry.centroid
    centroids_gdf = gpd.GeoDataFrame(geometry=centroids_projected, crs="EPSG:5070")
    centroids_wgs84 = centroids_gdf.to_crs("EPSG:4326")
    
    # Store the centroids in WGS84
    df['centroid'] = centroids_wgs84.geometry
    
    # Convert POIs to Points
    poi_points = []
    for poi in pois:
        # Debug POI structure only if verbose
        if verbose and len(poi_points) == 0:  # Only print the first POI as an example
            get_progress_bar().write(f"POI example: {json.dumps(poi, default=str)[:100]}...")
        
        if 'lon' in poi and 'lat' in poi:
            poi_points.append(Point(poi['lon'], poi['lat']))
        elif 'longitude' in poi and 'latitude' in poi:
            poi_points.append(Point(poi['longitude'], poi['latitude']))
        elif 'lng' in poi and 'lat' in poi:
            poi_points.append(Point(poi['lng'], poi['lat']))
        elif 'geometry' in poi and hasattr(poi['geometry'], 'x') and hasattr(poi['geometry'], 'y'):
            poi_points.append(Point(poi['geometry'].x, poi['geometry'].y))
        elif 'coordinates' in poi:
            coords = poi['coordinates']
            if isinstance(coords, list) and len(coords) >= 2:
                poi_points.append(Point(coords[0], coords[1]))
        elif 'properties' in poi and isinstance(poi['properties'], dict):
            props = poi['properties']
            if 'lon' in props and 'lat' in props:
                poi_points.append(Point(props['lon'], props['lat']))
            elif 'longitude' in props and 'latitude' in props:
                poi_points.append(Point(props['longitude'], props['latitude']))
            elif 'lng' in props and 'lat' in props:
                poi_points.append(Point(props['lng'], props['lat']))
    
    if not poi_points:
        get_progress_bar().write("WARNING: No POI points available for distance calculation!")
        if verbose:
            get_progress_bar().write(f"POI data example: {pois[0] if pois else None}")
        # Set distances to NaN instead of inf
        df['travel_distance_km'] = float('nan')
        df['travel_distance_miles'] = float('nan')
    else:
        # Initialize progress tracking
        total_calculations = len(df) * len(poi_points)
        get_progress_bar().write(f"Calculating distances for {len(df)} block groups and {len(poi_points)} POIs...")
        
        # For each block group, find the closest POI and calculate distance
        distances_km = []
        start_time = time.time()
        last_update_time = start_time
        update_interval = 10  # Update progress every 10 seconds (reduced frequency)
        
        # Track progress
        completed = 0
        batch_size = max(1, len(df) // 5)  # Report progress after every 20% of calculations
        progress_threshold = batch_size
        
        for idx, row in df.iterrows():
            # Calculate distance to each POI and find the minimum
            min_distance = float('inf')
            
            try:
                centroid = row['centroid']
                # Debug centroid info only if verbose
                if verbose and idx == 0:  # Only print for the first block group
                    get_progress_bar().write(f"Example centroid: {centroid}")
                
                # Calculate distance to each POI
                for i, point in enumerate(poi_points):
                    try:
                        # Direct distance calculation using the calculate_distance function
                        distance = calculate_distance(point, centroid)
                        
                        # Debug info only if verbose
                        if verbose and idx == 0 and i == 0:
                            get_progress_bar().write(f"Debug - POI: {point}, Centroid: {centroid}, Distance: {distance} km")
                        
                        # Update min distance
                        if distance < min_distance:
                            min_distance = distance
                        
                        # Update progress count
                        completed += 1
                        
                    except Exception as e:
                        if verbose:
                            get_progress_bar().write(f"Error calculating distance: {e}")
                        continue
                
                # Report progress periodically but with reduced frequency
                current_time = time.time()
                if completed >= progress_threshold or (current_time - last_update_time) >= update_interval:
                    elapsed = current_time - start_time
                    percentage = (completed / total_calculations) * 100
                    if elapsed > 0:
                        rate = completed / elapsed
                        remaining = (total_calculations - completed) / rate if rate > 0 else 0
                        # Simplified progress message
                        get_progress_bar().write(f"Distance calculation: {percentage:.1f}% complete, ~{remaining:.1f}s remaining")
                    else:
                        get_progress_bar().write(f"Distance calculation: {percentage:.1f}% complete")
                    
                    # Update tracking variables
                    last_update_time = current_time
                    progress_threshold = completed + batch_size
                
                # If we still have infinity, something went wrong
                if min_distance == float('inf'):
                    if verbose:
                        get_progress_bar().write(f"Warning: Unable to calculate distance for block group {idx}")
                    min_distance = float('nan')  # Use NaN instead of inf
                
                distances_km.append(min_distance)
            except Exception as e:
                if verbose:
                    get_progress_bar().write(f"Error processing block group {idx}: {e}")
                distances_km.append(float('nan'))
        
        # Final progress update (always show this)
        total_time = time.time() - start_time
        get_progress_bar().write(f"Distance calculation completed in {total_time:.2f}s.")
        
        # Add both km and miles
        df['travel_distance_km'] = distances_km
        df['travel_distance_miles'] = [d * 0.621371 if not pd.isna(d) else float('nan') for d in distances_km]  # Convert km to miles
    
    return df 