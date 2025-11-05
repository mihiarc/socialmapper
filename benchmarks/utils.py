"""
Benchmark utilities for SocialMapper performance testing.

This module provides shared utilities for running and reporting
performance benchmarks across the SocialMapper API.
"""

import json
import os
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd
import psutil
from rich.console import Console
from rich.table import Table


class BenchmarkTimer:
    """
    Context manager for timing benchmark operations.

    Parameters
    ----------
    name : str
        Name of the operation being timed.
    description : str, optional
        Description of what's being benchmarked.

    Attributes
    ----------
    elapsed : float
        Time elapsed in seconds after context exits.
    memory_start : float
        Memory usage in MB at start.
    memory_peak : float
        Peak memory usage in MB during execution.

    Examples
    --------
    >>> with BenchmarkTimer("test") as timer:
    ...     time.sleep(0.1)
    >>> timer.elapsed > 0.1
    True
    """

    def __init__(self, name: str, description: Optional[str] = None):
        self.name = name
        self.description = description or name
        self.elapsed = 0.0
        self.memory_start = 0.0
        self.memory_peak = 0.0
        self.process = psutil.Process()

    def __enter__(self):
        """Start timing and memory tracking."""
        self.memory_start = self.process.memory_info().rss / 1024 / 1024  # MB
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and capture memory peak."""
        self.elapsed = time.perf_counter() - self.start
        self.memory_peak = self.process.memory_info().rss / 1024 / 1024  # MB


class BenchmarkResult:
    """
    Container for benchmark results with statistics.

    Parameters
    ----------
    name : str
        Name of the benchmark.
    timings : list of float
        List of execution times in seconds.
    memory_usage : list of float, optional
        List of memory usage values in MB.
    metadata : dict, optional
        Additional metadata about the benchmark.

    Attributes
    ----------
    mean : float
        Mean execution time.
    std : float
        Standard deviation of execution times.
    min : float
        Minimum execution time.
    max : float
        Maximum execution time.
    median : float
        Median execution time.
    """

    def __init__(
        self,
        name: str,
        timings: List[float],
        memory_usage: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.timings = timings
        self.memory_usage = memory_usage or []
        self.metadata = metadata or {}
        self.iterations = len(timings)

        # Calculate statistics
        df = pd.DataFrame({"time": timings})
        self.mean = df["time"].mean()
        self.std = df["time"].std()
        self.min = df["time"].min()
        self.max = df["time"].max()
        self.median = df["time"].median()

        # Memory statistics
        if self.memory_usage:
            mem_df = pd.DataFrame({"memory": memory_usage})
            self.memory_mean = mem_df["memory"].mean()
            self.memory_peak = mem_df["memory"].max()
        else:
            self.memory_mean = 0.0
            self.memory_peak = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert benchmark result to dictionary.

        Returns
        -------
        dict
            Benchmark statistics and metadata.
        """
        return {
            "name": self.name,
            "iterations": self.iterations,
            "mean_time": self.mean,
            "std_time": self.std,
            "min_time": self.min,
            "max_time": self.max,
            "median_time": self.median,
            "memory_mean_mb": self.memory_mean,
            "memory_peak_mb": self.memory_peak,
            "raw_timings": self.timings,
            "metadata": self.metadata
        }


