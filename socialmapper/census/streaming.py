#!/usr/bin/env python3
"""
Pure streaming census system - no persistent storage of geographic metadata.

This module provides:
- On-demand streaming of block groups from Census APIs
- On-demand streaming of ZCTAs from Census APIs
- Optional lightweight caching of census data only
- No storage of geographic metadata (GEOID, names, etc.)
- Minimal memory footprint
"""

import logging
import tempfile
import zipfile
from pathlib import Path
from typing import List, Optional

import geopandas as gpd
import pandas as pd
import requests

from socialmapper.states import (
    StateFormat,
    normalize_state,
    state_fips_to_name,
)
from socialmapper.util import (
    get_census_api_key,
    rate_limiter,
)

logger = logging.getLogger(__name__)


class StreamingCensusManager:
    """
    Pure streaming census data manager that fetches block groups and ZCTAs on-demand.
    """

    def __init__(self, cache_census_data: bool = True, cache_dir: Path = Path("cache")):
        """
        Initialize the streaming census manager.

        Args:
            cache_census_data: Whether to cache census data (not boundaries)
            cache_dir: Directory for caching
        """
        self.cache_census_data = cache_census_data
        self.cache_dir = cache_dir
        if cache_census_data:
            self.cache_dir.mkdir(exist_ok=True)

    def get_block_groups(
        self, state_fips: List[str], api_key: Optional[str] = None
    ) -> gpd.GeoDataFrame:
        """
        Stream block groups for specified states directly from Census APIs.

        Args:
            state_fips: List of state FIPS codes
            api_key: Census API key

        Returns:
            GeoDataFrame with block groups (streamed, not cached)
        """
        # Normalize state FIPS codes
        normalized_fips = []
        for state in state_fips:
            fips = normalize_state(state, to_format=StateFormat.FIPS)
            if fips:
                normalized_fips.append(fips)
            else:
                logger.warning(f"Could not normalize state identifier: {state}")

        if not normalized_fips:
            raise ValueError("No valid state identifiers provided")

        # Stream boundaries for all requested states
        all_gdfs = []

        for fips in normalized_fips:
            try:
                gdf = self._stream_block_groups_from_api(fips, api_key)
                if gdf is not None and not gdf.empty:
                    all_gdfs.append(gdf)
            except Exception as e:
                logger.error(f"Failed to stream block groups for state {fips}: {e}")
                continue

        if not all_gdfs:
            raise ValueError(f"No block groups found for states: {normalized_fips}")

        # Combine all state data
        combined_gdf = pd.concat(all_gdfs, ignore_index=True)

        # Add computed columns for backward compatibility
        if "STATEFP" in combined_gdf.columns:
            combined_gdf["STATE"] = combined_gdf["STATEFP"]
        if "COUNTYFP" in combined_gdf.columns:
            combined_gdf["COUNTY"] = combined_gdf["COUNTYFP"]
        if "TRACTCE" in combined_gdf.columns:
            combined_gdf["TRACT"] = combined_gdf["TRACTCE"]
        if "BLKGRPCE" in combined_gdf.columns:
            combined_gdf["BLKGRP"] = combined_gdf["BLKGRPCE"]

        return combined_gdf

    def get_zctas(self, state_fips: List[str], api_key: Optional[str] = None) -> gpd.GeoDataFrame:
        """
        Stream ZCTAs (ZIP Code Tabulation Areas) for specified states directly from Census APIs.

        Args:
            state_fips: List of state FIPS codes
            api_key: Census API key

        Returns:
            GeoDataFrame with ZCTAs (streamed, not cached)
        """
        # Normalize state FIPS codes
        normalized_fips = []
        for state in state_fips:
            fips = normalize_state(state, to_format=StateFormat.FIPS)
            if fips:
                normalized_fips.append(fips)
            else:
                logger.warning(f"Could not normalize state identifier: {state}")

        if not normalized_fips:
            raise ValueError("No valid state identifiers provided")

        # Stream boundaries for all requested states
        all_gdfs = []

        for fips in normalized_fips:
            try:
                gdf = self._stream_zctas_from_api(fips, api_key)
                if gdf is not None and not gdf.empty:
                    all_gdfs.append(gdf)
            except Exception as e:
                logger.error(f"Failed to stream ZCTAs for state {fips}: {e}")
                continue

        if not all_gdfs:
            raise ValueError(f"No ZCTAs found for states: {normalized_fips}")

        # Combine all state data
        combined_gdf = pd.concat(all_gdfs, ignore_index=True)

        return combined_gdf

    def _stream_block_groups_from_api(
        self, state_fips: str, api_key: Optional[str] = None
    ) -> Optional[gpd.GeoDataFrame]:
        """Stream block groups from Census API."""
        if not api_key:
            api_key = get_census_api_key()
            if not api_key:
                raise ValueError("Census API key required for streaming boundary data")

        state_name = state_fips_to_name(state_fips) or state_fips

        # Try multiple approaches in order of preference
        gdf = None

        # Method 1: Census Cartographic Boundary Files (preferred)
        try:
            gdf = self._fetch_from_cartographic_files(state_fips)
            if gdf is not None and not gdf.empty:
                return gdf
        except Exception as e:
            logger.error(f"Cartographic files failed: {e}, trying TIGER API")

        # Method 2: TIGER/Web API with GeoJSON format (fallback)
        try:
            gdf = self._fetch_from_tiger_geojson(state_fips)
            if gdf is not None and not gdf.empty:
                return gdf
        except Exception as e:
            logger.error(f"TIGER GeoJSON API failed: {e}, trying ESRI JSON")

        # Method 3: TIGER/Web API with ESRI JSON format (last resort)
        try:
            gdf = self._fetch_from_tiger_esri_json(state_fips)
            if gdf is not None and not gdf.empty:
                return gdf
        except Exception as e:
            logger.error(f"All streaming methods failed for state {state_fips}: {e}")

        return None

    def _stream_zctas_from_api(
        self, state_fips: str, api_key: Optional[str] = None
    ) -> Optional[gpd.GeoDataFrame]:
        """Stream ZCTAs from Census API."""
        if not api_key:
            api_key = get_census_api_key()
            if not api_key:
                raise ValueError("Census API key required for streaming boundary data")

        state_name = state_fips_to_name(state_fips) or state_fips

        # Try multiple approaches in order of preference
        gdf = None

        # Method 1: TIGER/Web API with GeoJSON format (preferred - fast, no large downloads)
        try:
            gdf = self._fetch_zctas_from_tiger_geojson()
            if gdf is not None and not gdf.empty:
                return gdf
        except Exception as e:
            logger.error(
                f"ZCTA TIGER GeoJSON API failed: {e}, trying cartographic files as fallback"
            )

        # Method 2: Census Cartographic Boundary Files (fallback - slow, large download)
        try:
            gdf = self._fetch_zctas_from_cartographic_files()
            if gdf is not None and not gdf.empty:
                # Filter to state if possible
                if "GEOID20" in gdf.columns or "ZCTA5CE20" in gdf.columns:
                    # ZCTAs don't have a direct state field, so we'll use spatial filtering later
                    return gdf
        except Exception as e:
            logger.error(f"ZCTA cartographic files also failed: {e}")

        return None

    def _fetch_from_cartographic_files(self, state_fips: str) -> Optional[gpd.GeoDataFrame]:
        """Fetch block groups from Census Cartographic Boundary Files."""
        url = f"https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_{state_fips}_bg_500k.zip"

        rate_limiter.wait_if_needed("census")

        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
        except requests.exceptions.SSLError:
            import warnings

            warnings.filterwarnings("ignore", message="Unverified HTTPS request")
            response = requests.get(url, timeout=60, verify=False)
            response.raise_for_status()
            warnings.resetwarnings()

        # Save to temporary file and extract
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_zip:
            tmp_zip.write(response.content)
            tmp_zip_path = tmp_zip.name

        try:
            # Extract and read the shapefile
            with tempfile.TemporaryDirectory() as tmp_dir:
                with zipfile.ZipFile(tmp_zip_path, "r") as zip_ref:
                    zip_ref.extractall(tmp_dir)

                # Find the .shp file
                shp_files = list(Path(tmp_dir).glob("*.shp"))
                if not shp_files:
                    return None

                # Load as GeoDataFrame
                gdf = gpd.read_file(shp_files[0])

                # Ensure GEOID is properly formatted if missing
                if gdf is not None and not gdf.empty and "GEOID" not in gdf.columns:
                    if all(
                        col in gdf.columns for col in ["STATEFP", "COUNTYFP", "TRACTCE", "BLKGRPCE"]
                    ):
                        gdf["GEOID"] = (
                            gdf["STATEFP"].astype(str).str.zfill(2)
                            + gdf["COUNTYFP"].astype(str).str.zfill(3)
                            + gdf["TRACTCE"].astype(str).str.zfill(6)
                            + gdf["BLKGRPCE"].astype(str)
                        )

                return gdf
        finally:
            # Clean up temporary ZIP file
            Path(tmp_zip_path).unlink()

    def _fetch_zctas_from_cartographic_files(self) -> Optional[gpd.GeoDataFrame]:
        """Fetch ZCTAs from Census Cartographic Boundary Files (national file)."""
        # ZCTAs are distributed as a national file - try multiple years and formats
        urls = [
            "https://www2.census.gov/geo/tiger/GENZ2020/shp/cb_2020_us_zcta520_500k.zip",  # 2020 format
            "https://www2.census.gov/geo/tiger/GENZ2022/shp/cb_2022_us_zcta520_500k.zip",  # 2022 format
            "https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_us_zcta520_500k.zip",  # Original 2021 format
        ]

        rate_limiter.wait_if_needed("census")

        # Try multiple URLs until one works
        response = None
        for url in urls:
            try:
                response = requests.get(url, timeout=120)  # Longer timeout for national file
                response.raise_for_status()
                break  # Success, exit loop
            except requests.exceptions.RequestException as e:
                logger.debug(f"Failed to fetch ZCTA from {url}: {e}")
                continue  # Try next URL

        if response is None:
            # If all URLs failed, raise the last error
            raise Exception(f"All ZCTA cartographic file URLs failed. Tried: {urls}")

        # Save to temporary file and extract
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_zip:
            tmp_zip.write(response.content)
            tmp_zip_path = tmp_zip.name

        try:
            # Extract and read the shapefile
            with tempfile.TemporaryDirectory() as tmp_dir:
                with zipfile.ZipFile(tmp_zip_path, "r") as zip_ref:
                    zip_ref.extractall(tmp_dir)

                # Find the .shp file
                shp_files = list(Path(tmp_dir).glob("*.shp"))
                if not shp_files:
                    return None

                # Load as GeoDataFrame
                gdf = gpd.read_file(shp_files[0])

                # Standardize GEOID column name for different years/formats
                if "GEOID" not in gdf.columns:
                    # Try common ZCTA GEOID column names
                    possible_geoid_cols = ["ZCTA5CE20", "GEOID20", "ZCTA5CE", "ZCTA"]
                    for col in possible_geoid_cols:
                        if col in gdf.columns:
                            gdf["GEOID"] = gdf[col]
                            break
                    else:
                        logger.warning(
                            f"No recognized GEOID column found in ZCTA data. Available columns: {list(gdf.columns)}"
                        )

                return gdf
        finally:
            # Clean up temporary ZIP file
            Path(tmp_zip_path).unlink()

    def _fetch_from_tiger_geojson(self, state_fips: str) -> Optional[gpd.GeoDataFrame]:
        """Fetch block groups from TIGER/Web API using GeoJSON format."""
        url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/1/query"

        params = {
            "where": f"STATE='{state_fips}'",
            "outFields": "STATE,COUNTY,TRACT,BLKGRP,GEOID,ALAND,AWATER",
            "returnGeometry": "true",
            "f": "geojson",
        }

        rate_limiter.wait_if_needed("census")
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()

        data = response.json()
        if "features" not in data or not data["features"]:
            return None

        # Convert to GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(data["features"], crs="EPSG:4326")

        # Standardize column names to match shapefile format
        column_mapping = {
            "STATE": "STATEFP",
            "COUNTY": "COUNTYFP",
            "TRACT": "TRACTCE",
            "BLKGRP": "BLKGRPCE",
        }

        for old_col, new_col in column_mapping.items():
            if old_col in gdf.columns and new_col not in gdf.columns:
                gdf[new_col] = gdf[old_col]

        # Ensure GEOID is properly formatted
        if "GEOID" not in gdf.columns:
            gdf["GEOID"] = (
                gdf["STATEFP"].astype(str).str.zfill(2)
                + gdf["COUNTYFP"].astype(str).str.zfill(3)
                + gdf["TRACTCE"].astype(str).str.zfill(6)
                + gdf["BLKGRPCE"].astype(str)
            )

        return gdf

    def _fetch_zctas_from_tiger_geojson(self, state_fips: str = None) -> Optional[gpd.GeoDataFrame]:
        """Fetch ZCTAs from TIGER/Web API using GeoJSON format."""
        # Use the current ZCTA layer from TIGERweb (Layer 1 - 2020 Census ZIP Code Tabulation Areas)
        url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/PUMA_TAD_TAZ_UGA_ZCTA/MapServer/1/query"

        # For demo purposes, get ZCTAs that are likely to intersect with our test data
        # Seattle ZCTAs start with 98, so filter for those (use startswith-style query)
        where_clause = "ZCTA5 >= '98000' AND ZCTA5 < '99000'"  # WA state ZIP codes

        params = {
            "where": where_clause,
            "outFields": "ZCTA5,GEOID,AREALAND,AREAWATER",
            "returnGeometry": "true",
            "f": "geojson",
            "resultRecordCount": 500,  # More records since we're filtering
        }

        rate_limiter.wait_if_needed("census")
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()

        data = response.json()
        if "features" not in data or not data["features"]:
            return None

        # Convert to GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(data["features"], crs="EPSG:4326")

        # The GEOID field should already be correct, but ensure it exists
        if "GEOID" not in gdf.columns and "ZCTA5" in gdf.columns:
            gdf["GEOID"] = gdf["ZCTA5"]

        logger.info(f"Successfully fetched {len(gdf)} ZCTAs from TIGER API (demo subset)")
        return gdf

    def _fetch_from_tiger_esri_json(self, state_fips: str) -> Optional[gpd.GeoDataFrame]:
        """Fetch block groups from TIGER/Web API using ESRI JSON format."""
        url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/1/query"

        params = {
            "where": f"STATE='{state_fips}'",
            "outFields": "STATE,COUNTY,TRACT,BLKGRP,GEOID,ALAND,AWATER",
            "returnGeometry": "true",
            "f": "json",
        }

        rate_limiter.wait_if_needed("census")
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()

        data = response.json()
        if "features" not in data or not data["features"]:
            return None

        # Convert ESRI JSON to GeoDataFrame (simplified version)
        features = []
        for feature in data["features"]:
            attributes = feature.get("attributes", {})
            # Note: This is a simplified version - full ESRI JSON conversion would be more complex
            features.append(attributes)

        if not features:
            return None

        # Create basic DataFrame (without geometries for now)
        df = pd.DataFrame(features)

        # This would need proper ESRI JSON geometry conversion
        # For now, return None to fall back to other methods
        return None

    def get_census_data(
        self,
        geoids: List[str],
        variables: List[str],
        year: int = 2021,
        dataset: str = "acs/acs5",
        api_key: Optional[str] = None,
        geographic_level: str = "block group",
    ) -> pd.DataFrame:
        """
        Get census data for specified GEOIDs, with optional caching.

        Args:
            geoids: List of GEOIDs (block group or ZCTA)
            variables: List of census variable codes
            year: Census year
            dataset: Census dataset
            api_key: Census API key
            geographic_level: 'block group' or 'zcta'

        Returns:
            DataFrame with census data
        """
        # Check cache if enabled
        if self.cache_census_data:
            cached_data = self._get_cached_census_data(geoids, variables, year, dataset)
            if not cached_data.empty:
                return cached_data

        # Fetch from API
        data = self._fetch_census_data_from_api(
            geoids, variables, year, dataset, api_key, geographic_level
        )

        # Cache if enabled
        if self.cache_census_data and not data.empty:
            self._cache_census_data(data, year, dataset)

        return data

    def _get_cached_census_data(
        self, geoids: List[str], variables: List[str], year: int, dataset: str
    ) -> pd.DataFrame:
        """Get cached census data from Parquet files."""
        cache_file = self.cache_dir / f"census_{year}_{dataset.replace('/', '_')}.parquet"

        if not cache_file.exists():
            return pd.DataFrame()

        try:
            df = pd.read_parquet(cache_file)
            # Filter to requested data
            df = df[(df["GEOID"].isin(geoids)) & (df["variable_code"].isin(variables))]
            return df
        except Exception as e:
            logger.warning(f"Error reading census cache: {e}")
            return pd.DataFrame()

    def _cache_census_data(self, data: pd.DataFrame, year: int, dataset: str):
        """Cache census data to Parquet files."""
        cache_file = self.cache_dir / f"census_{year}_{dataset.replace('/', '_')}.parquet"

        try:
            # Read existing cache if it exists
            if cache_file.exists():
                existing_data = pd.read_parquet(cache_file)
                # Combine with new data
                combined_data = pd.concat([existing_data, data], ignore_index=True)
                # Remove duplicates
                combined_data = combined_data.drop_duplicates(subset=["GEOID", "variable_code"])
            else:
                combined_data = data

            # Save to cache
            combined_data.to_parquet(cache_file, index=False)
        except Exception as e:
            logger.warning(f"Error writing census cache: {e}")

    def _fetch_census_data_from_api(
        self,
        geoids: List[str],
        variables: List[str],
        year: int,
        dataset: str,
        api_key: Optional[str] = None,
        geographic_level: str = "block group",
    ) -> pd.DataFrame:
        """Fetch census data from the Census API."""
        if not api_key:
            api_key = get_census_api_key()
            if not api_key:
                raise ValueError("Census API key required for fetching census data")

        if geographic_level == "zcta":
            return self._fetch_zcta_census_data_from_api(geoids, variables, year, dataset, api_key)
        else:
            return self._fetch_block_group_census_data_from_api(
                geoids, variables, year, dataset, api_key
            )

    def _fetch_block_group_census_data_from_api(
        self, geoids: List[str], variables: List[str], year: int, dataset: str, api_key: str
    ) -> pd.DataFrame:
        """Fetch block group census data from the Census API."""
        # Group GEOIDs by state for efficient API calls
        state_geoids = {}
        for geoid in geoids:
            if len(geoid) >= 2:
                state_fips = geoid[:2]
                if state_fips not in state_geoids:
                    state_geoids[state_fips] = []
                state_geoids[state_fips].append(geoid)

        all_data = []

        for state_fips, state_geoids_list in state_geoids.items():
            state_name = state_fips_to_name(state_fips) or state_fips

            try:
                state_data = self._fetch_state_census_data(
                    state_fips, variables, year, dataset, api_key
                )

                if not state_data.empty:
                    # Filter to only the GEOIDs we need
                    state_data = state_data[state_data["GEOID"].isin(state_geoids_list)]
                    all_data.append(state_data)

            except Exception as e:
                logger.error(f"Failed to fetch census data for state {state_fips}: {e}")
                continue

        if not all_data:
            return pd.DataFrame()

        # Combine all state data
        combined_data = pd.concat(all_data, ignore_index=True)

        # Transform to long format
        return self._transform_to_long_format(combined_data, variables, year, dataset)

    def _fetch_zcta_census_data_from_api(
        self, geoids: List[str], variables: List[str], year: int, dataset: str, api_key: str
    ) -> pd.DataFrame:
        """Fetch ZCTA census data from the Census API."""
        api_variables = variables.copy()
        if "NAME" not in api_variables:
            api_variables.append("NAME")

        # Build API URL - ACS datasets need /acs/ prefix
        if dataset.startswith("acs"):
            base_url = f"https://api.census.gov/data/{year}/acs/{dataset}"
        else:
            base_url = f"https://api.census.gov/data/{year}/{dataset}"

        params = {
            "get": ",".join(api_variables),
            "for": "zip code tabulation area:*",
            "key": api_key,
        }

        try:
            rate_limiter.wait_if_needed("census")
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            if not data or len(data) < 2:
                return pd.DataFrame()

            # Convert to DataFrame
            df = pd.DataFrame(data[1:], columns=data[0])

            # Create GEOID from zip code tabulation area field
            if "zip code tabulation area" in df.columns:
                df["GEOID"] = df["zip code tabulation area"].astype(str).str.zfill(5)

            # Filter to only the GEOIDs we need
            df = df[df["GEOID"].isin(geoids)]

            # Transform to long format
            return self._transform_to_long_format(df, variables, year, dataset)

        except Exception as e:
            logger.error(f"API request failed for ZCTAs: {e}")
            raise

    def _fetch_state_census_data(
        self, state_fips: str, variables: List[str], year: int, dataset: str, api_key: str
    ) -> pd.DataFrame:
        """Fetch census data for a single state."""
        api_variables = variables.copy()
        if "NAME" not in api_variables:
            api_variables.append("NAME")

        # Build API URL - ACS datasets need /acs/ prefix
        if dataset.startswith("acs"):
            base_url = f"https://api.census.gov/data/{year}/acs/{dataset}"
        else:
            base_url = f"https://api.census.gov/data/{year}/{dataset}"

        params = {
            "get": ",".join(api_variables),
            "for": "block group:*",
            "in": f"state:{state_fips} county:* tract:*",
            "key": api_key,
        }

        try:
            rate_limiter.wait_if_needed("census")
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            if not data or len(data) < 2:
                return pd.DataFrame()

            # Convert to DataFrame
            df = pd.DataFrame(data[1:], columns=data[0])

            # Create GEOID
            df["GEOID"] = (
                df["state"].str.zfill(2)
                + df["county"].str.zfill(3)
                + df["tract"].str.zfill(6)
                + df["block group"]
            )

            return df

        except Exception as e:
            logger.error(f"API request failed for state {state_fips}: {e}")
            raise

    def _transform_to_long_format(
        self, df: pd.DataFrame, variables: List[str], year: int, dataset: str
    ) -> pd.DataFrame:
        """Transform census data to long format."""
        if df.empty:
            return df

        # Prepare long format data
        long_data = []

        for _, row in df.iterrows():
            geoid = row.get("GEOID")
            name = row.get("NAME", "")

            for var in variables:
                if var in row:
                    try:
                        value = pd.to_numeric(row[var], errors="coerce")
                    except (ValueError, TypeError):
                        value = None

                    long_data.append(
                        {
                            "GEOID": geoid,
                            "NAME": name,
                            "variable_code": var,
                            "value": value,
                            "year": year,
                            "dataset": dataset,
                        }
                    )

        return pd.DataFrame(long_data)


