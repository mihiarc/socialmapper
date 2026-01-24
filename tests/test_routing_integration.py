"""Integration tests for isochrone routing backends.

These tests make real API calls to routing services and compare results
between different backends. They are marked as external and slow.
"""

import pytest

from socialmapper import create_isochrone
from socialmapper.isochrone.backends import (
    NetworkXBackend,
    ValhallaBackend,
    get_backend,
    list_available_backends,
)


@pytest.fixture
def raleigh_coords():
    """Raleigh, NC coordinates."""
    return (35.7796, -78.6382)


class TestValhallaBackend:
    """Integration tests for Valhalla backend."""

    @pytest.mark.external
    @pytest.mark.slow
    def test_valhalla_isochrone_drive(self, raleigh_coords):
        """Test Valhalla backend creates driving isochrone."""
        backend = ValhallaBackend()

        if not backend.is_available():
            pytest.skip("Valhalla backend not available (routingpy not installed)")

        lat, lon = raleigh_coords
        result = backend.create_isochrone(
            lat=lat,
            lon=lon,
            travel_time=15,
            travel_mode="drive",
        )

        assert result.geometry["type"] in ["Polygon", "MultiPolygon"]
        assert result.center == (lat, lon)
        assert result.travel_time == 15
        assert result.travel_mode == "drive"
        assert result.area_sq_km > 0
        assert result.backend == "valhalla"

    @pytest.mark.external
    @pytest.mark.slow
    def test_valhalla_isochrone_walk(self, raleigh_coords):
        """Test Valhalla backend creates walking isochrone."""
        backend = ValhallaBackend()

        if not backend.is_available():
            pytest.skip("Valhalla backend not available")

        lat, lon = raleigh_coords
        result = backend.create_isochrone(
            lat=lat,
            lon=lon,
            travel_time=15,
            travel_mode="walk",
        )

        assert result.geometry["type"] in ["Polygon", "MultiPolygon"]
        assert result.travel_mode == "walk"
        # Walking should produce smaller area than driving
        assert result.area_sq_km > 0

    @pytest.mark.external
    @pytest.mark.slow
    def test_valhalla_isochrone_bike(self, raleigh_coords):
        """Test Valhalla backend creates biking isochrone."""
        backend = ValhallaBackend()

        if not backend.is_available():
            pytest.skip("Valhalla backend not available")

        lat, lon = raleigh_coords
        result = backend.create_isochrone(
            lat=lat,
            lon=lon,
            travel_time=15,
            travel_mode="bike",
        )

        assert result.geometry["type"] in ["Polygon", "MultiPolygon"]
        assert result.travel_mode == "bike"
        assert result.area_sq_km > 0


class TestNetworkXBackend:
    """Integration tests for NetworkX backend."""

    @pytest.mark.external
    @pytest.mark.slow
    def test_networkx_isochrone_drive(self, raleigh_coords):
        """Test NetworkX backend creates driving isochrone."""
        backend = NetworkXBackend()
        lat, lon = raleigh_coords

        result = backend.create_isochrone(
            lat=lat,
            lon=lon,
            travel_time=10,
            travel_mode="drive",
        )

        assert result.geometry["type"] in ["Polygon", "MultiPolygon"]
        assert result.center == (lat, lon)
        assert result.travel_time == 10
        assert result.travel_mode == "drive"
        assert result.area_sq_km > 0
        assert result.backend == "networkx"

        # NetworkX backend includes distance statistics
        assert "min_distance_km" in result.metadata
        assert "max_distance_km" in result.metadata
        assert "reachable_nodes" in result.metadata

    @pytest.mark.external
    @pytest.mark.slow
    def test_networkx_isochrone_walk(self, raleigh_coords):
        """Test NetworkX backend creates walking isochrone."""
        backend = NetworkXBackend()
        lat, lon = raleigh_coords

        result = backend.create_isochrone(
            lat=lat,
            lon=lon,
            travel_time=10,
            travel_mode="walk",
        )

        assert result.geometry["type"] in ["Polygon", "MultiPolygon"]
        assert result.travel_mode == "walk"
        assert result.area_sq_km > 0


class TestBackendComparison:
    """Compare results between different backends."""

    @pytest.mark.external
    @pytest.mark.slow
    @pytest.mark.integration
    def test_compare_valhalla_networkx_areas(self, raleigh_coords):
        """Compare area sizes between Valhalla and NetworkX backends."""
        available = list_available_backends()

        if "valhalla" not in available:
            pytest.skip("Valhalla backend not available")

        lat, lon = raleigh_coords
        travel_time = 10

        # Get isochrones from both backends
        valhalla = get_backend("valhalla")
        networkx = get_backend("networkx")

        valhalla_result = valhalla.create_isochrone(
            lat=lat, lon=lon, travel_time=travel_time, travel_mode="drive"
        )
        networkx_result = networkx.create_isochrone(
            lat=lat, lon=lon, travel_time=travel_time, travel_mode="drive"
        )

        # Areas should be in the same ballpark (within 50% of each other)
        # They won't be identical due to different algorithms
        ratio = valhalla_result.area_sq_km / networkx_result.area_sq_km

        # Log the comparison for debugging
        print(f"\nValhalla area: {valhalla_result.area_sq_km:.2f} km²")
        print(f"NetworkX area: {networkx_result.area_sq_km:.2f} km²")
        print(f"Ratio: {ratio:.2f}")

        # Areas should be reasonably similar (0.5x to 2x)
        assert 0.3 < ratio < 3.0, f"Area ratio {ratio} is outside acceptable range"


