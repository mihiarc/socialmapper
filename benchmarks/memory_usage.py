"""
Memory profiling benchmarks for SocialMapper.

This module profiles memory usage patterns to identify optimization
opportunities and potential memory leaks.
"""

import gc
import tracemalloc
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import psutil
from rich.console import Console
from rich.table import Table

# Optional import for memory_profiler
try:
    from memory_profiler import memory_usage
    HAS_MEMORY_PROFILER = True
except ImportError:
    HAS_MEMORY_PROFILER = False

# Import SocialMapper
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from socialmapper import (
    create_isochrone,
    create_map,
    get_census_blocks,
    get_census_data,
    get_poi
)

from .utils import TEST_COORDS, format_size


class MemoryProfiler:
    """
    Memory profiling suite for SocialMapper operations.

    Tracks memory allocation, peak usage, and identifies
    memory-intensive operations.
    """

    def __init__(self):
        """Initialize memory profiler."""
        self.console = Console()
        self.process = psutil.Process()
        self.results = []

    def profile_function_memory(
        self,
        func: callable,
        args: tuple = (),
        kwargs: dict = None,
        interval: float = 0.1
    ) -> Dict[str, Any]:
        """
        Profile memory usage of a function.

        Parameters
        ----------
        func : callable
            Function to profile.
        args : tuple, optional
            Function arguments.
        kwargs : dict, optional
            Function keyword arguments.
        interval : float, optional
            Memory sampling interval in seconds.

        Returns
        -------
        dict
            Memory profile results.
        """
        kwargs = kwargs or {}

        # Force garbage collection before profiling
        gc.collect()

        # Get baseline memory
        baseline = self.process.memory_info().rss / 1024 / 1024  # MB

        if HAS_MEMORY_PROFILER:
            # Use memory_profiler if available
            mem_usage = memory_usage(
                (func, args, kwargs),
                interval=interval,
                timeout=None,
                max_usage=True,
                retval=True,
                include_children=True
            )

            # Extract results
            memory_samples = mem_usage[0] if isinstance(mem_usage[0], list) else [mem_usage[0]]
            result = mem_usage[1] if len(mem_usage) > 1 else None
        else:
            # Simple memory profiling without memory_profiler
            import time
            memory_samples = [baseline]

            # Sample memory during execution
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()

            # Sample memory a few times during execution
            memory_samples.append(self.process.memory_info().rss / 1024 / 1024)

        # Get final memory
        final = self.process.memory_info().rss / 1024 / 1024

        return {
            "function": func.__name__,
            "baseline_mb": baseline,
            "peak_mb": max(memory_samples),
            "final_mb": final,
            "growth_mb": final - baseline,
            "peak_growth_mb": max(memory_samples) - baseline,
            "samples": memory_samples,
            "sample_count": len(memory_samples)
        }

    def profile_with_tracemalloc(
        self,
        func: callable,
        args: tuple = (),
        kwargs: dict = None
    ) -> Dict[str, Any]:
        """
        Profile memory allocations using tracemalloc.

        Parameters
        ----------
        func : callable
            Function to profile.
        args : tuple, optional
            Function arguments.
        kwargs : dict, optional
            Function keyword arguments.

        Returns
        -------
        dict
            Detailed memory allocation information.
        """
        kwargs = kwargs or {}

        # Start tracing
        tracemalloc.start()

        # Take snapshot before
        snapshot_before = tracemalloc.take_snapshot()

        # Execute function
        result = func(*args, **kwargs)

        # Take snapshot after
        snapshot_after = tracemalloc.take_snapshot()

        # Calculate statistics
        top_stats = snapshot_after.compare_to(snapshot_before, 'lineno')

        # Get current memory usage
        current, peak = tracemalloc.get_traced_memory()

        # Stop tracing
        tracemalloc.stop()

        # Extract top allocations
        top_allocations = []
        for stat in top_stats[:10]:
            top_allocations.append({
                "file": stat.traceback.format()[0] if stat.traceback else "unknown",
                "size_diff": stat.size_diff,
                "size_diff_mb": stat.size_diff / 1024 / 1024,
                "count_diff": stat.count_diff
            })

        return {
            "function": func.__name__,
            "current_mb": current / 1024 / 1024,
            "peak_mb": peak / 1024 / 1024,
            "top_allocations": top_allocations
        }

    def profile_core_operations(self) -> pd.DataFrame:
        """
        Profile memory usage of core SocialMapper operations.

        Returns
        -------
        DataFrame
            Memory profile for each operation.
        """
        self.console.print("\n[bold cyan]Profiling Core Operation Memory Usage[/bold cyan]")

        operations = [
            ("create_isochrone", create_isochrone, (TEST_COORDS["portland"],),
             {"travel_time": 15, "travel_mode": "drive"}),
            ("get_poi", get_poi, (TEST_COORDS["portland"],),
             {"limit": 100}),
            ("get_census_blocks", get_census_blocks, (),
             {"location": TEST_COORDS["portland"], "radius_km": 5}),
        ]

        profiles = []

        for name, func, args, kwargs in operations:
            self.console.print(f"\nProfiling {name}...")

            # Standard memory profiling
            profile = self.profile_function_memory(func, args, kwargs)
            profile["operation"] = name

            # Tracemalloc profiling
            trace_profile = self.profile_with_tracemalloc(func, args, kwargs)
            profile["traced_peak_mb"] = trace_profile["peak_mb"]
            profile["top_allocation_mb"] = (
                trace_profile["top_allocations"][0]["size_diff_mb"]
                if trace_profile["top_allocations"] else 0
            )

            profiles.append(profile)

            # Print immediate results
            self.console.print(f"  Peak memory: {profile['peak_mb']:.1f} MB")
            self.console.print(f"  Growth: {profile['growth_mb']:.1f} MB")

        return pd.DataFrame(profiles)

    def profile_data_scaling(self) -> Dict[str, Any]:
        """
        Profile memory usage with increasing data sizes.

        Returns
        -------
        dict
            Memory scaling analysis.
        """
        self.console.print("\n[bold cyan]Profiling Memory Scaling[/bold cyan]")

        scaling_results = {}

        # Test isochrone with different travel times (affects polygon complexity)
        travel_times = [5, 10, 15, 30, 60]
        isochrone_profiles = []

        for travel_time in travel_times:
            profile = self.profile_function_memory(
                create_isochrone,
                args=(TEST_COORDS["portland"],),
                kwargs={"travel_time": travel_time}
            )
            profile["travel_time"] = travel_time
            isochrone_profiles.append(profile)

        scaling_results["isochrone_scaling"] = isochrone_profiles

        # Test POI with different limits
        poi_limits = [10, 50, 100, 200, 500]
        poi_profiles = []

        for limit in poi_limits:
            profile = self.profile_function_memory(
                get_poi,
                args=(TEST_COORDS["portland"],),
                kwargs={"limit": limit}
            )
            profile["limit"] = limit
            poi_profiles.append(profile)

        scaling_results["poi_scaling"] = poi_profiles

        # Test census blocks with different radii
        radii = [1, 2, 5, 10, 15]
        blocks_profiles = []

        for radius in radii:
            profile = self.profile_function_memory(
                get_census_blocks,
                kwargs={"location": TEST_COORDS["portland"], "radius_km": radius}
            )
            profile["radius_km"] = radius
            blocks_profiles.append(profile)

        scaling_results["blocks_scaling"] = blocks_profiles

        return scaling_results

    def profile_cache_memory(self) -> Dict[str, Any]:
        """
        Profile memory usage of caching mechanisms.

        Returns
        -------
        dict
            Cache memory analysis.
        """
        self.console.print("\n[bold cyan]Profiling Cache Memory Usage[/bold cyan]")

        cache_results = {}

        # Measure memory before any operations
        gc.collect()
        initial_memory = self.process.memory_info().rss / 1024 / 1024

        # Perform operations that should be cached
        locations = [TEST_COORDS[city] for city in ["portland", "seattle", "denver"]]

        # First pass - populate cache
        first_pass_memory = []
        for location in locations:
            _ = create_isochrone(location, travel_time=15)
            _ = get_poi(location, limit=50)
            _ = get_census_blocks(location=location, radius_km=2)
            first_pass_memory.append(self.process.memory_info().rss / 1024 / 1024)

        cache_populated_memory = self.process.memory_info().rss / 1024 / 1024

        # Second pass - should use cache
        second_pass_memory = []
        for location in locations:
            _ = create_isochrone(location, travel_time=15)
            _ = get_poi(location, limit=50)
            _ = get_census_blocks(location=location, radius_km=2)
            second_pass_memory.append(self.process.memory_info().rss / 1024 / 1024)

        final_memory = self.process.memory_info().rss / 1024 / 1024

        cache_results = {
            "initial_memory_mb": initial_memory,
            "after_first_pass_mb": cache_populated_memory,
            "after_second_pass_mb": final_memory,
            "cache_size_mb": cache_populated_memory - initial_memory,
            "cache_growth_second_pass_mb": final_memory - cache_populated_memory,
            "first_pass_samples": first_pass_memory,
            "second_pass_samples": second_pass_memory
        }

        return cache_results

    def detect_memory_leaks(self) -> Dict[str, Any]:
        """
        Detect potential memory leaks through repeated operations.

        Returns
        -------
        dict
            Memory leak detection results.
        """
        self.console.print("\n[bold cyan]Detecting Memory Leaks[/bold cyan]")

        leak_results = {}
        iterations = 20

        # Test each operation repeatedly
        operations = [
            ("create_isochrone", create_isochrone, (TEST_COORDS["portland"],),
             {"travel_time": 10}),
            ("get_poi", get_poi, (TEST_COORDS["portland"],), {"limit": 50}),
            ("get_census_blocks", get_census_blocks, (),
             {"location": TEST_COORDS["portland"], "radius_km": 2})
        ]

        for name, func, args, kwargs in operations:
            memory_samples = []

            # Force initial garbage collection
            gc.collect()
            initial = self.process.memory_info().rss / 1024 / 1024

            # Run operation multiple times
            for i in range(iterations):
                _ = func(*args, **kwargs)

                # Collect garbage every 5 iterations
                if i % 5 == 0:
                    gc.collect()

                memory_samples.append(self.process.memory_info().rss / 1024 / 1024)

            # Final garbage collection
            gc.collect()
            final = self.process.memory_info().rss / 1024 / 1024

            # Analyze trend
            df = pd.DataFrame({"iteration": range(iterations), "memory": memory_samples})
            correlation = df["iteration"].corr(df["memory"])

            leak_results[name] = {
                "initial_mb": initial,
                "final_mb": final,
                "growth_mb": final - initial,
                "growth_per_iteration": (final - initial) / iterations,
                "correlation": correlation,
                "likely_leak": correlation > 0.8 and (final - initial) > 10,
                "samples": memory_samples
            }

        return leak_results

    def profile_complete_workflow(self) -> Dict[str, Any]:
        """
        Profile memory usage of complete workflow.

        Returns
        -------
        dict
            Complete workflow memory profile.
        """
        self.console.print("\n[bold cyan]Profiling Complete Workflow Memory[/bold cyan]")

        # Track memory at each step
        memory_checkpoints = {}

        gc.collect()
        memory_checkpoints["start"] = self.process.memory_info().rss / 1024 / 1024

        # Step 1: Create isochrone
        iso = create_isochrone(TEST_COORDS["portland"], travel_time=15)
        memory_checkpoints["after_isochrone"] = self.process.memory_info().rss / 1024 / 1024

        # Step 2: Get census blocks
        blocks = get_census_blocks(polygon=iso)
        memory_checkpoints["after_blocks"] = self.process.memory_info().rss / 1024 / 1024

        # Step 3: Get census data
        geoids = [b["geoid"] for b in blocks[:30]]
        census_data = get_census_data(geoids, ["population", "median_income"])
        memory_checkpoints["after_census"] = self.process.memory_info().rss / 1024 / 1024

        # Step 4: Get POIs
        pois = get_poi(TEST_COORDS["portland"], travel_time=15, limit=100)
        memory_checkpoints["after_poi"] = self.process.memory_info().rss / 1024 / 1024

        # Step 5: Create map
        for block in blocks[:30]:
            block["population"] = census_data.data.get(
                block["geoid"], {}
            ).get("population", 0)
        map_result = create_map(blocks[:30], "population", export_format="png")
        memory_checkpoints["after_map"] = self.process.memory_info().rss / 1024 / 1024

        # Cleanup
        del iso, blocks, census_data, pois, map_result
        gc.collect()
        memory_checkpoints["after_cleanup"] = self.process.memory_info().rss / 1024 / 1024

        # Calculate step-wise growth
        steps = list(memory_checkpoints.keys())
        growth = {}
        for i in range(1, len(steps)):
            prev_step = steps[i-1]
            curr_step = steps[i]
            growth[curr_step] = memory_checkpoints[curr_step] - memory_checkpoints[prev_step]

        return {
            "checkpoints": memory_checkpoints,
            "growth": growth,
            "total_peak": max(memory_checkpoints.values()),
            "retained_after_cleanup": memory_checkpoints["after_cleanup"] - memory_checkpoints["start"]
        }

    def generate_report(self, results: Dict[str, Any]):
        """
        Generate memory profiling report.

        Parameters
        ----------
        results : dict
            All memory profiling results.
        """
        self.console.print("\n[bold yellow]Memory Profiling Report[/bold yellow]")

        # Core operations summary
        if "core_operations" in results:
            table = Table(title="Core Operations Memory Usage")
            table.add_column("Operation", style="cyan")
            table.add_column("Peak (MB)", style="green")
            table.add_column("Growth (MB)", style="yellow")

            df = results["core_operations"]
            for _, row in df.iterrows():
                table.add_row(
                    row["operation"],
                    f"{row['peak_mb']:.1f}",
                    f"{row['growth_mb']:.1f}"
                )

            self.console.print(table)

        # Memory leak detection
        if "leak_detection" in results:
            self.console.print("\n[cyan]Memory Leak Detection:[/cyan]")
            for op, data in results["leak_detection"].items():
                status = "⚠️ LEAK DETECTED" if data["likely_leak"] else "✅ No leak"
                self.console.print(f"  {op}: {status} (growth: {data['growth_mb']:.1f} MB)")

        # Workflow memory
        if "workflow" in results:
            self.console.print("\n[cyan]Workflow Memory Checkpoints:[/cyan]")
            for step, memory in results["workflow"]["checkpoints"].items():
                growth = results["workflow"]["growth"].get(step, 0)
                self.console.print(f"  {step}: {memory:.1f} MB (+{growth:.1f} MB)")

    def run_all_profiles(self) -> Dict[str, Any]:
        """
        Run all memory profiling benchmarks.

        Returns
        -------
        dict
            All memory profiling results.
        """
        self.console.print("[bold green]Starting Memory Profiling[/bold green]")

        results = {}

        # Profile core operations
        results["core_operations"] = self.profile_core_operations()

        # Profile data scaling
        results["scaling"] = self.profile_data_scaling()

        # Profile cache memory
        results["cache"] = self.profile_cache_memory()

        # Detect memory leaks
        results["leak_detection"] = self.detect_memory_leaks()

        # Profile complete workflow
        results["workflow"] = self.profile_complete_workflow()

        # Generate report
        self.generate_report(results)

        return results


def main():
    """Run memory profiling benchmarks."""
    profiler = MemoryProfiler()
    results = profiler.run_all_profiles()
    return results


if __name__ == "__main__":
    main()