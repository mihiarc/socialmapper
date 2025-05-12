# SocialMapper Optimization Test Suite

This document outlines the test suite designed to evaluate various performance optimizations in SocialMapper, particularly focusing on the phase where POI locations are used to determine which census block groups need to be included in analyses.

## Overview of Tests

The test suite consists of multiple specialized tests, each evaluating different aspects of optimization:

1. **Spatial Index Testing**: Benchmarks performance of spatial indexes vs. API lookups
2. **Parallelization Testing**: Evaluates optimal worker counts and batch sizes for concurrent processing
3. **Caching Testing**: Measures the impact of memory and disk-based caching strategies
4. **Spatial Operations Testing**: Tests chunking and parallel processing for spatial operations
5. **Combined Testing**: Evaluates all optimizations together in realistic scenarios

## Running the Tests

Each test can be run independently with various configuration parameters. Here are the standard command-line patterns:

```bash
# Spatial Index Testing
python -m tests.test_spatial_index --poi-counts 10 100 1000 --region chicago

# Parallelization Testing
python -m tests.test_parallelization --poi-count 1000 --worker-counts 1 2 4 8 16 --batch-sizes 10 50 100 500

# Caching Testing
python -m tests.test_caching --poi-count 1000 --cache-sizes 1 5 10 20 50

# Spatial Operations Testing
python -m tests.test_spatial_operations --block-group-counts 100 500 --chunk-sizes 25 50 100 --worker-counts 1 2 4

# Combined Testing
python -m tests.test_combined --poi-count 100 --scenarios scattered clustered
```

## Test Results

### Spatial Index Testing

#### Test 1: Chicago Region (Initial Implementation)
- **Date**: May 11, 2025
- **Setup**: 10 and 50 POIs in Chicago region
- **Hardware**: MacBook Pro, Apple M2, 16GB RAM
- **Results**:
  - **10 POIs**: 
    - Spatial Index: 0.00s (3999.91 POIs/sec)
    - API: 3.29s (3.04 POIs/sec)
    - **Speedup**: 1317x
  - **50 POIs**:
    - Spatial Index: 0.01s (4052.91 POIs/sec) 
    - API: 16.18s (3.09 POIs/sec)
    - **Speedup**: 1311x

#### Test 2: Chicago Region (With Bundled Data)
- **Date**: May 11, 2025
- **Setup**: 10 and 100 POIs in Chicago region
- **Hardware**: MacBook Pro, Apple M2, 16GB RAM
- **Results**:
  - **10 POIs**: 
    - Spatial Index: 0.35s (28.88 POIs/sec)
    - API: 0.00s (54899.27 POIs/sec) - Note: This is using a mock API for testing
    - **Match Rate**: 100% match between API and Spatial Index results
  - **100 POIs**:
    - Spatial Index: 0.01s (7699.36 POIs/sec) 
    - API: 0.00s (729444.17 POIs/sec) - Note: This is using a mock API for testing
    - **Match Rate**: 100% match between API and Spatial Index results
  - **Observations**: 
    - The bundled data approach increases initial load time but provides very fast lookups after that
    - The 100% match rate confirms the spatial index is working correctly
    - The API timing in this test is artificially fast due to the test mocking - in reality spatial index is much faster

### Parallelization Testing

#### Test 1: Varying Worker Counts and Batch Sizes
- **Date**: May 11, 2025
- **Setup**: 1000 POIs, testing worker counts [1,2,4,8,16] and batch sizes [10,50,100,500]
- **Hardware**: MacBook Pro, Apple M2, 16GB RAM
- **Results**:
  - **Best Configuration**: 8 workers with batch size 100
    - Processing Time: 16.61s
    - Memory Usage: 267MB
  - **Observations**:
    - Increasing workers beyond 8 doesn't improve performance and increases memory usage
    - Small batch sizes create too much overhead
    - Very large batch sizes don't utilize parallelism effectively
    - The optimal batch size scales with the complexity of each POI lookup
  - **Performance Improvement**: 3.7x faster than baseline (single worker)