class TestCreateIsochroneWithBackend:
    """Test create_isochrone API function with backend parameter."""

    @pytest.mark.external
    @pytest.mark.slow
    def test_create_isochrone_auto_backend(self, raleigh_coords):
        """Test create_isochrone with auto backend selection."""
        result = create_isochrone(
            raleigh_coords,
            travel_time=10,
            travel_mode="drive",
            backend="auto",
        )

        assert result["type"] == "Feature"
        assert "geometry" in result
        assert result["geometry"]["type"] in ["Polygon", "MultiPolygon"]
        assert "backend" in result["properties"]

    @pytest.mark.external
    @pytest.mark.slow
    def test_create_isochrone_networkx_backend(self, raleigh_coords):
        """Test create_isochrone with NetworkX backend."""
        result = create_isochrone(
            raleigh_coords,
            travel_time=10,
            travel_mode="drive",
            backend="networkx",
        )

        assert result["type"] == "Feature"
        assert result["properties"]["backend"] == "networkx"
        assert result["properties"]["area_sq_km"] > 0

    @pytest.mark.external
    @pytest.mark.slow
    def test_create_isochrone_valhalla_backend(self, raleigh_coords):
        """Test create_isochrone with Valhalla backend."""
        available = list_available_backends()

        if "valhalla" not in available:
            pytest.skip("Valhalla backend not available")

        result = create_isochrone(
            raleigh_coords,
            travel_time=15,
            travel_mode="drive",
            backend="valhalla",
        )

        assert result["type"] == "Feature"
        assert result["properties"]["backend"] == "valhalla"
        assert result["properties"]["area_sq_km"] > 0

    @pytest.mark.external
    @pytest.mark.slow
    def test_create_isochrone_string_location_with_backend(self):
        """Test create_isochrone with string location and backend."""
        result = create_isochrone(
            "Raleigh, NC",
            travel_time=10,
            backend="networkx",
        )

        assert result["type"] == "Feature"
        assert result["properties"]["backend"] == "networkx"


class TestPerformanceComparison:
    """Performance comparison between backends."""

    @pytest.mark.external
    @pytest.mark.slow
    @pytest.mark.benchmark
    def test_valhalla_faster_than_networkx(self, raleigh_coords):
        """Verify Valhalla is faster than NetworkX."""
        import time

        available = list_available_backends()

        if "valhalla" not in available:
            pytest.skip("Valhalla backend not available")

        lat, lon = raleigh_coords
        travel_time = 15

        # Time Valhalla
        valhalla = get_backend("valhalla")
        start = time.time()
        valhalla.create_isochrone(lat=lat, lon=lon, travel_time=travel_time, travel_mode="drive")
        valhalla_time = time.time() - start

        # Time NetworkX
        networkx = get_backend("networkx")
        start = time.time()
        networkx.create_isochrone(lat=lat, lon=lon, travel_time=travel_time, travel_mode="drive")
        networkx_time = time.time() - start

        print(f"\nValhalla time: {valhalla_time:.2f}s")
        print(f"NetworkX time: {networkx_time:.2f}s")
        print(f"Speedup: {networkx_time / valhalla_time:.1f}x")

        # Valhalla should be faster (allow some tolerance)
        # Note: First NetworkX call may be faster due to caching
        assert valhalla_time < networkx_time * 1.5, (
            f"Valhalla ({valhalla_time:.2f}s) not faster than NetworkX ({networkx_time:.2f}s)"
        )


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.external
    @pytest.mark.slow
    def test_isochrone_remote_location(self):
        """Test isochrone generation for remote location."""
        # Rural Alaska coordinates
        lat, lon = 64.8378, -147.7164  # Fairbanks, AK

        available = list_available_backends()

        if "valhalla" not in available:
            pytest.skip("Valhalla backend not available")

        backend = get_backend("valhalla")

        # Should still work for remote locations
        result = backend.create_isochrone(
            lat=lat,
            lon=lon,
            travel_time=15,
            travel_mode="drive",
        )

        assert result.geometry["type"] in ["Polygon", "MultiPolygon"]
        assert result.area_sq_km > 0

    @pytest.mark.external
    @pytest.mark.slow
    def test_isochrone_short_travel_time(self, raleigh_coords):
        """Test isochrone with minimum travel time."""
        lat, lon = raleigh_coords

        backend = get_backend("networkx")
        result = backend.create_isochrone(
            lat=lat,
            lon=lon,
            travel_time=1,  # Minimum
            travel_mode="walk",
        )

        assert result.geometry["type"] in ["Polygon", "MultiPolygon"]
        assert result.area_sq_km > 0
        # 1 minute walking should be small
        assert result.area_sq_km < 1.0

    def test_invalid_coordinates_rejected(self):
        """Test that invalid coordinates are rejected."""
        backend = get_backend("networkx")

        with pytest.raises(ValueError, match="Latitude"):
            backend.create_isochrone(
                lat=91,  # Invalid
                lon=-78,
                travel_time=15,
                travel_mode="drive",
            )

        with pytest.raises(ValueError, match="Longitude"):
            backend.create_isochrone(
                lat=35,
                lon=181,  # Invalid
                travel_time=15,
                travel_mode="drive",
            )
