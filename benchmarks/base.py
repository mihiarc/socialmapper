"""Base classes and utilities for benchmarking.

This module provides the foundation for all benchmark tests including
timing utilities, base benchmark class, and the benchmark runner.
"""

import json
import logging
import platform
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import psutil

logger = logging.getLogger(__name__)


@contextmanager
def timer():
    """Context manager for timing code execution.

    Yields
    ------
    Timer
        Timer object with elapsed time.

    Examples
    --------
    >>> with timer() as t:
    ...     time.sleep(1)
    >>> print(f"Elapsed: {t.elapsed:.2f} seconds")
    Elapsed: 1.00 seconds
    """
    class Timer:
        def __init__(self):
            self.start = None
            self.end = None
            self.elapsed = None

    t = Timer()
    t.start = time.perf_counter()
    try:
        yield t
    finally:
        t.end = time.perf_counter()
        t.elapsed = t.end - t.start


class BaseBenchmark:
    """Base class for all benchmark suites.

    Provides common functionality for benchmark tests including
    timing, result formatting, and system information collection.
    """

    def __init__(self, config: Optional[dict] = None):
        """Initialize benchmark suite.

        Parameters
        ----------
        config : dict, optional
            Configuration dictionary for benchmark parameters.
        """
        self.config = config or {}
        self.results = []
        self.system_info = self._collect_system_info()

    def setup(self):
        """Setup method called before running benchmarks.

        Override this method to prepare test data or
        initialize resources.
        """
        pass

    def teardown(self):
        """Teardown method called after running benchmarks.

        Override this method to clean up resources.
        """
        pass

    def timer(self):
        """Get a timer context manager.

        Returns
        -------
        timer
            Timer context manager.
        """
        return timer()

    def format_result(
        self,
        name: str,
        time: float,
        operations: Optional[int] = None,
        **kwargs
    ) -> dict:
        """Format benchmark result.

        Parameters
        ----------
        name : str
            Name of the benchmark.
        time : float
            Execution time in seconds.
        operations : int, optional
            Number of operations performed.
        **kwargs
            Additional metrics to include.

        Returns
        -------
        dict
            Formatted result dictionary.
        """
        result = {
            'name': name,
            'time': time,
            'timestamp': datetime.now().isoformat(),
        }

        if operations:
            result['operations'] = operations
            result['ops_per_second'] = operations / time

        result.update(kwargs)
        return result

    def _collect_system_info(self) -> dict:
        """Collect system information.

        Returns
        -------
        dict
            System information dictionary.
        """
        import socialmapper

        return {
            'platform': platform.platform(),
            'python_version': sys.version,
            'cpu_count': psutil.cpu_count(),
            'memory_gb': psutil.virtual_memory().total / (1024 ** 3),
            'socialmapper_version': socialmapper.__version__,
        }

    def run_benchmarks(self) -> list[dict]:
        """Run all benchmark methods in the class.

        Returns
        -------
        list of dict
            List of benchmark results.
        """
        self.setup()
        results = []

        try:
            # Find all methods starting with 'bench_'
            for name in dir(self):
                if name.startswith('bench_'):
                    method = getattr(self, name)
                    if callable(method):
                        logger.info(f"Running {name}...")
                        try:
                            result = method()
                            if result:
                                results.append(result)
                        except Exception as e:
                            logger.error(f"Error in {name}: {e}")
                            results.append({
                                'name': name,
                                'error': str(e)
                            })
        finally:
            self.teardown()

        self.results = results
        return results


