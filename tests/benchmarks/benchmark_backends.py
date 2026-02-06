"""Benchmark runner for isochrone generation performance.

This module provides tools to benchmark Valhalla isochrone generation
across locations, travel times, and travel modes.
"""

import csv
import json
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

import socialmapper


@dataclass
class BenchmarkResult:
    """Result from a single benchmark run."""

    location: str
    travel_time: int
    travel_mode: str
    duration_seconds: float
    area_sq_km: float | None
    success: bool
    error: str | None = None


@dataclass
class BenchmarkSummary:
    """Aggregated summary for a backend."""

    total_time: float
    avg_time: float
    success_rate: float
    successful_count: int
    failed_count: int


@dataclass
class BenchmarkReport:
    """Complete benchmark report with metadata and results."""

    metadata: dict[str, Any]
    summary: dict[str, Any]
    results: list[dict[str, Any]]


# Test matrix configuration
LOCATIONS = [
    ("Portland, OR", (45.5152, -122.6784)),
    ("Seattle, WA", (47.6062, -122.3321)),
    ("Denver, CO", (39.7392, -104.9903)),
]

TRAVEL_TIMES = [5, 15, 30]  # minutes

TRAVEL_MODES = ["drive", "walk", "bike"]

class BenchmarkRunner:
    """Runs benchmark tests for Valhalla isochrone generation."""

    def __init__(
        self,
        locations: list[tuple[str, tuple[float, float]]] | None = None,
        travel_times: list[int] | None = None,
        travel_modes: list[str] | None = None,
    ):
        """Initialize the benchmark runner.

        Parameters
        ----------
        locations : list of tuples, optional
            List of (name, (lat, lon)) tuples. Defaults to LOCATIONS.
        travel_times : list of int, optional
            Travel times in minutes. Defaults to TRAVEL_TIMES.
        travel_modes : list of str, optional
            Travel modes to test. Defaults to TRAVEL_MODES.
        """
        self.locations = locations or LOCATIONS
        self.travel_times = travel_times or TRAVEL_TIMES
        self.travel_modes = travel_modes or TRAVEL_MODES
        self.results: list[BenchmarkResult] = []
        self.console = Console()

    def run_single_benchmark(
        self,
        location_name: str,
        coords: tuple[float, float],
        travel_time: int,
        travel_mode: str,
    ) -> BenchmarkResult:
        """Time a single isochrone generation call.

        Parameters
        ----------
        location_name : str
            Human-readable location name
        coords : tuple
            (latitude, longitude) coordinates
        travel_time : int
            Travel time in minutes
        travel_mode : str
            Mode of transportation

        Returns
        -------
        BenchmarkResult
            Result containing timing and success information
        """
        start_time = time.perf_counter()

        try:
            result = socialmapper.create_isochrone(
                location=coords,
                travel_time=travel_time,
                travel_mode=travel_mode,
            )

            end_time = time.perf_counter()
            duration = end_time - start_time

            # Calculate area from the geometry
            area_sq_km = result.get("properties", {}).get("area_sq_km")

            return BenchmarkResult(
                location=location_name,
                travel_time=travel_time,
                travel_mode=travel_mode,
                duration_seconds=round(duration, 3),
                area_sq_km=round(area_sq_km, 2) if area_sq_km else None,
                success=True,
                error=None,
            )

        except Exception as e:
            end_time = time.perf_counter()
            duration = end_time - start_time

            return BenchmarkResult(
                location=location_name,
                travel_time=travel_time,
                travel_mode=travel_mode,
                duration_seconds=round(duration, 3),
                area_sq_km=None,
                success=False,
                error=str(e),
            )

    def run_comprehensive_suite(
        self,
        show_progress: bool = True,
    ) -> list[BenchmarkResult]:
        """Run the full benchmark suite for all combinations.

        Parameters
        ----------
        show_progress : bool, optional
            Whether to print progress to console. Default True.

        Returns
        -------
        list of BenchmarkResult
            All benchmark results
        """
        self.results = []
        total_tests = (
            len(self.locations)
            * len(self.travel_times)
            * len(self.travel_modes)
        )

        if show_progress:
            self.console.print(
                f"\n[bold blue]Running {total_tests} benchmark tests...[/bold blue]\n"
            )

        test_num = 0
        for location_name, coords in self.locations:
            for travel_time in self.travel_times:
                for travel_mode in self.travel_modes:
                    test_num += 1

                    if show_progress:
                        self.console.print(
                            f"  [{test_num}/{total_tests}] "
                            f"{location_name}, {travel_time}min, {travel_mode}...",
                            end=" ",
                        )

                    result = self.run_single_benchmark(
                        location_name=location_name,
                        coords=coords,
                        travel_time=travel_time,
                        travel_mode=travel_mode,
                    )
                    self.results.append(result)

                    if show_progress:
                        if result.success:
                            self.console.print(
                                f"[green]{result.duration_seconds}s[/green]"
                            )
                        else:
                            self.console.print(
                                f"[red]FAILED: {result.error}[/red]"
                            )

        return self.results

    def get_summary(self) -> BenchmarkSummary:
        """Calculate summary statistics.

        Returns
        -------
        BenchmarkSummary
            Aggregated benchmark summary
        """
        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]

        total_time = sum(r.duration_seconds for r in self.results)
        avg_time = total_time / len(self.results) if self.results else 0
        success_rate = len(successful) / len(self.results) if self.results else 0

        return BenchmarkSummary(
            total_time=round(total_time, 2),
            avg_time=round(avg_time, 3),
            success_rate=round(success_rate, 3),
            successful_count=len(successful),
            failed_count=len(failed),
        )

    def create_report(self) -> BenchmarkReport:
        """Create a complete benchmark report.

        Returns
        -------
        BenchmarkReport
            Complete report with metadata, summary, and results
        """
        summary = self.get_summary()

        summary_dict = {
            "total_time": summary.total_time,
            "avg_time": summary.avg_time,
            "success_rate": summary.success_rate,
            "successful_count": summary.successful_count,
            "failed_count": summary.failed_count,
        }

        return BenchmarkReport(
            metadata={
                "timestamp": datetime.now().isoformat(),
                "socialmapper_version": socialmapper.__version__,
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "locations": [name for name, _ in self.locations],
                "travel_times": self.travel_times,
                "travel_modes": self.travel_modes,
            },
            summary=summary_dict,
            results=[asdict(r) for r in self.results],
        )

    def export_json(self, output_path: Path | str) -> Path:
        """Export benchmark results to JSON file.

        Parameters
        ----------
        output_path : Path or str
            Path for the output JSON file

        Returns
        -------
        Path
            Path to the created file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        report = self.create_report()

        data = {
            "metadata": report.metadata,
            "summary": report.summary,
            "results": report.results,
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        return output_path

    def export_csv(self, output_path: Path | str) -> Path:
        """Export benchmark results to CSV file.

        Parameters
        ----------
        output_path : Path or str
            Path for the output CSV file

        Returns
        -------
        Path
            Path to the created file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "location",
            "travel_time",
            "travel_mode",
            "duration_seconds",
            "area_sq_km",
            "success",
            "error",
        ]

        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for result in self.results:
                writer.writerow(asdict(result))

        return output_path

    def print_summary(self) -> None:
        """Print a rich summary table to the console."""
        summary = self.get_summary()

        table = Table(title="Benchmark Summary")
        table.add_column("Total Time (s)", justify="right")
        table.add_column("Avg Time (s)", justify="right")
        table.add_column("Success Rate", justify="right")
        table.add_column("Successful", justify="right", style="green")
        table.add_column("Failed", justify="right", style="red")

        table.add_row(
            f"{summary.total_time:.2f}",
            f"{summary.avg_time:.3f}",
            f"{summary.success_rate * 100:.1f}%",
            str(summary.successful_count),
            str(summary.failed_count),
        )

        self.console.print(table)
