# Cache Management in SocialMapper

SocialMapper uses multiple caching systems to improve performance and reduce API calls. This document explains how to manage, monitor, and clear these caches.

## Cache Types

SocialMapper maintains four different cache types:

### 1. Network Cache
- **Purpose**: Stores downloaded road network data from OpenStreetMap
- **Location**: `cache/networks/`
- **Format**: Compressed pickle files (`.pkl.gz`) with SQLite index
- **Features**:
  - Gzip compression for storage efficiency
  - SQLite database for spatial indexing
  - Intelligent overlap detection
  - LRU eviction policy

### 2. Geocoding Cache
- **Purpose**: Caches geocoded addresses to avoid repeated API calls
- **Location**: `cache/geocoding/`
- **Format**: Parquet file (`address_cache.parquet`)
- **Features**:
  - TTL-based expiration
  - Automatic cleanup on load

### 3. Census Cache
- **Purpose**: Stores census API responses
- **Location**: `cache/census/` and `.census_cache/`
- **Format**: Individual cache files (`.cache`)
- **Features**:
  - File-based persistence
  - API response caching

### 4. General Cache
- **Purpose**: General application cache for JSON responses
- **Location**: `cache/`
- **Format**: JSON files (`.json`)
- **Features**:
  - Simple file-based storage

## Cache Management Tools

### Command-Line Interface

A dedicated cache management script is available at `scripts/cache_manager.py`:

```bash
# Show cache statistics
uv run python scripts/cache_manager.py stats

# Show detailed cache information
uv run python scripts/cache_manager.py details

# Clear specific caches
uv run python scripts/cache_manager.py clear --network    # Clear network cache
uv run python scripts/cache_manager.py clear --geocoding  # Clear geocoding cache
uv run python scripts/cache_manager.py clear --census     # Clear census cache
uv run python scripts/cache_manager.py clear --all        # Clear all caches

# Skip confirmation prompt
uv run python scripts/cache_manager.py clear --all --yes

# Clean up expired entries
uv run python scripts/cache_manager.py cleanup
```

### Streamlit UI

The Streamlit application includes a cache management interface:

1. Navigate to the **Settings** page
2. Go to the **Cache** tab
3. View real-time cache statistics
4. Clear individual caches or all caches
5. Configure cache settings

### Python API

You can also manage caches programmatically:

```python
from socialmapper.cache_manager import (
    get_cache_statistics,
    clear_geocoding_cache,
    clear_census_cache,
    clear_all_caches
)
from socialmapper.isochrone import clear_network_cache

# Get cache statistics
stats = get_cache_statistics()
print(f"Total cache size: {stats['summary']['total_size_mb']:.2f} MB")
print(f"Total cached items: {stats['summary']['total_items']}")

# Clear individual caches
result = clear_geocoding_cache()
if result['success']:
    print(f"Cleared {result['cleared_size_mb']:.2f} MB from geocoding cache")

# Clear network cache
clear_network_cache()

# Clear all caches
result = clear_all_caches()
print(f"Total cleared: {result['summary']['total_cleared_mb']:.2f} MB")
```

## Cache Statistics

The cache statistics include:

- **Size**: Total disk space used by each cache
- **Item Count**: Number of cached entries
- **Status**: Whether the cache is active or empty
- **Age**: Oldest and newest entries
- **Performance** (Network cache only):
  - Cache hits/misses
  - Hit rate percentage
  - Average retrieval time
  - Total nodes and edges cached

## Cache Configuration

### Environment Variables

- `CENSUS_CACHE_ENABLED`: Enable/disable census caching (default: true)
- `CENSUS_CACHE_DIR`: Directory for census cache (default: `.census_cache`)

### Geocoding Cache Settings

Configure in `GeocodingConfig`:
- `enable_cache`: Enable/disable geocoding cache
- `cache_ttl_hours`: Time-to-live for cached entries
- `cache_max_size`: Maximum number of entries

### Network Cache Settings

Configure when creating cache instance:
- `max_cache_size_gb`: Maximum cache size in gigabytes (default: 5.0)
- Cache directory: `cache/networks`

## Best Practices

1. **Regular Cleanup**: Clear caches periodically to free disk space
2. **Monitor Performance**: Check cache hit rates to ensure effectiveness
3. **Selective Clearing**: Clear only specific caches when troubleshooting
4. **Before Updates**: Clear caches before updating SocialMapper
5. **Disk Space**: Monitor available disk space as caches can grow large

## Troubleshooting

### Cache Not Working

1. Check if caching is enabled in configuration
2. Verify cache directories have write permissions
3. Ensure sufficient disk space is available

### Performance Issues

1. Check cache hit rates - low rates indicate cache misses
2. Clear and rebuild cache if corrupted
3. Increase cache size limits if needed

### Clear Cache When

- Experiencing unexpected results
- After configuration changes
- Before/after software updates
- When disk space is low

## Implementation Details

### CacheManager Class

The `CacheManager` class in `socialmapper/cache_manager.py` provides:

- Centralized cache statistics gathering
- Unified cache clearing interface
- Cache size and age monitoring
- Cross-cache operations

### Cache Storage Formats

- **Network Cache**: Uses gzip compression with ~50% compression ratio
- **Geocoding Cache**: Parquet format for efficient columnar storage
- **Census Cache**: Pickle format for Python object serialization
- **General Cache**: Plain JSON for compatibility

### Thread Safety

All cache implementations are thread-safe:
- Network cache uses threading locks
- Geocoding cache uses file-based locking
- Census cache uses thread-safe operations