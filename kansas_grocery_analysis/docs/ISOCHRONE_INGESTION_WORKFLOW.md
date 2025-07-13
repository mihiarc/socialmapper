# Isochrone Ingestion Workflow

## Overview

Isochrones are ingested into the DuckDB cache **automatically during analysis**, not as a separate post-processing step. This ensures real-time caching and immediate reuse benefits.

## Ingestion Points

### 1. **During SocialMapper Analysis** (Primary Method)

When using the `CachedAnalysisRunner`, isochrones are cached as they're generated:

```python
from utils.cached_analysis import CachedAnalysisRunner

with CachedAnalysisRunner() as runner:
    results = runner.analyze_with_cache(
        poi_file='data/input/walmart_cleaned.csv',
        travel_time=30,
        travel_mode='drive',
        output_dir='data/output/analysis'
    )
```

**What happens internally:**
1. For each POI, check if isochrone exists in cache
2. If cached → use it (milliseconds)
3. If not cached → generate via SocialMapper → **automatically add to cache**
4. Continue with analysis using cached/new isochrones

### 2. **Post-Analysis Migration** (For Existing Data)

If you have existing isochrone files from previous analyses:

```bash
# One-time migration of existing isochrones
uv run python src/utils/migrate_to_cache.py
```

This scans for existing `.geoparquet` files and imports them into the cache.

### 3. **Direct Integration** (Custom Scripts)

For custom analysis scripts, integrate caching directly:

```python
from socialmapper import SocialMapperClient
from utils.isochrone_cache import IsochroneCache

# Initialize cache
cache = IsochroneCache()

# Your analysis loop
for poi in poi_list:
    # Check cache first
    cached = cache.get_isochrone(
        poi.lat, poi.lon, 
        travel_time=30, 
        travel_mode='drive'
    )
    
    if cached:
        # Use cached isochrone
        isochrone_geom = wkt.loads(cached['geometry_wkt'])
    else:
        # Generate new isochrone
        with SocialMapperClient() as client:
            result = client.analyze(
                location=f"{poi.lat}, {poi.lon}",
                poi_type="amenity",
                poi_name="grocery",
                travel_time=30
            )
            
            if result.is_ok():
                analysis = result.unwrap()
                # Extract isochrone geometry from analysis
                
                # Cache it immediately
                cache.add_isochrone(
                    {
                        'latitude': poi.lat,
                        'longitude': poi.lon,
                        'travel_time_minutes': 30,
                        'travel_mode': 'drive',
                        'origin_name': poi.name,
                        'origin_type': 'walmart'
                    },
                    isochrone_geom,
                    metadata={
                        'network_nodes': analysis.network_stats.get('nodes', 0),
                        'network_edges': analysis.network_stats.get('edges', 0)
                    }
                )
```

## Complete Example: Kansas Grocery Analysis

Here's how to run your Kansas grocery analysis with automatic caching:

```python
#!/usr/bin/env python3
"""
Run Kansas grocery analysis with isochrone caching.
"""

from pathlib import Path
from utils.cached_analysis import CachedAnalysisRunner

def analyze_kansas_groceries():
    """Analyze all grocery stores with caching."""
    
    # Input files
    poi_files = [
        'data/input/walmart_cleaned.csv',
        'data/input/target_cleaned.csv',
        'data/input/grocery_cleaned.csv'
    ]
    
    # Initialize runner (uses cache automatically)
    with CachedAnalysisRunner() as runner:
        
        for poi_file in poi_files:
            print(f"\nAnalyzing {poi_file}...")
            
            # Run analysis - caching happens automatically!
            results = runner.analyze_with_cache(
                poi_file=poi_file,
                travel_time=30,
                travel_mode='drive',
                output_dir=Path('data/output') / Path(poi_file).stem
            )
            
            # Show cache performance
            stats = results['cache_stats']
            hit_rate = stats['cache_hits'] / results['total_pois'] * 100
            
            print(f"  POIs processed: {results['total_pois']}")
            print(f"  Cache hit rate: {hit_rate:.1f}%")
            print(f"  Time saved: {stats['time_saved_seconds']/60:.1f} minutes")
        
        # Export cache report
        runner.export_cache_report('cache_performance.md')

if __name__ == "__main__":
    analyze_kansas_groceries()
```

## Workflow Diagram

```
┌─────────────────────────────────────────────────────┐
│                  Start Analysis                     │
└─────────────────────────────────────────────────────┘
                           │
                           ▼
                  ┌────────────────┐
                  │ For each POI   │
                  └────────────────┘
                           │
                           ▼
               ┌───────────────────────┐
               │ Check isochrone cache │
               └───────────────────────┘
                     │         │
              Found? │         │ Not found?
                     ▼         ▼
            ┌─────────────┐  ┌──────────────────┐
            │ Use cached  │  │ Generate via     │
            │ isochrone   │  │ SocialMapper     │
            │ (<10ms)     │  │ (5-10 seconds)   │
            └─────────────┘  └──────────────────┘
                     │               │
                     │               ▼
                     │         ┌─────────────┐
                     │         │  Validate   │
                     │         │  isochrone  │
                     │         └─────────────┘
                     │               │
                     │         Valid?│
                     │               ▼
                     │         ┌─────────────┐
                     │         │ Add to      │
                     │         │ cache       │
                     │         └─────────────┘
                     │               │
                     └───────────────┘
                           │
                           ▼
                  ┌────────────────┐
                  │ Continue with  │
                  │ analysis       │
                  └────────────────┘
```

## Benefits of Integrated Caching

1. **Automatic**: No manual cache management needed
2. **Real-time**: Isochrones cached as soon as generated
3. **Validated**: Only quality isochrones enter cache
4. **Efficient**: Subsequent runs are 16-20x faster
5. **Transparent**: Works with existing SocialMapper workflow

## Monitoring Cache Growth

```python
# Check cache statistics during analysis
cache = IsochroneCache()
stats = cache.get_statistics()

print(f"Total cached isochrones: {stats['total_isochrones']:,}")
print(f"Unique locations: {stats['unique_locations']:,}")
print(f"Average validation score: {stats['avg_validation_score']:.2f}")
print(f"Cache hit rate: {stats['total_hits'] / stats['total_isochrones']:.1f}")
```

## Advanced: Batch Pre-warming

For large analyses, you can pre-warm the cache:

```python
from utils.cache_warmer import warm_cache_for_region

# Pre-generate isochrones for a region
warm_cache_for_region(
    bounds={'north': 40.0, 'south': 37.0, 'east': -94.5, 'west': -102.0},
    poi_types=['grocery', 'pharmacy'],
    travel_times=[15, 30, 45],
    travel_modes=['drive', 'walk']
)
```

## Best Practices

1. **Always use CachedAnalysisRunner** for consistency
2. **Monitor cache hit rates** - should improve over time
3. **Run migration once** for existing data
4. **Let validation work** - don't disable unless necessary
5. **Export periodically** to GeoParquet for backup

## Troubleshooting

### Low Cache Hit Rate?
- Check coordinate precision (must match to 6 decimals)
- Verify travel parameters match exactly
- Consider if POIs are truly unique locations

### Validation Rejections?
- Review validation report for patterns
- Adjust thresholds if needed for your region
- Check OSM data quality in problem areas

### Performance Issues?
- Run `ANALYZE` on cache database
- Check spatial index exists
- Consider cache size limits

## Summary

Isochrone ingestion is **built into the analysis workflow**, not a separate step. Just use `CachedAnalysisRunner` and caching happens automatically with validation, giving you immediate performance benefits on subsequent runs.