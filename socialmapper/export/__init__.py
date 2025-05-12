#!/usr/bin/env python3
"""
Module to export census data to CSV or Parquet format.
"""
import os
import pandas as pd
import geopandas as gpd
from typing import Dict, List, Optional, Union
from pathlib import Path

# Import census variable mapping to get friendly names
from socialmapper.util import CENSUS_VARIABLE_MAPPING

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
    
    # Add intersection area percentage
    if 'pct' in df.columns:
        csv_data['area_within_travel_time_pct'] = df['pct']
    elif 'percent_overlap' in df.columns:
        csv_data['area_within_travel_time_pct'] = df['percent_overlap'] * 100
    elif 'overlap_pct' in df.columns:
        csv_data['area_within_travel_time_pct'] = df['overlap_pct']
    elif 'intersection_area_pct' in df.columns:
        csv_data['area_within_travel_time_pct'] = df['intersection_area_pct']
    
    # Copy travel information if already available in the input DataFrame
    travel_columns = [
        'poi_id', 'poi_name', 'travel_time_minutes', 
        'avg_travel_speed_kmh', 'avg_travel_speed_mph',
        'travel_distance_km', 'travel_distance_miles'
    ]
    
    for col in travel_columns:
        if col in df.columns:
            csv_data[col] = df[col]
    
    # Add census variables with friendly names but in lowercase with underscores
    # Create a mapping from census variable code to human-readable name
    code_to_name = {}
    for name, code in CENSUS_VARIABLE_MAPPING.items():
        code_to_name[code] = name
    
    # Add census variables
    exclude_cols = ['geometry', 'GEOID', 'STATE', 'COUNTY', 'TRACT', 'BLKGRP', 'NAME', 
                    'pct', 'percent_overlap', 'overlap_pct', 'intersection_area_pct', 'centroid']
    exclude_cols.extend(travel_columns)  # Don't duplicate travel columns
    
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