class BenchmarkRunner:
    """
    Runner for executing and reporting benchmarks.

    Parameters
    ----------
    name : str
        Name of the benchmark suite.
    output_dir : Path, optional
        Directory to save benchmark results.
    """

    def __init__(self, name: str, output_dir: Optional[Path] = None):
        self.name = name
        self.output_dir = output_dir or Path("benchmarks/results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[BenchmarkResult] = []
        self.console = Console()

    def run_benchmark(
        self,
        func: Callable,
        name: str,
        args: Tuple = (),
        kwargs: Dict = None,
        iterations: int = 10,
        warmup: int = 2
    ) -> BenchmarkResult:
        """
        Run a benchmark function multiple times.

        Parameters
        ----------
        func : callable
            Function to benchmark.
        name : str
            Name of the benchmark.
        args : tuple, optional
            Positional arguments for the function.
        kwargs : dict, optional
            Keyword arguments for the function.
        iterations : int, optional
            Number of iterations to run, default 10.
        warmup : int, optional
            Number of warmup runs before timing, default 2.

        Returns
        -------
        BenchmarkResult
            Benchmark results with statistics.

        Examples
        --------
        >>> runner = BenchmarkRunner("test")
        >>> result = runner.run_benchmark(time.sleep, "sleep", args=(0.01,))
        >>> result.mean > 0.01
        True
        """
        kwargs = kwargs or {}
        timings = []
        memory_usage = []

        self.console.print(f"[cyan]Running benchmark: {name}[/cyan]")

        # Warmup runs
        for _ in range(warmup):
            func(*args, **kwargs)

        # Timed runs
        for i in range(iterations):
            with BenchmarkTimer(f"{name}_{i}") as timer:
                func(*args, **kwargs)
            timings.append(timer.elapsed)
            memory_usage.append(timer.memory_peak - timer.memory_start)

        result = BenchmarkResult(name, timings, memory_usage)
        self.results.append(result)

        # Print immediate results
        self.console.print(
            f"  Mean: {result.mean:.3f}s ± {result.std:.3f}s "
            f"(min: {result.min:.3f}s, max: {result.max:.3f}s)"
        )

        return result

    def save_results(self, format: str = "json") -> Path:
        """
        Save benchmark results to file.

        Parameters
        ----------
        format : {'json', 'csv', 'markdown'}, optional
            Output format, default 'json'.

        Returns
        -------
        Path
            Path to saved file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "json":
            output_file = self.output_dir / f"{self.name}_{timestamp}.json"
            data = {
                "suite": self.name,
                "timestamp": timestamp,
                "results": [r.to_dict() for r in self.results]
            }
            with open(output_file, "w") as f:
                json.dump(data, f, indent=2)

        elif format == "csv":
            output_file = self.output_dir / f"{self.name}_{timestamp}.csv"
            df = pd.DataFrame([r.to_dict() for r in self.results])
            df.to_csv(output_file, index=False)

        elif format == "markdown":
            output_file = self.output_dir / f"{self.name}_{timestamp}.md"
            with open(output_file, "w") as f:
                f.write(self.generate_markdown_report())

        return output_file

    def generate_markdown_report(self) -> str:
        """
        Generate a markdown report of benchmark results.

        Returns
        -------
        str
            Markdown formatted report.
        """
        lines = [
            f"# {self.name} Benchmark Results",
            f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "\n## Summary\n",
            "| Operation | Mean Time | Std Dev | Min | Max | Memory Peak |",
            "|-----------|-----------|---------|-----|-----|-------------|"
        ]

        for result in self.results:
            lines.append(
                f"| {result.name} | "
                f"{result.mean:.3f}s | "
                f"{result.std:.3f}s | "
                f"{result.min:.3f}s | "
                f"{result.max:.3f}s | "
                f"{result.memory_peak:.1f} MB |"
            )

        return "\n".join(lines)

    def print_summary(self):
        """Print a rich formatted summary table to console."""
        table = Table(title=f"{self.name} Benchmark Results")
        table.add_column("Operation", style="cyan")
        table.add_column("Mean", style="green")
        table.add_column("Std Dev", style="yellow")
        table.add_column("Min", style="blue")
        table.add_column("Max", style="red")
        table.add_column("Memory", style="magenta")

        for result in self.results:
            table.add_row(
                result.name,
                f"{result.mean:.3f}s",
                f"{result.std:.3f}s",
                f"{result.min:.3f}s",
                f"{result.max:.3f}s",
                f"{result.memory_peak:.1f} MB"
            )

        self.console.print(table)


def compare_results(
    baseline: List[BenchmarkResult],
    current: List[BenchmarkResult]
) -> pd.DataFrame:
    """
    Compare two sets of benchmark results.

    Parameters
    ----------
    baseline : list of BenchmarkResult
        Baseline benchmark results.
    current : list of BenchmarkResult
        Current benchmark results.

    Returns
    -------
    DataFrame
        Comparison table with speedup/slowdown percentages.

    Examples
    --------
    >>> baseline = [BenchmarkResult("test", [1.0, 1.1, 0.9])]
    >>> current = [BenchmarkResult("test", [0.5, 0.6, 0.4])]
    >>> df = compare_results(baseline, current)
    >>> df["speedup"].iloc[0] > 1.5
    True
    """
    baseline_dict = {r.name: r for r in baseline}
    current_dict = {r.name: r for r in current}

    comparisons = []
    for name in baseline_dict:
        if name in current_dict:
            b = baseline_dict[name]
            c = current_dict[name]
            speedup = b.mean / c.mean
            comparisons.append({
                "operation": name,
                "baseline_mean": b.mean,
                "current_mean": c.mean,
                "speedup": speedup,
                "improvement_pct": (speedup - 1) * 100
            })

    return pd.DataFrame(comparisons)


def format_size(bytes: float) -> str:
    """
    Format bytes as human-readable string.

    Parameters
    ----------
    bytes : float
        Size in bytes.

    Returns
    -------
    str
        Human-readable size string.

    Examples
    --------
    >>> format_size(1024)
    '1.0 KB'
    >>> format_size(1024 * 1024)
    '1.0 MB'
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} TB"


