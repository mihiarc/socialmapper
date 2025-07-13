# DuckDB Isochrone Cache System

## Overview

The isochrone cache system uses DuckDB with the spatial extension to store validated isochrones for reuse across analyses. This dramatically improves performance by avoiding redundant network downloads and isochrone calculations.

## Key Features

- **High-Performance Storage**: DuckDB provides columnar storage with excellent compression
- **Spatial Indexing**: R-tree indexes and Hilbert curve ordering for fast spatial queries
- **GeoParquet Integration**: Native support for cloud-optimized geospatial formats
- **Automatic Deduplication**: Prevents storing duplicate isochrones
- **Cache Statistics**: Track hit rates and performance metrics

## Architecture

```
┌─────────────────────────────────────────┐
│         SocialMapper Analysis           │
│                                         │
│  ┌─────────────┐    ┌────────────────┐ │
│  │   Check     │    │   Generate     │ │
│  │   Cache     │───▶│   Missing      │ │
│  │             │    │   Isochrones   │ │
│  └─────────────┘    └────────────────┘ │
│         │                    │          │
│         ▼                    ▼          │
│  ┌─────────────────────────────────┐   │
│  │     DuckDB Isochrone Cache      │   │
│  │  ┌─────────────────────────┐    │   │
│  │  │   Spatial Index (R-tree)│    │   │
│  │  └─────────────────────────┘    │   │
│  │  ┌─────────────────────────┐    │   │
│  │  │  Compressed Geometries  │    │   │
│  │  └─────────────────────────┘    │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## Usage

### Basic Usage

```python
from utils.isochrone_cache import IsochroneCache

# Initialize cache
cache = IsochroneCache("cache/isochrones.duckdb")

# Check for cached isochrone
result = cache.get_isochrone(
    lat=39.3343285,
    lon=-101.7285206,
    travel_time=30,
    travel_mode='drive'
)

if result:
    print(f"Found cached isochrone: {result['area_km2']:.1f} km²")
else:
    print("Not in cache, need to generate")

# Add new isochrone to cache
isochrone_data = {
    'latitude': 39.3343285,
    'longitude': -101.7285206,
    'travel_time_minutes': 30,
    'travel_mode': 'drive',
    'origin_name': 'Walmart Goodland',
    'origin_type': 'walmart'
}

cache.add_isochrone(isochrone_data, geometry_object)
```

### Running Cached Analysis

```python
from utils.cached_analysis import CachedAnalysisRunner

with CachedAnalysisRunner() as runner:
    results = runner.analyze_with_cache(
        poi_file='data/input/walmart_cleaned.csv',
        travel_time=30,
        travel_mode='drive',
        output_dir='data/output/cached'
    )
    
    print(f"Cache hit rate: {results['cache_stats']['cache_hits'] / results['total_pois'] * 100:.1f}%")
```

### Migrating Existing Data

```bash
# Import existing isochrone files into cache
uv run python src/utils/migrate_to_cache.py
```

## Database Schema

### Main Table: `isochrone_cache`

| Column | Type | Description |
|--------|------|-------------|
| cache_key | VARCHAR | SHA256 hash of location + parameters |
| origin_lat | DOUBLE | Origin latitude |
| origin_lon | DOUBLE | Origin longitude |
| origin_name | VARCHAR | Name of the location |
| origin_type | VARCHAR | Type of POI (walmart, grocer, etc.) |
| travel_time_minutes | INTEGER | Travel time in minutes |
| travel_mode | VARCHAR | Mode of travel (walk, bike, drive) |
| geometry | GEOMETRY | Isochrone polygon |
| area_km2 | DOUBLE | Area in square kilometers |
| perimeter_km | DOUBLE | Perimeter in kilometers |
| bbox_* | DOUBLE | Bounding box coordinates |
| created_at | TIMESTAMP | When cached |
| last_accessed | TIMESTAMP | Last access time |
| access_count | INTEGER | Number of times accessed |
| is_validated | BOOLEAN | Validation status |

### Indexes

1. **Spatial Index**: R-tree index on geometry column for fast spatial queries
2. **Lookup Index**: Composite index on (lat, lon, time, mode) for exact matches
3. **Hilbert Ordering**: Results ordered by Hilbert curve for optimal spatial locality

## Performance Characteristics

### Cache Performance

- **Lookup Time**: < 10ms for exact match
- **Spatial Query**: < 50ms for nearby isochrones
- **Insert Time**: < 20ms per isochrone
- **Storage**: ~0.1 MB per isochrone (compressed)

### Expected Improvements

| Scenario | Without Cache | With Cache | Improvement |
|----------|--------------|------------|-------------|
| Re-analyze 100 Walmarts | 8-10 minutes | 30 seconds | 16-20x faster |
| Single location lookup | 5-10 seconds | < 0.1 seconds | 50-100x faster |
| Spatial search (5km radius) | N/A | < 0.1 seconds | New capability |

## Maintenance

### Regular Tasks

1. **Monitor Cache Size**
   ```python
   stats = cache.get_statistics()
   print(f"Cache size: {stats['total_isochrones']:,} isochrones")
   ```

2. **Clean Old Entries**
   ```python
   # Remove entries not accessed in 90 days
   removed = cache.cleanup_old_entries(days=90)
   ```

3. **Export Backup**
   ```python
   cache.export_to_geoparquet('backup/isochrones_2025.geoparquet')
   ```

### Validation

Periodically validate cached isochrones:

```python
# Validate random sample
validation_df = runner.validate_cache_quality(sample_size=20)
invalid_count = len(validation_df[~validation_df['is_valid']])

if invalid_count > 0:
    print(f"Warning: {invalid_count} invalid isochrones found")
```

## Best Practices

1. **Cache Key Generation**: Always use consistent coordinate rounding (6 decimal places)
2. **Batch Operations**: Use transactions for bulk inserts
3. **Regular Exports**: Export to GeoParquet for long-term archival
4. **Monitor Hit Rate**: Aim for >80% cache hit rate for repeated analyses
5. **Spatial Ordering**: Maintain Hilbert ordering for optimal performance

## Troubleshooting

### Common Issues

1. **Low Hit Rate**
   - Check coordinate rounding consistency
   - Verify travel parameters match exactly
   - Consider increasing coordinate tolerance

2. **Slow Queries**
   - Run `ANALYZE` to update statistics
   - Check if spatial index exists
   - Consider partitioning by travel_time

3. **Large Cache Size**
   - Run cleanup for old entries
   - Export and archive historical data
   - Consider compression settings

### Debug Queries

```sql
-- Check cache distribution
SELECT travel_mode, travel_time_minutes, COUNT(*) 
FROM isochrone_cache 
GROUP BY travel_mode, travel_time_minutes;

-- Find duplicate locations
SELECT origin_lat, origin_lon, COUNT(*) as count
FROM isochrone_cache
GROUP BY origin_lat, origin_lon
HAVING COUNT(*) > 1;

-- Analyze spatial distribution
SELECT 
    ST_Envelope(ST_Union_Agg(geometry)) as coverage_area,
    COUNT(*) as isochrone_count
FROM isochrone_cache;
```

## Future Enhancements

1. **Multi-modal Caching**: Cache combined walk+transit isochrones
2. **Time-based Variations**: Cache different times of day
3. **Quality Metrics**: Store OSM data age and quality indicators
4. **Distributed Cache**: Support for shared cache across teams
5. **ML-based Prediction**: Predict isochrone shapes for uncached locations