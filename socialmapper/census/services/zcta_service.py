"""
ZCTA Service for SocialMapper.

Handles ZIP Code Tabulation Area (ZCTA) operations including fetching boundaries,
batch processing, and TIGER/Line shapefile URL generation.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import geopandas as gpd
import pandas as pd

from ..domain.entities import CountyInfo
from ..domain.interfaces import (
    CensusAPIClient, 
    CacheProvider, 
    ConfigurationProvider,
    RateLimiter
)
from ...progress import get_progress_bar
from ...ui.rich_console import get_logger

logger = get_logger(__name__)


class ZctaService:
    """Service for managing ZIP Code Tabulation Area operations."""
    
    def __init__(
        self,
        config: ConfigurationProvider,
        api_client: CensusAPIClient,
        cache: Optional[CacheProvider] = None,
        rate_limiter: Optional[RateLimiter] = None
    ):
        self._config = config
        self._api_client = api_client
        self._cache = cache
        self._rate_limiter = rate_limiter
        
        # Configure geopandas for better performance if available
        self._use_arrow = self._check_arrow_support()
    
    def get_zctas_for_state(
        self, 
        state_fips: str
    ) -> gpd.GeoDataFrame:
        """
        Fetch ZCTA boundaries for a specific state using the correct TIGER REST API.
        
        Uses the official TIGER REST API endpoint:
        https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/PUMA_TAD_TAZ_UGA_ZCTA/MapServer/7
        
        Args:
            state_fips: State FIPS code
            
        Returns:
            GeoDataFrame with ZCTA boundaries
        """
        # Normalize FIPS code
        state_fips = state_fips.zfill(2)
        
        # Check cache first
        cache_key = f"zctas_{state_fips}_2020"
        if self._cache:
            cached_data = self._cache.get(cache_key)
            if cached_data:
                logger.info(f"Loaded cached ZCTAs for state {state_fips}")
                return cached_data
        
        # Fetch from Census TIGER REST API
        logger.info(f"Fetching ZCTAs for state {state_fips} from TIGER REST API")
        
        # Use the correct TIGER REST API endpoint for 2020 Census ZIP Code Tabulation Areas
        # Layer 7: 2020 Census ZIP Code Tabulation Areas
        base_url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/PUMA_TAD_TAZ_UGA_ZCTA/MapServer/7/query"
        
        # Build query parameters based on the API documentation
        params = {
            "where": "1=1",  # Get all ZCTAs (we'll filter by state if possible)
            "outFields": "*",  # Get all available fields
            "returnGeometry": "true",
            "f": "geojson",  # Use GeoJSON format for easier processing
            "resultRecordCount": 10000,  # Higher limit for state-level queries
            "spatialRel": "esriSpatialRelIntersects"
        }
        
        try:
            # Apply rate limiting
            if self._rate_limiter:
                self._rate_limiter.wait_if_needed("census")
            
            # Use requests directly for the TIGER REST API
            import requests
            response = requests.get(base_url, params=params, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"TIGER API response keys: {list(data.keys())}")
                
                # Handle GeoJSON response format
                if "features" in data and isinstance(data["features"], list):
                    logger.info(f"Found {len(data['features'])} ZCTA features in response")
                    
                    if not data["features"]:
                        logger.warning(f"No ZCTA features returned for query")
                        return gpd.GeoDataFrame()
                    
                    # Log sample feature for debugging
                    sample_feature = data["features"][0]
                    logger.debug(f"Sample ZCTA feature properties: {list(sample_feature.get('properties', {}).keys())}")
                    
                    # Convert GeoJSON to GeoDataFrame
                    zctas = gpd.GeoDataFrame.from_features(data["features"], crs="EPSG:4326")
                    logger.info(f"Created GeoDataFrame with {len(zctas)} ZCTAs")
                    logger.debug(f"ZCTA columns: {list(zctas.columns)}")
                    
                    # The TIGER API returns all ZCTAs nationally, so we need to filter by state
                    # ZCTAs don't have direct state FIPS, so we'll use spatial filtering or GEOID prefix
                    original_count = len(zctas)
                    
                    # Method 1: Try filtering by GEOID prefix (first 2 digits often correspond to state)
                    # Note: This is approximate since ZCTAs can cross state boundaries
                    if 'GEOID' in zctas.columns:
                        # Filter ZCTAs that start with the state FIPS (approximate)
                        state_mask = zctas['GEOID'].str.startswith(state_fips)
                        if state_mask.any():
                            zctas = zctas[state_mask].copy()
                            logger.info(f"Filtered by GEOID prefix: {len(zctas)} ZCTAs for state {state_fips}")
                        else:
                            logger.warning(f"No ZCTAs found with GEOID prefix {state_fips}")
                    
                    # Method 2: If we still have too many or too few, try spatial filtering
                    # This would require state boundaries, which we'll skip for now
                    
                    if len(zctas) == 0:
                        logger.warning(f"No ZCTAs found for state {state_fips} after filtering")
                        return gpd.GeoDataFrame()
                    
                    # Standardize column names based on TIGER API field names
                    # From the API docs: GEOID, ZCTA5, BASENAME, NAME, etc.
                    column_mapping = {
                        'ZCTA5': 'ZCTA5CE',  # Map to standard column name
                        'GEOID': 'GEOID',    # Keep as is
                        'BASENAME': 'BASENAME',
                        'NAME': 'NAME'
                    }
                    
                    for old_col, new_col in column_mapping.items():
                        if old_col in zctas.columns and old_col != new_col:
                            zctas[new_col] = zctas[old_col]
                    
                    # Ensure we have the essential columns
                    if 'GEOID' not in zctas.columns:
                        if 'ZCTA5' in zctas.columns:
                            zctas['GEOID'] = zctas['ZCTA5']
                        else:
                            logger.error("No GEOID or ZCTA5 column found in response")
                            return gpd.GeoDataFrame()
                    
                    if 'ZCTA5CE' not in zctas.columns:
                        if 'ZCTA5' in zctas.columns:
                            zctas['ZCTA5CE'] = zctas['ZCTA5']
                        elif 'GEOID' in zctas.columns:
                            zctas['ZCTA5CE'] = zctas['GEOID']
                    
                    # Add state FIPS for consistency (approximate)
                    zctas['STATEFP'] = state_fips
                    
                    # Validate geometries
                    zctas = zctas[zctas.geometry.is_valid].copy()
                    
                    if len(zctas) == 0:
                        logger.warning(f"No valid ZCTA geometries found for state {state_fips}")
                        return gpd.GeoDataFrame()
                    
                    # Cache the result
                    if self._cache:
                        self._cache.set(cache_key, zctas, ttl=86400)  # Cache for 24 hours
                    
                    logger.info(f"Successfully retrieved {len(zctas)} ZCTAs for state {state_fips} (filtered from {original_count})")
                    return zctas
                    
                else:
                    logger.error(f"Unexpected TIGER API response format: {list(data.keys())}")
                    return gpd.GeoDataFrame()
                    
            else:
                logger.error(f"TIGER API returned status code {response.status_code}: {response.text}")
                return gpd.GeoDataFrame()
                
        except Exception as e:
            logger.error(f"Error fetching ZCTAs for state {state_fips} from TIGER API: {e}")
            return gpd.GeoDataFrame()
    
    def get_zctas_for_states(
        self, 
        state_fips_list: List[str]
    ) -> gpd.GeoDataFrame:
        """
        Fetch ZCTAs for multiple states and combine them.
        
        Args:
            state_fips_list: List of state FIPS codes
            
        Returns:
            Combined GeoDataFrame with ZCTAs for all states
        """
        all_zctas = []
        
        with get_progress_bar(total=len(state_fips_list), desc="Fetching ZCTAs by state", unit="state") as pbar:
            for state_fips in state_fips_list:
                pbar.update(1)
            try:
                state_zctas = self.get_zctas_for_state(state_fips)
                if not state_zctas.empty:
                    all_zctas.append(state_zctas)
                else:
                    logger.warning(f"No ZCTAs retrieved for state {state_fips}")
            except Exception as e:
                logger.warning(f"Error fetching ZCTAs for state {state_fips}: {e}")
        
        if not all_zctas:
            logger.error("No ZCTA data could be retrieved for any state")
            return gpd.GeoDataFrame()
        
        # Combine all state ZCTAs
        combined_zctas = pd.concat(all_zctas, ignore_index=True)
        logger.info(f"Combined {len(combined_zctas)} ZCTAs from {len(all_zctas)} states")
        return combined_zctas
    
    def get_zcta_urls(self, year: int = 2020) -> Dict[str, str]:
        """
        Get the download URLs for ZCTA shapefiles from the Census Bureau.
        
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
        """
        Validate and clean ZCTA GeoDataFrame.
        
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
    
    def get_zcta_for_point(self, lat: float, lon: float) -> Optional[str]:
        """
        Get the ZCTA code for a specific point.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            ZCTA code or None if not found
        """
        try:
            # Use Census geocoding API to get ZCTA
            from ..infrastructure.geocoder import CensusGeocoder
            geocoder = CensusGeocoder(self._config)
            result = geocoder.geocode_point(lat, lon)
            return result.zcta_geoid if result else None
        except Exception as e:
            logger.warning(f"Failed to get ZCTA for point ({lat}, {lon}): {e}")
            return None
    
    def get_census_data(
        self,
        geoids: List[str],
        variables: List[str],
        api_key: Optional[str] = None,
        geographic_level: str = "zcta"
    ) -> 'pd.DataFrame':
        """
        Get census data for ZCTA geoids.
        
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
        cache_key = f"zcta_census_data_{hash(tuple(sorted(geoids)))}{hash(tuple(sorted(variables)))}"
        if self._cache:
            cached_data = self._cache.get(cache_key)
            if cached_data:
                logger.info("Loaded cached ZCTA census data")
                return cached_data.data
        
        try:
            # Use the Census Data API for ZCTA data
            # The API format requires individual calls for each ZCTA due to the 'for' parameter limitation
            all_responses = []
            
            # Process ZCTAs in batches to respect API limits but handle individual geography
            for i, geoid in enumerate(geoids):
                if self._rate_limiter:
                    self._rate_limiter.wait_if_needed("census")
                
                # Build the geography parameter for single ZCTA
                geography_param = f"zip code tabulation area:{geoid}"
                
                logger.debug(f"Fetching data for ZCTA {geoid} ({i+1}/{len(geoids)})")
                
                try:
                    # Make the API call using the modern API client
                    api_response = self._api_client.get_census_data(
                        variables=variables + ["NAME"],  # Always include NAME
                        geography=geography_param,
                        year=2023,  # Use most recent ACS 5-year data
                        dataset="acs/acs5"
                    )
                    
                    if api_response and len(api_response) >= 2:
                        all_responses.extend(api_response[1:])  # Skip header for subsequent calls
                    
                except Exception as e:
                    logger.warning(f"Failed to fetch data for ZCTA {geoid}: {e}")
                    continue
            
            if not all_responses:
                logger.warning("No data returned from Census API for any ZCTAs")
                return pd.DataFrame()
            
            # Use headers from the first successful response
            if geoids:
                # Get headers by making a sample call
                try:
                    sample_response = self._api_client.get_census_data(
                        variables=variables + ["NAME"],
                        geography=f"zip code tabulation area:{geoids[0]}",
                        year=2023,
                        dataset="acs/acs5"
                    )
                    headers = sample_response[0] if sample_response else []
                except:
                    headers = variables + ["NAME", "zip code tabulation area"]
            
            # Create DataFrame from collected responses
            df = pd.DataFrame(all_responses, columns=headers)
            
            # Transform to legacy format expected by the adapters
            legacy_rows = []
            for _, row in df.iterrows():
                geoid = row.get('zip code tabulation area', '')
                
                for variable in variables:
                    if variable in row and row[variable] is not None:
                        try:
                            value = float(row[variable]) if row[variable] != '' else None
                        except (ValueError, TypeError):
                            value = None
                        
                        legacy_rows.append({
                            'GEOID': geoid,
                            'variable_code': variable,
                            'value': value,
                            'year': 2023,
                            'dataset': 'acs5',
                            'NAME': f"ZCTA5 {geoid}"
                        })
            
            result_df = pd.DataFrame(legacy_rows)
            
            # Cache the result
            if self._cache:
                self._cache.set(cache_key, result_df, ttl=3600)  # Cache for 1 hour
            
            logger.info(f"Successfully fetched census data for {len(result_df)} ZCTA-variable combinations")
            return result_df
            
        except Exception as e:
            logger.error(f"Error fetching ZCTA census data: {e}")
            # Return empty DataFrame in legacy format on error
            return pd.DataFrame(columns=['GEOID', 'variable_code', 'value', 'year', 'dataset', 'NAME'])
    
    def get_census_data_efficient(
        self,
        geoids: List[str],
        variables: List[str],
        batch_size: int = 50,
        year: int = 2023,
        dataset: str = "acs/acs5"
    ) -> pd.DataFrame:
        """
        Efficiently fetch census data for multiple ZCTAs using optimized batching.
        
        Based on the Census API format:
        https://api.census.gov/data/2023/acs/acs5?get=NAME,B01001_001E&for=zip%20code%20tabulation%20area:77494
        
        Args:
            geoids: List of ZCTA geoids (e.g., ['77494', '27601'])
            variables: List of census variable codes (e.g., ['B01001_001E'])
            batch_size: Number of ZCTAs to process per batch
            year: Census year (default: 2023)
            dataset: Census dataset (default: acs/acs5)
            
        Returns:
            DataFrame with census data in consistent format
        """
        import pandas as pd
        
        if not geoids or not variables:
            return pd.DataFrame()
        
        # Apply rate limiting
        if self._rate_limiter:
            self._rate_limiter.wait_if_needed("census")
        
        logger.info(f"Efficiently fetching census data for {len(geoids)} ZCTAs and {len(variables)} variables")
        
        # Check cache first
        cache_key = f"zcta_efficient_{year}_{dataset}_{hash(tuple(sorted(geoids)))}{hash(tuple(sorted(variables)))}"
        if self._cache:
            cached_data = self._cache.get(cache_key)
            if cached_data:
                logger.info("Loaded cached efficient ZCTA census data")
                return cached_data
        
        all_data = []
        
        # Process in smaller batches to respect API limits and improve reliability
        for i in range(0, len(geoids), batch_size):
            batch_geoids = geoids[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(geoids) + batch_size - 1) // batch_size
            
            logger.debug(f"Processing efficient batch {batch_num}/{total_batches}: {len(batch_geoids)} ZCTAs")
            
            try:
                batch_data = self._fetch_zcta_batch_data(batch_geoids, variables, year, dataset)
                if not batch_data.empty:
                    all_data.append(batch_data)
                    
            except Exception as e:
                logger.warning(f"Error fetching efficient batch {batch_num}: {e}")
                continue
        
        if not all_data:
            logger.warning("No efficient ZCTA data could be retrieved")
            return pd.DataFrame()
        
        # Combine all batches
        result_df = pd.concat(all_data, ignore_index=True)
        
        # Cache the result
        if self._cache:
            self._cache.set(cache_key, result_df, ttl=3600)  # Cache for 1 hour
        
        logger.info(f"Successfully retrieved efficient census data for {len(result_df)} ZCTA-variable combinations")
        return result_df
    
    def _fetch_zcta_batch_data(
        self, 
        geoids: List[str], 
        variables: List[str], 
        year: int, 
        dataset: str
    ) -> pd.DataFrame:
        """
        Fetch data for a batch of ZCTAs using the proper Census API format.
        
        Args:
            geoids: List of ZCTA geoids for this batch
            variables: List of census variable codes
            year: Census year
            dataset: Census dataset
            
        Returns:
            DataFrame with batch data
        """
        import pandas as pd
        
        all_rows = []
        
        # The Census API requires individual calls for each ZCTA geography
        for geoid in geoids:
            try:
                if self._rate_limiter:
                    self._rate_limiter.wait_if_needed("census")
                
                # Use the exact format from the example: 
                # https://api.census.gov/data/2023/acs/acs5?get=NAME,B01001_001E&for=zip%20code%20tabulation%20area:77494
                geography_param = f"zip code tabulation area:{geoid}"
                
                api_response = self._api_client.get_census_data(
                    variables=variables + ["NAME"],
                    geography=geography_param,
                    year=year,
                    dataset=dataset
                )
                
                if api_response and len(api_response) >= 2:
                    # Response format: [["NAME","B01001_001E","zip code tabulation area"], ["ZCTA5 77494","137213","77494"]]
                    headers = api_response[0]
                    data_row = api_response[1]
                    
                    # Create a row dictionary
                    row_dict = dict(zip(headers, data_row))
                    row_dict['GEOID'] = geoid  # Ensure we have a clean GEOID
                    all_rows.append(row_dict)
                    
                    logger.debug(f"Successfully fetched data for ZCTA {geoid}")
                else:
                    logger.warning(f"No data returned for ZCTA {geoid}")
                    
            except Exception as e:
                logger.warning(f"Error fetching data for ZCTA {geoid}: {e}")
                continue
        
        if not all_rows:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(all_rows)
        
        # Transform to consistent format
        return self._transform_to_standard_format(df, variables, year, dataset)
    
    def _transform_to_standard_format(
        self, 
        df: pd.DataFrame, 
        variables: List[str], 
        year: int, 
        dataset: str
    ) -> pd.DataFrame:
        """
        Transform API response DataFrame to standard format for consistency.
        
        Args:
            df: Raw API response DataFrame
            variables: List of variable codes
            year: Census year
            dataset: Census dataset
            
        Returns:
            DataFrame in standard format
        """
        import pandas as pd
        
        standard_rows = []
        
        for _, row in df.iterrows():
            geoid = row.get('GEOID', row.get('zip code tabulation area', ''))
            name = row.get('NAME', f"ZCTA5 {geoid}")
            
            for variable in variables:
                if variable in row and row[variable] is not None:
                    try:
                        # Handle Census null values and convert to float
                        raw_value = row[variable]
                        if raw_value in ['-999999999', '', None]:
                            value = None
                        else:
                            value = float(raw_value)
                    except (ValueError, TypeError):
                        value = None
                    
                    standard_rows.append({
                        'GEOID': geoid,
                        'variable_code': variable,
                        'value': value,
                        'year': year,
                        'dataset': dataset.replace('/', ''),  # Clean dataset name
                        'NAME': name
                    })
        
        return pd.DataFrame(standard_rows)
    
    def _check_arrow_support(self) -> bool:
        """Check if PyArrow is available for better performance."""
        try:
            import pyarrow
            import os
            os.environ["PYOGRIO_USE_ARROW"] = "1"
            return True
        except ImportError:
            return False
    
    def get_zctas_for_counties(self, counties: List[Tuple[str, str]]) -> gpd.GeoDataFrame:
        """
        Get ZCTAs that intersect with specific counties.
        
        Args:
            counties: List of (state_fips, county_fips) tuples
            
        Returns:
            GeoDataFrame with ZCTAs that intersect the counties
        """
        # Get unique states from the counties list
        state_fips_set = set(county[0] for county in counties)
        
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
        state_fips_list: List[str], 
        batch_size: int = 5,
        progress_callback: Optional[callable] = None
    ) -> gpd.GeoDataFrame:
        """
        Get ZCTAs for multiple states with batching and progress tracking.
        
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
            batch = state_fips_list[i:i + batch_size]
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
        
        # Combine all ZCTAs
        combined_zctas = pd.concat(all_zctas, ignore_index=True)
        logger.info(f"Successfully retrieved {len(combined_zctas)} total ZCTAs")
        
        return combined_zctas
    
    def get_zcta_census_data_batch(
        self,
        state_fips_list: List[str],
        variables: List[str],
        batch_size: int = 100
    ) -> pd.DataFrame:
        """
        Get census data for ZCTAs across multiple states with efficient batching.
        
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
        geoids = all_zctas['GEOID'].tolist() if 'GEOID' in all_zctas.columns else []
        
        if not geoids:
            logger.warning("No GEOIDs found in ZCTA data")
            return pd.DataFrame()
        
        logger.info(f"Fetching census data for {len(geoids)} ZCTAs in batches of {batch_size}")
        
        all_data = []
        
        # Process in batches to avoid API limits
        for i in range(0, len(geoids), batch_size):
            batch_geoids = geoids[i:i + batch_size]
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
        """
        Create a legacy streaming interface compatible with old adapters.
        
        Returns:
            Object with legacy streaming methods
        """
        class LegacyZctaInterface:
            def __init__(self, zcta_service):
                self._zcta_service = zcta_service
            
            def get_zctas(self, state_fips_list: List[str]) -> gpd.GeoDataFrame:
                """Legacy method: Get ZCTAs for multiple states."""
                return self._zcta_service.get_zctas_for_states(state_fips_list)
            
            def get_census_data(
                self,
                geoids: List[str],
                variables: List[str],
                api_key: Optional[str] = None,
                geographic_level: str = "zcta"
            ) -> pd.DataFrame:
                """Legacy method: Get census data for ZCTAs."""
                return self._zcta_service.get_census_data(geoids, variables, api_key, geographic_level)
        
        return LegacyZctaInterface(self) 