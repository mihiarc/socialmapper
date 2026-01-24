"""Pytest configuration and fixtures for benchmark tests."""

from pathlib import Path

import pytest

from .benchmark_backends import BenchmarkRunner


@pytest.fixture(scope="session")
def benchmark_output_dir() -> Path:
    """Create and return the benchmark results directory.

    Returns
    -------
    Path
        Path to tests/benchmarks/results/ directory
    """
    output_dir = Path(__file__).parent / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


@pytest.fixture
def benchmark_runner() -> BenchmarkRunner:
    """Create a configured BenchmarkRunner instance.

    Returns
    -------
    BenchmarkRunner
        Runner configured with default test matrix
    """
    return BenchmarkRunner()


@pytest.fixture
def quick_benchmark_runner() -> BenchmarkRunner:
    """Create a BenchmarkRunner for quick tests with reduced matrix.

    Uses only one location, one travel time, and one mode for fast testing.

    Returns
    -------
    BenchmarkRunner
        Runner configured for quick testing
    """
    return BenchmarkRunner(
        locations=[("Portland, OR", (45.5152, -122.6784))],
        travel_times=[15],
        travel_modes=["drive"],
        backends=["networkx", "valhalla"],
    )


@pytest.fixture
def valhalla_only_runner() -> BenchmarkRunner:
    """Create a BenchmarkRunner that only tests Valhalla backend.

    Useful for quick API testing without slow NetworkX calls.

    Returns
    -------
    BenchmarkRunner
        Runner configured for Valhalla-only testing
    """
    return BenchmarkRunner(
        backends=["valhalla"],
    )


@pytest.fixture
def networkx_only_runner() -> BenchmarkRunner:
    """Create a BenchmarkRunner that only tests NetworkX backend.

    Useful for testing offline capability.

    Returns
    -------
    BenchmarkRunner
        Runner configured for NetworkX-only testing
    """
    return BenchmarkRunner(
        backends=["networkx"],
    )
