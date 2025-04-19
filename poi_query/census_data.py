#!/usr/bin/env python3
"""
Module to fetch census data for block groups identified by isochrone analysis.
"""
import os
import json
import pandas as pd
import geopandas as gpd
import requests
from typing import List, Dict, Any, Optional, Union
from pathlib import Path


def load_block_groups(geojson_path: str) -> gpd.GeoDataFrame:
    """
    Load block groups from a GeoJSON file produced by the blockgroups module.
    
    Args:
        geojson_path: Path to the GeoJSON file with block groups
        
    Returns:
        GeoDataFrame containing block groups
    """
    try:
        gdf = gpd.read_file(geojson_path)
        return gdf
    except Exception as e:
        raise ValueError(f"Error loading block groups file: {e}")


def extract_block_group_ids(gdf: gpd.GeoDataFrame) -> Dict[str, List[str]]:
    """
    Extract block group IDs from a GeoDataFrame, grouped by state.
    
    Args:
        gdf: GeoDataFrame containing block groups
        
    Returns:
        Dictionary mapping state FIPS codes to lists of block group IDs
    """
    state_block_groups = {}
    
    for _, row in gdf.iterrows():
        state = row.get('STATE')
        geoid = row.get('GEOID')
        
        if not state or not geoid:
            continue
        
        # Ensure state code is padded to 2 digits with leading zeros if needed
        state = state.zfill(2) if isinstance(state, str) else f"{state:02d}"
            
        if state not in state_block_groups:
            state_block_groups[state] = []
            
        # Ensure GEOID is properly formatted
        if isinstance(geoid, str) and len(geoid) >= 11:
            # Already in string format, ensure we have the full 12-character GEOID
            if len(geoid) == 11:  # Some GEOIDs might be missing leading zeros
                geoid = state + geoid[2:]  # Replace state portion to ensure consistency
            state_block_groups[state].append(geoid)
        else:
            print(f"Warning: Invalid GEOID format: {geoid}")
    
    # Print some diagnostics
    for state, geoids in state_block_groups.items():
        if geoids:
            print(f"State {state}: {len(geoids)} block groups, example GEOID: {geoids[0]}")
    
    return state_block_groups


def fetch_census_data_for_states(
    state_fips_list: List[str],
    variables: List[str],
    year: int = 2021,
    dataset: str = 'acs/acs5',
    api_key: Optional[str] = None
) -> pd.DataFrame:
    """
    Fetch census data for all block groups in specified states.
    
    Args:
        state_fips_list: List of state FIPS codes
        variables: List of Census API variable codes to retrieve
        year: Census year
        dataset: Census dataset
        api_key: Census API key (optional if set as environment variable)
        
    Returns:
        DataFrame with census data for all block groups in the specified states
    """
    if not api_key:
        api_key = os.getenv('CENSUS_API_KEY')
        if not api_key:
            raise ValueError("Census API key not found. Please set the 'CENSUS_API_KEY' environment variable or provide it as an argument.")
    
    # Ensure 'NAME' is included in variables if not already
    if 'NAME' not in variables:
        variables.append('NAME')
    
    # Base URL for Census API
    base_url = f'https://api.census.gov/data/{year}/{dataset}'
    
    # Initialize an empty list to store dataframes
    dfs = []
    
    # Loop over each state
    for state_code in state_fips_list:
        print(f"Fetching data for state {state_code}...")
        
        # Define the parameters for this state - following the pattern from 03_get_census_blockgroups_data.py
        params = {
            'get': ','.join(variables),
            'for': 'block group:*',
            'in': f'state:{state_code} county:* tract:*',
            'key': api_key
        }
        
        # Make the API request
        response = requests.get(base_url, params=params)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            
            # Convert to DataFrame
            df = pd.DataFrame(data[1:], columns=data[0])
            
            # Append the dataframe to the list
            dfs.append(df)
            
            print(f"  - Retrieved data for {len(df)} block groups")
            
        else:
            print(f"Error fetching data for state {state_code}: {response.status_code}")
            print(response.text)
    
    # Combine all data
    if not dfs:
        raise ValueError("No census data retrieved. Please check your API key and the census variables you're requesting.")
        
    final_df = pd.concat(dfs, ignore_index=True)
    
    # Create a GEOID column to match with GeoJSON - ensure proper formatting with leading zeros
    final_df['GEOID'] = (
        final_df['state'].str.zfill(2) + 
        final_df['county'].str.zfill(3) + 
        final_df['tract'].str.zfill(6) + 
        final_df['block group']
    )
    
    print(f"Successfully retrieved data for {len(final_df)} total block groups")
    return final_df


