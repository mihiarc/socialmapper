#!/usr/bin/env python3
"""Run complete SocialMapper benchmark suite.

This script executes all performance benchmarks and generates reports
for tracking and comparing SocialMapper performance across versions.

Usage:
    python -m benchmarks.run_all [options]

Examples:
    # Run all benchmarks with default settings
    python -m benchmarks.run_all

    # Run with comparison to baseline
    python -m benchmarks.run_all --compare

    # Run specific benchmark suite
    python -m benchmarks.run_all --suite core

    # Save results in specific format
    python -m benchmarks.run_all --format markdown
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from benchmarks import BENCHMARK_SUITES, BenchmarkRunner
from benchmarks.utils import format_results


def main():
    """Main entry point for benchmark runner."""
    parser = argparse.ArgumentParser(
        description="Run SocialMapper performance benchmarks"
    )

    parser.add_argument(
        "--suite",
        choices=["all", "core", "scaling", "cache", "memory"],
        default="all",
        help="Benchmark suite to run (default: all)"
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmarks/results"),
        help="Output directory for results (default: benchmarks/results)"
    )

    parser.add_argument(
        "--format",
        choices=["json", "markdown", "text"],
        default="json",
        help="Output format (default: json)"
    )

    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare with baseline results"
    )

    parser.add_argument(
        "--baseline",
        type=Path,
        help="Path to baseline results file"
    )

    parser.add_argument(
        "--save-baseline",
        action="store_true",
        help="Save current results as new baseline"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )

    parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="Number of iterations per benchmark (default: 5)"
    )

    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable caching for baseline measurements"
    )

    args = parser.parse_args()

    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)

    # Configure benchmark runner
    runner = BenchmarkRunner(
        output_dir=str(args.output),
        compare_baseline=args.compare,
        save_results=True
    )

    # Select benchmark suites to run
    if args.suite == "all":
        suites_to_run = BENCHMARK_SUITES
    else:
        # Filter to specific suite
        suite_map = {
            "core": "CoreBenchmarks",
            "scaling": "ScalingBenchmarks",
            "cache": "CacheBenchmarks",
            "memory": "MemoryBenchmarks"
        }
        suite_name = suite_map.get(args.suite)
        suites_to_run = [s for s in BENCHMARK_SUITES if s.__name__ == suite_name]

    if not suites_to_run:
        print(f"Warning: No benchmark suite found for '{args.suite}'")
        # Use available suites
        suites_to_run = BENCHMARK_SUITES[:1]  # Just run core benchmarks

    # Disable caching if requested
    if args.no_cache:
        from socialmapper.cache_manager import CacheManager
        cache = CacheManager()
        cache.clear_cache(cache_type='all')
        print("Cache cleared for baseline measurements")

    # Run benchmarks
    print(f"Running {len(suites_to_run)} benchmark suite(s)...")
    print("=" * 60)

    try:
        results = runner.run_all(suites_to_run)

        # Format and display results
        if args.verbose:
            formatted = format_results(results, format=args.format)
            print("\nResults:")
            print(formatted)

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if args.format == "json":
            output_file = args.output / f"benchmark_{timestamp}.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
        elif args.format == "markdown":
            output_file = args.output / f"benchmark_{timestamp}.md"
            formatted = format_results(results, format='markdown')
            with open(output_file, 'w') as f:
                f.write(formatted)
        else:
            output_file = args.output / f"benchmark_{timestamp}.txt"
            formatted = format_results(results, format='text')
            with open(output_file, 'w') as f:
                f.write(formatted)

        print(f"\nResults saved to: {output_file}")

        # Save as baseline if requested
        if args.save_baseline:
            baseline_file = args.output / "baseline.json"
            with open(baseline_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"Baseline saved to: {baseline_file}")

        # Compare with baseline if requested
        if args.compare:
            baseline_file = args.baseline or args.output / "baseline.json"
            if baseline_file.exists():
                print("\nComparison with baseline:")
                print("-" * 40)

                with open(baseline_file) as f:
                    baseline = json.load(f)

                # Simple comparison (could be enhanced)
                for suite_name in results.get('suites', {}):
                    if suite_name in baseline.get('suites', {}):
                        current_suite = results['suites'][suite_name]
                        baseline_suite = baseline['suites'][suite_name]

                        print(f"\n{suite_name}:")
                        for current_result in current_suite.get('results', []):
                            name = current_result.get('name')
                            current_time = current_result.get('time', 0)

                            # Find matching baseline
                            for baseline_result in baseline_suite.get('results', []):
                                if baseline_result.get('name') == name:
                                    baseline_time = baseline_result.get('time', 0)
                                    if baseline_time > 0:
                                        change = ((current_time - baseline_time) /
                                                baseline_time * 100)
                                        symbol = "🔴" if change > 5 else "🟢" if change < -5 else "🟡"
                                        print(f"  {symbol} {name}: {change:+.1f}% "
                                            f"({baseline_time:.2f}s → {current_time:.2f}s)")
                                    break
            else:
                print(f"No baseline found at {baseline_file}")

        # Print summary statistics
        print("\n" + "=" * 60)
        print("Summary:")
        total_time = 0
        total_ops = 0

        for suite_name, suite_data in results.get('suites', {}).items():
            for result in suite_data.get('results', []):
                if 'time' in result and not result.get('error'):
                    total_time += result['time']
                    total_ops += result.get('operations', 1)

        print(f"Total benchmark time: {total_time:.1f} seconds")
        print(f"Total operations: {total_ops}")
        if total_time > 0:
            print(f"Average ops/second: {total_ops/total_time:.1f}")

        # Exit with success
        return 0

    except Exception as e:
        print(f"\nError running benchmarks: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())