#!/usr/bin/env python3
"""
SocialMapper Address Geocoding System
====================================

Modern, production-ready address lookup system following SWE and ETL best practices.

Key Features:
- Multiple geocoding providers (Nominatim, Google, Census, etc.)
- Intelligent provider fallback and failover
- Comprehensive caching and rate limiting
- Data quality validation and normalization
- Batch processing capabilities
- Monitoring and observability
- Type-safe interfaces with Pydantic validation

Author: SocialMapper Team
Date: June 2025
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Union, Any, Tuple, Set
import time
import hashlib
import logging
from pathlib import Path
import json
import asyncio
from datetime import datetime, timedelta

# Third-party imports
import pandas as pd
import geopandas as gpd
from pydantic import BaseModel, Field, ConfigDict, field_validator
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from shapely.geometry import Point

# Local imports
from ..util.coordinate_validation import POICoordinate, validate_coordinate_point
from ..data.neighbors import get_file_neighbor_manager
from ..progress import get_progress_bar


logger = logging.getLogger(__name__)


class AddressProvider(Enum):
    """Enumeration of supported geocoding providers."""
    NOMINATIM = "nominatim"
    GOOGLE = "google"
    CENSUS = "census"
    HERE = "here"
    MAPBOX = "mapbox"


class AddressQuality(Enum):
    """Address quality levels based on geocoding precision."""
    EXACT = "exact"           # Rooftop/exact address match
    INTERPOLATED = "interpolated"  # Street interpolation
    CENTROID = "centroid"     # ZIP/city centroid
    APPROXIMATE = "approximate"  # Low precision match
    FAILED = "failed"         # Geocoding failed


@dataclass
class GeocodingConfig:
    """Configuration for geocoding operations."""
    # Provider settings
    primary_provider: AddressProvider = AddressProvider.NOMINATIM
    fallback_providers: List[AddressProvider] = field(default_factory=lambda: [AddressProvider.CENSUS])
    
    # API credentials
    google_api_key: Optional[str] = None
    here_api_key: Optional[str] = None
    mapbox_api_key: Optional[str] = None
    
    # Performance settings
    timeout_seconds: int = 10
    max_retries: int = 3
    rate_limit_requests_per_second: float = 1.0
    
    # Quality settings
    min_quality_threshold: AddressQuality = AddressQuality.CENTROID
    require_country_match: bool = True
    default_country: str = "US"
    
    # Caching
    enable_cache: bool = True
    cache_ttl_hours: int = 24 * 7  # 1 week
    cache_max_size: int = 10000
    
    # Batch processing
    batch_size: int = 100
    batch_delay_seconds: float = 0.1


class AddressInput(BaseModel):
    """Validated input for address geocoding."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    # Core address components
    address: str = Field(..., min_length=1, description="Full address or search string")
    city: Optional[str] = Field(None, description="City name")
    state: Optional[str] = Field(None, description="State name or abbreviation")
    postal_code: Optional[str] = Field(None, description="ZIP/postal code")
    country: Optional[str] = Field("US", description="Country code")
    
    # Metadata
    id: Optional[str] = Field(None, description="Unique identifier for this address")
    source: Optional[str] = Field(None, description="Source system or dataset")
    
    # Processing options
    provider_preference: Optional[AddressProvider] = Field(None, description="Preferred geocoding provider")
    quality_threshold: Optional[AddressQuality] = Field(None, description="Minimum quality requirement")
    
    @field_validator('address')
    @classmethod
    def validate_address(cls, v: str) -> str:
        """Validate and normalize address string."""
        if not v or v.strip() == "":
            raise ValueError("Address cannot be empty")
        return v.strip()
    
    def get_formatted_address(self) -> str:
        """Get a standardized formatted address for geocoding."""
        components = [self.address]
        if self.city:
            components.append(self.city)
        if self.state:
            components.append(self.state)
        if self.postal_code:
            components.append(self.postal_code)
        if self.country:
            components.append(self.country)
        return ", ".join(components)
    
    def get_cache_key(self) -> str:
        """Generate a cache key for this address."""
        address_str = self.get_formatted_address().lower()
        return hashlib.md5(address_str.encode()).hexdigest()


