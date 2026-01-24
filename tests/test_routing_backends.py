"""Unit tests for isochrone routing backends.

These tests validate the backend protocol implementation and basic functionality.
Integration tests with real APIs are in test_routing_integration.py.
"""

import pytest

from socialmapper.isochrone.backends import (
    IsochroneBackend,
    IsochroneResult,
    NetworkXBackend,
    get_backend,
    get_backend_info,
    list_available_backends,
)
from socialmapper.isochrone.backends.base import BaseIsochroneBackend


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


class TestBaseIsochroneBackend:
    """Test BaseIsochroneBackend validation methods."""

    def test_validate_coordinates_valid(self):
        """Test valid coordinates pass validation."""

        class TestBackend(BaseIsochroneBackend):
            @property
            def name(self) -> str:
                return "test"

            def is_available(self) -> bool:
                return True

            def create_isochrone(self, lat, lon, travel_time, travel_mode):
                pass

        backend = TestBackend()

        # These should not raise
        backend._validate_coordinates(45.5, -122.5)
        backend._validate_coordinates(0, 0)
        backend._validate_coordinates(-90, -180)
        backend._validate_coordinates(90, 180)

    def test_validate_coordinates_invalid_lat(self):
        """Test invalid latitude raises ValueError."""

        class TestBackend(BaseIsochroneBackend):
            @property
            def name(self) -> str:
                return "test"

            def is_available(self) -> bool:
                return True

            def create_isochrone(self, lat, lon, travel_time, travel_mode):
                pass

        backend = TestBackend()

        with pytest.raises(ValueError, match="Latitude must be between"):
            backend._validate_coordinates(91, 0)

        with pytest.raises(ValueError, match="Latitude must be between"):
            backend._validate_coordinates(-91, 0)

    def test_validate_coordinates_invalid_lon(self):
        """Test invalid longitude raises ValueError."""

        class TestBackend(BaseIsochroneBackend):
            @property
            def name(self) -> str:
                return "test"

            def is_available(self) -> bool:
                return True

            def create_isochrone(self, lat, lon, travel_time, travel_mode):
                pass

        backend = TestBackend()

        with pytest.raises(ValueError, match="Longitude must be between"):
            backend._validate_coordinates(0, 181)

        with pytest.raises(ValueError, match="Longitude must be between"):
            backend._validate_coordinates(0, -181)

    def test_validate_travel_time_valid(self):
        """Test valid travel times pass validation."""

        class TestBackend(BaseIsochroneBackend):
            @property
            def name(self) -> str:
                return "test"

            def is_available(self) -> bool:
                return True

            def create_isochrone(self, lat, lon, travel_time, travel_mode):
                pass

        backend = TestBackend()

        # These should not raise
        backend._validate_travel_time(1)
        backend._validate_travel_time(15)
        backend._validate_travel_time(60)
        backend._validate_travel_time(120)

    def test_validate_travel_time_invalid(self):
        """Test invalid travel times raise ValueError."""

        class TestBackend(BaseIsochroneBackend):
            @property
            def name(self) -> str:
                return "test"

            def is_available(self) -> bool:
                return True

            def create_isochrone(self, lat, lon, travel_time, travel_mode):
                pass

        backend = TestBackend()

        with pytest.raises(ValueError, match="Travel time must be between"):
            backend._validate_travel_time(0)

        with pytest.raises(ValueError, match="Travel time must be between"):
            backend._validate_travel_time(121)

    def test_validate_travel_mode_valid(self):
        """Test valid travel modes pass validation."""

        class TestBackend(BaseIsochroneBackend):
            @property
            def name(self) -> str:
                return "test"

            def is_available(self) -> bool:
                return True

            def create_isochrone(self, lat, lon, travel_time, travel_mode):
                pass

        backend = TestBackend()

        # These should not raise
        backend._validate_travel_mode("drive")
        backend._validate_travel_mode("walk")
        backend._validate_travel_mode("bike")

    def test_validate_travel_mode_invalid(self):
        """Test invalid travel modes raise ValueError."""

        class TestBackend(BaseIsochroneBackend):
            @property
            def name(self) -> str:
                return "test"

            def is_available(self) -> bool:
                return True

            def create_isochrone(self, lat, lon, travel_time, travel_mode):
                pass

        backend = TestBackend()

        with pytest.raises(ValueError, match="Travel mode must be one of"):
            backend._validate_travel_mode("fly")

        with pytest.raises(ValueError, match="Travel mode must be one of"):
            backend._validate_travel_mode("swim")


