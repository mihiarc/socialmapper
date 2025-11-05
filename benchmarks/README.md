# SocialMapper Benchmarks

## Overview

This directory contains performance benchmarks for SocialMapper, providing standardized tests to measure and track performance across different versions and configurations.

## Table of Contents

- [Quick Start](#quick-start)
- [Running Benchmarks](#running-benchmarks)
- [Benchmark Suites](#benchmark-suites)
- [Interpreting Results](#interpreting-results)
- [Benchmark Methodology](#benchmark-methodology)
- [Contributing Benchmarks](#contributing-benchmarks)
- [CI/CD Integration](#cicd-integration)
- [Performance Tracking](#performance-tracking)

## Quick Start

### Run All Benchmarks

```bash
# Install benchmark dependencies
uv pip install -e ".[benchmark]"

# Run complete benchmark suite
uv run python -m benchmarks.run_all

# Run with specific configuration
uv run python -m benchmarks.run_all --config production

# Generate comparison report
uv run python -m benchmarks.compare --baseline v0.8.0 --current v0.9.0
```

### Run Specific Benchmark

```bash
# Isochrone generation benchmarks
uv run python -m benchmarks.isochrone_bench

# Census data retrieval benchmarks
uv run python -m benchmarks.census_bench

# Caching performance benchmarks
uv run python -m benchmarks.cache_bench

# Memory profiling
uv run python -m benchmarks.memory_profile
```

## Running Benchmarks

### Basic Usage

```python
# benchmarks/run_all.py
from benchmarks import BenchmarkRunner

# Initialize runner
runner = BenchmarkRunner(
    output_dir="results",
    compare_baseline=True,
    save_results=True
)

# Run all benchmarks
results = runner.run_all()

# Generate report
runner.generate_report(results, format="markdown")
```

### Configuration Options

```yaml
# benchmarks/config.yaml
benchmark_config:
  # Test data configuration
  test_data:
    small_dataset: 10   # POIs
    medium_dataset: 50  # POIs
    large_dataset: 200  # POIs

  # Environment settings
  environment:
    cache_enabled: true
    concurrent_processing: true
    max_workers: 4

  # Benchmark parameters
  parameters:
    repetitions: 3
    warmup_runs: 1
    timeout_seconds: 300

  # Output settings
  output:
    format: json
    include_system_info: true
    include_git_info: true
```

### Command Line Interface

```bash
# Run with verbose output
uv run python -m benchmarks.run_all --verbose

# Run specific test sizes
uv run python -m benchmarks.run_all --size small,medium

# Disable caching for baseline comparison
uv run python -m benchmarks.run_all --no-cache

# Set custom output directory
uv run python -m benchmarks.run_all --output results/2024-11/

# Compare with previous results
uv run python -m benchmarks.run_all --compare results/baseline.json
```

## Benchmark Suites

### 1. Core Operations (`benchmarks/core.py`)

Tests fundamental SocialMapper operations:

```python
class CoreBenchmarks:
    """Core operation benchmarks."""

    def bench_single_isochrone(self):
        """Benchmark single isochrone generation."""
        location = "Portland, OR"
        travel_time = 15

        with timer() as t:
            result = api.create_isochrone(
                location=location,
                travel_time=travel_time,
                travel_mode="drive"
            )

        return {
            'operation': 'single_isochrone',
            'time': t.elapsed,
            'parameters': {'location': location, 'travel_time': travel_time}
        }

    def bench_batch_isochrones(self):
        """Benchmark batch isochrone processing."""
        # Test with 50 POIs
        ...

    def bench_census_retrieval(self):
        """Benchmark census data retrieval."""
        ...
```

### 2. Scaling Tests (`benchmarks/scaling.py`)

Measures performance at different scales:

```python
class ScalingBenchmarks:
    """Test performance scaling characteristics."""

    def bench_linear_scaling(self):
        """Test if performance scales linearly."""
        sizes = [10, 20, 40, 80, 160]
        times = []

        for size in sizes:
            pois = generate_test_pois(size)
            t = measure_processing_time(pois)
            times.append(t)

        # Analyze scaling factor
        scaling_factor = calculate_scaling_factor(sizes, times)
        return {
            'scaling_type': 'linear' if scaling_factor < 1.2 else 'super-linear',
            'scaling_factor': scaling_factor,
            'data_points': list(zip(sizes, times))
        }
```

### 3. Cache Performance (`benchmarks/cache.py`)

Tests caching effectiveness:

```python
class CacheBenchmarks:
    """Cache system performance tests."""

    def bench_cache_hit_rate(self):
        """Measure cache effectiveness."""
        # Cold cache run
        clear_all_caches()
        cold_time = measure_operation_time()

        # Warm cache run
        warm_time = measure_operation_time()

        improvement = (cold_time - warm_time) / cold_time
        return {
            'cold_cache_time': cold_time,
            'warm_cache_time': warm_time,
            'improvement_percent': improvement * 100,
            'cache_effectiveness': 'high' if improvement > 0.7 else 'low'
        }
```

### 4. Memory Profiling (`benchmarks/memory.py`)

Tracks memory usage patterns:

```python
from memory_profiler import memory_usage

class MemoryBenchmarks:
    """Memory usage profiling."""

    def profile_isochrone_memory(self):
        """Profile memory usage during isochrone generation."""

        def operation():
            return api.create_isochrones_batch(
                pois=self.test_pois,
                travel_time=30
            )

        mem_usage = memory_usage(operation, interval=0.1)

        return {
            'peak_memory_mb': max(mem_usage),
            'average_memory_mb': sum(mem_usage) / len(mem_usage),
            'memory_timeline': mem_usage
        }
```

### 5. Concurrent Processing (`benchmarks/concurrent.py`)

Tests parallel processing performance:

```python
class ConcurrentBenchmarks:
    """Concurrent processing benchmarks."""

    def bench_worker_scaling(self):
        """Test performance with different worker counts."""
        worker_counts = [1, 2, 4, 8, 16]
        results = []

        for workers in worker_counts:
            time = measure_with_workers(workers)
            results.append({
                'workers': workers,
                'time': time,
                'speedup': baseline_time / time
            })

        optimal_workers = find_optimal_workers(results)
        return {
            'optimal_workers': optimal_workers,
            'results': results
        }
```

## Interpreting Results

### Understanding Metrics

```json
{
  "benchmark_results": {
    "timestamp": "2024-11-05T10:30:00Z",
    "version": "0.9.0",
    "system_info": {
      "platform": "darwin",
      "cpu_count": 8,
      "memory_gb": 16
    },
    "tests": {
      "single_isochrone": {
        "mean_time": 5.23,
        "std_dev": 0.34,
        "min_time": 4.89,
        "max_time": 5.67,
        "iterations": 10
      },
      "batch_processing_50": {
        "total_time": 67.4,
        "per_item_time": 1.35,
        "speedup_vs_sequential": 6.3
      }
    },
    "comparisons": {
      "vs_baseline": {
        "overall_improvement": "23%",
        "regressions": [],
        "improvements": [
          "batch_processing: 31% faster",
          "cache_hit_rate: 15% better"
        ]
      }
    }
  }
}
```

### Performance Grades

| Grade | Criteria | Description |
|-------|----------|-------------|
| **A** | <2s single, <60s for 50 | Excellent performance |
| **B** | <5s single, <120s for 50 | Good performance |
| **C** | <10s single, <300s for 50 | Acceptable performance |
| **D** | <20s single, <600s for 50 | Needs optimization |
| **F** | >20s single, >600s for 50 | Critical issues |

### Regression Detection

```python
def detect_regressions(current, baseline, threshold=0.1):
    """Detect performance regressions."""
    regressions = []

    for test_name in current['tests']:
        current_time = current['tests'][test_name]['mean_time']
        baseline_time = baseline['tests'][test_name]['mean_time']

        regression_pct = (current_time - baseline_time) / baseline_time

        if regression_pct > threshold:
            regressions.append({
                'test': test_name,
                'regression': f"{regression_pct:.1%}",
                'current': current_time,
                'baseline': baseline_time
            })

    return regressions
```

## Benchmark Methodology

### Test Data Generation

```python
# benchmarks/test_data.py

def generate_test_dataset(size='medium', distribution='clustered'):
    """Generate standardized test datasets."""

    if distribution == 'clustered':
        # Realistic clustered distribution (cities)
        centers = [(45.52, -122.67), (47.60, -122.33)]  # Portland, Seattle
        return generate_clustered_pois(centers, size)

    elif distribution == 'uniform':
        # Uniform distribution for scaling tests
        bbox = (45.0, -124.0, 49.0, -116.0)  # Pacific Northwest
        return generate_uniform_pois(bbox, size)

    elif distribution == 'sparse':
        # Sparse rural distribution
        return generate_sparse_pois(size)
```

### Measurement Protocol

1. **Warmup Phase**
   - Run operation once to warm caches
   - Load necessary libraries and data
   - Establish network connections

2. **Measurement Phase**
   - Run operation N times (default: 10)
   - Measure wall-clock time
   - Record memory usage
   - Track cache statistics

3. **Analysis Phase**
   - Calculate mean, median, std deviation
   - Identify outliers
   - Compare with baseline
   - Generate report

### Statistical Rigor

```python
import scipy.stats as stats

def analyze_benchmark_results(times):
    """Perform statistical analysis of benchmark times."""

    # Remove outliers using IQR method
    q1, q3 = np.percentile(times, [25, 75])
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    filtered = [t for t in times if lower <= t <= upper]

    return {
        'mean': np.mean(filtered),
        'median': np.median(filtered),
        'std_dev': np.std(filtered),
        'cv': np.std(filtered) / np.mean(filtered),  # Coefficient of variation
        'ci_95': stats.t.interval(0.95, len(filtered)-1,
                                  np.mean(filtered),
                                  stats.sem(filtered)),
        'outliers_removed': len(times) - len(filtered)
    }
```

## Contributing Benchmarks

### Adding New Benchmarks

1. **Create benchmark file**
   ```python
   # benchmarks/my_feature_bench.py
   from benchmarks.base import BaseBenchmark

   class MyFeatureBenchmark(BaseBenchmark):
       """Benchmark for new feature."""

       def setup(self):
           """Setup test data."""
           self.test_data = generate_test_data()

       def bench_feature_performance(self):
           """Benchmark the feature."""
           with self.timer() as t:
               result = my_feature(self.test_data)

           return self.format_result(
               name='my_feature',
               time=t.elapsed,
               operations=len(self.test_data)
           )
   ```

2. **Register benchmark**
   ```python
   # benchmarks/__init__.py
   BENCHMARK_SUITES.append(MyFeatureBenchmark)
   ```

3. **Add to CI pipeline**
   ```yaml
   # .github/workflows/benchmark.yml
   - name: Run new benchmark
     run: uv run python -m benchmarks.my_feature_bench
   ```

### Benchmark Guidelines

1. **Be Realistic**: Use real-world data distributions
2. **Be Consistent**: Use standardized test data
3. **Be Comprehensive**: Test edge cases
4. **Be Fair**: Clear caches between cold/warm tests
5. **Be Statistical**: Run multiple iterations
6. **Be Informative**: Include context in results

## CI/CD Integration

### GitHub Actions Integration

```yaml
# .github/workflows/benchmark.yml
name: Performance Benchmarks

on:
  pull_request:
  push:
    branches: [main]
  schedule:
    - cron: '0 2 * * 1'  # Weekly on Monday

jobs:
  benchmark:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install uv
        uv pip install -e ".[benchmark]"

    - name: Run benchmarks
      run: |
        uv run python -m benchmarks.run_all \
          --output results/ \
          --format json

    - name: Compare with baseline
      run: |
        uv run python -m benchmarks.compare \
          --baseline .benchmarks/baseline.json \
          --current results/results.json

    - name: Post results to PR
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v6
      with:
        script: |
          const fs = require('fs');
          const results = JSON.parse(
            fs.readFileSync('results/comparison.md', 'utf8')
          );

          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: results
          });

    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: benchmark-results
        path: results/
```

### Performance Regression Prevention

```python
# benchmarks/regression_check.py

def check_for_regressions(results_file, threshold=0.15):
    """Check for performance regressions in CI."""

    with open(results_file) as f:
        results = json.load(f)

    regressions = []
    for test, metrics in results['comparisons'].items():
        if metrics['change'] > threshold:
            regressions.append(test)

    if regressions:
        print(f"❌ Performance regressions detected: {regressions}")
        sys.exit(1)
    else:
        print("✅ No performance regressions detected")
        sys.exit(0)
```

## Performance Tracking

### Historical Tracking

```python
# benchmarks/tracking.py

class PerformanceTracker:
    """Track performance over time."""

    def __init__(self, db_path="benchmarks/history.db"):
        self.db = sqlite3.connect(db_path)
        self.init_schema()

    def record_results(self, results):
        """Store benchmark results."""
        self.db.execute("""
            INSERT INTO benchmarks
            (timestamp, version, test_name, mean_time, std_dev)
            VALUES (?, ?, ?, ?, ?)
        """, (
            results['timestamp'],
            results['version'],
            results['test_name'],
            results['mean_time'],
            results['std_dev']
        ))

    def plot_trends(self, test_name, last_n_versions=10):
        """Generate performance trend charts."""
        data = self.db.execute("""
            SELECT version, mean_time
            FROM benchmarks
            WHERE test_name = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (test_name, last_n_versions)).fetchall()

        # Generate chart
        import matplotlib.pyplot as plt

        versions, times = zip(*data)
        plt.plot(versions, times, marker='o')
        plt.title(f"Performance Trend: {test_name}")
        plt.xlabel("Version")
        plt.ylabel("Time (seconds)")
        plt.savefig(f"trends/{test_name}.png")
```

### Dashboard Generation

```python
# benchmarks/dashboard.py

def generate_dashboard():
    """Generate HTML dashboard with benchmark results."""

    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SocialMapper Performance Dashboard</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    </head>
    <body>
        <h1>Performance Benchmarks</h1>

        <div id="current-performance"></div>
        <div id="trends"></div>
        <div id="comparisons"></div>

        <script>
            // Plotly charts for interactive visualization
            var currentData = {{ current_data }};
            var trendsData = {{ trends_data }};

            Plotly.newPlot('current-performance', currentData);
            Plotly.newPlot('trends', trendsData);
        </script>
    </body>
    </html>
    """

    # Generate and save dashboard
    with open('benchmarks/dashboard.html', 'w') as f:
        f.write(template)
```

### Automated Reporting

```python
# benchmarks/reporting.py

def generate_weekly_report():
    """Generate automated performance report."""

    report = PerformanceReport()

    # Gather data
    report.add_section("Current Performance", get_latest_results())
    report.add_section("Week-over-Week", compare_with_last_week())
    report.add_section("Regressions", detect_regressions())
    report.add_section("Improvements", detect_improvements())

    # Send notifications
    if report.has_regressions:
        notify_team(report.get_regression_summary())

    # Save report
    report.save(f"reports/week_{datetime.now().isocalendar()[1]}.md")
```

## Best Practices

### DO's

1. ✅ **Run benchmarks on consistent hardware**
2. ✅ **Use realistic test data**
3. ✅ **Include warmup runs**
4. ✅ **Measure multiple iterations**
5. ✅ **Clear caches between cold/warm tests**
6. ✅ **Document benchmark purpose and methodology**
7. ✅ **Version control benchmark code**
8. ✅ **Track results over time**

### DON'Ts

1. ❌ **Don't benchmark with tiny datasets**
2. ❌ **Don't ignore outliers without investigation**
3. ❌ **Don't compare results from different hardware**
4. ❌ **Don't benchmark with debug mode enabled**
5. ❌ **Don't mix benchmark types in single run**
6. ❌ **Don't forget to document environment**

## Troubleshooting

### Common Issues

**Issue**: Inconsistent benchmark results
```bash
# Solution: Ensure system is idle
nice -n -20 uv run python -m benchmarks.run_all
```

**Issue**: Out of memory during benchmarks
```bash
# Solution: Run memory-intensive benchmarks separately
uv run python -m benchmarks.memory_profile --max-size medium
```

**Issue**: Benchmarks timing out
```python
# Solution: Increase timeout in config
config['timeout_seconds'] = 600  # 10 minutes
```

## Resources

- [Python Performance Tips](https://wiki.python.org/moin/PythonSpeed)
- [Profiling Python Code](https://docs.python.org/3/library/profile.html)
- [Memory Profiler Documentation](https://pypi.org/project/memory-profiler/)
- [Statistical Analysis Best Practices](https://docs.scipy.org/doc/scipy/reference/stats.html)

---

*For questions about benchmarks, please open an issue or contact the maintainers.*