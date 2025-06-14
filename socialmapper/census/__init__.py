"""
Modern Census System for SocialMapper.

This module provides a comprehensive, modern census data system with:
- Domain-driven design with immutable entities
- Dependency injection for all external dependencies  
- Protocol-based interfaces for flexibility
- Clean separation of concerns
- Zero global state
- Full backward compatibility during transition

Key Components:
- CensusService: Core census data operations
- VariableService: Census variable mapping and validation
- GeographyService: State/county/geography operations
- BlockGroupService: Block group boundary operations
- GeocoderService: Point-to-geography lookups

Usage:
    # Basic usage with default configuration
    from socialmapper.census import get_census_system
    
    census = get_census_system()
    data = census.get_census_data(['B01003_001E'], ['37183'])
    
    # Advanced usage with custom configuration
    from socialmapper.census import CensusSystemBuilder
    
    census = (CensusSystemBuilder()
              .with_api_key("your_key")
              .with_cache_strategy("file")
              .with_rate_limit(2.0)
              .build())
"""

from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum
import os

# Import domain entities
from .domain.entities import (
    CensusDataPoint,
    GeographicUnit, 
    CensusVariable,
    StateInfo,
    CountyInfo,
    BlockGroupInfo,
    CacheEntry
)

# Import services
from .services.census_service import CensusService
from .services.variable_service import CensusVariableService, VariableFormat
from .services.geography_service import GeographyService, StateFormat
from .services.block_group_service import BlockGroupService
from .services.zcta_service import ZctaService

# Import infrastructure
from .infrastructure.configuration import CensusConfig, ConfigurationProvider
from .infrastructure.api_client import CensusAPIClientImpl
from .infrastructure.cache import (
    InMemoryCacheProvider,
    FileCacheProvider,
    HybridCacheProvider,
    NoOpCacheProvider
)
from .infrastructure.rate_limiter import TokenBucketRateLimiter
from .infrastructure.repository import (
    InMemoryRepository,
    SQLiteRepository,
    NoOpRepository
)
from .infrastructure.geocoder import CensusGeocoder

# Import adapters
# from .adapters.legacy_adapter import LegacyCensusAdapter  # Temporarily disabled to avoid circular imports


class CacheStrategy(Enum):
    """Cache strategy options."""
    IN_MEMORY = "in_memory"
    FILE = "file"
    HYBRID = "hybrid"
    NONE = "none"


class RepositoryType(Enum):
    """Repository type options."""
    IN_MEMORY = "in_memory"
    SQLITE = "sqlite"
    NONE = "none"


