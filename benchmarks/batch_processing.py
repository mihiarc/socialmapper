"""
Batch processing benchmarks for SocialMapper.

This module tests performance with multiple locations to evaluate
scalability and identify bottlenecks in batch operations.
"""

import concurrent.futures
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
import psutil
from rich.console import Console
from rich.progress import track

# Import SocialMapper
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from socialmapper import (
    create_isochrone,
    get_census_blocks,
    get_census_data,
    get_poi
)

from .utils import BenchmarkRunner, BenchmarkTimer, TEST_COORDS, format_size


class BatchProcessingBenchmark:
    """
    Benchmark suite for batch processing operations.

    Tests SocialMapper's performance with multiple locations
    to validate scalability claims.
    """

    def __init__(self, output_dir: Path = None):
        """
        Initialize batch processing benchmark.

        Parameters
        ----------
        output_dir : Path, optional
            Directory for saving results.
        """
        self.runner = BenchmarkRunner("batch_processing", output_dir)
        self.console = Console()
        self.process = psutil.Process()

    def generate_test_locations(self, count: int) -> List[Tuple[float, float]]:
        """
        Generate test location coordinates.

        Parameters
        ----------
        count : int
            Number of locations to generate.

        Returns
        -------
        list of tuple
            List of (latitude, longitude) coordinates.
        """
        # Use real test coordinates and interpolate between them
        base_coords = list(TEST_COORDS.values())
        locations = []

        for i in range(count):
            # Cycle through base coordinates
            base = base_coords[i % len(base_coords)]
            # Add small offset to create unique locations
            offset = (i // len(base_coords)) * 0.01
            locations.append((base[0] + offset, base[1] + offset))

        return locations

    def benchmark_sequential_processing(
        self,
        locations: List[Tuple[float, float]],
        operation: str
    ) -> Dict[str, Any]:
        """
        Benchmark sequential processing of multiple locations.

        Parameters
        ----------
        locations : list of tuple
            Location coordinates to process.
        operation : str
            Operation to benchmark (isochrone, poi, blocks).

        Returns
        -------
        dict
            Timing and memory statistics.
        """
        results = []
        memory_samples = []

        # Track initial memory
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB

        with BenchmarkTimer(f"sequential_{operation}_{len(locations)}_locations") as timer:
            for location in track(locations, description=f"Processing {operation}..."):
                # Sample memory periodically
                memory_samples.append(self.process.memory_info().rss / 1024 / 1024)

                if operation == "isochrone":
                    result = create_isochrone(location, travel_time=15)
                elif operation == "poi":
                    result = get_poi(location, limit=50)
                elif operation == "blocks":
                    result = get_census_blocks(location=location, radius_km=2)
                elif operation == "census":
                    blocks = get_census_blocks(location=location, radius_km=1)
                    geoids = [b["geoid"] for b in blocks[:10]]
                    result = get_census_data(geoids, ["population"])
                else:
                    raise ValueError(f"Unknown operation: {operation}")

                results.append(result)

        peak_memory = max(memory_samples)
        final_memory = self.process.memory_info().rss / 1024 / 1024

        return {
            "method": "sequential",
            "operation": operation,
            "location_count": len(locations),
            "total_time": timer.elapsed,
            "time_per_location": timer.elapsed / len(locations),
            "initial_memory_mb": initial_memory,
            "peak_memory_mb": peak_memory,
            "final_memory_mb": final_memory,
            "memory_growth_mb": final_memory - initial_memory,
            "result_count": len(results)
        }

    def benchmark_parallel_processing(
        self,
        locations: List[Tuple[float, float]],
        operation: str,
        max_workers: int = 4
    ) -> Dict[str, Any]:
        """
        Benchmark parallel processing of multiple locations.

        Parameters
        ----------
        locations : list of tuple
            Location coordinates to process.
        operation : str
            Operation to benchmark.
        max_workers : int, optional
            Maximum number of parallel workers, default 4.

        Returns
        -------
        dict
            Timing and memory statistics.
        """
        results = []
        memory_samples = []

        # Track initial memory
        initial_memory = self.process.memory_info().rss / 1024 / 1024

        def process_location(location):
            """Process a single location."""
            if operation == "isochrone":
                return create_isochrone(location, travel_time=15)
            elif operation == "poi":
                return get_poi(location, limit=50)
            elif operation == "blocks":
                return get_census_blocks(location=location, radius_km=2)
            elif operation == "census":
                blocks = get_census_blocks(location=location, radius_km=1)
                geoids = [b["geoid"] for b in blocks[:10]]
                return get_census_data(geoids, ["population"])
            else:
                raise ValueError(f"Unknown operation: {operation}")

        with BenchmarkTimer(f"parallel_{operation}_{len(locations)}_locations") as timer:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                futures = [
                    executor.submit(process_location, loc)
                    for loc in locations
                ]

                # Process results as they complete
                for future in concurrent.futures.as_completed(futures):
                    memory_samples.append(self.process.memory_info().rss / 1024 / 1024)
                    results.append(future.result())

        peak_memory = max(memory_samples) if memory_samples else initial_memory
        final_memory = self.process.memory_info().rss / 1024 / 1024

        return {
            "method": "parallel",
            "operation": operation,
            "location_count": len(locations),
            "max_workers": max_workers,
            "total_time": timer.elapsed,
            "time_per_location": timer.elapsed / len(locations),
            "initial_memory_mb": initial_memory,
            "peak_memory_mb": peak_memory,
            "final_memory_mb": final_memory,
            "memory_growth_mb": final_memory - initial_memory,
            "result_count": len(results)
        }

    def benchmark_batch_sizes(self) -> pd.DataFrame:
        """
        Benchmark different batch sizes.

        Returns
        -------
        DataFrame
            Performance metrics for different batch sizes.
        """
        self.console.print("\n[bold cyan]Benchmarking Batch Sizes[/bold cyan]")

        batch_sizes = [1, 5, 10, 25, 50, 100]
        operations = ["isochrone", "poi", "blocks"]
        results = []

        for size in batch_sizes:
            locations = self.generate_test_locations(size)

            for operation in operations:
                self.console.print(f"\nProcessing {size} locations - {operation}")

                # Sequential processing
                seq_result = self.benchmark_sequential_processing(locations, operation)
                results.append(seq_result)

                # Parallel processing (only for larger batches)
                if size >= 10:
                    par_result = self.benchmark_parallel_processing(
                        locations, operation, max_workers=4
                    )
                    results.append(par_result)

                # Add small delay to let memory settle
                time.sleep(1)

        return pd.DataFrame(results)

    def benchmark_scalability(self) -> Dict[str, Any]:
        """
        Test scalability with increasing load.

        Returns
        -------
        dict
            Scalability metrics and analysis.
        """
        self.console.print("\n[bold cyan]Benchmarking Scalability[/bold cyan]")

        # Test configurations
        configs = [
            (10, 2),   # 10 locations, 2 workers
            (50, 4),   # 50 locations, 4 workers
            (100, 8),  # 100 locations, 8 workers
        ]

        results = {
            "sequential": [],
            "parallel": []
        }

        for location_count, workers in configs:
            locations = self.generate_test_locations(location_count)

            # Complete workflow for each location
            def process_workflow(location):
                """Run complete analysis workflow."""
                iso = create_isochrone(location, travel_time=10)
                blocks = get_census_blocks(polygon=iso)[:10]
                geoids = [b["geoid"] for b in blocks]
                census = get_census_data(geoids, ["population"])
                pois = get_poi(location, limit=20)
                return {
                    "isochrone": iso,
                    "blocks": len(blocks),
                    "census": len(census.data),
                    "pois": len(pois)
                }

            # Sequential test
            self.console.print(f"\nSequential: {location_count} locations")
            with BenchmarkTimer(f"workflow_seq_{location_count}") as seq_timer:
                seq_results = []
                for loc in track(locations, description="Sequential processing..."):
                    seq_results.append(process_workflow(loc))

            results["sequential"].append({
                "locations": location_count,
                "total_time": seq_timer.elapsed,
                "per_location": seq_timer.elapsed / location_count,
                "throughput": location_count / seq_timer.elapsed
            })

            # Parallel test
            self.console.print(f"Parallel: {location_count} locations, {workers} workers")
            with BenchmarkTimer(f"workflow_par_{location_count}") as par_timer:
                with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                    par_results = list(executor.map(process_workflow, locations))

            results["parallel"].append({
                "locations": location_count,
                "workers": workers,
                "total_time": par_timer.elapsed,
                "per_location": par_timer.elapsed / location_count,
                "throughput": location_count / par_timer.elapsed,
                "speedup": seq_timer.elapsed / par_timer.elapsed
            })

        return results

    def benchmark_memory_growth(self) -> Dict[str, Any]:
        """
        Track memory growth during batch processing.

        Returns
        -------
        dict
            Memory usage patterns and leak detection.
        """
        self.console.print("\n[bold cyan]Benchmarking Memory Growth[/bold cyan]")

        memory_samples = []
        batch_sizes = [10, 25, 50, 75, 100]

        for size in batch_sizes:
            locations = self.generate_test_locations(size)

            # Force garbage collection before measurement
            import gc
            gc.collect()
            time.sleep(0.5)

            # Measure memory before
            mem_before = self.process.memory_info().rss / 1024 / 1024

            # Process batch
            for location in locations:
                _ = create_isochrone(location, travel_time=10)
                _ = get_poi(location, limit=20)

            # Measure memory after
            mem_after = self.process.memory_info().rss / 1024 / 1024

            # Force garbage collection
            gc.collect()
            time.sleep(0.5)

            # Measure memory after GC
            mem_after_gc = self.process.memory_info().rss / 1024 / 1024

            memory_samples.append({
                "batch_size": size,
                "memory_before_mb": mem_before,
                "memory_after_mb": mem_after,
                "memory_after_gc_mb": mem_after_gc,
                "growth_mb": mem_after - mem_before,
                "retained_after_gc_mb": mem_after_gc - mem_before,
                "growth_per_location": (mem_after - mem_before) / size
            })

        return {
            "samples": memory_samples,
            "analysis": self._analyze_memory_pattern(memory_samples)
        }

    def _analyze_memory_pattern(self, samples: List[Dict]) -> Dict[str, Any]:
        """
        Analyze memory growth pattern for leaks.

        Parameters
        ----------
        samples : list of dict
            Memory samples from batch processing.

        Returns
        -------
        dict
            Analysis of memory patterns.
        """
        df = pd.DataFrame(samples)

        # Calculate linear regression on memory growth
        from scipy import stats
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            df["batch_size"], df["retained_after_gc_mb"]
        )

        return {
            "memory_growth_linear": slope > 0.5,  # Significant growth
            "memory_per_location_mb": slope,
            "r_squared": r_value ** 2,
            "likely_memory_leak": slope > 1.0 and r_value ** 2 > 0.9,
            "average_growth_per_location": df["growth_per_location"].mean(),
            "max_memory_retained_mb": df["retained_after_gc_mb"].max()
        }

    def run_all_benchmarks(self) -> Dict[str, Any]:
        """
        Run all batch processing benchmarks.

        Returns
        -------
        dict
            All benchmark results.
        """
        self.console.print("[bold green]Starting Batch Processing Benchmarks[/bold green]")

        results = {}

        # Batch size benchmarks
        batch_df = self.benchmark_batch_sizes()
        results["batch_sizes"] = batch_df.to_dict()

        # Scalability benchmarks
        results["scalability"] = self.benchmark_scalability()

        # Memory growth analysis
        results["memory_growth"] = self.benchmark_memory_growth()

        # Generate summary report
        self._generate_report(results)

        # Save results
        self.runner.save_results("json")
        self.runner.save_results("markdown")

        return results

    def _generate_report(self, results: Dict[str, Any]):
        """
        Generate and print batch processing report.

        Parameters
        ----------
        results : dict
            Benchmark results to report.
        """
        self.console.print("\n[bold yellow]Batch Processing Summary[/bold yellow]")

        # Batch size analysis
        if "batch_sizes" in results:
            batch_df = pd.DataFrame.from_dict(results["batch_sizes"])

            # Group by method and batch size
            summary = batch_df.groupby(["method", "location_count"]).agg({
                "total_time": "mean",
                "peak_memory_mb": "max",
                "memory_growth_mb": "mean"
            }).round(2)

            self.console.print("\n[cyan]Performance by Batch Size:[/cyan]")
            self.console.print(summary)

        # Scalability analysis
        if "scalability" in results:
            self.console.print("\n[cyan]Scalability Results:[/cyan]")

            for method in ["sequential", "parallel"]:
                df = pd.DataFrame(results["scalability"][method])
                self.console.print(f"\n{method.capitalize()}:")
                self.console.print(df.to_string())

        # Memory analysis
        if "memory_growth" in results:
            analysis = results["memory_growth"]["analysis"]
            self.console.print("\n[cyan]Memory Analysis:[/cyan]")
            self.console.print(f"  Growth per location: {analysis['memory_per_location_mb']:.2f} MB")
            self.console.print(f"  Average growth: {analysis['average_growth_per_location']:.2f} MB")
            self.console.print(f"  Memory leak detected: {analysis['likely_memory_leak']}")


def main():
    """Run batch processing benchmarks."""
    benchmark = BatchProcessingBenchmark()
    results = benchmark.run_all_benchmarks()
    return results


if __name__ == "__main__":
    main()