# Test locations for benchmarks
TEST_LOCATIONS = {
    "portland": "Portland, OR",
    "san_francisco": "San Francisco, CA",
    "new_york": "New York, NY",
    "chicago": "Chicago, IL",
    "denver": "Denver, CO",
    "seattle": "Seattle, WA",
    "austin": "Austin, TX",
    "boston": "Boston, MA"
}

# Test coordinates for benchmarks
TEST_COORDS = {
    "portland": (45.5152, -122.6784),
    "san_francisco": (37.7749, -122.4194),
    "new_york": (40.7128, -74.0060),
    "chicago": (41.8781, -87.6298),
    "denver": (39.7392, -104.9903),
    "seattle": (47.6062, -122.3321),
    "austin": (30.2672, -97.7431),
    "boston": (42.3601, -71.0589)
}


def generate_test_data(data_type: str = "locations", count: int = 10) -> List[Any]:
    """
    Generate test data for benchmarks.

    Parameters
    ----------
    data_type : str, optional
        Type of test data to generate ('locations', 'geoids').
    count : int, optional
        Number of items to generate.

    Returns
    -------
    list
        Generated test data.

    Examples
    --------
    >>> locations = generate_test_data("locations", 5)
    >>> len(locations)
    5
    """
    if data_type == "locations":
        # Generate locations by interpolating between test coordinates
        base_coords = list(TEST_COORDS.values())
        locations = []
        for i in range(count):
            base = base_coords[i % len(base_coords)]
            offset = (i // len(base_coords)) * 0.01
            locations.append((base[0] + offset, base[1] + offset))
        return locations

    elif data_type == "geoids":
        # Generate sample GEOIDs
        geoids = []
        for i in range(count):
            state = str(i % 50 + 1).zfill(2)
            county = str(i % 100 + 1).zfill(3)
            tract = str(i % 9999 + 1).zfill(6)
            block = str(i % 9 + 1)
            geoids.append(f"{state}{county}{tract}{block}")
        return geoids

    else:
        raise ValueError(f"Unknown data type: {data_type}")


def format_results(results: Dict[str, Any], format_type: str = "table") -> str:
    """
    Format benchmark results for display.

    Parameters
    ----------
    results : dict
        Benchmark results to format.
    format_type : str, optional
        Format type ('table', 'json', 'markdown').

    Returns
    -------
    str
        Formatted results.

    Examples
    --------
    >>> results = {"test": {"mean": 1.5, "std": 0.1}}
    >>> output = format_results(results, "json")
    >>> isinstance(output, str)
    True
    """
    if format_type == "json":
        return json.dumps(results, indent=2, default=str)

    elif format_type == "markdown":
        lines = ["# Benchmark Results\n"]
        for name, data in results.items():
            lines.append(f"\n## {name}\n")
            if isinstance(data, dict):
                for key, value in data.items():
                    lines.append(f"- **{key}**: {value}")
        return "\n".join(lines)

    elif format_type == "table":
        from rich.table import Table
        from rich.console import Console
        import io

        buffer = io.StringIO()
        console = Console(file=buffer)

        table = Table(title="Benchmark Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        for name, data in results.items():
            if isinstance(data, dict):
                for key, value in data.items():
                    table.add_row(f"{name}.{key}", str(value))
            else:
                table.add_row(name, str(data))

        console.print(table)
        return buffer.getvalue()

    else:
        raise ValueError(f"Unknown format type: {format_type}")