class CensusSystem:
    """
    Main interface for the modern census system.
    
    Provides a unified API for all census operations while maintaining
    clean separation of concerns through dependency injection.
    """
    
    def __init__(
        self,
        census_service: CensusService,
        variable_service: CensusVariableService,
        geography_service: GeographyService,
        block_group_service: BlockGroupService,
        zcta_service: ZctaService,
        geocoder: CensusGeocoder
    ):
        self._census_service = census_service
        self._variable_service = variable_service
        self._geography_service = geography_service
        self._block_group_service = block_group_service
        self._zcta_service = zcta_service
        self._geocoder = geocoder
    
    # Census Data Operations
    def get_census_data(
        self, 
        variables: List[str], 
        geographic_units: List[str],
        year: int = 2022
    ) -> List[CensusDataPoint]:
        """Get census data for specified variables and geographic units."""
        return self._census_service.get_census_data(variables, geographic_units, year)
    
    def get_census_data_for_counties(
        self,
        variables: List[str],
        counties: List[Tuple[str, str]],
        year: int = 2022
    ) -> List[CensusDataPoint]:
        """Get census data for specified counties."""
        return self._census_service.get_census_data_for_counties(variables, counties, year)
    
    # Variable Operations
    def normalize_variable(self, variable: str) -> str:
        """Normalize a census variable to its code form."""
        return self._variable_service.normalize_variable(variable)
    
    def get_readable_variable(self, variable: str) -> str:
        """Get human-readable representation of a census variable."""
        return self._variable_service.get_readable_variable(variable)
    
    def get_readable_variables(self, variables: List[str]) -> List[str]:
        """Get human-readable representations for multiple variables."""
        return self._variable_service.get_readable_variables(variables)
    
    def validate_variable(self, variable: str) -> bool:
        """Validate a census variable code or name."""
        return self._variable_service.validate_variable(variable)
    
    def get_variable_colormap(self, variable: str) -> str:
        """Get recommended colormap for a census variable."""
        return self._variable_service.get_colormap(variable)
    
    # Geography Operations
    def normalize_state(
        self, 
        state: Union[str, int], 
        to_format: StateFormat = StateFormat.ABBREVIATION
    ) -> Optional[str]:
        """Convert state identifier to requested format."""
        return self._geography_service.normalize_state(state, to_format)
    
    def is_valid_state(self, state: Union[str, int]) -> bool:
        """Check if state identifier is valid."""
        return self._geography_service.is_valid_state(state)
    
    def get_all_states(self, format: StateFormat = StateFormat.ABBREVIATION) -> List[str]:
        """Get list of all US states in requested format."""
        return self._geography_service.get_all_states(format)
    
    def create_state_info(self, state: Union[str, int]) -> Optional[StateInfo]:
        """Create StateInfo entity from any state identifier."""
        return self._geography_service.create_state_info(state)
    
    def create_county_info(
        self, 
        state_fips: str, 
        county_fips: str, 
        name: Optional[str] = None
    ) -> CountyInfo:
        """Create CountyInfo entity."""
        return self._geography_service.create_county_info(state_fips, county_fips, name)
    
    # Block Group Operations
    def get_block_groups_for_county(
        self, 
        state_fips: str, 
        county_fips: str
    ) -> 'gpd.GeoDataFrame':
        """Fetch block group boundaries for a county."""
        return self._block_group_service.get_block_groups_for_county(state_fips, county_fips)
    
    def get_block_groups_for_counties(
        self, 
        counties: List[Tuple[str, str]]
    ) -> 'gpd.GeoDataFrame':
        """Fetch block groups for multiple counties."""
        return self._block_group_service.get_block_groups_for_counties(counties)
    
    def get_block_group_urls(self, state_fips: str, year: int = 2022) -> Dict[str, str]:
        """Get TIGER/Line shapefile URLs for block groups."""
        return self._block_group_service.get_block_group_urls(state_fips, year)
    
    # ZCTA Operations
    def get_zctas_for_state(self, state_fips: str) -> 'gpd.GeoDataFrame':
        """Fetch ZCTA boundaries for a state."""
        return self._zcta_service.get_zctas_for_state(state_fips)
    
    def get_zctas_for_states(self, state_fips_list: List[str]) -> 'gpd.GeoDataFrame':
        """Fetch ZCTAs for multiple states."""
        return self._zcta_service.get_zctas_for_states(state_fips_list)
    
    def get_zctas(self, state_fips_list: List[str]) -> 'gpd.GeoDataFrame':
        """Legacy compatibility method for get_zctas_for_states."""
        return self.get_zctas_for_states(state_fips_list)
    
    def get_zcta_urls(self, year: int = 2020) -> Dict[str, str]:
        """Get TIGER/Line shapefile URLs for ZCTAs."""
        return self._zcta_service.get_zcta_urls(year)
    
    # Enhanced ZCTA Operations (New methods to replace legacy adapters)
    def get_zctas_for_counties(self, counties: List[Tuple[str, str]]) -> 'gpd.GeoDataFrame':
        """Get ZCTAs that intersect with specific counties."""
        return self._zcta_service.get_zctas_for_counties(counties)
    
    def get_zcta_census_data(
        self,
        geoids: List[str],
        variables: List[str],
        api_key: Optional[str] = None
    ) -> 'pd.DataFrame':
        """Get census data for ZCTA GEOIDs."""
        return self._zcta_service.get_census_data(geoids, variables, api_key)
    
    def get_zcta_census_data_batch(
        self,
        state_fips_list: List[str],
        variables: List[str],
        batch_size: int = 100
    ) -> 'pd.DataFrame':
        """Get census data for ZCTAs across multiple states with efficient batching."""
        return self._zcta_service.get_zcta_census_data_batch(state_fips_list, variables, batch_size)
    
    def batch_get_zctas(
        self, 
        state_fips_list: List[str], 
        batch_size: int = 5,
        progress_callback: Optional[callable] = None
    ) -> 'gpd.GeoDataFrame':
        """Get ZCTAs for multiple states with batching and progress tracking."""
        return self._zcta_service.batch_get_zctas(state_fips_list, batch_size, progress_callback)
    
    def get_zcta_for_point(self, lat: float, lon: float) -> Optional[str]:
        """Get the ZCTA code for a specific point."""
        return self._zcta_service.get_zcta_for_point(lat, lon)
    
    def create_streaming_manager(self):
        """
        Create a streaming manager interface for backward compatibility.
        
        This replaces the legacy get_streaming_census_manager() function.
        
        Returns:
            Streaming manager with ZCTA and census data methods
        """
        class ModernStreamingManager:
            def __init__(self, census_system):
                self._census_system = census_system
            
            def get_zctas(self, state_fips_list: List[str]) -> 'gpd.GeoDataFrame':
                """Get ZCTAs for multiple states."""
                return self._census_system.get_zctas_for_states(state_fips_list)
            
            def get_census_data(
                self,
                geoids: List[str],
                variables: List[str],
                api_key: Optional[str] = None,
                geographic_level: str = "zcta"
            ) -> 'pd.DataFrame':
                """Get census data for ZCTAs."""
                return self._census_system.get_zcta_census_data(geoids, variables, api_key)
            
            def get_zctas_batch(
                self,
                state_fips_list: List[str], 
                batch_size: int = 5,
                progress_callback: Optional[callable] = None
            ) -> 'gpd.GeoDataFrame':
                """Get ZCTAs with batching support."""
                return self._census_system.batch_get_zctas(state_fips_list, batch_size, progress_callback)
        
        return ModernStreamingManager(self)
    
    # Geocoding Operations
    def get_geography_from_point(
        self, 
        lat: float, 
        lon: float
    ) -> Optional[Dict[str, Optional[str]]]:
        """Get geographic identifiers for a point."""
        try:
            result = self._geocoder.geocode_point(lat, lon)
            if result and result.state_fips:
                return {
                    "state_fips": result.state_fips,
                    "county_fips": result.county_fips,
                    "tract_geoid": result.tract_geoid,
                    "block_group_geoid": result.block_group_geoid,
                    "zcta_geoid": result.zcta_geoid,
                }
        except Exception as e:
            # Log the error but don't fail completely
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Geocoding failed for point ({lat}, {lon}): {e}")
        return None
    
    def get_counties_from_pois(
        self,
        pois: List[Dict[str, Any]],
        include_neighbors: bool = True
    ) -> List[Tuple[str, str]]:
        """Get counties for a list of POIs."""
        counties = set()
        failed_pois = 0
        
        for poi in pois:
            if "lat" in poi and "lon" in poi:
                geo_info = self.get_geography_from_point(poi["lat"], poi["lon"])
                if geo_info and geo_info.get("state_fips") and geo_info.get("county_fips"):
                    counties.add((geo_info["state_fips"], geo_info["county_fips"]))
                else:
                    failed_pois += 1
        
        if failed_pois > 0:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to geocode {failed_pois} out of {len(pois)} POIs")
        
        # TODO: Add neighbor functionality when neighbor system is integrated
        return sorted(list(counties))
    
    # Neighbor Operations
    def get_neighboring_states(self, state_fips: str) -> List[str]:
        """Get neighboring states for a given state."""
        # For now, return hardcoded neighbor relationships
        # TODO: Implement proper neighbor data loading and storage
        state_neighbors = {
            '01': ['13', '28', '47'],  # Alabama: GA, MS, TN
            '04': ['06', '08', '32', '35', '49'],  # Arizona: CA, CO, NV, NM, UT
            '05': ['22', '28', '29', '40', '47', '48'],  # Arkansas: LA, MS, MO, OK, TN, TX
            '06': ['04', '32', '41'],  # California: AZ, NV, OR
            '08': ['04', '20', '31', '35', '49', '56'],  # Colorado: AZ, KS, NE, NM, UT, WY
            '09': ['25', '36', '44'],  # Connecticut: MA, NY, RI
            '10': ['24', '34', '42'],  # Delaware: MD, NJ, PA
            '12': ['01', '13'],  # Florida: AL, GA
            '13': ['01', '12', '37', '45', '47'],  # Georgia: AL, FL, NC, SC, TN
            '16': ['30', '32', '41', '49', '53'],  # Idaho: MT, NV, OR, UT, WA
            '17': ['18', '19', '26', '29', '55'],  # Illinois: IN, IA, MI, MO, WI
            '18': ['17', '21', '26', '39'],  # Indiana: IL, KY, MI, OH
            '19': ['17', '20', '27', '29', '31', '46'],  # Iowa: IL, KS, MN, MO, NE, SD
            '20': ['08', '19', '29', '31', '40'],  # Kansas: CO, IA, MO, NE, OK
            '21': ['17', '18', '28', '29', '39', '47', '51', '54'],  # Kentucky: IL, IN, MS, MO, OH, TN, VA, WV
            '22': ['05', '28', '48'],  # Louisiana: AR, MS, TX
            '23': ['33'],  # Maine: NH
            '24': ['10', '34', '42', '51', '54'],  # Maryland: DE, NJ, PA, VA, WV
            '25': ['09', '33', '36', '44', '50'],  # Massachusetts: CT, NH, NY, RI, VT
            '26': ['17', '18', '39', '55'],  # Michigan: IL, IN, OH, WI
            '27': ['19', '30', '38', '46', '55'],  # Minnesota: IA, MT, ND, SD, WI
            '28': ['01', '05', '21', '22', '47'],  # Mississippi: AL, AR, KY, LA, TN
            '29': ['05', '17', '19', '20', '21', '31', '40', '47'],  # Missouri: AR, IL, IA, KS, KY, NE, OK, TN
            '30': ['16', '27', '38', '46', '56'],  # Montana: ID, MN, ND, SD, WY
            '31': ['08', '19', '20', '29', '46', '56'],  # Nebraska: CO, IA, KS, MO, SD, WY
            '32': ['04', '06', '16', '41', '49'],  # Nevada: AZ, CA, ID, OR, UT
            '33': ['23', '25', '50'],  # New Hampshire: ME, MA, VT
            '34': ['10', '24', '36', '42'],  # New Jersey: DE, MD, NY, PA
            '35': ['04', '08', '40', '48'],  # New Mexico: AZ, CO, OK, TX
            '36': ['09', '25', '34', '42', '50'],  # New York: CT, MA, NJ, PA, VT
            '37': ['13', '45', '47', '51'],  # North Carolina: GA, SC, TN, VA
            '38': ['27', '30', '46'],  # North Dakota: MN, MT, SD
            '39': ['18', '21', '26', '42', '54'],  # Ohio: IN, KY, MI, PA, WV
            '40': ['05', '08', '20', '29', '35', '48'],  # Oklahoma: AR, CO, KS, MO, NM, TX
            '41': ['06', '16', '32', '53'],  # Oregon: CA, ID, NV, WA
            '42': ['10', '24', '34', '36', '39', '54'],  # Pennsylvania: DE, MD, NJ, NY, OH, WV
            '44': ['09', '25'],  # Rhode Island: CT, MA
            '45': ['13', '37'],  # South Carolina: GA, NC
            '46': ['19', '27', '30', '31', '38', '56'],  # South Dakota: IA, MN, MT, NE, ND, WY
            '47': ['01', '05', '13', '21', '28', '29', '37', '51'],  # Tennessee: AL, AR, GA, KY, MS, MO, NC, VA
            '48': ['05', '22', '35', '40'],  # Texas: AR, LA, NM, OK
            '49': ['04', '08', '16', '32', '56'],  # Utah: AZ, CO, ID, NV, WY
            '50': ['25', '33', '36'],  # Vermont: MA, NH, NY
            '51': ['21', '24', '37', '47', '54'],  # Virginia: KY, MD, NC, TN, WV
            '53': ['16', '41'],  # Washington: ID, OR
            '54': ['21', '24', '39', '42', '51'],  # West Virginia: KY, MD, OH, PA, VA
            '55': ['17', '26', '27', '46'],  # Wisconsin: IL, MI, MN, SD
            '56': ['08', '16', '30', '31', '46', '49'],  # Wyoming: CO, ID, MT, NE, SD, UT
        }
        return state_neighbors.get(state_fips, [])
    
    def get_neighboring_counties(self, county_fips: str) -> List[str]:
        """Get neighboring counties for a given county."""
        # For now, return empty list as county neighbor data is more complex
        # TODO: Implement proper county neighbor data loading
        return []
    
    # Utility Methods
    def health_check(self) -> Dict[str, bool]:
        """Check health of all system components."""
        return {
            "api_client": self._census_service._api_client.health_check(),
            "geocoder": self._geocoder.health_check(),
            "cache": True,  # Cache is always available
            "rate_limiter": True,  # Rate limiter is always available
        }


