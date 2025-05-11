# Performance Optimizations for SocialMapper

This document details various performance optimizations implemented in the SocialMapper library, particularly focusing on the isochrone generation process which can be time-consuming for large numbers of POIs.

## 1. Network Graph Caching

### Problem
The original implementation downloaded a new road network for each POI, which was inefficient when multiple POIs were located in close proximity to each other.

### Solution
We implemented a spatial caching mechanism that:
- Stores network graphs in memory using an R-tree spatial index
- Reuses previously downloaded graphs for nearby POIs
- Implements an LRU (Least Recently Used) strategy to manage cache size

### Implementation Details
- Uses the `rtree` library for efficient spatial indexing
- Downloads slightly larger areas to improve cache hit rates
- Adds logging to track cache performance

### Expected Benefits
- Significant reduction in network download time
- Faster processing for clustered POIs
- Less data transfer from OpenStreetMap servers

### Testing
You can test the performance improvement using:
- `tests/test_isochrone_cache.py` - Basic test with synthetic POIs
- `examples/isochrone_cache_demo.py` - Real-world example with configurable parameters

### Example Usage

```python
# Run the cache demo with default settings (20 restaurants in San Francisco)
python examples/isochrone_cache_demo.py

# Run with custom parameters
python examples/isochrone_cache_demo.py --location "Chicago, IL" --poi-type "amenity=cafe" --limit 50 --travel-time 15
```

## 2. Parallel Processing

### Problem
Even with the caching mechanism, processing thousands of POIs sequentially is time-consuming, especially when multiple CPU cores are available.

### Solution
We implemented parallel processing using Python's `concurrent.futures` module:
- Uses a thread pool to process multiple POIs simultaneously
- Maintains the benefits of the caching mechanism across threads
- Automatically scales to the available CPU cores
- Provides a progress bar to track overall completion

### Implementation Details
- Uses `ThreadPoolExecutor` rather than `ProcessPoolExecutor` since:
  - The bottleneck is network I/O, not CPU computation
  - Thread-based parallelism allows sharing the graph cache
- Added a simple `n_jobs` parameter to control the number of parallel workers:
  - `n_jobs=1`: Sequential processing (default, no parallelism)
  - `n_jobs=-1`: Use all available CPU cores
  - `n_jobs=N`: Use a specific number of workers

### Expected Benefits
- Near-linear speedup for POIs that are geographically distributed
- Reduced processing time for large POI datasets
- Better utilization of available system resources

### Testing
You can test the parallel processing using:
- `tests/test_parallel_processing.py` - Benchmarks different numbers of workers

### Example Usage

```python
# Process POIs using all available CPU cores
python -m socialmapper.isochrone poi_data.json --jobs -1

# Process POIs using 4 worker threads
python -m socialmapper.isochrone poi_data.json --jobs 4
```

## Future Optimizations

The following optimizations are planned for future implementation:

1. **Batch Processing**: Process groups of POIs using a single larger network
2. **Graph Simplification**: Simplify road networks to reduce computation time
3. **Alpha Shapes**: Replace convex hulls with alpha shapes for more precise isochrones
4. **Optimized Graph Radius**: Calculate more conservative graph radii based on the road network

## Performance Metrics

When running the cache demo on a test dataset, we observed the following improvements:

### Initial Performance Estimates
| Optimization          | Average Time per POI | Improvement |
|-----------------------|----------------------|-------------|
| Baseline              | ~21 seconds          | -           |
| With Graph Caching    | ~5-10 seconds*       | 50-75%*     |

*Actual results vary based on POI density and geographic distribution

### Test Results
We ran the test with 10 POIs distributed randomly within a 5km radius of San Francisco:

| Metric                 | Without Cache        | With Cache           | Improvement     |
|------------------------|----------------------|----------------------|-----------------|
| Total Time             | 24.93 seconds        | 2.47 seconds         | 90.10%          |
| Average Time per POI   | 2.49 seconds         | 0.25 seconds         | 90.10%          |
| First POI (download)   | 22.64 seconds        | 0.26 seconds         | 98.85%          |
| Subsequent POIs (avg)  | 0.25 seconds         | 0.25 seconds         | -               |
| Graph Downloads        | 1                    | 0                    | 100.00%         |
| Cache Size             | 1 graph              | 1 graph              | -               |

The results show that:
1. First POI processing includes network download time (~20-22 seconds)
2. With caching, subsequent POIs in the same area process ~90% faster
3. For large datasets with thousands of POIs, the improvement would be substantial
4. The most significant gain comes from avoiding repeated network downloads

### Parallel Processing Results
We ran parallel processing benchmarks with 20 POIs in San Francisco using different numbers of worker threads:

| Configuration         | Total Time (s) | Time per POI (s) | Speedup | Improvement |
|-----------------------|----------------|------------------|---------|-------------|
| Sequential (1 worker) | 119.73         | 5.99             | 1.00    | Baseline    |
| 2 workers             | 122.26         | 6.11             | 0.98    | -2.07%      |
| 4 workers             | 175.74         | 8.79             | 0.68    | -31.87%     |
| 8 workers             | 232.70         | 11.63            | 0.51    | -48.55%     |

**Observations:**
1. Parallel processing did not improve performance for this workload
2. Adding more workers actually decreased performance
3. The best configuration was sequential processing (1 worker)

**Analysis:**
1. The performance degradation with more workers is likely due to:
   - Network contention - multiple simultaneous downloads competing for bandwidth
   - OpenStreetMap API rate limits - the service may throttle multiple concurrent requests
   - Thread overhead - the cost of thread management exceeds the benefits
2. The isochrone generation process is I/O-bound, not CPU-bound
3. The network graph downloading is the primary bottleneck

**Important Note on Internet Bandwidth:**
The parallel processing performance is heavily influenced by available internet bandwidth. Our tests were conducted with a standard consumer internet connection, where multiple workers competed for limited bandwidth, resulting in slower overall performance. With significantly higher bandwidth or in environments with:
- Enterprise-grade internet connections
- Proximity to OpenStreetMap servers
- No API rate limiting
- Distributed architecture

Parallel processing might show substantial improvements not seen in our tests. If you have access to high-bandwidth connections, you may want to run your own benchmarks to determine the optimal number of workers for your specific environment.

**Recommendations:**
1. For isochrone generation, use single-threaded processing with graph caching on standard internet connections
2. Consider batching POIs by geographic proximity to maximize cache usage
3. For very large datasets, explore dividing POIs into geographic regions and processing each region sequentially
4. If available bandwidth is high, experiment with 2-4 workers to find the optimal configuration for your environment

## Contributing

If you implement additional optimizations or improvements to the existing ones, please:
1. Add tests to verify the performance impact
2. Document your changes in this file
3. Include before/after benchmarks 