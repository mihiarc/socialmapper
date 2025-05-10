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

def export_census_data_to_csv(
    census_data: gpd.GeoDataFrame,
    poi_data: Union[Dict, List[Dict]],
    output_path: Optional[str] = None,
    base_filename: Optional[str] = None,
    output_dir: str = "output/csv"
) -> str:
    """
    Export census data to CSV format with block group identifiers and travel distances.
    
    Args:
        census_data: GeoDataFrame with census data for block groups
        poi_data: Dictionary with POI data or list of POIs
        output_path: Full path to save the CSV file
        base_filename: Base filename to use if output_path is not provided
        output_dir: Directory to save the CSV if output_path is not provided
        
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
    
    # Add identifier columns
    if 'GEOID' in df.columns:
        csv_data['census_block_group'] = df['GEOID']
    
    # Add county FIPS (from GEOID or COUNTY)
    if 'GEOID' in df.columns and df['GEOID'].iloc[0] is not None and len(df['GEOID'].iloc[0]) >= 5:
        # Extract county FIPS from GEOID (first 5 characters)
        csv_data['county_fips'] = df['GEOID'].str[:5]
    elif 'COUNTY' in df.columns and 'STATE' in df.columns:
        # Combine STATE and COUNTY
        csv_data['county_fips'] = df['STATE'].str.zfill(2) + df['COUNTY'].str.zfill(3)
    
    # Add state FIPS
    if 'STATE' in df.columns:
        csv_data['state_fips'] = df['STATE'].str.zfill(2)
    elif 'GEOID' in df.columns and df['GEOID'].iloc[0] is not None and len(df['GEOID'].iloc[0]) >= 2:
        # Extract state FIPS from GEOID (first 2 characters)
        csv_data['state_fips'] = df['GEOID'].str[:2]
    
    # Add all census variables (exclude geometry and identifier columns)
    exclude_cols = ['geometry', 'GEOID', 'STATE', 'COUNTY', 'TRACT', 'BLKGRP', 'NAME']
    for col in df.columns:
        if col not in exclude_cols:
            # Convert to numeric if possible, otherwise keep as is
            try:
                csv_data[col] = pd.to_numeric(df[col])
            except (ValueError, TypeError):
                csv_data[col] = df[col]
    
    # Calculate travel distances
    # Calculate centroids of block groups
    df['centroid'] = df.geometry.centroid
    
    # Convert POIs to GeoDataFrame
    poi_points = []
    for poi in pois:
        if 'lon' in poi and 'lat' in poi:
            poi_points.append(Point(poi['lon'], poi['lat']))
    
    if poi_points:
        # For each block group, find the closest POI and calculate distance
        distances = []
        
        for _, row in df.iterrows():
            # Calculate distance to each POI and find the minimum
            min_distance = float('inf')
            for point in poi_points:
                distance = calculate_distance(point, row['centroid'])
                min_distance = min(min_distance, distance)
            distances.append(min_distance)
        
        csv_data['travel_distance_km'] = distances
    
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
    
    # Save to CSV
    csv_data.to_csv(output_path, index=False)
    
    return output_path 