class CensusSystemBuilder:
    """
    Builder for creating configured CensusSystem instances.
    
    Provides a fluent interface for configuring all aspects of the census system
    while maintaining sensible defaults.
    """
    
    def __init__(self):
        self._api_key: Optional[str] = None
        self._cache_strategy: CacheStrategy = CacheStrategy.IN_MEMORY
        self._cache_dir: Optional[str] = None
        self._rate_limit: float = 1.0
        self._repository_type: RepositoryType = RepositoryType.IN_MEMORY
        self._api_timeout: int = 30
        self._max_retries: int = 3
    
    def with_api_key(self, api_key: str) -> 'CensusSystemBuilder':
        """Set the Census API key."""
        self._api_key = api_key
        return self
    
    def with_cache_strategy(self, strategy: Union[str, CacheStrategy]) -> 'CensusSystemBuilder':
        """Set the cache strategy."""
        if isinstance(strategy, str):
            strategy = CacheStrategy(strategy)
        self._cache_strategy = strategy
        return self
    
    def with_cache_dir(self, cache_dir: str) -> 'CensusSystemBuilder':
        """Set the cache directory."""
        self._cache_dir = cache_dir
        return self
    
    def with_rate_limit(self, requests_per_second: float) -> 'CensusSystemBuilder':
        """Set the rate limit for API requests."""
        self._rate_limit = requests_per_second
        return self
    
    def with_repository_type(self, repo_type: Union[str, RepositoryType]) -> 'CensusSystemBuilder':
        """Set the repository type for data persistence."""
        if isinstance(repo_type, str):
            repo_type = RepositoryType(repo_type)
        self._repository_type = repo_type
        return self
    
    def with_api_timeout(self, timeout_seconds: int) -> 'CensusSystemBuilder':
        """Set the API request timeout."""
        self._api_timeout = timeout_seconds
        return self
    
    def with_max_retries(self, max_retries: int) -> 'CensusSystemBuilder':
        """Set the maximum number of API request retries."""
        self._max_retries = max_retries
        return self
    
    def build(self) -> CensusSystem:
        """Build the configured CensusSystem."""
        # Create configuration
        config = ConfigurationProvider(CensusConfig(
            census_api_key=self._api_key or os.getenv("CENSUS_API_KEY"),
            api_timeout_seconds=self._api_timeout,
            max_retries=self._max_retries,
            rate_limit_requests_per_minute=int(self._rate_limit * 60),  # Convert to per minute
            cache_enabled=self._cache_strategy != CacheStrategy.NONE,
        ))
        
        # Create infrastructure components
        import logging
        logger = logging.getLogger(__name__)
        api_client = CensusAPIClientImpl(config, logger)
        rate_limiter = TokenBucketRateLimiter(
            requests_per_minute=config.get_setting("rate_limit_requests_per_minute", 60)
        )
        
        # Create cache
        if self._cache_strategy == CacheStrategy.IN_MEMORY:
            cache = InMemoryCacheProvider(max_size=1000)
        elif self._cache_strategy == CacheStrategy.FILE:
            cache_dir = self._cache_dir or "cache"
            cache = FileCacheProvider(cache_dir=cache_dir, max_files=10000)
        elif self._cache_strategy == CacheStrategy.HYBRID:
            cache_dir = self._cache_dir or "cache"
            cache = HybridCacheProvider(
                memory_cache_size=100,
                file_cache_dir=cache_dir,
                file_cache_max_files=10000
            )
        else:
            cache = NoOpCacheProvider()
        
        # Create repository
        if self._repository_type == RepositoryType.SQLITE:
            repository = SQLiteRepository(db_path="census_data.db", logger=logger)
        elif self._repository_type == RepositoryType.IN_MEMORY:
            repository = InMemoryRepository()
        else:
            repository = NoOpRepository()
        
        # Create geocoder
        geocoder = CensusGeocoder(config, logger)
        
        # Create dependency objects
        class Dependencies:
            def __init__(self, api_client, cache, repository, config, rate_limiter, logger):
                self.api_client = api_client
                self.cache = cache
                self.repository = repository
                self.config = config
                self.rate_limiter = rate_limiter
                self.logger = logger
        
        dependencies = Dependencies(api_client, cache, repository, config, rate_limiter, logger)
        
        # Create services
        census_service = CensusService(dependencies)
        variable_service = CensusVariableService(config)
        geography_service = GeographyService(config, geocoder)
        block_group_service = BlockGroupService(config, api_client, cache, rate_limiter)
        zcta_service = ZctaService(config, api_client, cache, rate_limiter)
        
        return CensusSystem(
            census_service=census_service,
            variable_service=variable_service,
            geography_service=geography_service,
            block_group_service=block_group_service,
            zcta_service=zcta_service,
            geocoder=geocoder
        )


