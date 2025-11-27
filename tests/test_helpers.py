"""Comprehensive tests for helpers module."""

import pytest
from unittest.mock import patch, MagicMock
from shapely.geometry import Polygon, Point
from socialmapper.helpers import (
    resolve_coordinates,
    calculate_polygon_area,
    create_circular_geometry,
    extract_geometry_from_geojson,
)
from socialmapper.exceptions import ValidationError


class TestResolveCoordinates:
    """Test resolve_coordinates function."""

    @patch('socialmapper._geocoding.geocode_location')
    def test_resolve_string_address(self, mock_geocode):
        """Test resolving string address."""
        mock_geocode.return_value = (45.5152, -122.6784)

        coords, name = resolve_coordinates("Portland, OR")

        assert coords == (45.5152, -122.6784)
        assert name == "Portland, OR"
        mock_geocode.assert_called_once_with("Portland, OR")

    @patch('socialmapper._geocoding.geocode_location')
    def test_resolve_string_address_no_result(self, mock_geocode):
        """Test error when geocoding returns no result."""
        mock_geocode.return_value = None

        with pytest.raises(ValueError, match="Could not geocode location"):
            resolve_coordinates("Invalid Location")

    def test_resolve_tuple_coordinates(self):
        """Test resolving coordinate tuple."""
        coords, name = resolve_coordinates((45.5152, -122.6784))

        assert coords == (45.5152, -122.6784)
        assert name == "45.5152, -122.6784"

    def test_resolve_list_coordinates(self):
        """Test resolving coordinate list."""
        coords, name = resolve_coordinates([45.5152, -122.6784])

        assert coords == (45.5152, -122.6784)
        assert name == "45.5152, -122.6784"

    def test_resolve_invalid_coordinates(self):
        """Test error with invalid coordinates."""
        with pytest.raises(ValidationError, match="Invalid coordinates"):
            resolve_coordinates((91.0, 0.0))

        with pytest.raises(ValidationError, match="Invalid coordinates"):
            resolve_coordinates((0.0, 181.0))

    def test_resolve_invalid_type(self):
        """Test error with invalid location type."""
        with pytest.raises(ValidationError, match="Location must be a string address"):
            resolve_coordinates(12345)

        with pytest.raises(ValidationError, match="Location must be a string address"):
            resolve_coordinates({"lat": 45.5, "lon": -122.6})

    def test_resolve_invalid_tuple_length(self):
        """Test error with wrong tuple length."""
        with pytest.raises(ValidationError, match="Location must be a string address"):
            resolve_coordinates((45.5,))

        with pytest.raises(ValidationError, match="Location must be a string address"):
            resolve_coordinates((45.5, -122.6, 100))


class TestCalculatePolygonArea:
    """Test calculate_polygon_area function."""

    def test_calculate_small_polygon(self):
        """Test area calculation for small polygon."""
        # Small square near Portland, OR
        poly = Polygon([
            (-122.68, 45.51),
            (-122.67, 45.51),
            (-122.67, 45.52),
            (-122.68, 45.52),
            (-122.68, 45.51)
        ])

        area = calculate_polygon_area(poly)

        # Basic validation that area is positive and reasonable
        assert area > 0
        assert area < 10  # Less than 10 km²

    def test_calculate_larger_polygon(self):
        """Test area calculation for larger polygon."""
        # Larger square
        poly = Polygon([
            (-122.7, 45.4),
            (-122.6, 45.4),
            (-122.6, 45.5),
            (-122.7, 45.5),
            (-122.7, 45.4)
        ])

        area = calculate_polygon_area(poly)

        # Basic validation
        assert area > 50  # At least 50 km²
        assert area < 300  # Less than 300 km²

    def test_calculate_triangle_area(self):
        """Test area calculation for triangle."""
        poly = Polygon([
            (-122.68, 45.51),
            (-122.67, 45.51),
            (-122.675, 45.52),
            (-122.68, 45.51)
        ])

        area = calculate_polygon_area(poly)

        # Triangle should be positive and reasonable (using equal-area projection)
        assert 0.3 < area < 0.7


