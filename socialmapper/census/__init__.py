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
        geocoder: CensusGeocoder
    ):
        self._census_service = census_service
        self._variable_service = variable_service
        self._geography_service = geography_service
        self._block_group_service = block_group_service
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
        
        return CensusSystem(
            census_service=census_service,
            variable_service=variable_service,
            geography_service=geography_service,
            block_group_service=block_group_service,
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


# Export main interfaces
__all__ = [
    # Main system
    "CensusSystem",
    "CensusSystemBuilder", 
    "get_census_system",
    "get_legacy_adapter",
    
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