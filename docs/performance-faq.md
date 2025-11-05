# Performance FAQ

Common questions about SocialMapper performance, optimization, and troubleshooting.

## General Performance

### Q: How fast is SocialMapper compared to alternatives?

**A:** With proper configuration, SocialMapper is competitive or faster than most alternatives:

- **Single isochrone**: 2-5 seconds (with warm cache)
- **50 POI batch**: 67 seconds with clustering (vs. 320-450 seconds for alternatives)
- **Census data**: Sub-second with caching (vs. repeated API calls)
- **POI search**: 2-5 seconds for typical queries

Our benchmarks show 4-8x performance improvements with concurrent processing and intelligent caching enabled.

### Q: Why is my first analysis slow?

**A:** The first run downloads and caches network data, which takes time. Subsequent runs are 5-10x faster because they use cached data. This is normal and expected behavior. For production use, consider warming the cache:

```python
from socialmapper import api

# Pre-warm cache for your area
api.warm_cache_for_area(
    bbox=(45.4, -123.0, 45.6, -122.5),  # Portland area
    travel_modes=['drive', 'walk']
)
```

### Q: What hardware do I need?

**A:** SocialMapper works on modest hardware:

- **Minimum**: 2 CPU cores, 4 GB RAM, 10 GB disk
- **Recommended**: 4 CPU cores, 16 GB RAM, 50 GB SSD
- **Optimal**: 8+ CPU cores, 32 GB RAM, 100 GB NVMe SSD

Most operations use <500 MB RAM. Large batch operations (100+ POIs) may use 1-2 GB.

## Optimization Tips

### Q: How can I make SocialMapper 10x faster?

**A:** Combine these optimizations:

1. **Enable caching** (enabled by default) - 5-10x speedup on repeated operations
2. **Use concurrent processing** - 3-4x speedup for batch operations
3. **Enable clustering** - 2-3x speedup for nearby POIs
4. **Choose appropriate travel modes** - Walking is 2-3x faster than driving
5. **Use GeoParquet format** - 3-5x faster than GeoJSON

Example optimized configuration:

```python
from socialmapper.isochrone import create_isochrones_from_poi_list

results = create_isochrones_from_poi_list(
    poi_data={'pois': pois},
    travel_time_limit=20,
    use_concurrent=True,        # Enable parallel processing
    use_clustering=True,         # Group nearby POIs
    max_workers=4,               # Use 4 CPU cores
    use_parquet=True,           # Fast file format
    simplify_tolerance=0.001    # Reduce geometry complexity
)
```

### Q: Which travel mode is fastest to process?

**A:** Processing speed by mode:

1. **Walking** (fastest): Smallest networks, ~2-3 seconds per isochrone
2. **Biking**: Moderate networks, ~3-5 seconds per isochrone
3. **Driving** (slowest): Largest networks, ~5-10 seconds per isochrone

For urban analysis, walking mode is often both faster and more relevant.

### Q: How much does caching help?

**A:** Caching provides dramatic improvements:

| Operation | Without Cache | With Cache | Improvement |
|-----------|--------------|------------|-------------|
| Single isochrone | 12 seconds | 2 seconds | 83% faster |
| Census data | 300ms | <10ms | 97% faster |
| POI search | 3 seconds | <100ms | 96% faster |
| Geocoding | 200ms | <5ms | 98% faster |

Cache hit rates typically exceed 85% in production use.

## Scalability

### Q: How many POIs can I process?

**A:** Practical limits by configuration:

- **Single machine, default settings**: 100-500 POIs comfortably
- **Single machine, optimized**: 1,000-5,000 POIs
- **With chunking/batching**: 10,000+ POIs
- **Distributed processing**: 100,000+ POIs

For large datasets, process in chunks:

```python
def process_large_dataset(locations, chunk_size=100):
    results = []
    for i in range(0, len(locations), chunk_size):
        chunk = locations[i:i+chunk_size]
        chunk_results = api.process_batch(chunk)
        results.extend(chunk_results)

        # Save intermediate results
        if i % 500 == 0:
            save_checkpoint(results)

    return results
```

### Q: How much disk space does the cache need?

**A:** Cache size depends on coverage area:

- **City (Portland)**: 100-500 MB
- **Metro area**: 500 MB - 1 GB
- **State (Oregon)**: 1-5 GB
- **Region (Pacific NW)**: 5-10 GB
- **Country (USA)**: 10-50 GB

You can limit cache size:

```python
from socialmapper.cache_manager import CacheManager

manager = CacheManager()
manager.set_cache_limit(max_size_gb=5)
```

## Troubleshooting

### Q: Why are my isochrones taking >30 seconds each?

**A:** Common causes:

1. **Cold cache** - First runs are slower
2. **Large travel times** - 60-minute isochrones are 10x slower than 15-minute
3. **Rural areas with driving mode** - Sparse networks require large downloads
4. **Poor network connectivity** - Check your internet connection
5. **Rate limiting** - Some APIs have request limits

