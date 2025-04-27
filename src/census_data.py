#!/usr/bin/env python3
"""
Module to fetch census data for block groups identified by isochrone analysis.
"""
import os
import pandas as pd
import geopandas as gpd
import requests
from typing import List, Dict, Any, Optional
from pathlib import Path
from tqdm import tqdm
from src.util import state_fips_to_abbreviation, STATE_NAMES_TO_ABBR


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
    
    tqdm.write("Extracting block group IDs by state...")
    for _, row in tqdm(gdf.iterrows(), desc="Processing block groups", unit="block", total=len(gdf)):
        state = row.get('STATE')
        geoid = row.get('GEOID')
        
        if not state or not geoid:
            continue
        
        # Ensure state code is padded to 2 digits with leading zeros if needed
        state = state.zfill(2) if isinstance(state, str) else f"{state:02d}"
            
        if state not in state_block_groups:
            state_block_groups[state] = []
            
        # Ensure GEOID is properly formatted
        if isinstance(geoid, str):
            # Standardize to 12-character GEOID format used by Census API
            # Format should be STATE(2) + COUNTY(3) + TRACT(6) + BLKGRP(1)
            if len(geoid) >= 11:
                # Some GEOIDs might be missing leading zeros or have different formats
                # Extract the last 10 digits (county + tract + block group) and prepend state
                if len(geoid) > 12:  
                    # If longer than standard, take the rightmost 10 digits and prepend state
                    geoid = state + geoid[-10:]
                elif len(geoid) < 12:
                    # If shorter than standard, ensure proper padding
                    county_tract_bg = geoid[len(state):]
                    geoid = state + county_tract_bg.zfill(10)
                
                # Now GEOID should be exactly 12 characters
                state_block_groups[state].append(geoid)
            else:
                # Try to construct from separate fields if available
                county = row.get('COUNTY', '')
                tract = row.get('TRACT', '')
                blkgrp = row.get('BLKGRP', '')
                
                if county and tract and blkgrp:
                    # Construct GEOID from components
                    constructed_geoid = (
                        state + 
                        county.zfill(3) + 
                        tract.zfill(6) + 
                        blkgrp
                    )
                    state_block_groups[state].append(constructed_geoid)
                else:
                    tqdm.write(f"Warning: Cannot standardize GEOID format: {geoid}")
        else:
            tqdm.write(f"Warning: Invalid GEOID format: {geoid}")

    return state_block_groups