# Convenience functions for common use cases
def get_census_system(
    api_key: Optional[str] = None,
    cache_strategy: str = "in_memory",
    cache_dir: Optional[str] = None
) -> CensusSystem:
    """
    Get a configured CensusSystem with sensible defaults.
    
    Args:
        api_key: Census API key (defaults to CENSUS_API_KEY env var)
        cache_strategy: Cache strategy ("in_memory", "file", "hybrid", "none")
        cache_dir: Cache directory (for file-based caching)
        
    Returns:
        Configured CensusSystem instance
    """
    builder = CensusSystemBuilder()
    
    if api_key:
        builder = builder.with_api_key(api_key)
    
    builder = builder.with_cache_strategy(cache_strategy)
    
    if cache_dir:
        builder = builder.with_cache_dir(cache_dir)
    
    return builder.build()


def get_legacy_adapter(census_system: Optional[CensusSystem] = None):
    """
    Get a legacy adapter for backward compatibility.
    
    Args:
        census_system: Optional CensusSystem instance (creates default if None)
        
    Returns:
        LegacyCensusAdapter instance
    """
    # Import here to avoid circular dependency
    from .adapters.legacy_adapter import LegacyCensusAdapter
    
    if census_system is None:
        census_system = get_census_system()
    
    return LegacyCensusAdapter(census_system)


