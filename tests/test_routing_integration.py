"""Integration tests for Valhalla isochrone routing backend.

These tests make real API calls to the Valhalla routing service.
They are marked as external and slow.
"""

import pytest

from socialmapper import create_isochrone
from socialmapper.isochrone.backends import (
    ValhallaBackend,
    get_backend,
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


class TestCreateIsochroneAPI:
    """Test create_isochrone API function."""

    @pytest.mark.external
    @pytest.mark.slow
    def test_create_isochrone_default(self, raleigh_coords):
        """Test create_isochrone with default settings."""
        result = create_isochrone(
            raleigh_coords,
            travel_time=10,
            travel_mode="drive",
        )

        assert result["type"] == "Feature"
        assert "geometry" in result
        assert result["geometry"]["type"] in ["Polygon", "MultiPolygon"]
        assert result["properties"]["backend"] == "valhalla"

    @pytest.mark.external
    @pytest.mark.slow
    def test_create_isochrone_string_location(self):
        """Test create_isochrone with string location."""
        result = create_isochrone(
            "Raleigh, NC",
            travel_time=10,
        )

        assert result["type"] == "Feature"
        assert result["properties"]["backend"] == "valhalla"
        assert result["properties"]["area_sq_km"] > 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.external
    @pytest.mark.slow
    def test_isochrone_remote_location(self):
        """Test isochrone generation for remote location."""
        # Fairbanks, AK
        lat, lon = 64.8378, -147.7164

        backend = get_backend("valhalla")

        result = backend.create_isochrone(
            lat=lat,
            lon=lon,
            travel_time=15,
            travel_mode="drive",
        )

        assert result.geometry["type"] in ["Polygon", "MultiPolygon"]
        assert result.area_sq_km > 0

    def test_invalid_coordinates_rejected(self):
        """Test that invalid coordinates are rejected."""
        backend = get_backend("valhalla")

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