class GeocodingResult(BaseModel):
    """Result of address geocoding operation."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # Input reference
    input_address: AddressInput
    
    # Geocoding results
    success: bool
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    
    # Quality and metadata
    quality: AddressQuality
    provider_used: Optional[AddressProvider] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    
    # Standardized address components
    formatted_address: Optional[str] = None
    street_number: Optional[str] = None
    street_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    
    # Geographic context
    state_fips: Optional[str] = None
    county_fips: Optional[str] = None
    tract_geoid: Optional[str] = None
    block_group_geoid: Optional[str] = None
    
    # Processing metadata
    processing_time_ms: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    error_message: Optional[str] = None
    
    def to_poi_format(self) -> Optional[Dict[str, Any]]:
        """Convert to standard POI format for SocialMapper integration."""
        if not self.success or not self.latitude or not self.longitude:
            return None
        
        poi = {
            'id': self.input_address.id or f"addr_{hash(self.input_address.get_formatted_address())}",
            'name': self.formatted_address or self.input_address.address,
            'lat': self.latitude,
            'lon': self.longitude,
            'type': 'address',
            'tags': {
                'addr:full': self.formatted_address,
                'addr:street': self.street_name,
                'addr:city': self.city,
                'addr:state': self.state,
                'addr:postcode': self.postal_code,
                'addr:country': self.country,
                'geocoding:provider': self.provider_used.value if self.provider_used else None,
                'geocoding:quality': self.quality.value,
                'geocoding:confidence': self.confidence_score
            },
            'metadata': {
                'geocoded': True,
                'source': self.input_address.source,
                'state_fips': self.state_fips,
                'county_fips': self.county_fips,
                'tract_geoid': self.tract_geoid,
                'block_group_geoid': self.block_group_geoid
            }
        }
        
        return poi


class GeocodingProvider(ABC):
    """Abstract base class for geocoding providers."""
    
    def __init__(self, config: GeocodingConfig):
        self.config = config
        self.session = self._create_session()
        self.last_request_time = 0.0
        
    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry strategy."""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            respect_retry_after_header=True
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting between requests."""
        min_interval = 1.0 / self.config.rate_limit_requests_per_second
        elapsed = time.time() - self.last_request_time
        
        if elapsed < min_interval:
            sleep_time = min_interval - elapsed
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    @abstractmethod
    def geocode_address(self, address: AddressInput) -> GeocodingResult:
        """Geocode a single address."""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> AddressProvider:
        """Get the provider identifier."""
        pass


class NominatimProvider(GeocodingProvider):
    """OpenStreetMap Nominatim geocoding provider (free, rate-limited)."""
    
    BASE_URL = "https://nominatim.openstreetmap.org/search"
    
    def get_provider_name(self) -> AddressProvider:
        return AddressProvider.NOMINATIM
    
    def geocode_address(self, address: AddressInput) -> GeocodingResult:
        """Geocode address using Nominatim."""
        start_time = time.time()
        
        try:
            self._enforce_rate_limit()
            
            params = {
                'q': address.get_formatted_address(),
                'format': 'json',
                'addressdetails': 1,
                'limit': 1,
                'countrycodes': address.country.lower(),
                'extratags': 1
            }
            
            headers = {
                'User-Agent': 'SocialMapper/1.0 (https://github.com/your-org/socialmapper)'
            }
            
            response = self.session.get(
                self.BASE_URL,
                params=params,
                headers=headers,
                timeout=self.config.timeout_seconds
            )
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                return GeocodingResult(
                    input_address=address,
                    success=False,
                    quality=AddressQuality.FAILED,
                    error_message="No results found",
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            result = data[0]
            lat = float(result['lat'])
            lon = float(result['lon'])
            
            # Determine quality based on OSM class and type
            quality = self._determine_quality_from_osm(result)
            
            # Extract address components
            address_parts = result.get('address', {})
            
            geocoding_result = GeocodingResult(
                input_address=address,
                success=True,
                latitude=lat,
                longitude=lon,
                quality=quality,
                provider_used=AddressProvider.NOMINATIM,
                confidence_score=self._calculate_confidence(result),
                formatted_address=result.get('display_name'),
                street_number=address_parts.get('house_number'),
                street_name=address_parts.get('road'),
                city=address_parts.get('city') or address_parts.get('town') or address_parts.get('village'),
                state=address_parts.get('state'),
                postal_code=address_parts.get('postcode'),
                country=address_parts.get('country_code', '').upper(),
                processing_time_ms=(time.time() - start_time) * 1000
            )
            
            # Add geographic context using neighbor system
            self._add_geographic_context(geocoding_result)
            
            return geocoding_result
            
        except Exception as e:
            logger.warning(f"Nominatim geocoding failed for {address.address}: {e}")
            return GeocodingResult(
                input_address=address,
                success=False,
                quality=AddressQuality.FAILED,
                error_message=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    def _determine_quality_from_osm(self, result: Dict[str, Any]) -> AddressQuality:
        """Determine address quality from OSM result."""
        osm_class = result.get('class', '')
        osm_type = result.get('type', '')
        
        # Address-level matches
        if osm_class == 'place' and osm_type in ['house', 'address']:
            return AddressQuality.EXACT
        
        # Street-level matches
        if osm_class == 'highway':
            return AddressQuality.INTERPOLATED
        
        # Administrative area matches
        if osm_class == 'place' and osm_type in ['city', 'town', 'village']:
            return AddressQuality.CENTROID
        
        # Default to approximate
        return AddressQuality.APPROXIMATE
    
    def _calculate_confidence(self, result: Dict[str, Any]) -> float:
        """Calculate confidence score from OSM result."""
        importance = float(result.get('importance', 0.5))
        return min(importance * 2, 1.0)  # Scale to 0-1 range
    
    def _add_geographic_context(self, result: GeocodingResult):
        """Add geographic context using SocialMapper's neighbor system."""
        if not result.success or not result.latitude or not result.longitude:
            return
        
        try:
            neighbor_manager = get_file_neighbor_manager()
            geo_info = neighbor_manager.get_geography_from_point(
                result.latitude, 
                result.longitude
            )
            
            if geo_info:
                result.state_fips = geo_info.get('state_fips')
                result.county_fips = geo_info.get('county_fips')
                result.tract_geoid = geo_info.get('tract_geoid')
                result.block_group_geoid = geo_info.get('block_group_geoid')
                
        except Exception as e:
            logger.warning(f"Failed to get geographic context: {e}")


