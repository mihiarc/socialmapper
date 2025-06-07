#!/usr/bin/env python3
"""
Address Geocoding Cache
======================

High-performance caching system for geocoded addresses using Parquet storage
and in-memory optimization following ETL best practices.

Author: SocialMapper Team
Date: June 2025
"""

import logging
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import pandas as pd

from . import GeocodingConfig, AddressInput, GeocodingResult

logger = logging.getLogger(__name__)


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