"""Pytest tests for running benchmarks and generating reports.

Run the comprehensive benchmark with:
    uv run pytest tests/benchmarks/test_benchmark_comparison.py -v -s

Run a quick benchmark with:
    uv run pytest tests/benchmarks/test_benchmark_comparison.py::TestBenchmarkComparison::test_quick_benchmark -v -s
"""

from datetime import datetime
from pathlib import Path

import pytest

from .benchmark_backends import BenchmarkRunner


class TestBenchmarkComparison:
    """Test class for running benchmark comparisons."""

    @pytest.mark.benchmark
    def test_run_comprehensive_benchmark(
        self,
        benchmark_runner: BenchmarkRunner,
        benchmark_output_dir: Path,
    ):
        """Run the full benchmark suite and generate reports.

        This test runs all combinations:
        - 3 locations (Portland, Seattle, Denver)
        - 3 travel times (5, 15, 30 minutes)
        - 3 travel modes (drive, walk, bike)

        Total: 27 benchmark calls
        """
        results = benchmark_runner.run_comprehensive_suite(show_progress=True)

        assert len(results) > 0, "No benchmark results generated"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        json_path = benchmark_output_dir / f"benchmark_{timestamp}.json"
        benchmark_runner.export_json(json_path)
        assert json_path.exists(), f"JSON file not created at {json_path}"

        csv_path = benchmark_output_dir / f"benchmark_{timestamp}.csv"
        benchmark_runner.export_csv(csv_path)
        assert csv_path.exists(), f"CSV file not created at {csv_path}"

        benchmark_runner.print_summary()

        report = benchmark_runner.create_report()
        assert "metadata" in report.__dict__
        assert "summary" in report.__dict__
        assert "results" in report.__dict__

        assert "timestamp" in report.metadata
        assert "socialmapper_version" in report.metadata
        assert "python_version" in report.metadata

        print(f"\nResults saved to:")
        print(f"  JSON: {json_path}")
        print(f"  CSV: {csv_path}")

    @pytest.mark.benchmark
    def test_quick_benchmark(
        self,
        quick_benchmark_runner: BenchmarkRunner,
        benchmark_output_dir: Path,
    ):
        """Run a quick benchmark with reduced test matrix.

        Tests only:
        - 1 location (Portland)
        - 1 travel time (15 min)
        - 1 travel mode (drive)

        Total: 1 benchmark call
        """
        results = quick_benchmark_runner.run_comprehensive_suite(show_progress=True)

        assert len(results) == 1, f"Expected 1 result, got {len(results)}"

        successful = [r for r in results if r.success]
        print(f"\nSuccessful: {len(successful)}/1")

        for result in results:
            status = "OK" if result.success else f"FAILED: {result.error}"
            print(f"  {result.travel_mode}: {result.duration_seconds}s - {status}")

        quick_benchmark_runner.print_summary()

    @pytest.mark.benchmark
    def test_full_benchmark(
        self,
        benchmark_runner: BenchmarkRunner,
        benchmark_output_dir: Path,
    ):
        """Run full benchmark across all locations/times/modes."""
        results = benchmark_runner.run_comprehensive_suite(show_progress=True)

        # Should have 27 results (3 locations x 3 times x 3 modes)
        expected = 3 * 3 * 3
        assert len(results) == expected, f"Expected {expected} results, got {len(results)}"

        benchmark_runner.print_summary()

        successful = [r for r in results if r.success]
        success_rate = len(successful) / len(results)
        print(f"\nSuccess rate: {success_rate * 100:.1f}%")

        # Assert reasonable success rate (API might have occasional failures)
        assert success_rate >= 0.8, f"Success rate too low: {success_rate}"


class TestBenchmarkRunner:
    """Unit tests for BenchmarkRunner functionality."""

    def test_runner_initialization_defaults(self):
        """Test runner initializes with correct defaults."""
        runner = BenchmarkRunner()

        assert len(runner.locations) == 3
        assert len(runner.travel_times) == 3
        assert len(runner.travel_modes) == 3
        assert runner.results == []

    def test_runner_initialization_custom(self):
        """Test runner accepts custom configuration."""
        runner = BenchmarkRunner(
            locations=[("Test City", (40.0, -74.0))],
            travel_times=[10],
            travel_modes=["drive"],
        )

        assert len(runner.locations) == 1
        assert len(runner.travel_times) == 1
        assert len(runner.travel_modes) == 1

    def test_single_benchmark(self):
        """Test running a single benchmark."""
        runner = BenchmarkRunner()

        result = runner.run_single_benchmark(
            location_name="Portland, OR",
            coords=(45.5152, -122.6784),
            travel_time=15,
            travel_mode="drive",
        )

        assert result.location == "Portland, OR"
        assert result.travel_time == 15
        assert result.travel_mode == "drive"
        assert result.duration_seconds > 0

        if result.success:
            assert result.area_sq_km is not None
            assert result.area_sq_km > 0
            assert result.error is None
        else:
            print(f"Benchmark failed: {result.error}")

    def test_get_summary_empty(self):
        """Test summary calculation with no results."""
        runner = BenchmarkRunner()
        summary = runner.get_summary()

        assert summary.total_time == 0
        assert summary.avg_time == 0

    def test_create_report_structure(self):
        """Test that report has correct structure."""
        runner = BenchmarkRunner(
            locations=[("Portland, OR", (45.5152, -122.6784))],
            travel_times=[15],
            travel_modes=["drive"],
        )

        runner.run_comprehensive_suite(show_progress=False)

        report = runner.create_report()

        assert "timestamp" in report.metadata
        assert "socialmapper_version" in report.metadata
        assert "python_version" in report.metadata

        assert "total_time" in report.summary

        assert len(report.results) == 1

    def test_export_json(self, benchmark_output_dir: Path):
        """Test JSON export functionality."""
        runner = BenchmarkRunner(
            locations=[("Portland, OR", (45.5152, -122.6784))],
            travel_times=[15],
            travel_modes=["drive"],
        )

        runner.run_comprehensive_suite(show_progress=False)

        json_path = benchmark_output_dir / "test_export.json"
        result_path = runner.export_json(json_path)

        assert result_path.exists()
        assert result_path.suffix == ".json"

        result_path.unlink()

    def test_export_csv(self, benchmark_output_dir: Path):
        """Test CSV export functionality."""
        runner = BenchmarkRunner(
            locations=[("Portland, OR", (45.5152, -122.6784))],
            travel_times=[15],
            travel_modes=["drive"],
        )

        runner.run_comprehensive_suite(show_progress=False)

        csv_path = benchmark_output_dir / "test_export.csv"
        result_path = runner.export_csv(csv_path)

        assert result_path.exists()
        assert result_path.suffix == ".csv"

        with open(result_path) as f:
            lines = f.readlines()
            assert len(lines) == 2  # Header + 1 result

        result_path.unlink()
