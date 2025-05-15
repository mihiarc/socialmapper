#!/usr/bin/env python3
"""
Module to fetch census data for block groups identified by isochrone analysis.
"""
import os
import pandas as pd
import geopandas as gpd
import requests
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
# Import the new progress bar utility
from socialmapper.progress import get_progress_bar
from tqdm import tqdm
from socialmapper.states import (
    normalize_state,
    normalize_state_list,
    StateFormat,
    is_fips_code,
    state_fips_to_name
)
from socialmapper.util import (
    census_code_to_name,
    normalize_census_variable,
    CENSUS_VARIABLE_MAPPING,
    get_readable_census_variables,
    get_census_api_key
)


def load_block_groups(geojson_path: Union[str, gpd.GeoDataFrame]) -> gpd.GeoDataFrame:
    """
    Load block groups from a GeoJSON file or directly from a GeoDataFrame.
    
    Args:
        geojson_path: Path to the GeoJSON file with block groups or a GeoDataFrame object
        
    Returns:
        GeoDataFrame containing block groups
    """
    try:
        if isinstance(geojson_path, gpd.GeoDataFrame):
            return geojson_path
        else:
            gdf = gpd.read_file(geojson_path)
            return gdf
    except Exception as e:
        # Prevent including the full DataFrame in the error message
        error_msg = str(e)
        if len(error_msg) > 500:
            error_msg = f"{error_msg[:200]}... (truncated error message)"
        raise ValueError(f"Error loading block groups file: {error_msg}")


def extract_block_group_ids(gdf: gpd.GeoDataFrame) -> Dict[str, List[str]]:
    """
    Extract block group IDs from a GeoDataFrame, grouped by state.
    
    Args:
        gdf: GeoDataFrame containing block groups
        
    Returns:
        Dictionary mapping state FIPS codes to lists of block group IDs
    """
    state_block_groups = {}
    
    get_progress_bar().write("Extracting block group IDs by state...")

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
                    get_progress_bar().write(f"Warning: Cannot standardize GEOID format: {geoid}")
        else:
            get_progress_bar().write(f"Warning: Invalid GEOID format: {geoid}")

    return state_block_groups


def get_state_name_from_fips(fips_code: str) -> str:
    """
    Get the state name from a FIPS code.
    
    Args:
        fips_code: State FIPS code (e.g., "06")
        
    Returns:
        State name or the FIPS code if not found
    """
    state_name = state_fips_to_name(fips_code)
    return state_name if state_name else fips_code


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
        api_key = get_census_api_key()
        if not api_key:
            raise ValueError("Census API key not found. Please set the 'CENSUS_API_KEY' environment variable or provide it as an argument.")
    
    # Create a copy of variables to avoid modifying the original list
    api_variables = []
    
    # Normalize variable names to Census API codes
    for var in variables:
        normalized_var = normalize_census_variable(var)
        api_variables.append(normalized_var)
    
    # Ensure 'NAME' is included in API variables if not already
    if 'NAME' not in api_variables:
        api_variables.append('NAME')
    
    # Validate variables
    invalid_vars = []
    for var in api_variables:
        if not isinstance(var, str):
            invalid_vars.append(f"{var} (type: {type(var)})")
    
    if invalid_vars:
        raise ValueError(f"Invalid variable types detected: {', '.join(invalid_vars)}. All variables must be strings.")
    
    # Base URL for Census API
    base_url = f'https://api.census.gov/data/{year}/{dataset}'
    
    # Verify the API URL with a test request
    test_url = f"{base_url}/variables.json"
    try:
        test_response = requests.get(test_url, params={'key': api_key})
        if test_response.status_code != 200:
            raise ValueError(f"Census API returned status code {test_response.status_code} for URL {test_url}")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Cannot connect to Census API: {str(e)}")
    
    # Initialize an empty list to store dataframes
    dfs = []
    
    # Loop over each state
    for state_code in get_progress_bar(state_fips_list, desc="Fetching census data by state", unit="state"):
        state_name = get_state_name_from_fips(state_code)
        
        # Define the parameters for this state
        params = {
            'get': ','.join(api_variables),
            'for': 'block group:*',
            'in': f'state:{state_code} county:* tract:*',
            'key': api_key
        }
        
        try:
            # Make the API request
            response = requests.get(base_url, params=params)
            
            # Check if the request was successful
            if response.status_code == 200:
                # Parse the JSON response
                data = response.json()
                
                # Validate response structure
                if not data or len(data) < 2:
                    continue
                
                # Convert to DataFrame
                df = pd.DataFrame(data[1:], columns=data[0])
                
                # Append the dataframe to the list
                dfs.append(df)
                
                get_progress_bar().write(f"  - Retrieved data for {len(df)} block groups")
                
            else:
                get_progress_bar().write(f"Error fetching data for {state_name}: Status {response.status_code}")
        
        except Exception as e:
            get_progress_bar().write(f"Exception while fetching data for {state_name}: {str(e)}")
    
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
    get_progress_bar().write(f"Merging census data ({len(census_df)} records) with block groups ({len(result_gdf)} records)...")
    result_gdf = result_gdf.merge(census_df, on='GEOID', how='left')
    
    return result_gdf


