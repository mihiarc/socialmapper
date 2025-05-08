# Block Group Selection Method Benchmarking

This directory contains scripts to benchmark the performance of two different approaches for selecting census block groups:

1. **State-based method**: The traditional approach that gets block groups for entire states
2. **County-based method**: The optimized approach that gets block groups only for relevant counties

## Prerequisites

Ensure you have installed all SocialMapper dependencies, including `cenpy` which is required for the county-based method:

```bash
uv pip install -r requirements.txt
```

## Running the Benchmarks

### Standard Benchmark Suite

The standard benchmark runs tests on predefined test cases including:
- Single POI in a small state (Rhode Island)
- Single POI in a large state (Texas)
- Multiple POIs in the same state (California)
- Multiple POIs across different states (New York and New Jersey)

To run the standard benchmark:

```bash
python benchmark_block_groups.py
```

Options:
- `--repeat N`: Run each test N times (default: 1)
- `--output FILENAME`: Base name for output files (without extension)

Example:

```bash
python benchmark_block_groups.py --repeat 3 --output my_benchmark_results
```

### Custom Benchmark

You can also run benchmarks using your own custom POI data:

```bash
python benchmark_custom.py path/to/your/poi_file.json
```

Options:
- `--name "Test Name"`: Custom name for the test case
- `--travel-time 15`: Travel time in minutes (default: 15)
- `--repeat N`: Run each test N times (default: 1)
- `--output FILENAME`: Base name for output files (without extension)

Example:

```bash
python benchmark_custom.py examples/custom_coordinates.csv --name "My Custom Test" --travel-time 20 --repeat 2
```

## Benchmark Results

The benchmark scripts generate several output files:

1. **JSON Results**: Contains detailed results for all test runs
   - `benchmark_results.json` or your custom output filename

2. **Performance Chart**: Visual comparison of both methods
   - `benchmark_results.png` or your custom output filename

3. **Block Group Files**: The actual block group GeoJSON files
   - Located in `benchmark_output/block_groups/`

## Interpreting Results

The benchmark output shows:
- Execution time for each method
- Number of block groups found
- Percentage improvement of county-based over state-based method

### Example Output:

```
Summary by test case and method:
                         case method      mean       min       max       std
0       Multiple POIs - Same State county  45.321  45.321  45.321  0.000000
1       Multiple POIs - Same State  state  98.765  98.765  98.765  0.000000
2  Multiple POIs - Different States county  32.456  32.456  32.456  0.000000
3  Multiple POIs - Different States  state  75.321  75.321  75.321  0.000000
4        Single POI - Large State county  28.654  28.654  28.654  0.000000
5        Single POI - Large State  state  62.123  62.123  62.123  0.000000
6        Single POI - Small State county  12.345  12.345  12.345  0.000000
7        Single POI - Small State  state  15.678  15.678  15.678  0.000000

Method comparison (mean execution time in seconds):
                               county    state  improvement
case                                                       
Multiple POIs - Different States  32.456  75.321      56.91
Multiple POIs - Same State        45.321  98.765      54.11
Single POI - Large State          28.654  62.123      53.87
Single POI - Small State          12.345  15.678      21.26
```

## Notes

- The benchmark always clears the cache before each test to ensure fair comparison
- For large states, the performance improvement is much more significant
- The county-based approach is designed to be more efficient when dealing with:
  - Large states
  - POIs that only cover a small portion of a state
  - Cross-state metropolitan areas 