#### Test 2: Parallelization with Bundled Data
- **Date**: May 11, 2025
- **Setup**: 100 POIs, testing worker counts [1,2,4,8] and batch sizes [10,20,50]
- **Hardware**: MacBook Pro, Apple M2, 16GB RAM
- **Results**:
  - **Initial Run**: 21.53s with 1 worker, batch size 10
    - This includes the one-time cost of loading the bundled data
  - **Subsequent Runs**: All configurations completed in < 0.01 seconds
  - **Memory Usage**: ~600MB peak for all configurations
  - **Observations**:
    - With bundled data, the initialization cost is the dominant factor
    - After initialization, all configurations have negligible execution time
    - Worker count and batch size have minimal impact on already-loaded data
    - The spatial index remains in memory between runs, eliminating the need for repeated loading

### Caching Testing

#### Test 1: Memory Caching (LRU Cache)
- **Date**: May 11, 2025
- **Setup**: 10 POIs in USA region with memory caching enabled vs. disabled
- **Hardware**: MacBook Pro, Apple M2, 16GB RAM
- **Results**:
  - **With Caching Enabled**:
    - Cold cache: 1.77s
    - Warm cache: 0.0001s (13,532x speedup)
    - Shuffled data: 0.00008s (22,150x speedup)
  - **With Caching Disabled**:
    - Consistent time: 2.31s for every run
  - **LRU Cache Benefit**: 17,597x faster with memory cache enabled
  - **Observations**:
    - The extreme speedup (>13,000x) demonstrates the massive impact of in-memory caching
    - Cached lookups are effectively instantaneous after initial population
    - The benefit increases with duplicate/nearby POIs that hit the same counties
    - The shuffled test confirms that cache lookups are by value, not by input order

### Spatial Operations Testing

#### Test 1: Chunking and Parallelism for Spatial Operations
- **Date**: May 11, 2025
- **Setup**: 100 and 500 block groups with various chunk sizes [25, 50, 100] and worker counts [1, 2, 4]
- **Hardware**: MacBook Pro, Apple M2, 16GB RAM
- **Results**:
  - **100 Block Groups**: 
    - Baseline: 0.02s, 155MB memory
    - Best Configuration: Parallel with 4 workers (2.24x speedup)
    - Memory Impact: Minimal (<1% increase across all optimizations)
  - **500 Block Groups**:
    - Baseline: 0.04s, 157MB memory
    - No significant speedup observed for this dataset size
    - Memory Impact: Minimal (<1.5% increase)
  - **Observations**:
    - For small datasets (<1000 block groups), parallel processing provides the best performance
    - Chunking helps manage memory usage but doesn't significantly improve performance for small datasets
    - Memory overhead of all optimization strategies is minimal (<1.5%)
    - The benefits of spatial optimizations are expected to be more pronounced with larger datasets (>1000 block groups)
    - The cost of setting up chunks and workers can sometimes outweigh the benefits for very small datasets

### Combined Testing

#### Test 1: All Optimizations with Different POI Distributions
- **Date**: May 11, 2025
- **Setup**: 100 POIs in the Chicago region with different distribution patterns (scattered and clustered)
- **Hardware**: MacBook Pro, Apple M2, 16GB RAM
- **Optimized Configuration**: 4 workers, batch size 100, chunk size 1000
- **Results**:
  - **Scattered POIs**:
    - Baseline: 56.44s, 671MB peak memory
      - County Determination: 14.59s (25.8%)
      - Block Group Fetching: 41.31s (73.2%)
      - Spatial Operations: 0.54s (1.0%)
    - Optimized: 1.15s, 337MB peak memory
      - County Determination: 0.02s (1.5%)
      - Block Group Fetching: 0.61s (52.8%)
      - Spatial Operations: 0.52s (45.7%)
    - **Speedup**: 49.19x
    - **Memory Impact**: 50% reduction
  - **Clustered POIs**:
    - Baseline: 0.87s, 361MB peak memory
      - County Determination: 0.01s (1.5%)
      - Block Group Fetching: 0.67s (77.5%)
      - Spatial Operations: 0.18s (20.9%)
    - Optimized: 0.74s, 367MB peak memory
      - County Determination: 0.01s (1.9%)
      - Block Group Fetching: 0.52s (70.3%)
      - Spatial Operations: 0.21s (27.8%)
    - **Speedup**: 1.17x
    - **Memory Impact**: 1.7% increase
  - **Observations**:
    - The impact of optimizations varies dramatically based on POI distribution
    - Scattered POIs: Massive 49.19x speedup due to highly effective caching and parallelism
    - Clustered POIs: Modest 1.17x speedup because data is already concentrated in fewer counties
    - In the scattered scenario, 74% of time was spent on block group fetching, which was reduced by 98.5% through caching
    - Memory usage decreased in the scattered scenario due to better resource management
    - The benefits of all optimizations combined are significantly greater than any individual optimization

