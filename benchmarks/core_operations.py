"""
Core operations benchmarks for SocialMapper API.

This module benchmarks the five core API functions to establish
baseline performance metrics and validate competitive claims.
"""

import time
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from rich.console import Console

# Import SocialMapper core functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from socialmapper import (
    create_isochrone,
    create_map,
    get_census_blocks,
    get_census_data,
    get_poi
)

from .utils import BenchmarkRunner, BenchmarkTimer, TEST_COORDS, TEST_LOCATIONS


class CoreOperationsBenchmark:
    """
    Benchmark suite for SocialMapper core operations.

    Tests the five core API functions under various conditions
    to establish performance baselines.
    """

    def __init__(self, output_dir: Path = None):
        """
        Initialize benchmark suite.

        Parameters
        ----------
        output_dir : Path, optional
            Directory for saving results.
        """
        self.runner = BenchmarkRunner("core_operations", output_dir)
        self.console = Console()
        self.test_location = TEST_LOCATIONS["portland"]
        self.test_coords = TEST_COORDS["portland"]

    def benchmark_create_isochrone(self) -> Dict[str, Any]:
        """
        Benchmark create_isochrone function.

        Tests different travel modes and times.

        Returns
        -------
        dict
            Benchmark results for isochrone creation.
        """
        self.console.print("\n[bold cyan]Benchmarking create_isochrone[/bold cyan]")
        results = {}

        # Test different travel modes
        for mode in ["drive", "walk", "bike"]:
            name = f"create_isochrone_{mode}_15min"
            result = self.runner.run_benchmark(
                create_isochrone,
                name,
                args=(self.test_coords,),
                kwargs={"travel_time": 15, "travel_mode": mode},
                iterations=10
            )
            results[name] = result

        # Test different travel times for driving
        for travel_time in [5, 15, 30, 60]:
            name = f"create_isochrone_drive_{travel_time}min"
            result = self.runner.run_benchmark(
                create_isochrone,
                name,
                args=(self.test_coords,),
                kwargs={"travel_time": travel_time, "travel_mode": "drive"},
                iterations=5
            )
            results[name] = result

        return results

    def benchmark_get_poi(self) -> Dict[str, Any]:
        """
        Benchmark get_poi function.

        Tests different categories and limits.

        Returns
        -------
        dict
            Benchmark results for POI retrieval.
        """
        self.console.print("\n[bold cyan]Benchmarking get_poi[/bold cyan]")
        results = {}

        # Test different POI counts
        for limit in [10, 50, 100]:
            name = f"get_poi_{limit}_items"
            result = self.runner.run_benchmark(
                get_poi,
                name,
                args=(self.test_coords,),
                kwargs={"limit": limit},
                iterations=10
            )
            results[name] = result

        # Test with categories
        categories_tests = [
            (["restaurant", "cafe"], "food"),
            (["school", "library"], "education"),
            (["hospital", "pharmacy"], "health"),
            (None, "all_categories")
        ]

        for categories, label in categories_tests:
            name = f"get_poi_{label}"
            result = self.runner.run_benchmark(
                get_poi,
                name,
                args=(self.test_coords,),
                kwargs={"categories": categories, "limit": 50},
                iterations=5
            )
            results[name] = result

        # Test with travel time boundary
        name = "get_poi_with_isochrone"
        result = self.runner.run_benchmark(
            get_poi,
            name,
            args=(self.test_coords,),
            kwargs={"travel_time": 15, "limit": 100},
            iterations=5
        )
        results[name] = result

        return results

    def benchmark_get_census_blocks(self) -> Dict[str, Any]:
        """
        Benchmark get_census_blocks function.

        Tests different area sizes and input types.

        Returns
        -------
        dict
            Benchmark results for census block retrieval.
        """
        self.console.print("\n[bold cyan]Benchmarking get_census_blocks[/bold cyan]")
        results = {}

        # Test with different radii
        for radius in [1, 3, 5, 10]:
            name = f"get_census_blocks_{radius}km"
            result = self.runner.run_benchmark(
                get_census_blocks,
                name,
                kwargs={"location": self.test_coords, "radius_km": radius},
                iterations=10
            )
            results[name] = result

        # Test with isochrone polygon
        iso = create_isochrone(self.test_coords, travel_time=15, travel_mode="drive")
        name = "get_census_blocks_polygon"
        result = self.runner.run_benchmark(
            get_census_blocks,
            name,
            kwargs={"polygon": iso},
            iterations=10
        )
        results[name] = result

        return results

    def benchmark_get_census_data(self) -> Dict[str, Any]:
        """
        Benchmark get_census_data function.

        Tests different data retrieval scenarios.

        Returns
        -------
        dict
            Benchmark results for census data retrieval.
        """
        self.console.print("\n[bold cyan]Benchmarking get_census_data[/bold cyan]")
        results = {}

        # Get some test GEOIDs
        blocks = get_census_blocks(location=self.test_coords, radius_km=2)
        test_geoids = [b["geoid"] for b in blocks[:10]]

        # Test with different variable counts
        variable_tests = [
            (["population"], "1_var"),
            (["population", "median_income"], "2_vars"),
            (["population", "median_income", "median_age"], "3_vars"),
            (["B01003_001E", "B19013_001E", "B01002_001E", "B25077_001E"], "4_census_codes")
        ]

        for variables, label in variable_tests:
            name = f"get_census_data_{label}"
            result = self.runner.run_benchmark(
                get_census_data,
                name,
                args=(test_geoids,),
                kwargs={"variables": variables},
                iterations=10
            )
            results[name] = result

        # Test with different location types
        location_tests = [
            (self.test_coords, "point"),
            (test_geoids[:5], "5_geoids"),
            (test_geoids[:20], "20_geoids")
        ]

        for location, label in location_tests:
            name = f"get_census_data_{label}"
            result = self.runner.run_benchmark(
                get_census_data,
                name,
                args=(location,),
                kwargs={"variables": ["population", "median_income"]},
                iterations=5
            )
            results[name] = result

        return results

    def benchmark_create_map(self) -> Dict[str, Any]:
        """
        Benchmark create_map function.

        Tests different visualization scenarios.

        Returns
        -------
        dict
            Benchmark results for map creation.
        """
        self.console.print("\n[bold cyan]Benchmarking create_map[/bold cyan]")
        results = {}

        # Prepare test data
        blocks = get_census_blocks(location=self.test_coords, radius_km=2)
        geoids = [b["geoid"] for b in blocks[:20]]
        census_data = get_census_data(geoids, ["population"])

        # Add population data to blocks
        for block in blocks[:20]:
            block["population"] = census_data.data.get(
                block["geoid"], {}
            ).get("population", 0)

        # Test different data sizes
        data_sizes = [
            (blocks[:5], "5_features"),
            (blocks[:10], "10_features"),
            (blocks[:20], "20_features")
        ]

        for data, label in data_sizes:
            name = f"create_map_{label}_png"
            result = self.runner.run_benchmark(
                create_map,
                name,
                args=(data, "population"),
                kwargs={"title": f"Test Map {label}", "export_format": "png"},
                iterations=5
            )
            results[name] = result

        # Test different export formats
        formats = ["png", "pdf", "svg", "geojson"]
        for fmt in formats:
            name = f"create_map_format_{fmt}"
            result = self.runner.run_benchmark(
                create_map,
                name,
                args=(blocks[:10], "population"),
                kwargs={"export_format": fmt},
                iterations=5
            )
            results[name] = result

        return results

    def benchmark_end_to_end_workflow(self) -> Dict[str, Any]:
        """
        Benchmark complete end-to-end workflow.

        Tests the full 5-function analysis pipeline.

        Returns
        -------
        dict
            Benchmark results for complete workflow.
        """
        self.console.print("\n[bold cyan]Benchmarking End-to-End Workflow[/bold cyan]")

        def complete_workflow():
            """Run complete SocialMapper workflow."""
            # 1. Create isochrone
            iso = create_isochrone(self.test_coords, travel_time=15, travel_mode="drive")

            # 2. Get census blocks
            blocks = get_census_blocks(polygon=iso)

            # 3. Get census data
            geoids = [b["geoid"] for b in blocks[:30]]
            census_data = get_census_data(geoids, ["population", "median_income"])

            # 4. Get POIs
            pois = get_poi(self.test_coords, travel_time=15, limit=50)

            # 5. Create map
            for block in blocks[:30]:
                block["population"] = census_data.data.get(
                    block["geoid"], {}
                ).get("population", 0)
            map_result = create_map(blocks[:30], "population", export_format="png")

            return iso, blocks, census_data, pois, map_result

        # Run end-to-end benchmark
        result = self.runner.run_benchmark(
            complete_workflow,
            "complete_workflow",
            iterations=10
        )

        # Run with different configurations
        configs = [
            ("small", 10, 5, 20),  # travel_time, radius_km, poi_limit
            ("medium", 15, 10, 50),
            ("large", 30, 15, 100)
        ]

        results = {"complete_workflow": result}

        for label, travel_time, radius, poi_limit in configs:
            def workflow_variant():
                iso = create_isochrone(self.test_coords, travel_time=travel_time)
                blocks = get_census_blocks(location=self.test_coords, radius_km=radius)
                geoids = [b["geoid"] for b in blocks[:20]]
                census_data = get_census_data(geoids, ["population"])
                pois = get_poi(self.test_coords, limit=poi_limit)
                return iso, blocks, census_data, pois

            name = f"workflow_{label}"
            result = self.runner.run_benchmark(
                workflow_variant,
                name,
                iterations=5
            )
            results[name] = result

        return results

    def run_all_benchmarks(self) -> Dict[str, Any]:
        """
        Run all core operation benchmarks.

        Returns
        -------
        dict
            All benchmark results.
        """
        self.console.print("[bold green]Starting Core Operations Benchmarks[/bold green]")

        all_results = {}

        # Run individual function benchmarks
        all_results.update(self.benchmark_create_isochrone())
        all_results.update(self.benchmark_get_poi())
        all_results.update(self.benchmark_get_census_blocks())
        all_results.update(self.benchmark_get_census_data())
        all_results.update(self.benchmark_create_map())

        # Run end-to-end workflow
        all_results.update(self.benchmark_end_to_end_workflow())

        # Print summary
        self.runner.print_summary()

        # Save results
        json_path = self.runner.save_results("json")
        md_path = self.runner.save_results("markdown")

        self.console.print(f"\n[green]Results saved to:[/green]")
        self.console.print(f"  - {json_path}")
        self.console.print(f"  - {md_path}")

        return all_results


def main():
    """Run core operations benchmarks."""
    benchmark = CoreOperationsBenchmark()
    results = benchmark.run_all_benchmarks()
    return results


if __name__ == "__main__":
    main()