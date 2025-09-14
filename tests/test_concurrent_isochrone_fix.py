#!/usr/bin/env python3
"""Test for concurrent isochrone generation bug fix.

This test reproduces the issue described in GitHub issue #45 where
concurrent processing produces incorrect (truncated) isochrones for
certain locations, particularly Goodland, KS.
"""

import threading
import time
from unittest.mock import Mock, patch
import pytest
import geopandas as gpd
from shapely.geometry import Polygon

from socialmapper.isochrone.concurrent import ConcurrentIsochroneProcessor
from socialmapper.isochrone.cache import ModernNetworkCache


class TestConcurrentIsochroneFix:
    """Test that concurrent processing produces correct isochrones."""

    def test_network_download_locking(self):
        """Test that network downloads are properly synchronized."""
        cache = ModernNetworkCache()

        # Create a cache key for testing
        test_bbox = (39.3, -101.7, 39.4, -101.6)
        cache_key = cache._generate_cache_key(test_bbox, "drive", 30)

        # Get the download lock
        lock1 = cache._get_download_lock(cache_key)
        lock2 = cache._get_download_lock(cache_key)

        # Should be the same lock object
        assert lock1 is lock2

        # Test that locks prevent concurrent access
        access_order = []

        def access_with_lock(thread_id):
            with cache._get_download_lock(cache_key):
                access_order.append(f"start_{thread_id}")
                time.sleep(0.1)  # Simulate download time
                access_order.append(f"end_{thread_id}")

        # Start two threads that try to access the same resource
        t1 = threading.Thread(target=access_with_lock, args=(1,))
        t2 = threading.Thread(target=access_with_lock, args=(2,))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Check that access was serialized (no interleaving)
        assert access_order in [
            ["start_1", "end_1", "start_2", "end_2"],
            ["start_2", "end_2", "start_1", "end_1"]
        ]

    def test_isochrone_size_validation(self):
        """Test that abnormally small isochrones are detected."""
        processor = ConcurrentIsochroneProcessor()

        # Create a small isochrone (truncated)
        small_polygon = Polygon([
            (-101.7, 39.3), (-101.69, 39.3), (-101.69, 39.31),
            (-101.7, 39.31), (-101.7, 39.3)
        ])
        small_gdf = gpd.GeoDataFrame([{"geometry": small_polygon}], crs="EPSG:4326")
        small_gdf = small_gdf.to_crs("EPSG:3857")  # Project for area calculation

        # This should be detected as too small for 30 minutes driving
        from socialmapper.isochrone.travel_modes import TravelMode
        is_valid = processor._validate_isochrone_size(
            small_gdf, 30, TravelMode.DRIVE
        )
        assert not is_valid, "Small isochrone should be detected as invalid"

        # Create a reasonably sized isochrone (larger area)
        # For 30 minutes driving, we need a much larger area
        large_polygon = Polygon([
            (-102.5, 38.8), (-101.0, 38.8), (-101.0, 39.8),
            (-102.5, 39.8), (-102.5, 38.8)
        ])
        large_gdf = gpd.GeoDataFrame([{"geometry": large_polygon}], crs="EPSG:4326")
        large_gdf = large_gdf.to_crs("EPSG:3857")

        # This should be valid for 30 minutes driving
        is_valid = processor._validate_isochrone_size(
            large_gdf, 30, TravelMode.DRIVE
        )
        assert is_valid, "Large isochrone should be valid"

    @patch('socialmapper.isochrone.concurrent.download_and_cache_network')
    @patch('socialmapper.isochrone.concurrent.create_isochrone_from_poi_with_network')
    def test_retry_on_small_isochrone(self, mock_create_isochrone, mock_download):
        """Test that small isochrones trigger retry with fresh network."""
        processor = ConcurrentIsochroneProcessor()

        # Create a POI
        poi = {
            "id": "goodland_walmart",
            "name": "Walmart Goodland",
            "lat": 39.3343285,
            "lon": -101.7285206
        }

        # First attempt returns small isochrone
        small_polygon = Polygon([
            (-101.73, 39.33), (-101.72, 39.33), (-101.72, 39.34),
            (-101.73, 39.34), (-101.73, 39.33)
        ])
        small_gdf = gpd.GeoDataFrame([{"geometry": small_polygon}], crs="EPSG:4326")
        small_gdf = small_gdf.to_crs("EPSG:3857")

        # Second attempt (retry) returns correct isochrone
        large_polygon = Polygon([
            (-102.0, 39.0), (-101.4, 39.0), (-101.4, 39.6),
            (-102.0, 39.6), (-102.0, 39.0)
        ])
        large_gdf = gpd.GeoDataFrame([{"geometry": large_polygon}], crs="EPSG:4326")
        large_gdf = large_gdf.to_crs("EPSG:3857")

        # Configure mocks
        mock_create_isochrone.side_effect = [small_gdf, large_gdf]
        mock_network = Mock()
        mock_network.graph = {"crs": "EPSG:3857"}
        mock_download.return_value = mock_network

        # Test retry logic
        from socialmapper.isochrone.travel_modes import TravelMode
        result = processor._retry_with_fresh_network(poi, 30, TravelMode.DRIVE)

        # Should return the large (valid) isochrone
        assert result is not None
        assert result.geometry.area.sum() > small_gdf.geometry.area.sum()

    def test_goodland_case_simulation(self):
        """Simulate the Goodland, KS case that was failing."""
        # Create POIs including Goodland
        pois = [
            {
                "id": "goodland",
                "name": "Walmart Goodland",
                "lat": 39.3343285,
                "lon": -101.7285206
            }
        ]
        # Add more POIs to trigger concurrent processing (10+ required)
        pois.extend([
            {"id": f"poi_{i}", "lat": 39.0 + i*0.1, "lon": -101.0 - i*0.1}
            for i in range(10)
        ])

        processor = ConcurrentIsochroneProcessor(
            max_network_workers=4,
            max_isochrone_workers=2
        )

        # The fix should ensure that even with concurrent processing,
        # each POI gets a properly sized isochrone or triggers a retry
        # This is a smoke test to ensure no crashes occur
        with patch('socialmapper.isochrone.concurrent.download_and_cache_network') as mock_download:
            with patch('socialmapper.isochrone.concurrent.create_isochrone_from_poi_with_network') as mock_create:
                # Mock successful network download
                mock_network = Mock()
                mock_network.graph = {"crs": "EPSG:3857"}
                mock_network.nodes = list(range(1000))  # Simulate reasonable network
                mock_network.edges = [(i, i+1) for i in range(999)]
                mock_download.return_value = mock_network

                # Mock isochrone creation
                polygon = Polygon([
                    (-102.0, 39.0), (-101.4, 39.0), (-101.4, 39.6),
                    (-102.0, 39.6), (-102.0, 39.0)
                ])
                gdf = gpd.GeoDataFrame([{"geometry": polygon}], crs="EPSG:4326")
                gdf = gdf.to_crs("EPSG:3857")
                mock_create.return_value = gdf

                # This should not raise any exceptions
                from socialmapper.isochrone.travel_modes import TravelMode
                results = processor.process_pois_concurrent(
                    pois[:3],  # Use fewer POIs for faster test
                    travel_time_minutes=30,
                    travel_mode=TravelMode.DRIVE
                )

                # Should return results for all POIs
                assert len(results) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])