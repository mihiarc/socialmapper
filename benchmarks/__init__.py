"""SocialMapper Performance Benchmarking Suite.

This module provides comprehensive performance benchmarking for SocialMapper,
including core operations, scaling tests, cache performance, and memory profiling.
"""

from .base import BaseBenchmark, BenchmarkRunner, timer
from .core import CoreBenchmarks
from .utils import generate_test_data, format_results

__all__ = [
    'BaseBenchmark',
    'BenchmarkRunner',
    'CoreBenchmarks',
    'timer',
    'generate_test_data',
    'format_results'
]

# Register benchmark suites
BENCHMARK_SUITES = [
    CoreBenchmarks,
]

def run_all_benchmarks(**kwargs):
    """Run complete benchmark suite.

    Parameters
    ----------
    **kwargs : dict
        Additional arguments passed to BenchmarkRunner.

    Returns
    -------
    dict
        Benchmark results dictionary.
    """
    runner = BenchmarkRunner(**kwargs)
    return runner.run_all(BENCHMARK_SUITES)