def get_streaming_census_manager(
    cache_census_data: bool = False, 
    cache_dir: Optional[str] = None
):
    """
    Modern replacement for legacy streaming census manager.
    
    This function provides the same interface as the legacy version
    but uses the modern census system underneath.
    
    Args:
        cache_census_data: Whether to enable caching (legacy parameter)
        cache_dir: Cache directory (legacy parameter)
        
    Returns:
        Modern streaming manager with ZCTA functionality
    """
    # Configure cache strategy based on legacy parameters
    cache_strategy = "file" if cache_dir else "in_memory"
    
    # Create modern census system with appropriate caching
    builder = CensusSystemBuilder()
    if cache_dir:
        builder = builder.with_cache_dir(cache_dir)
    
    census_system = builder.with_cache_strategy(cache_strategy).build()
    
    # Return the modern streaming manager
    return census_system.create_streaming_manager()


# Export main interfaces
__all__ = [
    # Main system
    "CensusSystem",
    "CensusSystemBuilder", 
    "get_census_system",
    "get_legacy_adapter",
    "get_streaming_census_manager",  # Modern replacement for legacy function
    
    # Domain entities
    "CensusDataPoint",
    "GeographicUnit",
    "CensusVariable", 
    "StateInfo",
    "CountyInfo",
    "BlockGroupInfo",
    
    # Services
    "CensusService",
    "CensusVariableService",
    "GeographyService", 
    "BlockGroupService",
    "ZctaService",
    
    # Enums
    "StateFormat",
    "VariableFormat",
    "CacheStrategy",
    "RepositoryType",
    
    # Infrastructure (for advanced usage)
    "CensusConfig",
    "ConfigurationProvider",
    "CensusAPIClientImpl",
    "CensusGeocoder",
    "InMemoryCacheProvider",
    "FileCacheProvider", 
    "HybridCacheProvider",
    "NoOpCacheProvider",
    "TokenBucketRateLimiter",
] 