def get_state_name_from_fips(fips_code: str) -> str:
    """
    Get the state name from a FIPS code.
    
    Args:
        fips_code: State FIPS code (e.g., "06")
        
    Returns:
        State name or the FIPS code if not found
    """
    # Get state abbreviation from FIPS code
    state_abbr = state_fips_to_abbreviation(fips_code)
    
    if not state_abbr:
        return fips_code
    
    # Reverse lookup in STATE_NAMES_TO_ABBR dictionary
    for state_name, abbr in STATE_NAMES_TO_ABBR.items():
        if abbr == state_abbr:
            return state_name
    
    # If no match found, return the abbreviation
    return state_abbr


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
    
    # Create a copy of variables to avoid modifying the original list
    api_variables = variables.copy()
    
    # Ensure 'NAME' is included in API variables if not already
    if 'NAME' not in api_variables:
        api_variables.append('NAME')
    
    # Base URL for Census API
    base_url = f'https://api.census.gov/data/{year}/{dataset}'
    
    # Initialize an empty list to store dataframes
    dfs = []
    
    # Loop over each state
    for state_code in tqdm(state_fips_list, desc="Fetching census data by state", unit="state"):
        state_name = get_state_name_from_fips(state_code)
        tqdm.write(f"Fetching data for {state_name} ({state_code})...")
        
        # Define the parameters for this state
        params = {
            'get': ','.join(api_variables),
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
            
            tqdm.write(f"  - Retrieved data for {len(df)} block groups")
            
        else:
            tqdm.write(f"Error fetching data for {state_name} ({state_code}): {response.status_code}")
            tqdm.write(response.text)
    
    # Combine all data
    if not dfs:
        raise ValueError("No census data retrieved. Please check your API key and the census variables you're requesting.")
        
    final_df = pd.concat(dfs, ignore_index=True)
    
    # Create a GEOID column to match with GeoJSON - ensure proper formatting with leading zeros
    # Census API returns components as:
    # state, county, tract, block group
    final_df['GEOID'] = (
        final_df['state'].str.zfill(2) + 
        final_df['county'].str.zfill(3) + 
        final_df['tract'].str.zfill(6) + 
        final_df['block group']
    )
    
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
    
    # If GEOIDs might have format inconsistencies, try to standardize them
    # First, check if we need to standardize GEOIDs in our GeoDataFrame
    if 'GEOID' in result_gdf.columns:
        # Standardize GEOIDs in the GeoDataFrame if needed
        if result_gdf['GEOID'].str.len().min() != result_gdf['GEOID'].str.len().max():
            tqdm.write("Standardizing variable-length GEOIDs in GeoDataFrame")
            
            # We need to work with individual components
            # Assume we can construct from STATE, COUNTY, TRACT, BLKGRP columns
            if all(col in result_gdf.columns for col in ['STATE', 'COUNTY', 'TRACT', 'BLKGRP']):
                result_gdf['GEOID'] = (
                    result_gdf['STATE'].astype(str).str.zfill(2) + 
                    result_gdf['COUNTY'].astype(str).str.zfill(3) + 
                    result_gdf['TRACT'].astype(str).str.zfill(6) + 
                    result_gdf['BLKGRP'].astype(str)
                )

    # Merge the census data with the GeoDataFrame
    tqdm.write(f"Merging census data ({len(census_df)} records) with block groups ({len(result_gdf)} records)...")
    result_gdf = result_gdf.merge(census_df, on='GEOID', how='left')
    
    return result_gdf


def get_census_data_for_block_groups(
    geojson_path: str,
    variables: List[str],
    output_path: Optional[str] = None,
    variable_mapping: Optional[Dict[str, str]] = None,
    year: int = 2021,
    dataset: str = 'acs/acs5',
    api_key: Optional[str] = None,
    exclude_from_visualization: List[str] = ['NAME']
) -> gpd.GeoDataFrame:
    """
    Main function to fetch census data for block groups identified by isochrone analysis.
    
    Args:
        geojson_path: Path to GeoJSON file with block groups
        variables: List of Census API variable codes to retrieve
        output_path: Path to save the result (defaults to output/census_data/[filename]_census.geojson)
        variable_mapping: Optional dictionary mapping Census API variable codes to readable column names
        year: Census year
        dataset: Census dataset
        api_key: Census API key (optional if set as environment variable)
        exclude_from_visualization: Variables to exclude from visualization (default: ['NAME'])
        
    Returns:
        GeoDataFrame with block group geometries and census data. 
        Note: The returned data will include all requested variables including those in exclude_from_visualization,
        but the 'variables_for_visualization' attribute will be added to indicate which ones are meant for maps.
    """
    # Load block groups
    tqdm.write(f"Loading block groups from {geojson_path}...")
    block_groups_gdf = load_block_groups(geojson_path)
    
    if len(block_groups_gdf) == 0:
        raise ValueError(f"No block groups found in {geojson_path}")
    
    # Extract block group IDs by state
    block_groups_by_state = extract_block_group_ids(block_groups_gdf)
    
    if not block_groups_by_state:
        raise ValueError(f"Could not extract valid block group IDs from {geojson_path}")
    
    # Get the list of states we need to query
    state_fips_list = list(block_groups_by_state.keys())
    
    # Get state names for better logging
    state_names = [get_state_name_from_fips(fips) for fips in state_fips_list]
    tqdm.write(f"Found block groups in these states: {', '.join(state_names)}")
    
    # Fetch census data for all block groups in the relevant states
    try:
        all_state_census_data = fetch_census_data_for_states(
            state_fips_list,
            variables,
            year=year,
            dataset=dataset,
            api_key=api_key
        )
        
        # Extract just the GEOIDs we need from all the block groups
        needed_geoids = []
        for state_ids in block_groups_by_state.values():
            needed_geoids.extend(state_ids)
        
        # Print the total count and a few needed GEOIDs for diagnostic purposes
        tqdm.write(f"Looking for {len(needed_geoids)} specific block groups in the census data")
        
        # Filter to only the block groups we identified in the isochrone
        census_data = all_state_census_data[all_state_census_data['GEOID'].isin(needed_geoids)]
        tqdm.write(f"Found {len(census_data)} of {len(needed_geoids)} block groups in census data")
        
    except Exception as e:
        # If we couldn't fetch data, create a minimal dataframe with GEOID to allow saving the file
        tqdm.write(f"Error fetching census data: {e}")
        tqdm.write("Creating a placeholder dataframe with just GEOID and empty values for the requested variables")
        
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
    for var in tqdm(variables, desc="Converting numeric columns", unit="column"):
        if var != 'NAME' and var in result_gdf.columns:
            result_gdf[var] = pd.to_numeric(result_gdf[var], errors='coerce')
    
    # Generate default output path if none provided
    if output_path is None:
        # Extract filename from input path without extension
        input_name = Path(geojson_path).stem
        output_path = Path(f"output/census_data/{input_name}_census.geojson")
    else:
        output_path = Path(output_path)
    
    # Ensure output directory exists
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save to file
    tqdm.write(f"Saving result with census data to {output_path}...")
    result_gdf.to_file(output_path, driver="GeoJSON")
    tqdm.write(f"Saved result with census data to {output_path}")
    
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
        tqdm.write(f"Fetching variable metadata for {dataset} {year}...")
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
    parser.add_argument("--output", help="Output GeoJSON file path (defaults to output/census_data/[filename]_census.geojson)")
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
    tqdm.write(f"Added census data for {len(result)} block groups") 