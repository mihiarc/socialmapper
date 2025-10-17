#!/usr/bin/env python3
"""Data preparation utilities for export operations.

This module contains common data preparation functions used across different export formats.
"""

import logging

import geopandas as gpd
import pandas as pd

from ..constants import FULL_BLOCK_GROUP_GEOID_LENGTH
from .base import DataPrepConfig

logger = logging.getLogger(__name__)


def extract_geoid_components(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract tract and block group components from GEOID.

    Parses census GEOID strings to extract tract and block group
    identifiers as separate columns for geographic analysis.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with GEOID column containing census identifiers.

    Returns
    -------
    pd.DataFrame
        DataFrame with added tract and block_group columns.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({'GEOID': ['370630001001']})
    >>> result = extract_geoid_components(df)
    >>> 'tract' in result.columns
    True
    """
    if "GEOID" not in df.columns or df["GEOID"].empty:
        return df

    try:
        # Ensure GEOID is string type
        df["GEOID"] = df["GEOID"].astype(str)

        # Check if GEOID has sufficient length
        if len(str(df["GEOID"].iloc[0])) >= FULL_BLOCK_GROUP_GEOID_LENGTH:
            df["tract"] = df["GEOID"].str[5:11]
            df["block_group"] = df["GEOID"].str[11:12]
    except (IndexError, TypeError) as e:
        logger.warning(f"Unable to extract tract and block group from GEOID: {e}")

    return df


def process_fips_codes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process and add FIPS codes for state and county.

    Formats and zero-pads state and county FIPS codes to standard
    2-digit and 5-digit formats respectively.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with STATE and COUNTY columns containing numeric
        FIPS codes.

    Returns
    -------
    pd.DataFrame
        DataFrame with added state_fips and county_fips columns
        formatted with proper zero-padding.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({'STATE': ['37'], 'COUNTY': ['63']})
    >>> result = process_fips_codes(df)
    >>> result['state_fips'].iloc[0]
    '37'
    >>> result['county_fips'].iloc[0]
    '37063'
    """
    # Process state FIPS
    if "STATE" in df.columns and not df["STATE"].empty:
        try:
            df["STATE"] = df["STATE"].astype(str)
            df["state_fips"] = df["STATE"].str.zfill(2)
        except (AttributeError, ValueError) as e:
            logger.warning(f"Error processing STATE column: {e}")

    # Process county FIPS
    if "COUNTY" in df.columns and "STATE" in df.columns:
        try:
            df["COUNTY"] = df["COUNTY"].astype(str)
            df["STATE"] = df["STATE"].astype(str)
            df["county_fips"] = df["STATE"].str.zfill(2) + df["COUNTY"].str.zfill(3)
        except (AttributeError, ValueError) as e:
            logger.warning(f"Error processing COUNTY column: {e}")

    return df


def add_travel_columns(
    df: pd.DataFrame,
    poi_data: dict | list[dict],
    travel_time_minutes: int | None = None,
    travel_mode: str | None = None,
) -> pd.DataFrame:
    """
    Add POI and travel-related columns to the dataframe.

    Enriches census data with point-of-interest information and
    travel time/mode metadata for accessibility analysis.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to add columns to.
    poi_data : dict or list of dict
        POI data dictionary or list containing POI information with
        keys: 'name', 'type', 'lat', 'lon'.
    travel_time_minutes : int, optional
        Travel time in minutes from census area to POI.
    travel_mode : str, optional
        Travel mode used (e.g., 'walk', 'bike', 'drive').

    Returns
    -------
    pd.DataFrame
        DataFrame with added columns: poi_name, poi_type, poi_lat,
        poi_lon, travel_time_minutes, travel_mode.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({'pop': [100]})
    >>> poi = {'name': 'Park', 'type': 'recreation', 'lat': 35.0,
    ...        'lon': -78.0}
    >>> result = add_travel_columns(df, poi, 15, 'walk')
    >>> result['poi_name'].iloc[0]
    'Park'
    """
    # Extract POIs from dictionary if needed
    pois = poi_data
    if isinstance(poi_data, dict) and "pois" in poi_data:
        pois = poi_data["pois"]
    if not isinstance(pois, list):
        pois = [pois]

    # Add POI information
    if pois:
        # Get first POI for basic info (assuming single POI analysis)
        first_poi = pois[0] if pois else {}
        df["poi_name"] = first_poi.get("name", "Unknown")
        df["poi_type"] = first_poi.get("type", "Unknown")
        df["poi_lat"] = first_poi.get("lat", None)
        df["poi_lon"] = first_poi.get("lon", None)

    # Add travel time and mode
    if travel_time_minutes is not None:
        df["travel_time_minutes"] = travel_time_minutes

    if travel_mode is not None:
        df["travel_mode"] = travel_mode

    return df


def reorder_columns(
    df: pd.DataFrame, config: DataPrepConfig, exclude_missing: bool = True
) -> pd.DataFrame:
    """
    Reorder DataFrame columns according to preferred order.

    Arranges columns in a logical order for export, placing key
    identifiers first followed by demographic data.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to reorder.
    config : DataPrepConfig
        Data preparation configuration with preferred column order
        and exclusion rules.
    exclude_missing : bool, optional
        Whether to exclude columns not in dataframe, by default True.

    Returns
    -------
    pd.DataFrame
        DataFrame with reordered columns and excluded columns removed.

    Examples
    --------
    >>> import pandas as pd
    >>> from socialmapper.export.base import DataPrepConfig
    >>> df = pd.DataFrame({'b': [1], 'a': [2]})
    >>> config = DataPrepConfig()
    >>> result = reorder_columns(df, config)
    """
    # Get columns that exist in both preferred order and dataframe
    existing_preferred = [col for col in config.preferred_column_order if col in df.columns]

    # Get remaining columns not in preferred order
    remaining_cols = [col for col in df.columns if col not in config.preferred_column_order]

    # Combine in order
    new_column_order = existing_preferred + remaining_cols

    # Exclude unwanted columns
    columns_to_keep = [col for col in new_column_order if col not in config.excluded_columns]

    return df[columns_to_keep]


def deduplicate_records(
    df: pd.DataFrame, config: DataPrepConfig, additional_groupby_cols: list[str] | None = None
) -> pd.DataFrame:
    """
    Deduplicate records based on grouping columns.

    Removes duplicate rows by grouping on key columns and applying
    aggregation rules to consolidate multiple records.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to deduplicate.
    config : DataPrepConfig
        Data preparation configuration with deduplication columns and
        aggregation rules.
    additional_groupby_cols : list of str, optional
        Additional columns to include in grouping beyond those in
        config.

    Returns
    -------
    pd.DataFrame
        Deduplicated DataFrame with aggregated values.

    Examples
    --------
    >>> import pandas as pd
    >>> from socialmapper.export.base import DataPrepConfig
    >>> df = pd.DataFrame({
    ...     'census_block_group': ['001', '001'],
    ...     'poi_name': ['Park', 'Park'],
    ...     'distance': [1.0, 1.5]
    ... })
    >>> config = DataPrepConfig()
    >>> result = deduplicate_records(df, config)
    >>> len(result)
    1
    """
    if df.empty:
        return df

    # Determine groupby columns
    groupby_cols = config.deduplication_columns.copy()
    if additional_groupby_cols:
        groupby_cols.extend(additional_groupby_cols)

    # Only use columns that exist in dataframe
    groupby_cols = [col for col in groupby_cols if col in df.columns]

    if not groupby_cols:
        logger.warning("No valid groupby columns found for deduplication")
        return df

    try:
        # Create aggregation dictionary
        agg_dict = {}
        for col in df.columns:
            if col not in groupby_cols:
                # Use configured aggregation rule or default to 'first'
                agg_dict[col] = config.deduplication_agg_rules.get(col, "first")

        # Apply aggregation
        df_dedup = df.groupby(groupby_cols, as_index=False).agg(agg_dict)

        logger.info(f"Deduplication complete: {len(df)} → {len(df_dedup)} rows")
        return df_dedup

    except Exception as e:
        logger.warning(f"Error during deduplication: {e}")
        return df


def prepare_census_data(
    census_data: gpd.GeoDataFrame,
    poi_data: dict | list[dict],
    config: DataPrepConfig | None = None,
    travel_time_minutes: int | None = None,
    travel_mode: str | None = None,
    deduplicate: bool = True,
) -> pd.DataFrame:
    """
    Prepare census data for export with all transformations.

    Applies a comprehensive pipeline of transformations including GEOID
    parsing, FIPS formatting, travel metadata addition, deduplication,
    and column reordering to prepare census data for export.

    Parameters
    ----------
    census_data : gpd.GeoDataFrame
        GeoDataFrame with census demographic and geographic data.
    poi_data : dict or list of dict
        POI data dictionary or list with location information.
    config : DataPrepConfig, optional
        Data preparation configuration. Creates default if None.
    travel_time_minutes : int, optional
        Travel time in minutes for accessibility analysis.
    travel_mode : str, optional
        Travel mode (e.g., 'walk', 'bike', 'drive').
    deduplicate : bool, optional
        Whether to deduplicate records, by default True.

    Returns
    -------
    pd.DataFrame
        Prepared DataFrame ready for export with all transformations
        applied.

    Examples
    --------
    >>> import geopandas as gpd
    >>> census = gpd.GeoDataFrame({'GEOID': ['370630001001']})
    >>> poi = {'name': 'Park', 'type': 'recreation'}
    >>> result = prepare_census_data(census, poi)
    >>> 'census_block_group' in result.columns
    True
    """
    config = config or DataPrepConfig()

    # Check if census data is empty
    if census_data is None or census_data.empty:
        logger.warning("Census data is empty, creating minimal output")
        return pd.DataFrame()

    # Create a copy to avoid modifying original
    df = census_data.copy()

    # Add census block group column
    if "GEOID" in df.columns:
        df["census_block_group"] = df["GEOID"]

    # Extract GEOID components
    df = extract_geoid_components(df)

    # Process FIPS codes
    df = process_fips_codes(df)

    # Add travel-related columns
    df = add_travel_columns(df, poi_data, travel_time_minutes, travel_mode)

    # Deduplicate if requested
    if deduplicate and len(df) > 0:
        df = deduplicate_records(df, config)

    # Reorder columns
    df = reorder_columns(df, config)

    return df
