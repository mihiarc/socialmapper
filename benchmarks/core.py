"""Core operation benchmarks for SocialMapper.

This module contains benchmarks for fundamental SocialMapper operations
including isochrone generation, census data retrieval, POI search, and
geocoding operations.
"""

import time
from typing import Any

from socialmapper import api
from socialmapper.cache_manager import CacheManager

from .base import BaseBenchmark
from .utils import TEST_LOCATIONS, TEST_COORDS


class CoreBenchmarks(BaseBenchmark):
    """Benchmarks for core SocialMapper operations.

    Tests fundamental operations with various configurations
    to establish performance baselines.
    """

    def setup(self):
        """Prepare test data and warm up imports."""
        # Use standardized test data
        self.test_locations = list(TEST_LOCATIONS.values())[:5]
        self.test_coords = list(TEST_COORDS.values())[:5]

        # Generate POI test data (simplified for now)
        self.small_pois = self._generate_test_pois(10)
        self.medium_pois = self._generate_test_pois(50)

        # Initialize cache manager
        self.cache_manager = CacheManager()

    def _generate_test_pois(self, count: int) -> list:
        """Generate test POI data."""
        import random
        pois = []
        for i in range(count):
            # Use test coordinates as centers
            center = random.choice(self.test_coords)
            poi = {
                'id': f'poi_{i}',
                'lat': center[0] + random.gauss(0, 0.05),
                'lon': center[1] + random.gauss(0, 0.05),
                'tags': {
                    'name': f'Test POI {i}',
                    'amenity': random.choice(['hospital', 'school', 'grocery'])
                }
            }
            pois.append(poi)
        return pois

    def bench_single_isochrone_cold_cache(self):
        """Benchmark single isochrone with cold cache.

        Tests worst-case performance when no data is cached.
        """
        # Clear cache to ensure cold start
        self.cache_manager.clear_cache(cache_type='network')

        location = self.test_locations[0]
        travel_time = 15

        with self.timer() as t:
            result = api.create_isochrone(
                location=location,
                travel_time=travel_time,
                travel_mode="drive"
            )

        return self.format_result(
            name='single_isochrone_cold',
            time=t.elapsed,
            location=location,
            travel_time=travel_time,
            cache_state='cold'
        )

    def bench_single_isochrone_warm_cache(self):
        """Benchmark single isochrone with warm cache.

        Tests performance with pre-cached network data.
        """
        location = self.test_locations[0]
        travel_time = 15

        # Warm the cache
        api.create_isochrone(
            location=location,
            travel_time=travel_time,
            travel_mode="drive"
        )

        # Measure with warm cache
        with self.timer() as t:
            result = api.create_isochrone(
                location=location,
                travel_time=travel_time,
                travel_mode="drive"
            )

        return self.format_result(
            name='single_isochrone_warm',
            time=t.elapsed,
            location=location,
            travel_time=travel_time,
            cache_state='warm'
        )

    def bench_batch_isochrones_sequential(self):
        """Benchmark sequential batch processing.

        Tests baseline performance without optimizations.
        """
        locations = self.test_locations[:5]
        travel_time = 20

        with self.timer() as t:
            results = []
            for location in locations:
                iso = api.create_isochrone(
                    location=location,
                    travel_time=travel_time,
                    travel_mode="drive"
                )
                results.append(iso)

        return self.format_result(
            name='batch_sequential',
            time=t.elapsed,
            operations=len(locations),
            method='sequential'
        )

    def bench_batch_isochrones_concurrent(self):
        """Benchmark concurrent batch processing.

        Tests performance with concurrent processing enabled.
        """
        # Use POI data for concurrent processing
        pois = self.medium_pois
        travel_time = 20

        with self.timer() as t:
            from socialmapper.isochrone import create_isochrones_from_poi_list

            results = create_isochrones_from_poi_list(
                poi_data={'pois': pois},
                travel_time_limit=travel_time,
                use_concurrent=True,
                max_workers=4,
                save_individual_files=False
            )

        return self.format_result(
            name='batch_concurrent',
            time=t.elapsed,
            operations=len(pois),
            method='concurrent',
            workers=4
        )

    def bench_batch_isochrones_clustered(self):
        """Benchmark batch processing with clustering.

        Tests performance with intelligent clustering optimization.
        """
        pois = self.medium_pois
        travel_time = 20

        with self.timer() as t:
            from socialmapper.isochrone import create_isochrones_from_poi_list

            results = create_isochrones_from_poi_list(
                poi_data={'pois': pois},
                travel_time_limit=travel_time,
                use_clustering=True,
                max_cluster_radius_km=15,
                save_individual_files=False
            )

        return self.format_result(
            name='batch_clustered',
            time=t.elapsed,
            operations=len(pois),
            method='clustered'
        )

    def bench_census_data_single(self):
        """Benchmark single census data retrieval."""
        location = self.test_coords[0]

        with self.timer() as t:
            result = api.get_census_data(
                location=location,
                radius=5000
            )

        return self.format_result(
            name='census_single',
            time=t.elapsed,
            radius=5000
        )

    def bench_census_data_batch(self):
        """Benchmark batch census data retrieval."""
        locations = self.test_coords[:5]

        with self.timer() as t:
            results = []
            for location in locations:
                data = api.get_census_data(
                    location=location,
                    radius=5000
                )
                results.append(data)

        return self.format_result(
            name='census_batch',
            time=t.elapsed,
            operations=len(locations)
        )

    def bench_poi_search_small(self):
        """Benchmark POI search for small area."""
        location = self.test_locations[0]

        with self.timer() as t:
            result = api.search_pois(
                location=location,
                query="grocery store",
                radius=5000
            )

        poi_count = len(result.get('pois', []))

        return self.format_result(
            name='poi_search_small',
            time=t.elapsed,
            radius=5000,
            poi_count=poi_count
        )

    def bench_poi_search_large(self):
        """Benchmark POI search for large area."""
        location = self.test_locations[0]

        with self.timer() as t:
            result = api.search_pois(
                location=location,
                query="hospital",
                radius=25000
            )

        poi_count = len(result.get('pois', []))

        return self.format_result(
            name='poi_search_large',
            time=t.elapsed,
            radius=25000,
            poi_count=poi_count
        )

    def bench_geocoding_forward(self):
        """Benchmark forward geocoding (address to coordinates)."""
        addresses = [
            "1000 SW Broadway, Portland, OR 97205",
            "1600 Pennsylvania Avenue NW, Washington, DC 20500",
            "1 Infinite Loop, Cupertino, CA 95014",
            "350 5th Ave, New York, NY 10118",
            "233 S Wacker Dr, Chicago, IL 60606"
        ]

        with self.timer() as t:
            results = []
            for address in addresses:
                coords = api.geocode(address)
                results.append(coords)

        return self.format_result(
            name='geocoding_forward',
            time=t.elapsed,
            operations=len(addresses)
        )

    def bench_cache_performance(self):
        """Benchmark cache system performance.

        Measures cache hit rates and performance improvements.
        """
        # Get initial cache stats
        initial_stats = self.cache_manager.get_cache_statistics()

        # Perform operations that should hit cache
        location = self.test_locations[0]
        operations = 10

        times = []
        for i in range(operations):
            start = time.perf_counter()
            api.create_isochrone(
                location=location,
                travel_time=15,
                travel_mode="drive"
            )
            elapsed = time.perf_counter() - start
            times.append(elapsed)

        # Get final cache stats
        final_stats = self.cache_manager.get_cache_statistics()

        # Calculate cache effectiveness
        first_run = times[0]
        cached_runs = times[1:]
        avg_cached = sum(cached_runs) / len(cached_runs)
        improvement = (first_run - avg_cached) / first_run * 100

        return self.format_result(
            name='cache_performance',
            time=sum(times),
            operations=operations,
            first_run_time=first_run,
            avg_cached_time=avg_cached,
            cache_improvement_percent=improvement,
            cache_hits=final_stats['network'].get('hits', 0) -
                      initial_stats['network'].get('hits', 0)
        )

    def bench_travel_modes(self):
        """Benchmark different travel modes.

        Compares performance across walk, bike, and drive modes.
        """
        location = self.test_locations[0]
        travel_time = 15
        modes = ['walk', 'bike', 'drive']

        results = {}
        for mode in modes:
            # Clear cache for fair comparison
            self.cache_manager.clear_cache(cache_type='network')

            with self.timer() as t:
                iso = api.create_isochrone(
                    location=location,
                    travel_time=travel_time,
                    travel_mode=mode
                )

            results[mode] = t.elapsed

        return self.format_result(
            name='travel_modes_comparison',
            time=sum(results.values()),
            walk_time=results['walk'],
            bike_time=results['bike'],
            drive_time=results['drive']
        )

    def bench_export_formats(self):
        """Benchmark different export formats.

        Compares GeoJSON vs GeoParquet performance.
        """
        # Generate test data
        location = self.test_locations[0]
        iso = api.create_isochrone(
            location=location,
            travel_time=15,
            travel_mode="drive"
        )

        # Test GeoJSON export
        with self.timer() as t_json:
            api.export_results(
                data=iso,
                format='geojson',
                output_path='/tmp/test.geojson'
            )

        # Test GeoParquet export
        with self.timer() as t_parquet:
            api.export_results(
                data=iso,
                format='geoparquet',
                output_path='/tmp/test.parquet'
            )

        return self.format_result(
            name='export_formats',
            time=t_json.elapsed + t_parquet.elapsed,
            geojson_time=t_json.elapsed,
            geoparquet_time=t_parquet.elapsed,
            speedup_factor=t_json.elapsed / t_parquet.elapsed
        )