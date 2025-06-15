"""
Census Service - Main business logic for census data operations.

This service coordinates between the domain layer and infrastructure layer,
implementing the core business logic without depending on specific implementations.
"""

import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple

from ..domain.entities import CensusDataPoint, CensusVariable, GeographicUnit
from ..domain.interfaces import CensusDataDependencies


class CensusService:
    """Main service for census data operations."""
    
    def __init__(self, dependencies: CensusDataDependencies):
        """Initialize with injected dependencies."""
        self._api_client = dependencies.api_client
        self._cache = dependencies.cache
        self._repository = dependencies.repository
        self._config = dependencies.config
        self._rate_limiter = dependencies.rate_limiter
        self._logger = dependencies.logger
    
    def get_census_data(
        self,
        geoids: List[str],
        variable_codes: List[str],
        year: int = 2021,
        dataset: str = "acs/acs5",
        use_cache: bool = True
    ) -> List[CensusDataPoint]:
        """
        Get census data for specified geographic units and variables.
        
        Args:
            geoids: List of geographic unit identifiers
            variable_codes: List of census variable codes
            year: Census year
            dataset: Census dataset identifier
            use_cache: Whether to use cached data
            
        Returns:
            List of census data points
        """
        self._logger.info(
            f"Fetching census data for {len(geoids)} units, "
            f"{len(variable_codes)} variables"
        )
        
        # Try cache first if enabled
        if use_cache and self._config.cache_enabled:
            cached_data = self._get_cached_data(geoids, variable_codes, year, dataset)
            if cached_data:
                self._logger.debug(f"Retrieved {len(cached_data)} points from cache")
                return cached_data
        
        # Fetch from repository
        stored_data = self._repository.get_census_data(geoids, variable_codes)
        if stored_data:
            self._logger.debug(f"Retrieved {len(stored_data)} points from repository")
            if use_cache:
                self._cache_data(stored_data, year, dataset)
            return stored_data
        
        # Fetch from API as last resort
        api_data = self._fetch_from_api(geoids, variable_codes, year, dataset)
        
        # Store in repository for future use
        if api_data:
            self._repository.save_census_data(api_data)
            if use_cache:
                self._cache_data(api_data, year, dataset)
        
        self._logger.info(f"Successfully retrieved {len(api_data)} data points")
        return api_data
    
    def get_block_groups(
        self,
        state_fips: List[str],
        use_cache: bool = True
    ) -> List[GeographicUnit]:
        """
        Get block groups for specified states.
        
        Args:
            state_fips: List of state FIPS codes
            use_cache: Whether to use cached data
            
        Returns:
            List of geographic units representing block groups
        """
        self._logger.info(f"Fetching block groups for states: {state_fips}")
        
        cache_key = f"block_groups:{':'.join(sorted(state_fips))}"
        
        # Try cache first
        if use_cache and self._config.cache_enabled:
            cached_entry = self._cache.get(cache_key)
            if cached_entry and not cached_entry.is_expired:
                self._logger.debug("Retrieved block groups from cache")
                return cached_entry.data
        
        # Fetch from API
        block_groups = []
        for state in state_fips:
            self._rate_limiter.wait_if_needed("census_api")
            
            try:
                api_response = self._api_client.get_geographies(
                    geography_type="block group",
                    state_code=state
                )
                
                # Convert API response to domain entities
                for item in api_response.get("features", []):
                    props = item.get("properties", {})
                    geoid = props.get("GEOID")
                    if geoid:
                        unit = GeographicUnit(
                            geoid=geoid,
                            name=props.get("NAME"),
                            state_fips=props.get("STATEFP"),
                            county_fips=props.get("COUNTYFP"),
                            tract_code=props.get("TRACTCE"),
                            block_group_code=props.get("BLKGRPCE")
                        )
                        block_groups.append(unit)
                        
            except Exception as e:
                self._logger.error(f"Failed to fetch block groups for state {state}: {e}")
                continue
        
        # Cache the results
        if use_cache and block_groups:
            self._cache.set(
                cache_key, 
                block_groups, 
                ttl=self._config.cache_ttl_seconds
            )
        
        self._logger.info(f"Retrieved {len(block_groups)} block groups")
        return block_groups
    
    def _get_cached_data(
        self,
        geoids: List[str],
        variable_codes: List[str],
        year: int,
        dataset: str
    ) -> Optional[List[CensusDataPoint]]:
        """Retrieve cached census data."""
        cache_key = self._generate_cache_key(geoids, variable_codes, year, dataset)
        cached_entry = self._cache.get(cache_key)
        
        if cached_entry and not cached_entry.is_expired:
            return cached_entry.data
        
        return None
    
    def _cache_data(
        self,
        data: List[CensusDataPoint],
        year: int,
        dataset: str
    ) -> None:
        """Cache census data."""
        if not data:
            return
        
        # Group by geoids and variables for efficient caching
        geoids = list(set(point.geoid for point in data))
        variable_codes = list(set(point.variable.code for point in data))
        
        cache_key = self._generate_cache_key(geoids, variable_codes, year, dataset)
        self._cache.set(cache_key, data, ttl=self._config.cache_ttl_seconds)
    
    def _fetch_from_api(
        self,
        geoids: List[str],
        variable_codes: List[str],
        year: int,
        dataset: str
    ) -> List[CensusDataPoint]:
        """Fetch data from Census API."""
        data_points = []
        
        # Group GEOIDs by state and county for more specific API calls
        state_county_groups = self._group_geoids_by_state_and_county(geoids)
        
        for (state_fips, county_fips), county_geoids in state_county_groups.items():
            self._rate_limiter.wait_if_needed("census_api")
            
            try:
                # Build geography parameter for API - use separate 'for' and 'in' parameters
                geography = "block group:*"
                in_clause = f"state:{state_fips} county:{county_fips}"
                
                api_response = self._api_client.get_census_data(
                    variables=variable_codes + ["NAME"],
                    geography=geography,
                    year=year,
                    dataset=dataset,
                    **{"in": in_clause}  # Pass 'in' as a keyword argument
                )
                
                # Convert API response to domain entities
                data_points.extend(
                    self._convert_api_response(api_response, variable_codes, year, dataset)
                )
                
            except Exception as e:
                self._logger.error(f"API request failed for state {state_fips} county {county_fips}: {e}")
                continue
        
        # Filter to only requested GEOIDs
        filtered_data = [
            point for point in data_points 
            if point.geoid in geoids
        ]
        
        return filtered_data
    
    def _convert_api_response(
        self,
        api_response: Dict[str, Any],
        variable_codes: List[str],
        year: int,
        dataset: str
    ) -> List[CensusDataPoint]:
        """Convert API response to domain entities."""
        data_points = []
        
        # API returns data as list of lists, first row is headers
        if not api_response or len(api_response) < 2:
            return data_points
        
        headers = api_response[0]
        rows = api_response[1:]
        
        for row in rows:
            row_dict = dict(zip(headers, row, strict=False))
            
            # Build GEOID from components
            geoid = self._build_geoid_from_components(row_dict)
            if not geoid:
                continue
            
            # Create data points for each variable
            for var_code in variable_codes:
                if var_code in row_dict:
                    try:
                        value = float(row_dict[var_code]) if row_dict[var_code] != "-999999999" else None
                    except (ValueError, TypeError):
                        value = None
                    
                    # Create a minimal variable entity (name lookup would need separate service)
                    variable = CensusVariable(code=var_code, name=var_code)
                    
                    data_point = CensusDataPoint(
                        geoid=geoid,
                        variable=variable,
                        value=value,
                        year=year,
                        dataset=dataset
                    )
                    data_points.append(data_point)
        
        return data_points
    
    def _build_geoid_from_components(self, row_dict: Dict[str, str]) -> Optional[str]:
        """Build GEOID from API response components."""
        try:
            state = row_dict.get("state", "").zfill(2)
            county = row_dict.get("county", "").zfill(3)
            tract = row_dict.get("tract", "").zfill(6)
            block_group = row_dict.get("block group", "")
            
            if all([state, county, tract, block_group]):
                return f"{state}{county}{tract}{block_group}"
        except (KeyError, AttributeError):
            pass
        
        return None
    
    def _group_geoids_by_state(self, geoids: List[str]) -> Dict[str, List[str]]:
        """Group GEOIDs by state for efficient API calls."""
        state_groups = {}
        
        for geoid in geoids:
            if len(geoid) >= 2:
                state_fips = geoid[:2]
                if state_fips not in state_groups:
                    state_groups[state_fips] = []
                state_groups[state_fips].append(geoid)
        
        return state_groups
    
    def _group_geoids_by_state_and_county(self, geoids: List[str]) -> Dict[Tuple[str, str], List[str]]:
        """Group GEOIDs by state and county for more specific API calls."""
        state_county_groups = {}
        
        for geoid in geoids:
            if len(geoid) >= 5:  # Need at least state (2) + county (3) digits
                state_fips = geoid[:2]
                county_fips = geoid[2:5]
                key = (state_fips, county_fips)
                if key not in state_county_groups:
                    state_county_groups[key] = []
                state_county_groups[key].append(geoid)
        
        return state_county_groups
    
    def _generate_cache_key(
        self,
        geoids: List[str],
        variable_codes: List[str],
        year: int,
        dataset: str
    ) -> str:
        """Generate a cache key for the request."""
        # Create a stable hash of the request parameters
        request_data = {
            "geoids": sorted(geoids),
            "variables": sorted(variable_codes),
            "year": year,
            "dataset": dataset
        }
        
        request_json = json.dumps(request_data, sort_keys=True)
        hash_object = hashlib.md5(request_json.encode())
        return f"census_data:{hash_object.hexdigest()}" 