"""
Census data caching implementation.

This module provides caching mechanisms to avoid repetitive Census API calls,
improving performance for repeated queries and reducing the risk of hitting API limits.
"""

import os
import time
import json
import hashlib
import pickle
import sqlite3
from functools import lru_cache
from typing import List, Dict, Any, Optional, Tuple
import logging

import pandas as pd

from socialmapper.util import normalize_census_variable
from socialmapper.census_data.async_census import fetch_census_data_for_states_async
from socialmapper.progress import get_progress_bar

# Add a logger for this module
logger = logging.getLogger(__name__)

# Default cache settings
DEFAULT_CACHE_DIR = os.path.join("cache", "census_data")
DEFAULT_MEMORY_CACHE_SIZE = 64
DEFAULT_MAX_AGE_DAYS = 30


def generate_cache_key(
    state_fips_list: List[str], variables: List[str], year: int, dataset: str
) -> str:
    """
    Generate a unique cache key for the given parameters.
    
    Args:
        state_fips_list: List of state FIPS codes
        variables: List of census variables (will be normalized if needed)
        year: Census year
        dataset: Census dataset
        
    Returns:
        A unique string key
    """
    # Sort inputs to ensure consistent keys
    sorted_states = sorted(state_fips_list)
    
    # Variables should be already normalized by the caller to avoid redundant normalization
    # But handle the case where they're not normalized for backwards compatibility
    sorted_vars = sorted(variables)
    
    # Create a dictionary of parameters
    params = {
        'states': sorted_states,
        'variables': sorted_vars,
        'year': year,
        'dataset': dataset
    }
    
    # Convert to a consistent string representation and hash it
    param_str = json.dumps(params, sort_keys=True)
    return hashlib.md5(param_str.encode('utf-8')).hexdigest()


