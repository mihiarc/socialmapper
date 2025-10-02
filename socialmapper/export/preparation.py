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
    """Extract tract and block group components from GEOID.

    Args:
        df: DataFrame with GEOID column

    Returns:
        DataFrame with added tract and block_group columns
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
    """Process and add FIPS codes for state and county.

    Args:
        df: DataFrame with STATE and COUNTY columns

    Returns:
        DataFrame with added state_fips and county_fips columns
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
    """Add POI and travel-related columns to the dataframe.

    Args:
        df: DataFrame to add columns to
        poi_data: POI data dictionary or list
        travel_time_minutes: Travel time in minutes
        travel_mode: Travel mode (walk, bike, drive)

    Returns:
        DataFrame with added travel columns
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
    """Reorder DataFrame columns according to preferred order.

    Args:
        df: DataFrame to reorder
        config: Data preparation configuration
        exclude_missing: Whether to exclude columns not in dataframe

    Returns:
        DataFrame with reordered columns
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
    """Deduplicate records based on grouping columns.

    Args:
        df: DataFrame to deduplicate
        config: Data preparation configuration
        additional_groupby_cols: Additional columns to group by

    Returns:
        Deduplicated DataFrame
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
    """Prepare census data for export with all common transformations.

    Args:
        census_data: GeoDataFrame with census data
        poi_data: POI data dictionary or list
        config: Data preparation configuration
        travel_time_minutes: Travel time in minutes
        travel_mode: Travel mode
        deduplicate: Whether to deduplicate records

    Returns:
        Prepared DataFrame ready for export
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