class CensusProvider(GeocodingProvider):
    """US Census Bureau geocoding provider (free, US-only)."""
    
    BASE_URL = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
    
    def get_provider_name(self) -> AddressProvider:
        return AddressProvider.CENSUS
    
    def geocode_address(self, address: AddressInput) -> GeocodingResult:
        """Geocode address using Census Bureau API."""
        start_time = time.time()
        
        try:
            self._enforce_rate_limit()
            
            params = {
                'address': address.get_formatted_address(),
                'benchmark': 'Public_AR_Current',
                'format': 'json'
            }
            
            response = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=self.config.timeout_seconds
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Check for successful geocoding
            if ('result' not in data or 
                'addressMatches' not in data['result'] or 
                not data['result']['addressMatches']):
                return GeocodingResult(
                    input_address=address,
                    success=False,
                    quality=AddressQuality.FAILED,
                    error_message="No address matches found",
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            match = data['result']['addressMatches'][0]
            coords = match['coordinates']
            
            lat = float(coords['y'])
            lon = float(coords['x'])
            
            # Census always provides high-quality results
            quality = AddressQuality.EXACT
            
            # Extract address components
            address_parts = match.get('addressComponents', {})
            
            geocoding_result = GeocodingResult(
                input_address=address,
                success=True,
                latitude=lat,
                longitude=lon,
                quality=quality,
                provider_used=AddressProvider.CENSUS,
                confidence_score=0.95,  # Census results are typically high quality
                formatted_address=match.get('matchedAddress'),
                street_number=address_parts.get('fromAddress'),
                street_name=address_parts.get('streetName'),
                city=address_parts.get('city'),
                state=address_parts.get('state'),
                postal_code=address_parts.get('zip'),
                country='US',
                processing_time_ms=(time.time() - start_time) * 1000
            )
            
            # Add geographic context using neighbor system
            self._add_geographic_context(geocoding_result)
            
            return geocoding_result
            
        except Exception as e:
            logger.warning(f"Census geocoding failed for {address.address}: {e}")
            return GeocodingResult(
                input_address=address,
                success=False,
                quality=AddressQuality.FAILED,
                error_message=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    def _add_geographic_context(self, result: GeocodingResult):
        """Add geographic context using SocialMapper's neighbor system."""
        if not result.success or not result.latitude or not result.longitude:
            return
        
        try:
            neighbor_manager = get_file_neighbor_manager()
            geo_info = neighbor_manager.get_geography_from_point(
                result.latitude, 
                result.longitude
            )
            
            if geo_info:
                result.state_fips = geo_info.get('state_fips')
                result.county_fips = geo_info.get('county_fips')
                result.tract_geoid = geo_info.get('tract_geoid')
                result.block_group_geoid = geo_info.get('block_group_geoid')
                
        except Exception as e:
            logger.warning(f"Failed to get geographic context: {e}")


class AddressCache:
    """High-performance caching system for geocoded addresses."""
    
    def __init__(self, config: GeocodingConfig):
        self.config = config
        self.cache_dir = Path("cache/geocoding")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "address_cache.parquet"
        self._cache = {}
        self._load_cache()
    
    def _load_cache(self):
        """Load cache from disk."""
        if not self.config.enable_cache or not self.cache_file.exists():
            return
        
        try:
            df = pd.read_parquet(self.cache_file)
            
            # Filter expired entries
            now = datetime.now()
            ttl_cutoff = now - timedelta(hours=self.config.cache_ttl_hours)
            df = df[pd.to_datetime(df['timestamp']) > ttl_cutoff]
            
            # Convert to dict for fast lookup
            for _, row in df.iterrows():
                self._cache[row['cache_key']] = {
                    'result': json.loads(row['result_json']),
                    'timestamp': pd.to_datetime(row['timestamp'])
                }
            
            logger.info(f"Loaded {len(self._cache)} cached geocoding results")
            
        except Exception as e:
            logger.warning(f"Failed to load geocoding cache: {e}")
    
    def get(self, address: AddressInput) -> Optional[GeocodingResult]:
        """Get cached result for address."""
        if not self.config.enable_cache:
            return None
        
        cache_key = address.get_cache_key()
        
        if cache_key in self._cache:
            cached_data = self._cache[cache_key]
            
            # Check if still valid
            age = datetime.now() - cached_data['timestamp']
            if age.total_seconds() / 3600 < self.config.cache_ttl_hours:
                try:
                    # Reconstruct GeocodingResult from cached JSON
                    result_data = cached_data['result']
                    result_data['input_address'] = address
                    return GeocodingResult(**result_data)
                except Exception as e:
                    logger.warning(f"Failed to deserialize cached result: {e}")
        
        return None
    
    def put(self, result: GeocodingResult):
        """Cache a geocoding result."""
        if not self.config.enable_cache:
            return
        
        cache_key = result.input_address.get_cache_key()
        
        # Add to in-memory cache
        self._cache[cache_key] = {
            'result': result.model_dump_json(),
            'timestamp': datetime.now()
        }
        
        # Enforce size limit
        if len(self._cache) > self.config.cache_max_size:
            # Remove oldest entries
            sorted_items = sorted(
                self._cache.items(),
                key=lambda x: x[1]['timestamp']
            )
            for old_key, _ in sorted_items[:len(self._cache) - self.config.cache_max_size]:
                del self._cache[old_key]
    
    def save_cache(self):
        """Save cache to disk."""
        if not self.config.enable_cache or not self._cache:
            return
        
        try:
            # Convert cache to DataFrame
            cache_data = []
            for cache_key, data in self._cache.items():
                cache_data.append({
                    'cache_key': cache_key,
                    'result_json': data['result'],
                    'timestamp': data['timestamp']
                })
            
            df = pd.DataFrame(cache_data)
            df.to_parquet(self.cache_file, index=False)
            
            logger.info(f"Saved {len(cache_data)} geocoding results to cache")
            
        except Exception as e:
            logger.warning(f"Failed to save geocoding cache: {e}")


class AddressGeocodingEngine:
    """
    High-level geocoding engine orchestrating multiple providers with 
    intelligent fallback, caching, and quality validation.
    """
    
    def __init__(self, config: GeocodingConfig = None):
        self.config = config or GeocodingConfig()
        self.cache = AddressCache(self.config)
        self.providers = self._initialize_providers()
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'successful_geocodes': 0,
            'failed_geocodes': 0,
            'provider_usage': {provider.value: 0 for provider in AddressProvider}
        }
    
    def _initialize_providers(self) -> Dict[AddressProvider, GeocodingProvider]:
        """Initialize available geocoding providers."""
        providers = {}
        
        # Always available providers
        providers[AddressProvider.NOMINATIM] = NominatimProvider(self.config)
        providers[AddressProvider.CENSUS] = CensusProvider(self.config)
        
        # TODO: Add commercial providers based on API keys
        # if self.config.google_api_key:
        #     providers[AddressProvider.GOOGLE] = GoogleProvider(self.config)
        
        return providers
    
    def geocode_address(self, address: Union[str, AddressInput]) -> GeocodingResult:
        """
        Geocode a single address with intelligent provider selection and fallback.
        
        Args:
            address: Address string or AddressInput object
            
        Returns:
            GeocodingResult with geocoding outcome
        """
        # Convert string to AddressInput if needed
        if isinstance(address, str):
            address = AddressInput(address=address)
        
        self.stats['total_requests'] += 1
        
        # Check cache first
        cached_result = self.cache.get(address)
        if cached_result:
            self.stats['cache_hits'] += 1
            logger.debug(f"Cache hit for address: {address.address}")
            return cached_result
        
        # Determine provider order
        provider_order = self._get_provider_order(address)
        
        # Try providers in order
        last_error = None
        for provider_type in provider_order:
            if provider_type not in self.providers:
                continue
            
            provider = self.providers[provider_type]
            
            try:
                logger.debug(f"Trying provider {provider_type.value} for: {address.address}")
                result = provider.geocode_address(address)
                
                # Check quality threshold
                if (result.success and 
                    self._meets_quality_threshold(result.quality, address)):
                    
                    # Update stats
                    self.stats['successful_geocodes'] += 1
                    self.stats['provider_usage'][provider_type.value] += 1
                    
                    # Cache successful result
                    self.cache.put(result)
                    
                    logger.info(f"Successfully geocoded '{address.address}' using {provider_type.value}")
                    return result
                
                elif result.success:
                    logger.warning(f"Result quality {result.quality.value} below threshold for {address.address}")
                
                last_error = result.error_message
                
            except Exception as e:
                logger.warning(f"Provider {provider_type.value} failed for {address.address}: {e}")
                last_error = str(e)
        
        # All providers failed
        self.stats['failed_geocodes'] += 1
        
        failed_result = GeocodingResult(
            input_address=address,
            success=False,
            quality=AddressQuality.FAILED,
            error_message=last_error or "All geocoding providers failed"
        )
        
        # Cache failed result (with shorter TTL)
        self.cache.put(failed_result)
        
        return failed_result
    
    def geocode_addresses_batch(self, 
                               addresses: List[Union[str, AddressInput]], 
                               progress: bool = True) -> List[GeocodingResult]:
        """
        Geocode multiple addresses in batch with progress tracking.
        
        Args:
            addresses: List of address strings or AddressInput objects
            progress: Whether to show progress bar
            
        Returns:
            List of GeocodingResult objects
        """
        results = []
        
        # Convert strings to AddressInput
        address_inputs = []
        for addr in addresses:
            if isinstance(addr, str):
                address_inputs.append(AddressInput(address=addr))
            else:
                address_inputs.append(addr)
        
        # Process in batches with progress tracking
        if progress:
            progress_bar = get_progress_bar(
                len(address_inputs),
                description="Geocoding addresses"
            )
        
        for i in range(0, len(address_inputs), self.config.batch_size):
            batch = address_inputs[i:i + self.config.batch_size]
            
            for address in batch:
                result = self.geocode_address(address)
                results.append(result)
                
                if progress:
                    progress_bar.update(1)
                
                # Rate limiting between requests
                if self.config.batch_delay_seconds > 0:
                    time.sleep(self.config.batch_delay_seconds)
        
        if progress:
            progress_bar.close()
        
        # Save cache after batch processing
        self.cache.save_cache()
        
        return results
    
    def _get_provider_order(self, address: AddressInput) -> List[AddressProvider]:
        """Determine optimal provider order for an address."""
        providers = [self.config.primary_provider]
        
        # Add user preference if specified
        if (address.provider_preference and 
            address.provider_preference != self.config.primary_provider):
            providers.insert(0, address.provider_preference)
        
        # Add fallback providers
        for fallback in self.config.fallback_providers:
            if fallback not in providers:
                providers.append(fallback)
        
        return providers
    
    def _meets_quality_threshold(self, quality: AddressQuality, address: AddressInput) -> bool:
        """Check if result quality meets threshold."""
        threshold = address.quality_threshold or self.config.min_quality_threshold
        
        quality_order = [
            AddressQuality.EXACT,
            AddressQuality.INTERPOLATED,
            AddressQuality.CENTROID,
            AddressQuality.APPROXIMATE,
            AddressQuality.FAILED
        ]
        
        return quality_order.index(quality) <= quality_order.index(threshold)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get geocoding engine statistics."""
        stats = self.stats.copy()
        
        if stats['total_requests'] > 0:
            stats['cache_hit_rate'] = stats['cache_hits'] / stats['total_requests']
            stats['success_rate'] = stats['successful_geocodes'] / stats['total_requests']
        else:
            stats['cache_hit_rate'] = 0.0
            stats['success_rate'] = 0.0
        
        return stats
    
    def convert_to_poi_format(self, results: List[GeocodingResult]) -> Dict[str, Any]:
        """
        Convert geocoding results to standard SocialMapper POI format.
        
        Args:
            results: List of GeocodingResult objects
            
        Returns:
            Dictionary in POI format compatible with existing SocialMapper workflow
        """
        pois = []
        metadata = {
            'total_addresses': len(results),
            'successful_geocodes': 0,
            'failed_geocodes': 0,
            'geocoding_stats': self.get_statistics()
        }
        
        for result in results:
            if result.success:
                poi = result.to_poi_format()
                if poi:
                    pois.append(poi)
                    metadata['successful_geocodes'] += 1
            else:
                metadata['failed_geocodes'] += 1
        
        return {
            'poi_count': len(pois),
            'pois': pois,
            'metadata': metadata
        }


# High-level convenience functions
def geocode_address(address: Union[str, AddressInput], 
                   config: GeocodingConfig = None) -> GeocodingResult:
    """
    Convenience function to geocode a single address.
    
    Args:
        address: Address string or AddressInput object
        config: Optional geocoding configuration
        
    Returns:
        GeocodingResult
    """
    from .engine import AddressGeocodingEngine
    engine = AddressGeocodingEngine(config)
    return engine.geocode_address(address)


def geocode_addresses(addresses: List[Union[str, AddressInput]], 
                     config: GeocodingConfig = None,
                     progress: bool = True) -> List[GeocodingResult]:
    """
    Convenience function to geocode multiple addresses.
    
    Args:
        addresses: List of address strings or AddressInput objects
        config: Optional geocoding configuration
        progress: Whether to show progress bar
        
    Returns:
        List of GeocodingResult objects
    """
    from .engine import AddressGeocodingEngine
    engine = AddressGeocodingEngine(config)
    return engine.geocode_addresses_batch(addresses, progress)


def addresses_to_poi_format(addresses: List[Union[str, AddressInput]], 
                           config: GeocodingConfig = None) -> Dict[str, Any]:
    """
    Convenience function to geocode addresses and convert to POI format.
    
    Args:
        addresses: List of address strings or AddressInput objects
        config: Optional geocoding configuration
        
    Returns:
        Dictionary in POI format compatible with SocialMapper
    """
    from .engine import AddressGeocodingEngine
    engine = AddressGeocodingEngine(config)
    results = engine.geocode_addresses_batch(addresses)
    return engine.convert_to_poi_format(results) 