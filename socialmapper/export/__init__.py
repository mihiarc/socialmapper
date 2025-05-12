#!/usr/bin/env python3
"""
Module to export census data to CSV format with travel distances.
"""
import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import numpy as np
from typing import Dict, List, Optional, Union
from pathlib import Path
from scipy.spatial import cKDTree

# Import census variable mapping to get friendly names
from socialmapper.util import CENSUS_VARIABLE_MAPPING

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

def calculate_distances_vectorized(centroids, poi_points, crs="EPSG:5070"):
    """
    Calculate distances between block group centroids and POIs using vectorized operations.
    
    Args:
        centroids: List or array of block group centroid points
        poi_points: List or array of POI points
        crs: Projected CRS to use for distance calculation
        
    Returns:
        Array of minimum distances from each centroid to the nearest POI in kilometers
    """
    if not centroids or not poi_points:
        return []
    
    # Create GeoDataFrames for centroids and POIs
    centroids_gdf = gpd.GeoDataFrame(geometry=centroids, crs="EPSG:4326")
    pois_gdf = gpd.GeoDataFrame(geometry=poi_points, crs="EPSG:4326")
    
    # Project to specified CRS for accurate distance calculation
    centroids_gdf = centroids_gdf.to_crs(crs)
    pois_gdf = pois_gdf.to_crs(crs)
    
    # Extract coordinates for KDTree
    centroids_coords = np.array([(p.x, p.y) for p in centroids_gdf.geometry])
    pois_coords = np.array([(p.x, p.y) for p in pois_gdf.geometry])
    
    # Check for NaN or infinite values and remove them
    valid_centroid_mask = np.isfinite(centroids_coords).all(axis=1)
    valid_poi_mask = np.isfinite(pois_coords).all(axis=1)
    
    if not np.all(valid_centroid_mask):
        print(f"Warning: Found {np.sum(~valid_centroid_mask)} non-finite values in centroids. These will be excluded.")
        centroids_coords = centroids_coords[valid_centroid_mask]
    
    if not np.all(valid_poi_mask):
        print(f"Warning: Found {np.sum(~valid_poi_mask)} non-finite values in POIs. These will be excluded.")
        pois_coords = pois_coords[valid_poi_mask]
    
    # Make sure we still have valid points
    if len(centroids_coords) == 0 or len(pois_coords) == 0:
        print("Warning: No valid coordinates left after filtering out non-finite values.")
        return np.array([float('inf')] * len(centroids))
    
    # Build KDTree for efficient nearest neighbor queries
    tree = cKDTree(pois_coords)
    
    # Find distances to nearest POI for each centroid
    distances_m, _ = tree.query(centroids_coords, k=1)
    
    # If we filtered some centroids, we need to reconstruct the full array
    if not np.all(valid_centroid_mask):
        full_distances = np.array([float('inf')] * len(valid_centroid_mask))
        full_distances[valid_centroid_mask] = distances_m
        distances_m = full_distances
    
    # Convert to kilometers
    return distances_m / 1000

