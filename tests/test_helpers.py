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

        # Triangle should have roughly half the area of the square
        assert 0.5 < area < 1.0


class TestCreateCircularGeometry:
    """Test create_circular_geometry function."""

    def test_create_circle_5km(self):
        """Test creating 5km radius circle."""
        circle = create_circular_geometry((45.5152, -122.6784), 5.0)

        assert circle.geom_type == "Polygon"

        # Calculate area - should be approximately π * r²
        area = calculate_polygon_area(circle)
        expected_area = 3.14159 * 5 * 5  # π * r²

        # Allow 10% tolerance for projection effects
        assert expected_area * 0.9 < area < expected_area * 1.1

    def test_create_circle_1km(self):
        """Test creating 1km radius circle."""
        circle = create_circular_geometry((45.5152, -122.6784), 1.0)

        assert circle.geom_type == "Polygon"

        area = calculate_polygon_area(circle)
        expected_area = 3.14159 * 1 * 1

        assert expected_area * 0.9 < area < expected_area * 1.1

    def test_create_circle_different_location(self):
        """Test creating circle at different location."""
        # Test at equator
        circle = create_circular_geometry((0.0, 0.0), 10.0)

        assert circle.geom_type == "Polygon"

        area = calculate_polygon_area(circle)
        expected_area = 3.14159 * 10 * 10

        assert expected_area * 0.9 < area < expected_area * 1.1

    def test_create_circle_large_radius(self):
        """Test creating circle with large radius."""
        circle = create_circular_geometry((45.5152, -122.6784), 50.0)

        assert circle.geom_type == "Polygon"

        area = calculate_polygon_area(circle)
        expected_area = 3.14159 * 50 * 50

        # Larger circles may have more projection distortion
        assert expected_area * 0.8 < area < expected_area * 1.2


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