class MemoryCache:
    """In-memory LRU cache implementation using Python's lru_cache decorator."""
    
    def __init__(self, maxsize: int = DEFAULT_MEMORY_CACHE_SIZE):
        """
        Initialize the memory cache.
        
        Args:
            maxsize: Maximum number of items to store in cache
        """
        self.maxsize = maxsize
        self._fetch_census_data = lru_cache(maxsize=maxsize)(self._fetch_data_uncached)
        self.hits = 0
        self.misses = 0
        self.total_calls = 0
    
    def _fetch_data_uncached(
        self, 
        cache_key: str, 
        states_tuple: Tuple[str], 
        vars_tuple: Tuple[str], 
        year: int, 
        dataset: str, 
        api_key: str, 
        use_async: bool
    ) -> pd.DataFrame:
        """
        Fetch census data without caching.
        
        Args:
            cache_key: Unique cache key for this request
            states_tuple: Tuple of state FIPS codes
            vars_tuple: Tuple of census variables
            year: Census year
            dataset: Census dataset
            api_key: Census API key
            use_async: Whether to use async implementation
            
        Returns:
            DataFrame with census data
        """
        self.misses += 1
        
        import requests
        import pandas as pd
        import asyncio
        
        # Convert from tuples back to lists
        state_fips_list = list(states_tuple)
        variables = list(vars_tuple)
        
        # Make sure 'NAME' is included
        api_variables = list(variables)
        if 'NAME' not in api_variables:
            api_variables.append('NAME')
            
        # Use async implementation if requested
        if use_async and len(state_fips_list) > 1:
            logger.debug(f"Using asynchronous implementation to fetch data for {len(state_fips_list)} states...")
            
            # Import here to avoid circular imports at top level
            from socialmapper.census_data.async_census import fetch_census_data_for_states_async
            
            try:
                # Handle async execution in a way compatible with Python 3.10+ asyncio changes
                try:
                    # Get the current event loop or create a new one
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    # No event loop exists in this thread, create a new one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                # Run the async function
                if loop.is_running():
                    # If the loop is already running (e.g., in Jupyter/IPython), use run_coroutine_threadsafe
                    import concurrent.futures
                    future = asyncio.run_coroutine_threadsafe(
                        fetch_census_data_for_states_async(
                            state_fips_list=state_fips_list,
                            variables=api_variables,
                            year=year,
                            dataset=dataset,
                            api_key=api_key,
                            concurrency=10  # Use default concurrency
                        ),
                        loop
                    )
                    final_df = future.result()
                else:
                    # If no loop is running, run until complete
                    final_df = loop.run_until_complete(
                        fetch_census_data_for_states_async(
                            state_fips_list=state_fips_list,
                            variables=api_variables,
                            year=year,
                            dataset=dataset,
                            api_key=api_key,
                            concurrency=10  # Use default concurrency
                        )
                    )
                return final_df
            except Exception as e:
                logger.warning(f"Error using async implementation, falling back to synchronous: {str(e)}")
        
        # Original synchronous implementation (kept for fallback and single-state requests)
        # Base URL for Census API
        base_url = f'https://api.census.gov/data/{year}/{dataset}'
        
        # Verify the API URL with a test request
        test_url = f"{base_url}/variables.json"
        try:
            test_response = requests.get(test_url, params={'key': api_key})
            if test_response.status_code != 200:
                raise ValueError(f"Census API returned status code {test_response.status_code} for URL {test_url}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Cannot connect to Census API: {str(e)}")
        
        # Initialize an empty list to store dataframes
        dfs = []
        
        # Helper function to get state name
        def get_state_name(fips_code):
            """Get state name from FIPS code for better logging."""
            # Import here to avoid circular dependency
            from socialmapper.census_data import state_fips_to_name
            state_name = state_fips_to_name(fips_code)
            return state_name if state_name else fips_code
        
        # Loop over each state
        for state_code in get_progress_bar(state_fips_list, desc="Fetching census data by state", unit="state"):
            state_name = get_state_name(state_code)
            
            # Define the parameters for this state
            params = {
                'get': ','.join(api_variables),
                'for': 'block group:*',
                'in': f'state:{state_code} county:* tract:*',
                'key': api_key
            }
            
            try:
                # Make the API request
                response = requests.get(base_url, params=params)
                
                # Check if the request was successful
                if response.status_code == 200:
                    # Parse the JSON response
                    data = response.json()
                    
                    # Validate response structure
                    if not data or len(data) < 2:
                        continue
                    
                    # Convert to DataFrame
                    df = pd.DataFrame(data[1:], columns=data[0])
                    
                    # Append the dataframe to the list
                    dfs.append(df)
                    
                    logger.debug(f"  - Retrieved data for {len(df)} block groups")
                    
                else:
                    logger.warning(f"Error fetching data for {state_name}: Status {response.status_code}")
            
            except Exception as e:
                logger.warning(f"Exception while fetching data for {state_name}: {str(e)}")
        
        # Combine all data
        if not dfs:
            raise ValueError("No census data retrieved. Please check your API key and the census variables you're requesting.")
            
        final_df = pd.concat(dfs, ignore_index=True)
        
        # Create a GEOID column to match with GeoJSON - ensure proper formatting with leading zeros
        final_df['GEOID'] = (
            final_df['state'].str.zfill(2) + 
            final_df['county'].str.zfill(3) + 
            final_df['tract'].str.zfill(6) + 
            final_df['block group']
        )
        
        return final_df
    
    def get_or_fetch(
        self, 
        state_fips_list: List[str], 
        variables: List[str],
        year: int, 
        dataset: str, 
        api_key: str,
        use_async: bool = True
    ) -> pd.DataFrame:
        """
        Get data from cache or fetch if not available.
        
        Args:
            state_fips_list: List of state FIPS codes
            variables: List of census variables
            year: Census year
            dataset: Census dataset
            api_key: Census API key
            use_async: Whether to use async implementation
            
        Returns:
            DataFrame with census data
        """
        self.total_calls += 1
        
        # Normalize variables once upfront
        normalized_variables = [normalize_census_variable(v) for v in variables]
        
        cache_key = generate_cache_key(state_fips_list, normalized_variables, year, dataset)
        
        # Convert lists to tuples for hashability in lru_cache
        states_tuple = tuple(sorted(state_fips_list))
        vars_tuple = tuple(sorted(normalized_variables))
        
        # Check if already in cache
        if hasattr(self._fetch_census_data, 'cache_info'):
            before_info = self._fetch_census_data.cache_info()
        
        # Get or fetch
        result = self._fetch_census_data(
            cache_key, states_tuple, vars_tuple, year, dataset, api_key, use_async
        )
        
        # Update hit/miss stats
        if hasattr(self._fetch_census_data, 'cache_info'):
            after_info = self._fetch_census_data.cache_info()
            if before_info.hits < after_info.hits:
                self.hits += 1
        
        return result
    
    def clear(self):
        """Clear the cache."""
        if hasattr(self._fetch_census_data, 'cache_clear'):
            self._fetch_census_data.cache_clear()
        self.hits = 0
        self.misses = 0
        self.total_calls = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            'hits': self.hits,
            'misses': self.misses,
            'total_calls': self.total_calls,
            'hit_rate': (self.hits / self.total_calls * 100) if self.total_calls > 0 else 0,
            'type': 'memory'
        }
        
        if hasattr(self._fetch_census_data, 'cache_info'):
            cache_info = self._fetch_census_data.cache_info()
            stats.update({
                'maxsize': cache_info.maxsize,
                'currsize': cache_info.currsize
            })
        
        return stats