def export_census_data_to_csv(
    census_data: gpd.GeoDataFrame,
    poi_data: Union[Dict, List[Dict]],
    output_path: Optional[str] = None,
    base_filename: Optional[str] = None,
    output_dir: str = "output/csv",
    optimize_memory: bool = True,
    chunk_size: Optional[int] = None,
    mock_distance: bool = False
) -> str:
    """
    Export census data to CSV format with block group identifiers and travel distances.
    
    Args:
        census_data: GeoDataFrame with census data for block groups
        poi_data: Dictionary with POI data or list of POIs
        output_path: Full path to save the CSV file
        base_filename: Base filename to use if output_path is not provided
        output_dir: Directory to save the CSV if output_path is not provided
        optimize_memory: Whether to optimize memory usage with appropriate column types
        chunk_size: Number of rows to write at a time (None means write all at once)
        mock_distance: Whether to use mock distance values (for testing only)
        
    Returns:
        Path to the saved CSV file
    """
    # Extract POIs from dictionary if needed
    pois = poi_data
    if isinstance(poi_data, dict) and 'pois' in poi_data:
        pois = poi_data['pois']
    if not isinstance(pois, list):
        pois = [pois]
    
    # Create a copy of the census data to avoid modifying the original
    df = census_data.copy()
    
    # Create a new dataframe for the CSV with required columns
    csv_data = pd.DataFrame()
    
    # Extract components from the GEOID if available
    if 'GEOID' in df.columns:
        csv_data['census_block_group'] = df['GEOID']
        
        # Extract tract and block group components
        if df['GEOID'].iloc[0] and len(df['GEOID'].iloc[0]) >= 12:
            csv_data['tract'] = df['GEOID'].str[5:11]
            csv_data['block_group'] = df['GEOID'].str[11:12]

    # Add county and state FIPS codes
    if 'STATE' in df.columns:
        csv_data['state_fips'] = df['STATE'].str.zfill(2)

    if 'COUNTY' in df.columns:
        if 'STATE' in df.columns:
            csv_data['county_fips'] = df['STATE'].str.zfill(2) + df['COUNTY'].str.zfill(3)
        else:
            csv_data['county_fips'] = df['COUNTY'].str.zfill(3)
    
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
    
    # Add POI information to all rows
    csv_data['poi_id'] = poi_id
    csv_data['poi_name'] = poi_name
    csv_data['travel_time_minutes'] = travel_time_minutes
    
    # Add average travel speed from isochrone calculation - standard value from the isochrone module
    # The default speed in the isochrone module is 50 km/h (31 mph) 
    csv_data['avg_travel_speed_kmh'] = 50  # Default from isochrone.py
    csv_data['avg_travel_speed_mph'] = 31  # Default from isochrone.py
    
    # Add intersection area percentage
    if 'pct' in df.columns:
        csv_data['area_within_travel_time_pct'] = df['pct']
    elif 'percent_overlap' in df.columns:
        csv_data['area_within_travel_time_pct'] = df['percent_overlap'] * 100
    elif 'overlap_pct' in df.columns:
        csv_data['area_within_travel_time_pct'] = df['overlap_pct']
    elif 'intersection_area_pct' in df.columns:
        csv_data['area_within_travel_time_pct'] = df['intersection_area_pct']
    
    # Add census variables with friendly names but in lowercase with underscores
    # Create a mapping from census variable code to human-readable name
    code_to_name = {}
    for name, code in CENSUS_VARIABLE_MAPPING.items():
        code_to_name[code] = name
    
    # Add census variables
    exclude_cols = ['geometry', 'GEOID', 'STATE', 'COUNTY', 'TRACT', 'BLKGRP', 'NAME', 
                    'pct', 'percent_overlap', 'overlap_pct', 'intersection_area_pct', 'centroid']
    
    for col in df.columns:
        if col not in exclude_cols:
            # Convert census variable code to human-readable name if possible
            if col.startswith('B') and '_' in col and col.endswith('E'):
                # This looks like a census variable code
                column_name = code_to_name.get(col, col).lower()
            else:
                # Not a census variable code, use as is but convert to lowercase with underscores
                column_name = col.lower().replace(' ', '_')
            
            # Convert to numeric if possible, otherwise keep as is
            try:
                csv_data[column_name] = pd.to_numeric(df[col])
            except (ValueError, TypeError):
                csv_data[column_name] = df[col]
    
    # Calculate travel distances or use mock values for testing
    if mock_distance:
        # Use fixed mock values for testing
        num_rows = len(csv_data)
        csv_data['travel_distance_km'] = np.linspace(1.0, 10.0, num_rows)
        csv_data['travel_distance_miles'] = csv_data['travel_distance_km'] * 0.621371  # Convert km to miles
    else:
        # Reproject to Albers Equal Area (EPSG:5070) for accurate centroid calculations
        df_projected = df.copy()
        if df_projected.crs is None:
            # If no CRS is set, assume WGS84
            df_projected.set_crs("EPSG:4326", inplace=True)
        
        # Reproject to a suitable projection for North America
        df_projected = df_projected.to_crs("EPSG:5070")
        
        # Calculate centroids of block groups in the projected CRS
        if 'centroid' not in df.columns:
            df['centroid'] = df_projected.geometry.centroid
        
        # Convert POIs to GeoDataFrame
        poi_points = []
        for poi in pois:
            if 'lon' in poi and 'lat' in poi:
                poi_points.append(Point(poi['lon'], poi['lat']))
        
        if poi_points:
            # Use vectorized distance calculation for improved performance
            distances_km = calculate_distances_vectorized(df['centroid'].tolist(), poi_points)
            
            # Add both km and miles
            csv_data['travel_distance_km'] = distances_km
            csv_data['travel_distance_miles'] = [d * 0.621371 for d in distances_km]  # Convert km to miles
    
    # Reorder columns in the preferred order, explicitly exclude 'state' and 'county'
    preferred_order = [
        'census_block_group', 'state_fips', 'county_fips', 'tract', 'block_group',
        'poi_id', 'poi_name', 'travel_time_minutes', 'avg_travel_speed_kmh', 'avg_travel_speed_mph',
        'travel_distance_km', 'travel_distance_miles', 'area_within_travel_time_pct'
    ]
    
    # Add remaining columns, but specifically exclude 'state' and 'county'
    excluded_columns = ['state', 'county', 'State', 'County']
    all_columns = preferred_order + [col for col in csv_data.columns 
                                     if col not in preferred_order and col not in excluded_columns]
    
    # Ensure 'state' and 'county' columns are not included, even if they were created
    for col in excluded_columns:
        if col in csv_data.columns:
            csv_data = csv_data.drop(columns=[col])
    
    # Reorder columns (only include those that exist)
    existing_columns = [col for col in all_columns if col in csv_data.columns]
    csv_data = csv_data[existing_columns]
    
    # Final check before saving - absolutely ensure no state or county column
    for col in csv_data.columns:
        if col.lower() in ['state', 'county']:
            csv_data = csv_data.drop(columns=[col])
    
    # Optimize memory usage by converting columns to appropriate types
    if optimize_memory and len(csv_data) > 0:
        # Columns that should be categorical (typically have few unique values)
        categorical_candidates = ['state_fips', 'county_fips', 'block_group', 'poi_id', 'poi_name']
        
        # Convert appropriate string columns to categorical
        for col in categorical_candidates:
            if col in csv_data.columns and csv_data[col].dtype == 'object':
                n_unique = csv_data[col].nunique()
                n_total = len(csv_data)
                
                # Only convert to categorical if it would save memory
                # (categorical is beneficial when n_unique is much smaller than n_total)
                if n_unique / n_total < 0.5:  # Rule of thumb: convert if less than 50% unique values
                    csv_data[col] = csv_data[col].astype('category')
        
        # Downcast numeric columns to the smallest possible type
        for col in csv_data.columns:
            if pd.api.types.is_integer_dtype(csv_data[col].dtype):
                csv_data[col] = pd.to_numeric(csv_data[col], downcast='integer')
            elif pd.api.types.is_float_dtype(csv_data[col].dtype):
                csv_data[col] = pd.to_numeric(csv_data[col], downcast='float')
    
    # Create output directory if it doesn't exist
    if output_path is None:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Generate output path based on base_filename
        if base_filename is None:
            base_filename = "census_data"
        
        output_path = os.path.join(output_dir, f"{base_filename}_export.csv")
    else:
        # Ensure directory for output_path exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to CSV, using chunked writing for large datasets if requested
    if chunk_size is not None and len(csv_data) > chunk_size:
        # Calculate the total number of chunks
        total_chunks = (len(csv_data) + chunk_size - 1) // chunk_size  # Ceiling division
        
        # Write the first chunk with headers
        csv_data.iloc[:chunk_size].to_csv(output_path, index=False)
        
        # Append the rest without headers
        for i in range(1, total_chunks):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, len(csv_data))
            csv_data.iloc[start_idx:end_idx].to_csv(
                output_path, 
                mode='a', 
                header=False, 
                index=False
            )
    else:
        # Write all at once
        csv_data.to_csv(output_path, index=False)
    
    return output_path 