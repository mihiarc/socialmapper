"""Redis-based caching service for API responses and data."""

import json
import logging
import hashlib
from typing import Any, Optional, Dict, List
from datetime import timedelta
import pickle

import redis
from redis import Redis, ConnectionPool
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError

from ..config import get_settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching service with intelligent TTL and cache warming."""
    
    # Cache key prefixes
    CENSUS_PREFIX = "census:"
    POI_PREFIX = "poi:"
    ISOCHRONE_PREFIX = "isochrone:"
    RESULT_PREFIX = "result:"
    DEMO_PREFIX = "demo:"
    
    # Default TTL values (in seconds)
    DEFAULT_TTL = 3600  # 1 hour
    CENSUS_TTL = 86400  # 24 hours (census data changes rarely)
    POI_TTL = 7200  # 2 hours (POI data may update more frequently)
    ISOCHRONE_TTL = 3600  # 1 hour (travel times may vary)
    RESULT_TTL = 1800  # 30 minutes (full results)
    DEMO_TTL = 86400  # 24 hours (demo data for showcase)
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        max_connections: int = 50,
        socket_timeout: int = 5,
        retry_on_timeout: bool = True,
        decode_responses: bool = False
    ):
        """Initialize Redis cache service with connection pooling.
        
        Args:
            host: Redis server host
            port: Redis server port
            db: Redis database number
            password: Redis password if required
            max_connections: Maximum connections in pool
            socket_timeout: Socket timeout in seconds
            retry_on_timeout: Whether to retry on timeout
            decode_responses: Whether to decode responses to strings
        """
        self.enabled = True
        
        try:
            # Create connection pool for better performance
            self.pool = ConnectionPool(
                host=host,
                port=port,
                db=db,
                password=password,
                max_connections=max_connections,
                socket_timeout=socket_timeout,
                retry_on_timeout=retry_on_timeout,
                decode_responses=decode_responses,
                health_check_interval=30
            )
            
            self.redis_client: Redis = redis.Redis(connection_pool=self.pool)
            
            # Test connection
            self.redis_client.ping()
            logger.info(f"Redis cache service connected to {host}:{port}")
            
        except (RedisError, RedisConnectionError) as e:
            logger.warning(f"Redis connection failed: {e}. Cache service disabled.")
            self.enabled = False
            self.redis_client = None
    
    def _generate_cache_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """Generate a deterministic cache key from parameters.
        
        Args:
            prefix: Cache key prefix
            params: Parameters to include in key
            
        Returns:
            Cache key string
        """
        # Sort params for consistent key generation
        sorted_params = json.dumps(params, sort_keys=True)
        
        # Create hash for compact key
        param_hash = hashlib.md5(sorted_params.encode()).hexdigest()
        
        return f"{prefix}{param_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self.enabled:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                # Try to deserialize as JSON first, then pickle
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    try:
                        return pickle.loads(value)
                    except:
                        return value
            return None
            
        except RedisError as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with optional TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        if not self.enabled:
            return False
        
        try:
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized = json.dumps(value)
            else:
                serialized = pickle.dumps(value)
            
            # Set with TTL if provided
            if ttl:
                self.redis_client.setex(key, ttl, serialized)
            else:
                self.redis_client.set(key, serialized)
            
            return True
            
        except RedisError as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted
        """
        if not self.enabled:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except RedisError as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if exists
        """
        if not self.enabled:
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except RedisError as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def cache_census_data(
        self,
        location: str,
        variables: List[str],
        data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache census API response data.
        
        Args:
            location: Location identifier
            variables: Census variables requested
            data: Census data to cache
            ttl: Custom TTL or use default
            
        Returns:
            True if cached successfully
        """
        key = self._generate_cache_key(
            self.CENSUS_PREFIX,
            {"location": location, "variables": sorted(variables)}
        )
        
        return await self.set(key, data, ttl or self.CENSUS_TTL)
    
    async def get_census_data(
        self,
        location: str,
        variables: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Get cached census data.
        
        Args:
            location: Location identifier
            variables: Census variables requested
            
        Returns:
            Cached census data or None
        """
        key = self._generate_cache_key(
            self.CENSUS_PREFIX,
            {"location": location, "variables": sorted(variables)}
        )
        
        return await self.get(key)
    
    async def cache_poi_data(
        self,
        location: str,
        poi_type: str,
        poi_name: str,
        data: List[Dict[str, Any]],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache POI discovery results.
        
        Args:
            location: Location identifier
            poi_type: Type of POI
            poi_name: Name/category of POI
            data: POI data to cache
            ttl: Custom TTL or use default
            
        Returns:
            True if cached successfully
        """
        key = self._generate_cache_key(
            self.POI_PREFIX,
            {
                "location": location,
                "type": poi_type,
                "name": poi_name
            }
        )
        
        return await self.set(key, data, ttl or self.POI_TTL)
    
    async def get_poi_data(
        self,
        location: str,
        poi_type: str,
        poi_name: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached POI data.
        
        Args:
            location: Location identifier
            poi_type: Type of POI
            poi_name: Name/category of POI
            
        Returns:
            Cached POI data or None
        """
        key = self._generate_cache_key(
            self.POI_PREFIX,
            {
                "location": location,
                "type": poi_type,
                "name": poi_name
            }
        )
        
        return await self.get(key)
    
    async def warm_demo_cache(self) -> int:
        """Pre-populate cache with demo scenario data.
        
        Returns:
            Number of demo entries cached
        """
        if not self.enabled:
            return 0
        
        # Demo scenarios to pre-cache
        demo_scenarios = [
            {
                "location": "Portland, OR",
                "poi_type": "amenity",
                "poi_name": "library",
                "census_variables": ["B01003_001E"],
            },
            {
                "location": "Portland, OR",
                "poi_type": "amenity",
                "poi_name": "hospital",
                "census_variables": ["B01003_001E", "B25001_001E"],
            },
            {
                "location": "Seattle, WA",
                "poi_type": "amenity",
                "poi_name": "school",
                "census_variables": ["B01003_001E"],
            },
            {
                "location": "San Francisco, CA",
                "poi_type": "shop",
                "poi_name": "supermarket",
                "census_variables": ["B01003_001E", "B19013_001E"],
            },
        ]
        
        cached_count = 0
        
        for scenario in demo_scenarios:
            # Create demo POI data
            demo_pois = [
                {
                    "name": f"Demo {scenario['poi_name'].title()} {i}",
                    "lat": 45.5152 + (i * 0.01),
                    "lon": -122.6784 + (i * 0.01),
                    "type": scenario["poi_type"],
                    "subtype": scenario["poi_name"],
                }
                for i in range(5)
            ]
            
            # Cache POI data
            if await self.cache_poi_data(
                scenario["location"],
                scenario["poi_type"],
                scenario["poi_name"],
                demo_pois,
                self.DEMO_TTL
            ):
                cached_count += 1
            
            # Create demo census data
            demo_census = {
                "B01003_001E": 15420,  # Population
                "B25001_001E": 6234,   # Housing units
                "B19013_001E": 65740,  # Median income
            }
            
            # Cache census data
            if await self.cache_census_data(
                scenario["location"],
                scenario["census_variables"],
                demo_census,
                self.DEMO_TTL
            ):
                cached_count += 1
        
        logger.info(f"Warmed cache with {cached_count} demo entries")
        return cached_count
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Cache statistics dictionary
        """
        if not self.enabled:
            return {"enabled": False}
        
        try:
            info = self.redis_client.info("stats")
            memory = self.redis_client.info("memory")
            
            return {
                "enabled": True,
                "connected": True,
                "total_keys": self.redis_client.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0) /
                    max(1, info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0))
                ),
                "memory_used_mb": round(memory.get("used_memory", 0) / 1024 / 1024, 2),
                "memory_peak_mb": round(memory.get("used_memory_peak", 0) / 1024 / 1024, 2),
                "connected_clients": info.get("connected_clients", 0),
            }
            
        except RedisError as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"enabled": True, "connected": False, "error": str(e)}
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern.
        
        Args:
            pattern: Key pattern to match (e.g., "census:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.enabled:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
            
        except RedisError as e:
            logger.error(f"Failed to clear pattern {pattern}: {e}")
            return 0
    
    async def close(self):
        """Close Redis connection pool."""
        if self.pool:
            self.pool.disconnect()
            logger.info("Redis cache service disconnected")


class CacheServiceSingleton:
    """Singleton manager for CacheService."""
    
    _instance: Optional[CacheService] = None
    
    @classmethod
    def get_instance(cls) -> CacheService:
        """Get the singleton cache service instance."""
        if cls._instance is None:
            settings = get_settings()
            cls._instance = CacheService(
                host=getattr(settings, "redis_host", "localhost"),
                port=getattr(settings, "redis_port", 6379),
                db=getattr(settings, "redis_db", 0),
                password=getattr(settings, "redis_password", None),
                max_connections=50
            )
        return cls._instance
    
    @classmethod
    async def close_instance(cls):
        """Close and clear the singleton instance."""
        if cls._instance:
            await cls._instance.close()
            cls._instance = None


def get_cache_service() -> CacheService:
    """Get the global cache service instance."""
    return CacheServiceSingleton.get_instance()