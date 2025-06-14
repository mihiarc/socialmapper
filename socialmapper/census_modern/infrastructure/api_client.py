"""
Census Bureau API client implementation.

Handles all interactions with the Census Bureau's APIs including:
- Data API for census variables
- Geography API for boundaries
- Proper error handling and retries
- Rate limiting compliance
"""

import requests
import time
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlencode

from ..domain.interfaces import ConfigurationProvider


class CensusAPIError(Exception):
    """Base exception for Census API errors."""
    pass


class CensusAPIRateLimitError(CensusAPIError):
    """Raised when API rate limit is exceeded."""
    pass


class CensusAPIClientImpl:
    """
    Concrete implementation of Census Bureau API client.
    
    Handles all the complexity of interacting with Census APIs while
    providing a clean interface to the service layer.
    """
    
    def __init__(self, config: ConfigurationProvider, logger: logging.Logger):
        """Initialize with configuration and logger."""
        self._config = config
        self._logger = logger
        self._session = self._create_session()
        
        # API endpoints
        self._data_base_url = config.get_setting("api_base_url", "https://api.census.gov/data")
        self._geo_base_url = "https://tigerweb.geo.census.gov/arcgis/rest/services"
        
    def get_census_data(
        self, 
        variables: List[str],
        geography: str,
        year: int,
        dataset: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch census data from the Census Bureau Data API.
        
        Args:
            variables: List of variable codes to fetch
            geography: Geography specification (e.g., "block group:*")
            year: Census year
            dataset: Dataset identifier (e.g., "acs/acs5")
            **kwargs: Additional parameters for the API call
            
        Returns:
            Raw API response as dictionary
            
        Raises:
            CensusAPIError: If the API request fails
        """
        # Build the API URL
        url = f"{self._data_base_url}/{year}/{dataset}"
        
        # Prepare parameters
        params = {
            "get": ",".join(variables),
            "for": geography,
            **kwargs
        }
        
        # Add API key if available
        if self._config.census_api_key:
            params["key"] = self._config.census_api_key
        
        self._logger.debug(f"Census API request: {url} with params: {params}")
        
        # Make the request with retries
        response_data = self._make_request_with_retries(url, params)
        
        self._logger.debug(f"Census API response: {len(response_data) if response_data else 0} rows")
        return response_data
    
    def get_geographies(
        self,
        geography_type: str,
        state_code: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch geographic boundaries from Census TIGER/Web services.
        
        Args:
            geography_type: Type of geography (e.g., "block group", "tract")
            state_code: Optional state FIPS code to filter by
            **kwargs: Additional parameters
            
        Returns:
            GeoJSON-like response with geographic features
            
        Raises:
            CensusAPIError: If the API request fails
        """
        # Map geography types to TIGER service endpoints
        service_map = {
            "block group": "Census2020/tigerWMS_Census2020_Tracts_Blocks/MapServer/1",
            "tract": "Census2020/tigerWMS_Census2020_Tracts_Blocks/MapServer/0", 
            "county": "Census2020/tigerWMS_Census2020_State_County/MapServer/1",
            "state": "Census2020/tigerWMS_Census2020_State_County/MapServer/0"
        }
        
        service_path = service_map.get(geography_type.lower())
        if not service_path:
            raise CensusAPIError(f"Unsupported geography type: {geography_type}")
        
        # Build URL for TIGER Web service
        url = f"{self._geo_base_url}/{service_path}/query"
        
        # Prepare parameters for ArcGIS REST API
        params = {
            "where": "1=1",  # Get all features
            "outFields": "*",
            "f": "geojson",
            "returnGeometry": "true"
        }
        
        # Add state filter if provided
        if state_code:
            params["where"] = f"STATEFP='{state_code.zfill(2)}'"
        
        # Add any additional parameters
        params.update(kwargs)
        
        self._logger.debug(f"Geography API request: {url} with params: {params}")
        
        # Make the request
        response_data = self._make_request_with_retries(url, params)
        
        feature_count = len(response_data.get("features", []))
        self._logger.debug(f"Geography API response: {feature_count} features")
        
        return response_data
    
    def _create_session(self) -> requests.Session:
        """Create a configured requests session."""
        session = requests.Session()
        
        # Set timeout from config
        timeout = self._config.get_setting("api_timeout_seconds", 30)
        session.timeout = timeout
        
        # Set user agent
        session.headers.update({
            "User-Agent": "SocialMapper/1.0 (https://github.com/your-org/socialmapper)"
        })
        
        return session
    
    def _make_request_with_retries(
        self, 
        url: str, 
        params: Dict[str, Any],
        max_retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request with exponential backoff retry logic.
        
        Args:
            url: Request URL
            params: Request parameters
            max_retries: Maximum number of retries (uses config default if None)
            
        Returns:
            Parsed JSON response
            
        Raises:
            CensusAPIError: If all retries are exhausted
        """
        if max_retries is None:
            max_retries = self._config.get_setting("max_retries", 3)
        
        backoff_factor = self._config.get_setting("retry_backoff_factor", 0.5)
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                # Log API requests if enabled
                if self._config.get_setting("log_api_requests", False):
                    self._logger.info(f"API Request (attempt {attempt + 1}): {url}")
                
                response = self._session.get(url, params=params)
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    self._logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    time.sleep(retry_after)
                    raise CensusAPIRateLimitError("Rate limit exceeded")
                
                # Raise for other HTTP errors
                response.raise_for_status()
                
                # Parse JSON response
                try:
                    data = response.json()
                except ValueError as e:
                    raise CensusAPIError(f"Invalid JSON response: {e}")
                
                # Check for API-level errors
                if isinstance(data, dict) and "error" in data:
                    error_msg = data.get("error", "Unknown API error")
                    raise CensusAPIError(f"Census API error: {error_msg}")
                
                return data
                
            except (requests.RequestException, CensusAPIError) as e:
                last_exception = e
                
                if attempt < max_retries:
                    # Calculate backoff delay
                    delay = backoff_factor * (2 ** attempt)
                    self._logger.warning(
                        f"Request failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                        f"Retrying in {delay:.1f} seconds..."
                    )
                    time.sleep(delay)
                else:
                    self._logger.error(f"All retries exhausted. Last error: {e}")
        
        # If we get here, all retries failed
        raise CensusAPIError(f"Request failed after {max_retries + 1} attempts: {last_exception}")
    
    def get_variable_metadata(self, year: int, dataset: str) -> Dict[str, Any]:
        """
        Get metadata about available variables for a dataset.
        
        Args:
            year: Census year
            dataset: Dataset identifier
            
        Returns:
            Variable metadata dictionary
        """
        url = f"{self._data_base_url}/{year}/{dataset}/variables.json"
        
        self._logger.debug(f"Fetching variable metadata: {url}")
        
        try:
            response_data = self._make_request_with_retries(url, {})
            return response_data.get("variables", {})
        except CensusAPIError as e:
            self._logger.warning(f"Failed to fetch variable metadata: {e}")
            return {}
    
    def get_geography_metadata(self, year: int, dataset: str) -> Dict[str, Any]:
        """
        Get metadata about available geographies for a dataset.
        
        Args:
            year: Census year  
            dataset: Dataset identifier
            
        Returns:
            Geography metadata dictionary
        """
        url = f"{self._data_base_url}/{year}/{dataset}/geography.json"
        
        self._logger.debug(f"Fetching geography metadata: {url}")
        
        try:
            response_data = self._make_request_with_retries(url, {})
            return response_data
        except CensusAPIError as e:
            self._logger.warning(f"Failed to fetch geography metadata: {e}")
            return {}
    
    def health_check(self) -> bool:
        """
        Check if the Census API is accessible.
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            # Simple request to check API availability
            url = f"{self._data_base_url}/2021/acs/acs5/variables.json"
            self._make_request_with_retries(url, {}, max_retries=1)
            return True
        except CensusAPIError:
            return False 