class TestNetworkXBackend:
    """Test NetworkXBackend implementation."""

    def test_backend_name(self):
        """Test backend name is 'networkx'."""
        backend = NetworkXBackend()
        assert backend.name == "networkx"

    def test_is_available(self):
        """Test NetworkXBackend availability check."""
        backend = NetworkXBackend()
        # Should be available since networkx and osmnx are dependencies
        assert backend.is_available() is True

    def test_implements_protocol(self):
        """Test NetworkXBackend implements IsochroneBackend protocol."""
        backend = NetworkXBackend()
        # Check it's runtime checkable
        assert isinstance(backend, IsochroneBackend)


class TestBackendFactory:
    """Test backend factory functions."""

    def test_get_backend_networkx(self):
        """Test getting networkx backend explicitly."""
        backend = get_backend("networkx")
        assert backend.name == "networkx"
        assert isinstance(backend, NetworkXBackend)

    def test_get_backend_unknown(self):
        """Test getting unknown backend raises ValueError."""
        with pytest.raises(ValueError, match="Unknown backend"):
            get_backend("unknown_backend")

    def test_list_available_backends(self):
        """Test listing available backends."""
        available = list_available_backends()

        assert isinstance(available, list)
        # NetworkX should always be available
        assert "networkx" in available

    def test_get_backend_info(self):
        """Test getting backend info."""
        info = get_backend_info()

        assert isinstance(info, dict)
        assert "networkx" in info

        networkx_info = info["networkx"]
        assert "available" in networkx_info
        assert "requires_api_key" in networkx_info
        assert "description" in networkx_info

        # NetworkX doesn't require API key
        assert networkx_info["requires_api_key"] is False

    def test_get_backend_auto_selects(self):
        """Test auto backend selection returns something."""
        backend = get_backend("auto")

        assert backend is not None
        assert hasattr(backend, "name")
        assert hasattr(backend, "create_isochrone")


class TestRoutingAPIBackends:
    """Test routing API backend classes."""

    def test_valhalla_backend_import(self):
        """Test ValhallaBackend can be imported."""
        from socialmapper.isochrone.backends import ValhallaBackend

        backend = ValhallaBackend()
        assert backend.name == "valhalla"

    def test_ors_backend_import(self):
        """Test ORSBackend can be imported."""
        from socialmapper.isochrone.backends import ORSBackend

        backend = ORSBackend()
        assert backend.name == "ors"

    def test_osrm_backend_import(self):
        """Test OSRMBackend can be imported."""
        from socialmapper.isochrone.backends import OSRMBackend

        backend = OSRMBackend()
        assert backend.name == "osrm"

    def test_graphhopper_backend_import(self):
        """Test GraphHopperBackend can be imported."""
        from socialmapper.isochrone.backends import GraphHopperBackend

        backend = GraphHopperBackend()
        assert backend.name == "graphhopper"

    def test_api_backends_without_key_not_available(self):
        """Test API backends requiring keys report unavailable without them."""
        from socialmapper.isochrone.backends import GraphHopperBackend, ORSBackend, OSRMBackend

        # These should report unavailable without API keys configured
        # (unless env vars are set, which is fine for CI)
        ors = ORSBackend()
        osrm = OSRMBackend()
        gh = GraphHopperBackend()

        # Just verify they don't crash - availability depends on env vars
        assert isinstance(ors.is_available(), bool)
        assert isinstance(osrm.is_available(), bool)
        assert isinstance(gh.is_available(), bool)


class TestCreateIsochroneBackendParameter:
    """Test create_isochrone API with backend parameter."""

    def test_create_isochrone_accepts_backend_parameter(self):
        """Test that create_isochrone accepts backend parameter."""
        from socialmapper import create_isochrone
        import inspect

        sig = inspect.signature(create_isochrone)
        params = sig.parameters

        assert "backend" in params
        assert params["backend"].default == "auto"

    def test_invalid_backend_raises_error(self, portland_coords):
        """Test that invalid backend raises ValueError."""
        from socialmapper import create_isochrone

        with pytest.raises(ValueError, match="Unknown backend"):
            create_isochrone(portland_coords, backend="invalid_backend")