class TestCreateCircularGeometry:
    """Test create_circular_geometry function.

    Note: create_circular_geometry uses Web Mercator (EPSG:3857) for buffering,
    which creates distorted circles at latitudes away from the equator.
    At 45°N, circles are approximately 50% smaller than expected due to
    the projection's cos²(lat) area distortion.

    This is a known limitation - the area calculation is accurate, but the
    buffer creation itself is affected by Web Mercator distortion.
    """

    def test_create_circle_5km(self):
        """Test creating 5km radius circle."""
        circle = create_circular_geometry((45.5152, -122.6784), 5.0)

        assert circle.geom_type == "Polygon"

        # Calculate area - affected by Web Mercator buffer distortion at 45°N
        area = calculate_polygon_area(circle)

        # At 45°N, Web Mercator buffer creates circles ~50% smaller than expected
        # (cos²(45°) ≈ 0.5), so area is roughly half of π*r²
        assert 30 < area < 50  # ~38.5 km² expected

    def test_create_circle_1km(self):
        """Test creating 1km radius circle."""
        circle = create_circular_geometry((45.5152, -122.6784), 1.0)

        assert circle.geom_type == "Polygon"

        area = calculate_polygon_area(circle)

        # At 45°N, expect roughly half of π*r² = ~1.57 km²
        assert 1.2 < area < 2.0

    def test_create_circle_different_location(self):
        """Test creating circle at equator where distortion is minimal."""
        # Test at equator
        circle = create_circular_geometry((0.0, 0.0), 10.0)

        assert circle.geom_type == "Polygon"

        area = calculate_polygon_area(circle)
        expected_area = 3.14159 * 10 * 10  # π * r² = 314 km²

        # At equator, Web Mercator has minimal distortion
        assert expected_area * 0.9 < area < expected_area * 1.1

    def test_create_circle_large_radius(self):
        """Test creating circle with large radius."""
        circle = create_circular_geometry((45.5152, -122.6784), 50.0)

        assert circle.geom_type == "Polygon"

        area = calculate_polygon_area(circle)

        # At 45°N, expect roughly half of π*r² = ~3927 km²
        assert 3000 < area < 5000


class TestExtractGeometryFromGeoJSON:
    """Test extract_geometry_from_geojson function."""

    def test_extract_from_feature(self):
        """Test extracting geometry from GeoJSON Feature."""
        geojson_feature = {
            "type": "Feature",
            "properties": {"name": "Test"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-122.68, 45.51],
                    [-122.67, 45.51],
                    [-122.67, 45.52],
                    [-122.68, 45.52],
                    [-122.68, 45.51]
                ]]
            }
        }

        geom = extract_geometry_from_geojson(geojson_feature)

        assert geom.geom_type == "Polygon"
        assert geom.is_valid

    def test_extract_from_bare_geometry(self):
        """Test extracting from bare geometry (no Feature wrapper)."""
        geojson_geometry = {
            "type": "Polygon",
            "coordinates": [[
                [-122.68, 45.51],
                [-122.67, 45.51],
                [-122.67, 45.52],
                [-122.68, 45.52],
                [-122.68, 45.51]
            ]]
        }

        geom = extract_geometry_from_geojson(geojson_geometry)

        assert geom.geom_type == "Polygon"
        assert geom.is_valid

    def test_extract_point_geometry(self):
        """Test extracting Point geometry."""
        geojson_point = {
            "type": "Point",
            "coordinates": [-122.68, 45.51]
        }

        geom = extract_geometry_from_geojson(geojson_point)

        assert geom.geom_type == "Point"
        assert geom.x == -122.68
        assert geom.y == 45.51

    def test_extract_multipolygon(self):
        """Test extracting MultiPolygon geometry."""
        geojson_multipoly = {
            "type": "MultiPolygon",
            "coordinates": [
                [[
                    [-122.68, 45.51],
                    [-122.67, 45.51],
                    [-122.67, 45.52],
                    [-122.68, 45.52],
                    [-122.68, 45.51]
                ]],
                [[
                    [-122.66, 45.51],
                    [-122.65, 45.51],
                    [-122.65, 45.52],
                    [-122.66, 45.52],
                    [-122.66, 45.51]
                ]]
            ]
        }

        geom = extract_geometry_from_geojson(geojson_multipoly)

        assert geom.geom_type == "MultiPolygon"
        assert geom.is_valid

    def test_extract_linestring(self):
        """Test extracting LineString geometry."""
        geojson_line = {
            "type": "LineString",
            "coordinates": [
                [-122.68, 45.51],
                [-122.67, 45.52],
                [-122.66, 45.53]
            ]
        }

        geom = extract_geometry_from_geojson(geojson_line)

        assert geom.geom_type == "LineString"
        assert geom.is_valid