def get_census_data_for_block_groups(
    geojson_path: Union[str, gpd.GeoDataFrame],
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
        geojson_path: Path to GeoJSON file with block groups or a GeoDataFrame object
        variables: List of Census API variable codes or human-readable names (e.g., 'total_population', 'B01003_001E')
                  Human-readable names will be automatically converted to Census API codes
        output_path: Path to save the result (no longer used - kept for backwards compatibility)
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
    # Load block groups - this can now handle both string paths and GeoDataFrames
    if isinstance(geojson_path, gpd.GeoDataFrame):
        get_progress_bar().write("Using provided GeoDataFrame for block groups...")
    else:
        get_progress_bar().write(f"Loading block groups from {geojson_path}...")
    
    block_groups_gdf = load_block_groups(geojson_path)
    
    if len(block_groups_gdf) == 0:
        raise ValueError("No block groups found in input data")
    
    # Extract block group IDs by state
    block_groups_by_state = extract_block_group_ids(block_groups_gdf)
    
    if not block_groups_by_state:
        raise ValueError("Could not extract valid block group IDs from block groups data")
    
    # Get the list of states we need to query
    state_fips_list = list(block_groups_by_state.keys())
    
    # Get state names for better logging
    state_names = [get_state_name_from_fips(fips) for fips in state_fips_list]
    get_progress_bar().write(f"Found block groups in these states: {', '.join(state_names)}")
    
    # Log variable normalization for better UX
    get_progress_bar().write(f"Input variables: {', '.join(variables)}")
    normalized_variables = [normalize_census_variable(var) for var in variables]
    for var, norm_var in zip(variables, normalized_variables):
        if var != norm_var:
            get_progress_bar().write(f"  - Will convert '{var}' to Census API code '{norm_var}'")
    
    # Display readable names for census variables using the utility function
    readable_vars = get_readable_census_variables(normalized_variables)
    
    # Fetch census data for all block groups in the relevant states
    get_progress_bar().write(f"Fetching census data for: {', '.join(readable_vars)}")
    
    # Print API key status (masked for security)
    if api_key:
        masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
        get_progress_bar().write(f"Using provided API key: {masked_key}")
    else:
        env_key = os.getenv('CENSUS_API_KEY')
        if env_key:
            masked_key = env_key[:4] + "..." + env_key[-4:] if len(env_key) > 8 else "***"
            get_progress_bar().write(f"Using environment API key: {masked_key}")
        else:
            get_progress_bar().write("WARNING: No Census API key provided!")
    
    # Fetch census data
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
    
    # Filter to only the block groups we identified in the isochrone
    census_data = all_state_census_data[all_state_census_data['GEOID'].isin(needed_geoids)]
    get_progress_bar().write(f"Found {len(census_data)} of {len(needed_geoids)} block groups in census data")
    
    # Merge census data with block group geometries
    result_gdf = merge_census_data(
        block_groups_gdf,
        census_data,
        variable_mapping
    )
    
    # Convert numeric columns
    get_progress_bar().write("Converting numeric columns...")
    for var in variables:
        if var != 'NAME' and var in result_gdf.columns:
            result_gdf[var] = pd.to_numeric(result_gdf[var], errors='coerce')
    
    # Check if NAME column is present and not null
    if 'NAME' in result_gdf.columns:
        null_names = result_gdf['NAME'].isnull().sum()
        if null_names > 0:
            result_gdf['NAME'] = result_gdf['NAME'].fillna("Block Group").astype(str)
    
    # Set attributes on GeoDataFrame for visualization
    variables_for_viz = [var for var in normalized_variables if var not in exclude_from_visualization]
    result_gdf.attrs['variables_for_visualization'] = variables_for_viz
    
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
        api_key = get_census_api_key()
        if not api_key:
            raise ValueError("Census API key not found. Please set the 'CENSUS_API_KEY' environment variable or provide it as an argument.")
    
    # Base URL for Census API variables
    url = f'https://api.census.gov/data/{year}/{dataset}/variables.json'
    
    try:
        # Make the API request
        get_progress_bar().write(f"Fetching variable metadata for {dataset} {year}...")
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
    
    # Prepare mapping description for help text
    variable_examples = ", ".join([f"'{name}' -> '{code}'" for name, code in list(CENSUS_VARIABLE_MAPPING.items())[:3]])
    mapping_help = f"Available human-readable names include: {variable_examples}, etc."
    
    parser = argparse.ArgumentParser(description="Fetch census data for block groups identified by isochrone analysis")
    parser.add_argument("geojson", help="Path to GeoJSON file with block groups")
    parser.add_argument("--variables", required=True, nargs="+", 
                       help=f"Census API variable codes or human-readable names. {mapping_help}")
    parser.add_argument("--output", help="Output GeoJSON file path (defaults to output/census/[filename]_census.geojson)")
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
    get_progress_bar().write(f"Added census data for {len(result)} block groups") 