Solutions:
```python
# Use smaller travel times
isochrone = api.create_isochrone(location, travel_time=15)  # Not 60

# Use clustering for rural areas
results = api.create_isochrones_batch(
    pois=rural_pois,
    use_clustering=True,
    max_cluster_radius_km=25  # Larger radius for rural
)

# Check network latency
import requests
response = requests.get("https://overpass-api.de/api/status")
print(f"Latency: {response.elapsed.total_seconds():.1f}s")
```

### Q: How can I reduce memory usage?

**A:** Memory optimization strategies:

1. **Enable geometry simplification**:
```python
results = api.create_isochrones(
    simplify_tolerance=0.001  # Reduces memory by 30-50%
)
```

2. **Process in smaller batches**:
```python
for chunk in chunks(locations, size=25):
    process_and_save(chunk)
    gc.collect()  # Force garbage collection
```

3. **Use memory-efficient formats**:
```python
# GeoParquet uses 60% less memory than GeoJSON
gdf.to_parquet("output.parquet")
```

4. **Clear intermediate results**:
```python
results.to_file("output.geojson")
del results
gc.collect()
```

### Q: I'm getting rate limit errors

**A:** Handle rate limits gracefully:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def robust_api_call():
    try:
        return api.make_request()
    except RateLimitError:
        time.sleep(60)  # Wait for rate limit reset
        raise
```

Or use batch operations to reduce API calls:

```python
# Instead of individual geocoding
for address in addresses:
    coords = api.geocode(address)  # Many API calls

# Use batch geocoding
coords = api.batch_geocode(addresses)  # Single API call
```

## Production Use

### Q: Is SocialMapper suitable for production?

**A:** Yes! SocialMapper includes production-ready features:

- ✅ Comprehensive error handling
- ✅ Automatic retries with exponential backoff
- ✅ Resource monitoring and limits
- ✅ Cache persistence across sessions
- ✅ Concurrent processing with thread/process safety
- ✅ Memory management and garbage collection
- ✅ 255+ tests with high coverage

### Q: How do I monitor performance in production?

**A:** Use built-in monitoring tools:

```python
from socialmapper.cache_manager import CacheManager
from socialmapper.monitoring import ResourceMonitor

# Monitor cache performance
cache = CacheManager()
stats = cache.get_cache_statistics()
print(f"Cache hit rate: {stats['summary']['hit_rate']:.1%}")

# Monitor resource usage
monitor = ResourceMonitor()
monitor.start()

# Run your analysis
results = api.complex_analysis()

stats = monitor.stop()
print(f"Peak memory: {stats['peak_memory_mb']:.1f} MB")
print(f"CPU time: {stats['cpu_seconds']:.1f} seconds")
```

### Q: Can I use SocialMapper in a web service?

**A:** Yes, with proper configuration:

```python
from socialmapper import api
from socialmapper.performance import get_performance_config

# Configure for web service
config = get_performance_config(
    preset='balanced',
    http_timeout_seconds=10,  # Quick timeout for web
    max_workers=2,  # Limit concurrent workers
    cache_enabled=True
)

# Use in your web framework
@app.route('/isochrone')
def generate_isochrone():
    location = request.args.get('location')

    # Use timeout to prevent hanging
    with timeout(30):
        result = api.create_isochrone(
            location=location,
            travel_time=15
        )

    return jsonify(result)
```

## Advanced Topics

### Q: How does the clustering algorithm work?

**A:** SocialMapper uses DBSCAN machine learning to intelligently group POIs:

1. Analyzes POI spatial distribution
2. Groups nearby POIs (within max_cluster_radius_km)
3. Downloads one network per cluster (not per POI)
4. Reduces network downloads by 60-80%

This provides optimal performance for dense urban areas while handling sparse rural regions correctly.

### Q: Can I use custom caching backends?

**A:** Yes, SocialMapper's cache system is extensible:

```python
from socialmapper.cache_manager import CacheManager

# Use Redis for distributed caching
cache = CacheManager(
    backend='redis',
    redis_url='redis://localhost:6379'
)

# Use S3 for persistent cloud caching
cache = CacheManager(
    backend='s3',
    bucket='my-cache-bucket'
)
```

### Q: How do I profile performance?

**A:** Use built-in profiling tools:

```python
import cProfile
import pstats

# CPU profiling
profiler = cProfile.Profile()
profiler.enable()

# Your analysis code
results = api.analyze_accessibility(...)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)  # Top 10 time consumers

# Memory profiling
from memory_profiler import profile

@profile
def memory_intensive_operation():
    return api.process_large_dataset(...)
```

## Getting Help

### Q: Where can I get more help with performance?

**A:** Resources available:

1. **[Full Performance Guide](performance.md)** - Comprehensive documentation
2. **[Benchmarks README](../benchmarks/README.md)** - How to run and interpret benchmarks
3. **[GitHub Issues](https://github.com/mihiarc/socialmapper/issues)** - Report problems or ask questions
4. **[Example Scripts](https://github.com/mihiarc/socialmapper/tree/main/examples)** - Optimized code examples

### Q: How can I contribute performance improvements?

**A:** We welcome contributions! See our [Benchmarks README](../benchmarks/README.md) for:

- How to run performance tests
- How to add new benchmarks
- Performance testing guidelines
- Current optimization opportunities

---

*Last updated: November 2024 | SocialMapper v0.9.0*