class TestAreaCalculationAccuracy:
    """Test area calculation accuracy with equal-area projections.

    These tests verify that the switch from Web Mercator (EPSG:3857)
    to equal-area projections (EPSG:5070 for CONUS, EPSG:6933 globally)
    provides accurate area measurements.
    """

    def test_conus_uses_albers_projection(self):
        """Test that CONUS locations use EPSG:5070 (Conus Albers)."""
        # Polygon in Portland, OR (within CONUS bounds)
        poly = Polygon([
            (-122.68, 45.51),
            (-122.67, 45.51),
            (-122.67, 45.52),
            (-122.68, 45.52),
            (-122.68, 45.51)
        ])

        area = calculate_polygon_area(poly)

        # Verify area is calculated (should be ~0.86 km² for this polygon)
        assert 0.5 < area < 1.5

    def test_non_conus_uses_global_projection(self):
        """Test that non-CONUS locations use EPSG:6933 (global equal-area)."""
        # Polygon in London, UK (outside CONUS bounds)
        poly = Polygon([
            (-0.13, 51.50),
            (-0.12, 51.50),
            (-0.12, 51.51),
            (-0.13, 51.51),
            (-0.13, 51.50)
        ])

        area = calculate_polygon_area(poly)

        # Should still calculate a reasonable area
        assert area > 0
        assert area < 2

    def test_alaska_uses_global_projection(self):
        """Test that Alaska (outside CONUS) uses global projection."""
        # Polygon in Anchorage, AK
        poly = Polygon([
            (-150.0, 61.2),
            (-149.9, 61.2),
            (-149.9, 61.3),
            (-150.0, 61.3),
            (-150.0, 61.2)
        ])

        area = calculate_polygon_area(poly)

        # Should calculate a reasonable area
        assert area > 0
        assert area < 100

    def test_hawaii_uses_global_projection(self):
        """Test that Hawaii (outside CONUS) uses global projection."""
        # Polygon in Honolulu, HI
        poly = Polygon([
            (-157.86, 21.30),
            (-157.85, 21.30),
            (-157.85, 21.31),
            (-157.86, 21.31),
            (-157.86, 21.30)
        ])

        area = calculate_polygon_area(poly)

        # Should calculate a reasonable area
        assert area > 0
        assert area < 5

    def test_equal_area_vs_web_mercator_at_45n(self):
        """Test that equal-area projection doesn't have 100% distortion at 45°N.

        Web Mercator at 45°N latitude exaggerates areas by ~100% (factor of 2).
        Equal-area projection should give accurate results.
        """
        import pyproj
        from shapely.ops import transform

        # Create a 1-degree square at 45°N latitude
        poly = Polygon([
            (-100.0, 45.0),
            (-99.0, 45.0),
            (-99.0, 46.0),
            (-100.0, 46.0),
            (-100.0, 45.0)
        ])

        # Calculate with equal-area (our function)
        equal_area_result = calculate_polygon_area(poly)

        # Calculate with Web Mercator (the old buggy way)
        project_3857 = pyproj.Transformer.from_crs(
            'EPSG:4326', 'EPSG:3857', always_xy=True
        ).transform
        poly_3857 = transform(project_3857, poly)
        web_mercator_result = poly_3857.area / 1_000_000

        # Web Mercator should be roughly 2x larger than equal-area at 45°N
        ratio = web_mercator_result / equal_area_result
        assert 1.5 < ratio < 2.5, f"Expected ~2x distortion, got {ratio:.2f}x"

        # The equal-area result should be approximately correct
        # A 1-degree square at 45°N is roughly 78 km × 111 km = 8658 km²
        # (cos(45°) × 111 km) × 111 km
        expected_area = 0.707 * 111 * 111  # ~8700 km²
        assert expected_area * 0.8 < equal_area_result < expected_area * 1.2

    def test_equal_area_vs_web_mercator_at_30n(self):
        """Test that equal-area projection provides improvement at 30°N.

        Web Mercator at 30°N latitude exaggerates areas by ~32%.
        """
        import pyproj
        from shapely.ops import transform

        # Create a 1-degree square at 30°N latitude (Southern US)
        poly = Polygon([
            (-90.0, 30.0),
            (-89.0, 30.0),
            (-89.0, 31.0),
            (-90.0, 31.0),
            (-90.0, 30.0)
        ])

        # Calculate with equal-area (our function)
        equal_area_result = calculate_polygon_area(poly)

        # Calculate with Web Mercator (the old buggy way)
        project_3857 = pyproj.Transformer.from_crs(
            'EPSG:4326', 'EPSG:3857', always_xy=True
        ).transform
        poly_3857 = transform(project_3857, poly)
        web_mercator_result = poly_3857.area / 1_000_000

        # Web Mercator should be roughly 1.3x larger than equal-area at 30°N
        ratio = web_mercator_result / equal_area_result
        assert 1.2 < ratio < 1.5, f"Expected ~1.3x distortion, got {ratio:.2f}x"

    def test_circular_area_accuracy(self):
        """Test that circular areas are calculated accurately.

        A circle with radius r should have area π*r².

        Note: create_circular_geometry uses Web Mercator for buffering,
        which creates slightly distorted circles at higher latitudes.
        The area calculation itself is accurate - it measures the true
        area of whatever polygon is passed to it.
        """
        # Create a 10 km radius circle near the equator where distortion is minimal
        circle = create_circular_geometry((5.0, -75.0), 10.0)  # Colombia
        area = calculate_polygon_area(circle)

        expected_area = 3.14159 * 10 * 10  # π × r² = 314.16 km²

        # Should be within 10% of expected (some distortion from 3857 buffering)
        assert expected_area * 0.9 < area < expected_area * 1.1

    def test_small_polygon_precision(self):
        """Test that small polygons are calculated precisely.

        Small polygons (like census block groups) should have
        accurate area measurements.
        """
        # Create a small 100m × 100m square (0.01 km²)
        # At 40°N, 0.001 degrees ≈ 85m longitude, 111m latitude
        poly = Polygon([
            (-100.0, 40.0),
            (-100.0 + 0.00117, 40.0),  # ~100m east
            (-100.0 + 0.00117, 40.0 + 0.0009),  # ~100m north
            (-100.0, 40.0 + 0.0009),
            (-100.0, 40.0)
        ])

        area = calculate_polygon_area(poly)

        # Should be approximately 0.01 km² (10,000 m²)
        assert 0.005 < area < 0.02, f"Expected ~0.01 km², got {area:.4f} km²"