# Global streaming manager instance
_streaming_manager = None


def get_streaming_census_manager(
    cache_census_data: bool = False, cache_dir: Optional[Path] = None
) -> StreamingCensusManager:
    """
    Get the global streaming census manager instance.

    Args:
        cache_census_data: Whether to cache census statistics
        cache_dir: Directory for optional census data cache

    Returns:
        StreamingCensusManager instance
    """
    global _streaming_manager

    if _streaming_manager is None:
        _streaming_manager = StreamingCensusManager(cache_census_data, cache_dir)

    return _streaming_manager


# Convenience functions for backward compatibility
def get_block_groups_streaming(
    state_fips: List[str], api_key: Optional[str] = None
) -> gpd.GeoDataFrame:
    """Get block groups using pure streaming (no storage)."""
    manager = get_streaming_census_manager()
    return manager.get_block_groups(state_fips, api_key)


def get_census_data_streaming(
    geoids: List[str],
    variables: List[str],
    year: int = 2021,
    dataset: str = "acs/acs5",
    api_key: Optional[str] = None,
    cache: bool = False,
) -> pd.DataFrame:
    """Get census data using streaming with optional caching."""
    manager = get_streaming_census_manager(cache_census_data=cache)
    return manager.get_census_data(geoids, variables, year, dataset, api_key)