def merge_census_data(
    gdf: gpd.GeoDataFrame,
    census_df: pd.DataFrame,
    variable_mapping: Optional[Dict[str, str]] = None
) -> gpd.GeoDataFrame:
    """
    Merge census data with block group GeoDataFrame.
    
    Args:
        gdf: GeoDataFrame containing block group geometries
        census_df: DataFrame with census data
        variable_mapping: Optional dictionary mapping Census API variable codes to readable column names
        
    Returns:
        GeoDataFrame with census data merged in
    """
    # Make a copy to avoid modifying the original
    result_gdf = gdf.copy()
    
    # Rename census variables if mapping is provided
    if variable_mapping:
        census_df = census_df.rename(columns=variable_mapping)
    
    # Merge the census data with the GeoDataFrame
    result_gdf = result_gdf.merge(census_df, on='GEOID', how='left')
    
    # Check for missing matches - use 'NAME' which is always included
    # If NAME isn't found, try to use any column from census_df other than GEOID
    check_column = 'NAME'
    if check_column not in result_gdf.columns and len(census_df.columns) > 1:
        for col in census_df.columns:
            if col != 'GEOID' and col in result_gdf.columns:
                check_column = col
                break
    
    if check_column in result_gdf.columns:
        missing_count = result_gdf[check_column].isna().sum()
        if missing_count > 0:
            print(f"Warning: {missing_count} out of {len(result_gdf)} block groups have no census data.")
    
    return result_gdf


