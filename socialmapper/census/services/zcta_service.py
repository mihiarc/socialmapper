"""ZCTA Service for SocialMapper.

Handles ZIP Code Tabulation Area (ZCTA) operations including fetching boundaries,
batch processing, and TIGER/Line shapefile URL generation.
"""

import logging
from collections.abc import Callable

import geopandas as gpd
import pandas as pd

from ...constants import HTTP_OK
from ...progress import get_progress_bar
from ..domain.interfaces import CacheProvider, CensusAPIClient, ConfigurationProvider, RateLimiter

logger = logging.getLogger(__name__)


class ZctaService:
    """Service for managing ZIP Code Tabulation Area operations."""

    def __init__(
        self,
        config: ConfigurationProvider,
        api_client: CensusAPIClient,
        cache: CacheProvider | None = None,
        rate_limiter: RateLimiter | None = None,
    ):
        self._config = config
        self._api_client = api_client
        self._cache = cache
        self._rate_limiter = rate_limiter

        # Configure geopandas for better performance if available
        self._use_arrow = self._check_arrow_support()

    def get_zctas_for_state(self, state_fips: str) -> gpd.GeoDataFrame:
        """Fetch ZCTA boundaries for a specific state.

        Args:
            state_fips: State FIPS code

        Returns:
            GeoDataFrame with ZCTA boundaries
        """
        # Normalize FIPS code
        state_fips = state_fips.zfill(2)

        # Check cache first
        cache_key = f"zctas_{state_fips}"
        if self._cache:
            cached_data = self._cache.get(cache_key)
            if cached_data:
                logger.info(f"Loaded cached ZCTAs for state {state_fips}")
                return cached_data

        # Fetch from Census API
        logger.info(f"Fetching ZCTAs for state {state_fips}")

        # Use the Census 2020 TIGER REST API endpoint for ZCTA boundaries (Layer 2)
        base_url = "https://tigerweb.geo.census.gov/arcgis/rest/services/Census2020/PUMA_TAD_TAZ_UGA_ZCTA/MapServer/2/query"

        # Map state FIPS to common ZCTA prefixes (postal code patterns)
        state_zcta_prefixes = {
            "37": ["27", "28"],  # North Carolina: 27xxx, 28xxx
            "45": ["29"],  # South Carolina: 29xxx
            "13": ["30", "31"],  # Georgia: 30xxx, 31xxx
            "51": ["22", "23", "24"],  # Virginia: 22xxx, 23xxx, 24xxx
            "06": ["90", "91", "92", "93", "94", "95", "96"],  # California
            "36": ["10", "11", "12", "13", "14"],  # New York
            "48": ["75", "76", "77", "78", "79"],  # Texas
        }

        # Get ZCTA prefixes for this state
        zcta_prefixes = state_zcta_prefixes.get(state_fips, [])

        if not zcta_prefixes:
            logger.warning(f"No ZCTA prefix mapping for state {state_fips}")
            raise ValueError(f"No ZCTA prefix mapping available for state {state_fips}")

        # Fetch ZCTAs for each prefix separately (API doesn't handle complex OR clauses well)
        all_zctas = []

        for prefix in zcta_prefixes:
            logger.info(f"Fetching ZCTAs with prefix {prefix}")

            params = {
                "where": f"GEOID LIKE '{prefix}%'",
                "outFields": "GEOID,ZCTA5,NAME,POP100,HU100,AREALAND,AREAWATER,CENTLAT,CENTLON",
                "returnGeometry": "true",
                "f": "geojson",
                "resultRecordCount": 2000,
            }

            try:
                # Apply rate limiting
                if self._rate_limiter:
                    self._rate_limiter.wait_if_needed("census")

                # Use requests directly since we're calling a different API
                import requests

                response = requests.get(base_url, params=params, timeout=60)

                logger.info(f"API request URL: {response.url}")
                logger.info(f"Response status: {response.status_code}")

                if response.status_code == HTTP_OK:
                    # Parse the GeoJSON response
                    try:
                        data = response.json()
                        logger.info(f"API response keys: {list(data.keys())}")
                    except Exception as json_error:
                        logger.error(f"Failed to parse JSON response: {json_error}")
                        logger.error(f"Raw response: {response.text[:500]}")
                        continue  # Skip this prefix and try the next one

                    # Handle GeoJSON format
                    if "features" in data and isinstance(data["features"], list):
                        logger.info(f"Found {len(data['features'])} features for prefix {prefix}")

                        if data["features"]:
                            # Create GeoDataFrame directly from GeoJSON
                            prefix_zctas = gpd.GeoDataFrame.from_features(
                                data["features"], crs="EPSG:4326"
                            )
                            all_zctas.append(prefix_zctas)
                            logger.info(f"Added {len(prefix_zctas)} ZCTAs for prefix {prefix}")
                        else:
                            logger.info(f"No ZCTAs found for prefix {prefix}")
                    else:
                        logger.warning(
                            f"Unexpected response format for prefix {prefix}: {list(data.keys())}"
                        )
                else:
                    logger.warning(
                        f"API returned status code {response.status_code} for prefix {prefix}"
                    )

            except Exception as e:
                logger.error(f"Error fetching ZCTAs for prefix {prefix}: {e}")
                continue  # Skip this prefix and try the next one

        # Combine all ZCTAs
        if all_zctas:
            zctas = pd.concat(all_zctas, ignore_index=True)
            # Ensure result is a GeoDataFrame
            if not isinstance(zctas, gpd.GeoDataFrame):
                zctas = gpd.GeoDataFrame(zctas, crs=all_zctas[0].crs)

            logger.info(f"Combined {len(zctas)} ZCTAs from {len(all_zctas)} prefixes")

            # Standardize column names for consistency
            if "ZCTA5CE" not in zctas.columns and "ZCTA5" in zctas.columns:
                zctas["ZCTA5CE"] = zctas["ZCTA5"]

            # Ensure state FIPS is available
            if "STATEFP" not in zctas.columns:
                zctas["STATEFP"] = state_fips

            # Cache the result
            if self._cache:
                self._cache.set(cache_key, zctas)

            logger.info(f"Retrieved {len(zctas)} ZCTAs for state {state_fips}")
            return zctas
        else:
            raise ValueError(f"No ZCTAs found for any prefix in state {state_fips}")

    def get_zctas_for_states(self, state_fips_list: list[str]) -> gpd.GeoDataFrame:
        """Fetch ZCTAs for multiple states and combine them.

        Args:
            state_fips_list: List of state FIPS codes

        Returns:
            Combined GeoDataFrame with ZCTAs for all states
        """
        all_zctas = []

        # Use progress bar correctly
        with get_progress_bar(
            total=len(state_fips_list), desc="Fetching ZCTAs by state", unit="state"
        ) as pbar:
            for state_fips in state_fips_list:
                try:
                    state_zctas = self.get_zctas_for_state(state_fips)
                    all_zctas.append(state_zctas)
                    pbar.update(1)
                except Exception as e:
                    logger.warning(f"Error fetching ZCTAs for state {state_fips}: {e}")
                    pbar.update(1)  # Still update progress even on error

        if not all_zctas:
            raise ValueError("No ZCTA data could be retrieved")

        # Combine all state ZCTAs - preserve GeoDataFrame type
        combined = pd.concat(all_zctas, ignore_index=True)
        # Ensure result is a GeoDataFrame
        if not isinstance(combined, gpd.GeoDataFrame):
            combined = gpd.GeoDataFrame(combined, crs=all_zctas[0].crs)
        return combined

    def get_zcta_urls(self, year: int = 2020) -> dict[str, str]:
        """Get the download URLs for ZCTA shapefiles from the Census Bureau.

        Args:
            year: Year for the TIGER/Line shapefiles

        Returns:
            Dictionary mapping dataset name to download URLs
        """
        # Base URL for Census Bureau TIGER/Line shapefiles
        base_url = f"https://www2.census.gov/geo/tiger/TIGER{year}/ZCTA520"

        # The URL pattern for ZCTA shapefiles (national file)
        url = f"{base_url}/tl_{year}_us_zcta520.zip"

        # Return a dictionary mapping dataset to the URL
        return {"national_zcta": url}

    def validate_zcta_data(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Validate and clean ZCTA GeoDataFrame.

        Args:
            gdf: ZCTA GeoDataFrame

        Returns:
            Cleaned GeoDataFrame
        """
        if gdf.empty:
            return gdf

        # Ensure required columns exist
        required_columns = ["ZCTA5CE", "GEOID"]
        missing_columns = [col for col in required_columns if col not in gdf.columns]

        if missing_columns:
            logger.warning(f"Missing required columns: {missing_columns}")

        # Ensure GEOID column exists and is properly formatted
        if "GEOID" not in gdf.columns and "ZCTA5CE" in gdf.columns:
            gdf["GEOID"] = gdf["ZCTA5CE"].astype(str)

        # Remove invalid geometries
        if "geometry" in gdf.columns:
            valid_geom = gdf.geometry.notna() & gdf.geometry.is_valid
            if not valid_geom.all():
                logger.warning(f"Removing {(~valid_geom).sum()} invalid geometries")
                gdf = gdf[valid_geom].copy()

        return gdf

    def get_zcta_for_point(self, lat: float, lon: float) -> str | None:
        """Get the ZCTA code for a specific point.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            ZCTA code or None if not found
        """
        try:
            # Use Census geocoding API to get ZCTA
            # Create logger for geocoder
            import logging

            from ..infrastructure.geocoder import CensusGeocoder
            geocoder_logger = logging.getLogger(f"{__name__}.geocoder")

            geocoder = CensusGeocoder(self._config, geocoder_logger)
            result = geocoder.geocode_point(lat, lon)
            return result.zcta_geoid if result else None
        except Exception as e:
            logger.warning(f"Failed to get ZCTA for point ({lat}, {lon}): {e}")
            return None

    def get_census_data(
        self,
        geoids: list[str],
        variables: list[str],
        api_key: str | None = None,
        geographic_level: str = "zcta",
    ) -> pd.DataFrame:
        """Get census data for ZCTA geoids.

        Args:
            geoids: List of ZCTA geoids
            variables: List of census variable codes
            api_key: Census API key (optional)
            geographic_level: Geographic level (should be "zcta")

        Returns:
            DataFrame with census data in legacy format
        """
        import pandas as pd

        # Apply rate limiting
        if self._rate_limiter:
            self._rate_limiter.wait_if_needed("census")

        logger.info(f"Fetching census data for {len(geoids)} ZCTAs and {len(variables)} variables")

        # Check cache first
        cache_key = (
            f"zcta_census_data_{hash(tuple(sorted(geoids)))}{hash(tuple(sorted(variables)))}"
        )
        if self._cache:
            cached_data = self._cache.get(cache_key)
            if cached_data:
                logger.info("Loaded cached ZCTA census data")
                return cached_data.data

        try:
            # Use the Census Data API for ZCTA data
            # Build the geography parameter for ZCTAs
            geography_param = f"zip code tabulation area:{','.join(geoids)}"

            # Make the API call using the modern API client
            api_response = self._api_client.get_census_data(
                variables=variables,
                geography=geography_param,
                year=2023,  # Use most recent ACS 5-year data
                dataset="acs/acs5",
            )

            if not api_response or len(api_response) < 2:  # Need header + data rows
                logger.warning("No data returned from Census API for ZCTAs")
                return pd.DataFrame()

            # Convert API response to DataFrame
            # First row is headers, rest are data
            headers = api_response[0]
            data_rows = api_response[1:]

            # Create DataFrame
            df = pd.DataFrame(data_rows, columns=headers)

            # Transform to legacy format expected by the adapters
            legacy_rows = []
            for _, row in df.iterrows():
                geoid = row.get("zip code tabulation area", "")

                for variable in variables:
                    if variable in row and row[variable] is not None:
                        try:
                            raw_value = row[variable]

                            # Handle census placeholder values
                            if raw_value in ["-999999999", "-888888888", "-666666666", "-555555555", "-222222222", "-111111111", "null", ""]:
                                value = None
                            else:
                                value = float(raw_value)

                                # For income and financial variables, negative values are placeholders
                                if (variable.startswith(('B19', 'B25')) and value < 0) or value < -100000:
                                    value = None

                        except (ValueError, TypeError):
                            value = None

                        legacy_rows.append(
                            {
                                "GEOID": geoid,
                                "variable_code": variable,
                                "value": value,
                                "year": 2023,
                                "dataset": "acs5",
                                "NAME": f"ZCTA5 {geoid}",
                            }
                        )

            result_df = pd.DataFrame(legacy_rows)

            # Cache the result
            if self._cache:
                self._cache.set(cache_key, result_df, ttl=3600)  # Cache for 1 hour

            logger.info(
                f"Successfully fetched census data for {len(result_df)} ZCTA-variable combinations"
            )
            return result_df

        except Exception as e:
            logger.error(f"Error fetching ZCTA census data: {e}")
            # Return empty DataFrame in legacy format on error
            return pd.DataFrame(
                columns=["GEOID", "variable_code", "value", "year", "dataset", "NAME"]
            )

    def _check_arrow_support(self) -> bool:
        """Check if PyArrow is available for better performance."""
        import importlib.util
        import os

        if importlib.util.find_spec("pyarrow") is not None:
            os.environ["PYOGRIO_USE_ARROW"] = "1"
            return True
        return False

    def get_zctas_for_counties(self, counties: list[tuple[str, str]]) -> gpd.GeoDataFrame:
        """Get ZCTAs that intersect with specific counties.

        Args:
            counties: List of (state_fips, county_fips) tuples

        Returns:
            GeoDataFrame with ZCTAs that intersect the counties
        """
        # Get unique states from the counties list
        state_fips_set = {county[0] for county in counties}

        # Fetch ZCTAs for all relevant states
        all_zctas = self.get_zctas_for_states(list(state_fips_set))

        if all_zctas.empty:
            return all_zctas

        # Filter ZCTAs by county intersection if needed
        # Note: This is a simplified implementation - in reality you'd want
        # to do spatial intersection with county boundaries
        logger.info(f"Retrieved {len(all_zctas)} ZCTAs for {len(counties)} counties")
        return all_zctas

    def batch_get_zctas(
        self,
        state_fips_list: list[str],
        batch_size: int = 5,
        progress_callback: Callable | None = None,
    ) -> gpd.GeoDataFrame:
        """Get ZCTAs for multiple states with batching and progress tracking.

        Args:
            state_fips_list: List of state FIPS codes
            batch_size: Number of states to process in each batch
            progress_callback: Optional callback for progress updates

        Returns:
            Combined GeoDataFrame with all ZCTAs
        """
        all_zctas = []
        total_states = len(state_fips_list)

        for i in range(0, total_states, batch_size):
            batch = state_fips_list[i : i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_states + batch_size - 1) // batch_size

            logger.info(f"Processing ZCTA batch {batch_num}/{total_batches}: states {batch}")

            for state_fips in batch:
                try:
                    state_zctas = self.get_zctas_for_state(state_fips)
                    all_zctas.append(state_zctas)

                    if progress_callback:
                        progress = len(all_zctas) / total_states
                        progress_callback(progress, f"Completed state {state_fips}")

                except Exception as e:
                    logger.warning(f"Error fetching ZCTAs for state {state_fips}: {e}")

        if not all_zctas:
            logger.warning("No ZCTA data could be retrieved")
            return gpd.GeoDataFrame()

        # Combine all ZCTAs - preserve GeoDataFrame type
        combined_zctas = pd.concat(all_zctas, ignore_index=True)
        # Ensure result is a GeoDataFrame
        if not isinstance(combined_zctas, gpd.GeoDataFrame):
            combined_zctas = gpd.GeoDataFrame(combined_zctas, crs=all_zctas[0].crs)

        logger.info(f"Successfully retrieved {len(combined_zctas)} total ZCTAs")
        return combined_zctas

    def get_zcta_census_data_batch(
        self, state_fips_list: list[str], variables: list[str], batch_size: int = 100
    ) -> pd.DataFrame:
        """Get census data for ZCTAs across multiple states with efficient batching.

        Args:
            state_fips_list: List of state FIPS codes
            variables: List of census variable codes
            batch_size: Number of ZCTAs to process per API call

        Returns:
            DataFrame with census data for all ZCTAs
        """
        # First get all ZCTAs for the states
        all_zctas = self.get_zctas_for_states(state_fips_list)

        if all_zctas.empty:
            return pd.DataFrame()

        # Extract GEOID list
        geoids = all_zctas["GEOID"].tolist() if "GEOID" in all_zctas.columns else []

        if not geoids:
            logger.warning("No GEOIDs found in ZCTA data")
            return pd.DataFrame()

        logger.info(f"Fetching census data for {len(geoids)} ZCTAs in batches of {batch_size}")

        all_data = []

        # Process in batches to avoid API limits
        for i in range(0, len(geoids), batch_size):
            batch_geoids = geoids[i : i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(geoids) + batch_size - 1) // batch_size

            logger.info(f"Processing census data batch {batch_num}/{total_batches}")

            try:
                batch_data = self.get_census_data(batch_geoids, variables)
                if not batch_data.empty:
                    all_data.append(batch_data)
            except Exception as e:
                logger.warning(f"Error fetching census data for batch {batch_num}: {e}")

        if not all_data:
            return pd.DataFrame()

        # Combine all batches
        combined_data = pd.concat(all_data, ignore_index=True)
        logger.info(f"Retrieved census data for {len(combined_data)} ZCTA-variable combinations")

        return combined_data

    def create_legacy_streaming_interface(self):
        """Create a legacy streaming interface compatible with old adapters.

        Returns:
            Object with legacy streaming methods
        """

        class LegacyZctaInterface:
            def __init__(self, zcta_service):
                self._zcta_service = zcta_service

            def get_zctas(self, state_fips_list: list[str]) -> gpd.GeoDataFrame:
                """Legacy method: Get ZCTAs for multiple states."""
                return self._zcta_service.get_zctas_for_states(state_fips_list)

            def get_census_data(
                self,
                geoids: list[str],
                variables: list[str],
                api_key: str | None = None,
                geographic_level: str = "zcta",
            ) -> pd.DataFrame:
                """Legacy method: Get census data for ZCTAs."""
                return self._zcta_service.get_census_data(
                    geoids, variables, api_key, geographic_level
                )

        return LegacyZctaInterface(self)
