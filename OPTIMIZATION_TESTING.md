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
python -m tests.test_spatial_operations --poi-count 1000 --chunk-sizes 50 100 500 --workers 1 4 8

# Combined Testing
python -m tests.test_combined --poi-count 1000 --scenario basic advanced extreme
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

## Recommendations

Based on the test results, the following configurations are recommended:

1. **Default Configuration**:
   - Spatial Index: Enabled with bundled data
   - Workers: 8
   - Batch Size: 100

2. **Low-Memory Configuration**:
   - Workers: 4
   - Batch Size: 50
   - Cache Size: 5

3. **High-Performance Configuration**:
   - Workers: 16
   - Batch Size: 100
   - Chunk Size: 500

## Future Work

Additional tests and optimizations to consider:

1. Evaluate disk-based spatial indexes for very large datasets
2. Implement clustered cache invalidation strategies
3. Test with distributed processing for extremely large POI sets
4. Add load-on-demand option for bundled data to reduce memory usage when not needed 