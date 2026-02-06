"""Unit tests for isochrone routing backends.

These tests validate the Valhalla backend protocol implementation and basic
functionality. Integration tests with real APIs are in test_routing_integration.py.
"""

import pytest

from socialmapper.isochrone.backends import (
    IsochroneBackend,
    IsochroneResult,
    ValhallaBackend,
    get_backend,
)


class TestIsochroneResult:
    """Test IsochroneResult dataclass."""

    def test_create_result(self):
        """Test creating an IsochroneResult."""
        result = IsochroneResult(
            geometry={"type": "Polygon", "coordinates": [[[-122, 45], [-122, 46], [-121, 46], [-122, 45]]]},
            center=(45.5, -122.5),
            travel_time=15,
            travel_mode="drive",
            area_sq_km=100.5,
            backend="test",
            metadata={"key": "value"},
        )

        assert result.geometry["type"] == "Polygon"
        assert result.center == (45.5, -122.5)
        assert result.travel_time == 15
        assert result.travel_mode == "drive"
        assert result.area_sq_km == 100.5
        assert result.backend == "test"
        assert result.metadata == {"key": "value"}

    def test_result_optional_metadata(self):
        """Test IsochroneResult with no metadata."""
        result = IsochroneResult(
            geometry={"type": "Polygon", "coordinates": []},
            center=(0, 0),
            travel_time=10,
            travel_mode="walk",
            area_sq_km=5.0,
            backend="test",
        )

        assert result.metadata is None


class TestValhallaBackend:
    """Test ValhallaBackend implementation."""

    def test_backend_name(self):
        """Test backend name is 'valhalla'."""
        backend = ValhallaBackend()
        assert backend.name == "valhalla"

    def test_implements_protocol(self):
        """Test ValhallaBackend implements IsochroneBackend protocol."""
        backend = ValhallaBackend()
        assert isinstance(backend, IsochroneBackend)

    def test_valhalla_backend_import(self):
        """Test ValhallaBackend can be imported."""
        from socialmapper.isochrone.backends import ValhallaBackend

        backend = ValhallaBackend()
        assert backend.name == "valhalla"


class TestBackendFactory:
    """Test backend factory functions."""

    def test_get_backend_valhalla(self):
        """Test getting valhalla backend explicitly."""
        backend = get_backend("valhalla")
        assert backend.name == "valhalla"
        assert isinstance(backend, ValhallaBackend)

    def test_get_backend_unknown(self):
        """Test getting unknown backend raises ValueError."""
        with pytest.raises(ValueError, match="Unknown backend"):
            get_backend("unknown_backend")

    def test_get_backend_auto_selects(self):
        """Test auto backend selection returns Valhalla."""
        backend = get_backend("auto")

        assert backend is not None
        assert backend.name == "valhalla"
        assert hasattr(backend, "create_isochrone")