class DiskCache:
    """Disk-based cache implementation using SQLite."""
    
    def __init__(self, db_path: Optional[str] = None, maxage_days: int = DEFAULT_MAX_AGE_DAYS):
        """
        Initialize the disk cache.
        
        Args:
            db_path: Path to SQLite database file. If None, uses default path.
            maxage_days: Maximum age of cached data in days
        """
        if db_path is None:
            self.db_path = os.path.join(DEFAULT_CACHE_DIR, 'census_cache.db')
        else:
            self.db_path = db_path
            
        self.maxage_days = maxage_days
        self.hits = 0
        self.misses = 0
        self.total_calls = 0
        
        # Ensure cache directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Initialize the SQLite database schema."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tables if they don't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS census_cache (
                cache_key TEXT PRIMARY KEY,
                timestamp INTEGER,
                year INTEGER,
                dataset TEXT,
                states TEXT,
                variables TEXT,
                data BLOB
            )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Error initializing cache database: {e}")
    
    def get_or_fetch(
        self, 
        state_fips_list: List[str], 
        variables: List[str],
        year: int, 
        dataset: str, 
        api_key: str,
        use_async: bool = True
    ) -> pd.DataFrame:
        """
        Get data from cache or fetch if not available.
        
        Args:
            state_fips_list: List of state FIPS codes
            variables: List of census variables
            year: Census year
            dataset: Census dataset
            api_key: Census API key
            use_async: Whether to use async implementation
            
        Returns:
            DataFrame with census data
        """
        self.total_calls += 1
        
        # Normalize variables once upfront
        normalized_variables = [normalize_census_variable(v) for v in variables]
        
        cache_key = generate_cache_key(state_fips_list, normalized_variables, year, dataset)
        
        # Try to get from cache
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            self.hits += 1
            logger.info(f"Census data cache hit: using cached data for {len(state_fips_list)} states, {len(normalized_variables)} variables.")
            return cached_data
        
        # Fetch new data
        self.misses += 1
        logger.info(f"Census data cache miss: fetching fresh data...")
        
        from socialmapper.census_data import fetch_census_data_for_states
        
        data = fetch_census_data_for_states(
            state_fips_list=state_fips_list,
            variables=normalized_variables,
            year=year,
            dataset=dataset,
            api_key=api_key,
            use_async=use_async,
            use_internal_cache=False  # Prevent infinite recursion
        )
        
        # Store in cache
        self._store_in_cache(cache_key, data, state_fips_list, normalized_variables, year, dataset)
        
        return data
    
    def _get_from_cache(self, cache_key: str) -> Optional[pd.DataFrame]:
        """
        Get data from the cache.
        
        Args:
            cache_key: Unique cache key
            
        Returns:
            DataFrame if found and valid, None otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query the cache, respecting maxage
            max_age_timestamp = int(time.time()) - (self.maxage_days * 24 * 60 * 60)
            cursor.execute(
                "SELECT data FROM census_cache WHERE cache_key = ? AND timestamp > ?",
                (cache_key, max_age_timestamp)
            )
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                # Deserialize the data
                data_bytes = row[0]
                return pickle.loads(data_bytes)
            
            return None
        except Exception as e:
            logger.warning(f"Error retrieving from cache: {e}")
            return None
    
    def _store_in_cache(
        self, 
        cache_key: str, 
        data: pd.DataFrame,
        state_fips_list: List[str], 
        variables: List[str],
        year: int, 
        dataset: str
    ):
        """
        Store data in the cache.
        
        Args:
            cache_key: Unique cache key
            data: DataFrame to cache
            state_fips_list: List of state FIPS codes
            variables: List of census variables
            year: Census year
            dataset: Census dataset
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Serialize the data
            data_bytes = pickle.dumps(data)
            timestamp = int(time.time())
            
            # Store metadata for diagnostics - variables should already be normalized
            states_json = json.dumps(sorted(state_fips_list))
            vars_json = json.dumps(sorted(variables))
            
            # Insert or replace
            cursor.execute(
                """
                INSERT OR REPLACE INTO census_cache 
                (cache_key, timestamp, year, dataset, states, variables, data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (cache_key, timestamp, year, dataset, states_json, vars_json, data_bytes)
            )
            
            conn.commit()
            conn.close()
            logger.debug(f"Stored census data in cache.")
        except Exception as e:
            logger.warning(f"Error storing in cache: {e}")
    
    def clear(self):
        """Clear the cache."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM census_cache")
            conn.commit()
            conn.close()
            self.hits = 0
            self.misses = 0
            self.total_calls = 0
            logger.debug(f"Cleared census data cache.")
        except Exception as e:
            logger.warning(f"Error clearing cache: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            'hits': self.hits,
            'misses': self.misses,
            'total_calls': self.total_calls,
            'hit_rate': (self.hits / self.total_calls * 100) if self.total_calls > 0 else 0,
            'type': 'disk',
            'path': self.db_path,
            'maxage_days': self.maxage_days
        }
        
        # Get additional stats from the database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Count entries
            cursor.execute("SELECT COUNT(*) FROM census_cache")
            stats['entry_count'] = cursor.fetchone()[0]
            
            # Get DB size
            cursor.execute("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()")
            db_size_bytes = cursor.fetchone()[0]
            stats['size_mb'] = db_size_bytes / (1024 * 1024)
            
            # Get average entry size
            if stats['entry_count'] > 0:
                cursor.execute("SELECT AVG(LENGTH(data)) FROM census_cache")
                avg_size_bytes = cursor.fetchone()[0] or 0
                stats['avg_entry_size_kb'] = avg_size_bytes / 1024
            
            conn.close()
        except Exception as e:
            logger.warning(f"Error getting cache stats: {e}")
        
        return stats


