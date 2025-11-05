#!/usr/bin/env python
"""
Quick test to verify benchmarks work.

This script runs minimal benchmark tests to ensure the framework is functional.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console

console = Console()


def test_core_operations():
    """Test core operations benchmark with minimal iterations."""
    console.print("\n[cyan]Testing Core Operations Benchmark...[/cyan]")

    try:
        from benchmarks.core_operations import CoreOperationsBenchmark

        benchmark = CoreOperationsBenchmark()

        # Test single isochrone benchmark
        from socialmapper import create_isochrone
        result = benchmark.runner.run_benchmark(
            create_isochrone,
            "test_isochrone",
            args=((45.5152, -122.6784),),  # Portland
            kwargs={"travel_time": 5, "travel_mode": "drive"},
            iterations=2,
            warmup=1
        )

        console.print(f"  ✅ Isochrone benchmark: {result.mean:.2f}s")

        # Test POI benchmark
        from socialmapper import get_poi
        result = benchmark.runner.run_benchmark(
            get_poi,
            "test_poi",
            args=((45.5152, -122.6784),),
            kwargs={"limit": 10},
            iterations=2,
            warmup=1
        )

        console.print(f"  ✅ POI benchmark: {result.mean:.2f}s")

        return True

    except Exception as e:
        console.print(f"  ❌ Core operations failed: {e}")
        return False


def test_memory_profiling():
    """Test memory profiling with minimal operations."""
    console.print("\n[cyan]Testing Memory Profiling...[/cyan]")

    try:
        from benchmarks.memory_usage import MemoryProfiler
        from socialmapper import create_isochrone

        profiler = MemoryProfiler()

        # Profile single operation
        profile = profiler.profile_function_memory(
            create_isochrone,
            args=((45.5152, -122.6784),),
            kwargs={"travel_time": 5}
        )

        console.print(f"  ✅ Memory profiling: Peak {profile['peak_mb']:.1f} MB")
        return True

    except Exception as e:
        console.print(f"  ❌ Memory profiling failed: {e}")
        return False


def test_batch_processing():
    """Test batch processing with small batch."""
    console.print("\n[cyan]Testing Batch Processing...[/cyan]")

    try:
        from benchmarks.batch_processing import BatchProcessingBenchmark

        benchmark = BatchProcessingBenchmark()

        # Test with 3 locations
        locations = benchmark.generate_test_locations(3)
        result = benchmark.benchmark_sequential_processing(locations, "isochrone")

        console.print(f"  ✅ Batch processing: {result['time_per_location']:.2f}s per location")
        return True

    except Exception as e:
        console.print(f"  ❌ Batch processing failed: {e}")
        return False


def test_comparison():
    """Test comparison framework."""
    console.print("\n[cyan]Testing Comparison Framework...[/cyan]")

    try:
        from benchmarks.comparison import AlternativeComparison

        comparison = AlternativeComparison()

        # Test setup benchmark
        sm_setup = comparison.benchmark_socialmapper_setup()
        console.print(f"  ✅ SocialMapper setup: {sm_setup['total_time']:.2f}s")

        # Test DIY estimation
        diy_setup = comparison.benchmark_diy_setup()
        console.print(f"  ✅ DIY setup estimate: {diy_setup['total_time_minutes']:.1f} minutes")

        return True

    except Exception as e:
        console.print(f"  ❌ Comparison failed: {e}")
        return False


def test_utilities():
    """Test benchmark utilities."""
    console.print("\n[cyan]Testing Utilities...[/cyan]")

    try:
        from benchmarks.utils import (
            BenchmarkTimer,
            BenchmarkResult,
            generate_test_data,
            format_results
        )

        # Test timer
        import time
        with BenchmarkTimer("test_timer") as timer:
            time.sleep(0.1)

        assert timer.elapsed > 0.1
        console.print(f"  ✅ Timer: {timer.elapsed:.2f}s")

        # Test result container
        result = BenchmarkResult("test", [0.1, 0.2, 0.15])
        console.print(f"  ✅ Result stats: mean={result.mean:.2f}, std={result.std:.2f}")

        # Test data generation
        locations = generate_test_data("locations", 5)
        assert len(locations) == 5
        console.print(f"  ✅ Test data generation: {len(locations)} locations")

        # Test result formatting
        output = format_results({"test": 123}, "json")
        assert "test" in output
        console.print(f"  ✅ Result formatting works")

        return True

    except Exception as e:
        console.print(f"  ❌ Utilities failed: {e}")
        import traceback
        console.print(traceback.format_exc())
        return False


def main():
    """Run all benchmark tests."""
    console.print("[bold green]🧪 Testing SocialMapper Benchmarks[/bold green]")

    tests = [
        test_utilities,
        test_core_operations,
        test_memory_profiling,
        test_batch_processing,
        test_comparison
    ]

    results = []
    for test_func in tests:
        try:
            success = test_func()
            results.append(success)
        except Exception as e:
            console.print(f"\n[red]Error in {test_func.__name__}: {e}[/red]")
            results.append(False)

    # Summary
    passed = sum(results)
    total = len(results)

    console.print("\n" + "=" * 50)
    if passed == total:
        console.print(f"[bold green]✅ All tests passed! ({passed}/{total})[/bold green]")
    else:
        console.print(f"[bold yellow]⚠️ {passed}/{total} tests passed[/bold yellow]")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())