## Implementation Notes

### Spatial Index Implementation

The spatial index is implemented using:
1. **RTtree Index**: For fast spatial lookups
2. **Bundled County Data**: Pre-loaded county geometries packaged with the library
3. **LRU Caching**: For repeated lookups

The county shapefile is loaded once at startup and remains in memory for quick lookups. This trades some initial memory overhead for significant performance gains during operation.

### Parallelization Implementation

Parallelization uses:
1. **ThreadPoolExecutor**: For I/O bound operations
2. **Batch Processing**: To optimize worker assignment and reduce overhead
3. **Dynamic Thread Count**: Adjusts based on system capabilities

### Caching Implementation

Two types of caching are implemented:
1. **Memory Caching**: 
   - Uses Python's `@lru_cache` decorator for in-memory caching
   - Applied to frequently called functions like county lookups
   - Provides massive speedups for repeated operations (>13,000x)
   - Automatically evicts least recently used entries when full

2. **Disk Caching**:
   - Persists geographical data between runs in the cache directory
   - Used for county boundaries, block groups, and other large datasets
   - Formatted as GeoJSON for compatibility and easy inspection
   - Files are named based on their content (e.g., `block_groups_06_037.geojson` for LA County)

### Spatial Operations Implementation

Spatial operations optimizations include:
1. **Chunking**: 
   - Divides large datasets into manageable chunks to reduce memory pressure
   - Processes each chunk independently and combines results
   - Scales well with very large datasets

2. **Parallel Processing**:
   - Uses ThreadPoolExecutor for concurrent processing of spatial operations
   - Particularly effective for CPU-intensive operations like spatial joins
   - Distributes work across multiple CPU cores for better resource utilization

3. **Spatial Filtering**:
   - Uses bounding box filtering as a pre-processing step to reduce data volume
   - Significantly reduces the number of costly point-in-polygon operations
   - Example: Reduced test datasets by ~30% (500 → 362 block groups)

## Recommendations

Based on the test results, the following configurations are recommended:

1. **Default Configuration**:
   - Spatial Index: Enabled with bundled data
   - Workers: 4
   - Batch Size: 100
   - Chunk Size: 1000
   - LRU Cache: Enabled with default size (1024 entries)

2. **Low-Memory Configuration**:
   - Workers: 4
   - Batch Size: 50
   - Cache Size: 5
   - Bundled Data: Load on-demand

3. **High-Performance Configuration**:
   - Workers: 8
   - Batch Size: 100
   - Chunk Size: 1000
   - LRU Cache: Increased to 2048 entries
   - Preload all spatial indexes

## Future Work

Additional tests and optimizations to consider:

1. Evaluate disk-based spatial indexes for very large datasets
2. Implement clustered cache invalidation strategies
3. Test with distributed processing for extremely large POI sets
4. Add load-on-demand option for bundled data to reduce memory usage when not needed
5. Implement tiered caching strategy with both memory and disk components for optimal performance and resource usage
6. Evaluate spatial operations with much larger datasets (>10,000 block groups) to better demonstrate chunking benefits 