class HybridCache:
    """Combined memory and disk cache implementation."""
    
    def __init__(
        self, 
        memory_maxsize: int = DEFAULT_MEMORY_CACHE_SIZE, 
        db_path: Optional[str] = None, 
        maxage_days: int = DEFAULT_MAX_AGE_DAYS
    ):
        """
        Initialize the hybrid cache.
        
        Args:
            memory_maxsize: Maximum number of items in memory cache
            db_path: Path to SQLite database. If None, uses default path.
            maxage_days: Maximum age of cached data in days
        """
        self.memory_cache = MemoryCache(maxsize=memory_maxsize)
        self.disk_cache = DiskCache(db_path=db_path, maxage_days=maxage_days)
        self.memory_hits = 0
        self.disk_hits = 0
        self.misses = 0
        self.total_calls = 0
    
    def get_or_fetch(
        self, 
        state_fips_list: List[str], 
        variables: List[str],
        year: int, 
        dataset: str, 
        api_key: str,
        use_async: bool = True
    ) -> pd.DataFrame:
        """
        Get data from cache or fetch if not available.
        
        Args:
            state_fips_list: List of state FIPS codes
            variables: List of census variables
            year: Census year
            dataset: Census dataset
            api_key: Census API key
            use_async: Whether to use async implementation
            
        Returns:
            DataFrame with census data
        """
        self.total_calls += 1
        
        # Normalize variables once upfront
        normalized_variables = [normalize_census_variable(v) for v in variables]
        
        # Check memory cache first (faster)
        memory_calls_before = self.memory_cache.total_calls
        memory_hits_before = self.memory_cache.hits
        
        data = self.memory_cache.get_or_fetch(
            state_fips_list, normalized_variables, year, dataset, api_key, use_async
        )
        
        # Check if it was a memory hit
        if self.memory_cache.hits > memory_hits_before:
            self.memory_hits += 1
            logger.debug(f"Memory cache hit: using in-memory census data.")
            return data
        
        # If not in memory, check if it was a disk hit
        disk_calls_before = self.disk_cache.total_calls
        disk_hits_before = self.disk_cache.hits
        
        # This will be cached in memory for next time
        data = self.disk_cache.get_or_fetch(
            state_fips_list, normalized_variables, year, dataset, api_key, use_async
        )
        
        if self.disk_cache.hits > disk_hits_before:
            self.disk_hits += 1
        else:
            self.misses += 1
        
        return data
    
    def clear(self):
        """Clear both caches."""
        self.memory_cache.clear()
        self.disk_cache.clear()
        self.memory_hits = 0
        self.disk_hits = 0
        self.misses = 0
        self.total_calls = 0
        logger.debug(f"Cleared all census data caches.")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get combined cache statistics."""
        memory_stats = self.memory_cache.get_stats()
        disk_stats = self.disk_cache.get_stats()
        
        return {
            'memory_hits': self.memory_hits,
            'disk_hits': self.disk_hits,
            'misses': self.misses,
            'total_calls': self.total_calls,
            'hit_rate': ((self.memory_hits + self.disk_hits) / self.total_calls * 100) 
                        if self.total_calls > 0 else 0,
            'memory_cache': memory_stats,
            'disk_cache': disk_stats,
            'type': 'hybrid'
        }


# Default global cache instance
_default_cache = HybridCache()

def get_default_cache() -> HybridCache:
    """Get the default global cache instance."""
    return _default_cache 