def get_census_data_for_block_groups(
    geojson_path: str,
    variables: List[str],
    output_path: Optional[str] = None,
    variable_mapping: Optional[Dict[str, str]] = None,
    year: int = 2021,
    dataset: str = 'acs/acs5',
    api_key: Optional[str] = None
) -> gpd.GeoDataFrame:
    """
    Main function to fetch census data for block groups identified by isochrone analysis.
    
    Args:
        geojson_path: Path to GeoJSON file with block groups
        variables: List of Census API variable codes to retrieve
        output_path: Optional path to save the result GeoJSON
        variable_mapping: Optional dictionary mapping Census API variable codes to readable column names
        year: Census year
        dataset: Census dataset
        api_key: Census API key (optional if set as environment variable)
        
    Returns:
        GeoDataFrame with block group geometries and census data
    """
    # Load block groups
    block_groups_gdf = load_block_groups(geojson_path)
    
    if len(block_groups_gdf) == 0:
        raise ValueError(f"No block groups found in {geojson_path}")
    
    # Print the available columns to help with debugging
    print(f"Columns in block_groups GeoJSON: {block_groups_gdf.columns.tolist()}")
    
    # Check if there are any GEOID values for diagnostics
    if 'GEOID' in block_groups_gdf.columns:
        sample_geoids = block_groups_gdf['GEOID'].head(3).tolist()
        print(f"Sample GEOIDs from file: {sample_geoids}")
    
    # Extract block group IDs by state
    block_groups_by_state = extract_block_group_ids(block_groups_gdf)
    
    if not block_groups_by_state:
        raise ValueError(f"Could not extract valid block group IDs from {geojson_path}")
    
    # Get the list of states we need to query
    state_fips_list = list(block_groups_by_state.keys())
    print(f"Found block groups in these states: {', '.join(state_fips_list)}")
    
    # Fetch census data for all block groups in the relevant states
    try:
        all_state_census_data = fetch_census_data_for_states(
            state_fips_list,
            variables,
            year=year,
            dataset=dataset,
            api_key=api_key
        )
        
        # Print a few example GEOIDs from the census data for comparison
        sample_census_geoids = all_state_census_data['GEOID'].head(3).tolist()
        print(f"Sample GEOIDs from census API: {sample_census_geoids}")
        
        # Extract just the GEOIDs we need from all the block groups
        needed_geoids = []
        for state_ids in block_groups_by_state.values():
            needed_geoids.extend(state_ids)
        
        # Print the total count and a few needed GEOIDs for diagnostic purposes
        print(f"Looking for {len(needed_geoids)} specific block groups in the census data")
        if needed_geoids:
            print(f"Sample needed GEOIDs: {needed_geoids[:3]}")
        
        # Filter to only the block groups we identified in the isochrone
        census_data = all_state_census_data[all_state_census_data['GEOID'].isin(needed_geoids)]
        
        # If we got zero matches, try to diagnose the issue
        if len(census_data) == 0 and len(all_state_census_data) > 0:
            print("WARNING: Zero matches found. This could be due to GEOID format differences.")
            
            # Try a more flexible matching approach
            matched_data = []
            for needed_id in needed_geoids:
                # Try matching just the digits, ignoring leading zeros
                for census_id in all_state_census_data['GEOID']:
                    if needed_id.lstrip('0') == census_id.lstrip('0'):
                        matched_row = all_state_census_data[all_state_census_data['GEOID'] == census_id].copy()
                        matched_row['GEOID'] = needed_id  # Use the exact GEOID from our data
                        matched_data.append(matched_row)
                        break
            
            if matched_data:
                census_data = pd.concat(matched_data, ignore_index=True)
                print(f"After flexible matching: found {len(census_data)} matches")
        
        print(f"Filtered from {len(all_state_census_data)} total block groups to {len(census_data)} within the isochrone")
        
    except Exception as e:
        # If we couldn't fetch data, create a minimal dataframe with GEOID to allow saving the file
        print(f"Error fetching census data: {e}")
        print("Creating a placeholder dataframe with just GEOID and empty values for the requested variables")
        
        # Gather all block group IDs
        all_ids = []
        for state_ids in block_groups_by_state.values():
            all_ids.extend(state_ids)
            
        placeholder_data = {'GEOID': all_ids}
        for var in variables:
            if var != 'NAME':
                placeholder_data[var] = [None] * len(all_ids)
        placeholder_data['NAME'] = [None] * len(all_ids)
        
        census_data = pd.DataFrame(placeholder_data)
    
    # Merge census data with block group geometries
    result_gdf = merge_census_data(
        block_groups_gdf,
        census_data,
        variable_mapping
    )
    
    # Convert numeric columns
    for var in variables:
        if var != 'NAME' and var in result_gdf.columns:
            result_gdf[var] = pd.to_numeric(result_gdf[var], errors='coerce')
    
    # Save to file if output path is provided
    if output_path:
        result_gdf.to_file(output_path, driver="GeoJSON")
        print(f"Saved result with census data to {output_path}")
    
    return result_gdf


def get_variable_metadata(
    year: int = 2021,
    dataset: str = 'acs/acs5',
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get metadata about available census variables.
    
    Args:
        year: Census year
        dataset: Census dataset
        api_key: Census API key (optional if set as environment variable)
        
    Returns:
        Dictionary with variable metadata
    """
    if not api_key:
        api_key = os.getenv('CENSUS_API_KEY')
        if not api_key:
            raise ValueError("Census API key not found. Please set the 'CENSUS_API_KEY' environment variable or provide it as an argument.")
    
    # Base URL for Census API variables
    url = f'https://api.census.gov/data/{year}/{dataset}/variables.json'
    
    try:
        # Make the API request
        response = requests.get(url, params={'key': api_key})
        
        # Check if the request was successful
        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError(f"Error fetching variable metadata: {response.status_code} - {response.text}")
    except Exception as e:
        raise ValueError(f"Error connecting to Census API: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch census data for block groups identified by isochrone analysis")
    parser.add_argument("geojson", help="Path to GeoJSON file with block groups")
    parser.add_argument("--variables", required=True, nargs="+", help="Census API variable codes")
    parser.add_argument("--output", help="Output GeoJSON file path")
    parser.add_argument("--year", type=int, default=2021, help="Census year")
    parser.add_argument("--dataset", default="acs/acs5", help="Census dataset")
    parser.add_argument("--api-key", help="Census API key (optional if set as environment variable)")
    
    args = parser.parse_args()
    
    result = get_census_data_for_block_groups(
        geojson_path=args.geojson,
        variables=args.variables,
        output_path=args.output,
        year=args.year,
        dataset=args.dataset,
        api_key=args.api_key
    )
    
    # Print summary
    print(f"Added census data for {len(result)} block groups") 