class BenchmarkRunner:
    """Orchestrates benchmark execution and reporting.

    Handles running multiple benchmark suites, comparing results,
    and generating reports.
    """

    def __init__(
        self,
        output_dir: str = "results",
        compare_baseline: bool = False,
        save_results: bool = True
    ):
        """Initialize benchmark runner.

        Parameters
        ----------
        output_dir : str, optional
            Directory for saving results, by default "results".
        compare_baseline : bool, optional
            Whether to compare with baseline, by default False.
        save_results : bool, optional
            Whether to save results to disk, by default True.
        """
        self.output_dir = Path(output_dir)
        self.compare_baseline = compare_baseline
        self.save_results = save_results

        if save_results:
            self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_all(self, benchmark_suites: list) -> dict:
        """Run all benchmark suites.

        Parameters
        ----------
        benchmark_suites : list
            List of benchmark suite classes.

        Returns
        -------
        dict
            Combined results from all suites.
        """
        all_results = {
            'timestamp': datetime.now().isoformat(),
            'suites': {}
        }

        for suite_class in benchmark_suites:
            suite_name = suite_class.__name__
            logger.info(f"Running suite: {suite_name}")

            suite = suite_class()
            results = suite.run_benchmarks()

            all_results['suites'][suite_name] = {
                'results': results,
                'system_info': suite.system_info
            }

        if self.save_results:
            self._save_results(all_results)

        if self.compare_baseline:
            self._compare_with_baseline(all_results)

        return all_results

    def _save_results(self, results: dict):
        """Save results to disk.

        Parameters
        ----------
        results : dict
            Results dictionary to save.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"benchmark_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"Results saved to {filename}")

        # Also save as latest for easy access
        latest_file = self.output_dir / "latest.json"
        with open(latest_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

    def _compare_with_baseline(self, current: dict):
        """Compare current results with baseline.

        Parameters
        ----------
        current : dict
            Current benchmark results.
        """
        baseline_file = self.output_dir / "baseline.json"

        if not baseline_file.exists():
            logger.warning("No baseline found for comparison")
            return

        with open(baseline_file) as f:
            baseline = json.load(f)

        comparison = self._generate_comparison(current, baseline)
        self._save_comparison(comparison)

    def _generate_comparison(self, current: dict, baseline: dict) -> dict:
        """Generate comparison between current and baseline results.

        Parameters
        ----------
        current : dict
            Current results.
        baseline : dict
            Baseline results.

        Returns
        -------
        dict
            Comparison results.
        """
        comparison = {
            'timestamp': datetime.now().isoformat(),
            'improvements': [],
            'regressions': [],
            'unchanged': []
        }

        # Compare each suite
        for suite_name in current['suites']:
            if suite_name not in baseline['suites']:
                continue

            current_suite = current['suites'][suite_name]
            baseline_suite = baseline['suites'][suite_name]

            # Compare individual benchmarks
            for current_result in current_suite['results']:
                name = current_result.get('name')
                if 'error' in current_result:
                    continue

                # Find matching baseline
                baseline_result = None
                for br in baseline_suite['results']:
                    if br.get('name') == name:
                        baseline_result = br
                        break

                if not baseline_result or 'error' in baseline_result:
                    continue

                # Calculate change
                current_time = current_result.get('time', 0)
                baseline_time = baseline_result.get('time', 0)

                if baseline_time > 0:
                    change = (current_time - baseline_time) / baseline_time

                    result = {
                        'suite': suite_name,
                        'benchmark': name,
                        'current': current_time,
                        'baseline': baseline_time,
                        'change_percent': change * 100
                    }

                    if change < -0.05:  # 5% improvement
                        comparison['improvements'].append(result)
                    elif change > 0.05:  # 5% regression
                        comparison['regressions'].append(result)
                    else:
                        comparison['unchanged'].append(result)

        return comparison

    def _save_comparison(self, comparison: dict):
        """Save comparison results.

        Parameters
        ----------
        comparison : dict
            Comparison results.
        """
        filename = self.output_dir / "comparison.json"
        with open(filename, 'w') as f:
            json.dump(comparison, f, indent=2)

        # Generate markdown report
        self._generate_markdown_report(comparison)

    def _generate_markdown_report(self, comparison: dict):
        """Generate markdown report from comparison.

        Parameters
        ----------
        comparison : dict
            Comparison results.
        """
        report = ["# Benchmark Comparison Report\n"]
        report.append(f"Generated: {comparison['timestamp']}\n")

        if comparison['improvements']:
            report.append("\n## Improvements\n")
            for item in comparison['improvements']:
                report.append(
                    f"- **{item['benchmark']}**: "
                    f"{item['change_percent']:.1f}% faster "
                    f"({item['baseline']:.2f}s → {item['current']:.2f}s)\n"
                )

        if comparison['regressions']:
            report.append("\n## Regressions\n")
            for item in comparison['regressions']:
                report.append(
                    f"- **{item['benchmark']}**: "
                    f"{abs(item['change_percent']):.1f}% slower "
                    f"({item['baseline']:.2f}s → {item['current']:.2f}s)\n"
                )

        if not comparison['improvements'] and not comparison['regressions']:
            report.append("\n## No significant changes detected\n")

        report_file = self.output_dir / "comparison.md"
        with open(report_file, 'w') as f:
            f.writelines(report)

        logger.info(f"Markdown report saved to {report_file}")