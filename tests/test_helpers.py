"""Comprehensive tests for socialmapper.helpers module with real API calls.

Tests all helper functions:
- resolve_coordinates
- calculate_polygon_area
- create_circular_geometry
- extract_geometry_from_geojson
"""

import math
from unittest import TestCase

import pyproj
import pytest
from shapely.geometry import Point, Polygon, shape
from shapely.ops import transform

from socialmapper.helpers import (
    calculate_polygon_area,
    create_circular_geometry,
    extract_geometry_from_geojson,
    resolve_coordinates,
)


class TestResolveCoordinates(TestCase):
    """Test resolve_coordinates function with real geocoding."""

    def test_resolve_coordinates_with_address(self):
        """Test resolving coordinates from an address string."""
        coords, name = resolve_coordinates("Chapel Hill, NC")

        self.assertIsInstance(coords, tuple)
        self.assertEqual(len(coords), 2)

        lat, lon = coords
        # Chapel Hill coordinates (approximately)
        self.assertAlmostEqual(lat, 35.9132, places=1)
        self.assertAlmostEqual(lon, -79.0558, places=1)

        self.assertEqual(name, "Chapel Hill, NC")

    def test_resolve_coordinates_with_tuple(self):
        """Test resolving coordinates from a coordinate tuple."""
        input_coords = (35.9132, -79.0558)
        coords, name = resolve_coordinates(input_coords)

        self.assertEqual(coords, input_coords)
        self.assertEqual(name, "35.9132, -79.0558")

    def test_resolve_coordinates_with_list(self):
        """Test resolving coordinates from a list."""
        input_coords = [40.7128, -74.0060]  # NYC
        coords, name = resolve_coordinates(input_coords)

        self.assertEqual(coords[0], 40.7128)
        self.assertEqual(coords[1], -74.0060)
        self.assertEqual(name, "40.7128, -74.0060")

    def test_resolve_coordinates_invalid_address(self):
        """Test error handling for invalid address."""
        with self.assertRaises(ValueError) as context:
            resolve_coordinates("This is not a real place 12345ABCDE")

        self.assertIn("Could not geocode location", str(context.exception))

    def test_resolve_coordinates_invalid_coords(self):
        """Test error handling for invalid coordinates."""
        # Latitude out of range
        with self.assertRaises(ValueError) as context:
            resolve_coordinates((91, 0))
        self.assertIn("Invalid coordinates", str(context.exception))

        # Longitude out of range
        with self.assertRaises(ValueError) as context:
            resolve_coordinates((0, 181))
        self.assertIn("Invalid coordinates", str(context.exception))

        # Invalid latitude
        with self.assertRaises(ValueError):
            resolve_coordinates((-91, 0))

    def test_resolve_coordinates_major_cities(self):
        """Test resolving coordinates for major US cities."""
        cities = [
            ("New York, NY", 40.7, -74.0),
            ("Los Angeles, CA", 34.0, -118.2),
            ("Chicago, IL", 41.8, -87.6),
            ("Houston, TX", 29.7, -95.3),
            ("Phoenix, AZ", 33.4, -112.0),
        ]

        for city, expected_lat, expected_lon in cities:
            coords, name = resolve_coordinates(city)
            lat, lon = coords

            # Check coordinates are approximately correct (within 0.5 degrees)
            self.assertAlmostEqual(lat, expected_lat, delta=0.5)
            self.assertAlmostEqual(lon, expected_lon, delta=0.5)
            self.assertEqual(name, city)


class TestCalculatePolygonArea(TestCase):
    """Test calculate_polygon_area function."""

    def test_calculate_area_square(self):
        """Test area calculation for a square polygon."""
        # Create a 1-degree square around the equator
        # At the equator, 1 degree ≈ 111 km
        square = Polygon([
            (0, 0),
            (1, 0),
            (1, 1),
            (0, 1),
            (0, 0)
        ])

        area = calculate_polygon_area(square)

        # Should be approximately 111 * 111 = 12,321 km²
        # Allow for projection distortion
        self.assertGreater(area, 10000)
        self.assertLess(area, 15000)

    def test_calculate_area_triangle(self):
        """Test area calculation for a triangular polygon."""
        triangle = Polygon([
            (-122.5, 45.5),
            (-122.4, 45.5),
            (-122.45, 45.6),
            (-122.5, 45.5)
        ])

        area = calculate_polygon_area(triangle)

        # Should be positive and reasonable
        self.assertGreater(area, 0)
        self.assertLess(area, 1000)  # Less than 1000 km²

    def test_calculate_area_complex_polygon(self):
        """Test area calculation for a complex polygon."""
        # Create an L-shaped polygon
        l_shape = Polygon([
            (0, 0),
            (0.5, 0),
            (0.5, 0.25),
            (0.25, 0.25),
            (0.25, 0.5),
            (0, 0.5),
            (0, 0)
        ])

        area = calculate_polygon_area(l_shape)

        self.assertGreater(area, 0)
        # Area should be less than the bounding box (0.5 * 0.5 degrees)
        bbox_area = calculate_polygon_area(
            Polygon([(0, 0), (0.5, 0), (0.5, 0.5), (0, 0.5)])
        )
        self.assertLess(area, bbox_area)

    def test_calculate_area_high_latitude(self):
        """Test area calculation at high latitudes."""
        # Polygon near the Arctic Circle
        arctic_poly = Polygon([
            (-150, 65),
            (-149, 65),
            (-149, 66),
            (-150, 66),
            (-150, 65)
        ])

        area = calculate_polygon_area(arctic_poly)

        # At high latitudes, area should be less than at equator
        self.assertGreater(area, 0)
        self.assertLess(area, 12000)  # Less than equatorial equivalent


class TestCreateCircularGeometry(TestCase):
    """Test create_circular_geometry function."""

    def test_create_circle_basic(self):
        """Test creating a basic circular geometry."""
        center = (35.9132, -79.0558)  # Chapel Hill
        radius_km = 5.0

        circle = create_circular_geometry(center, radius_km)

        self.assertEqual(circle.geom_type, "Polygon")

        # Check that the area is approximately π * r²
        area = calculate_polygon_area(circle)
        expected_area = math.pi * radius_km * radius_km

        # Allow 10% tolerance for projection effects
        self.assertAlmostEqual(area, expected_area, delta=expected_area * 0.1)

    def test_create_circle_various_radii(self):
        """Test creating circles with various radii."""
        center = (40.7128, -74.0060)  # NYC
        radii = [1, 5, 10, 20, 50]

        for radius_km in radii:
            circle = create_circular_geometry(center, radius_km)

            # Check area is approximately correct
            area = calculate_polygon_area(circle)
            expected_area = math.pi * radius_km * radius_km

            # Tolerance increases with radius due to projection effects
            tolerance = 0.1 if radius_km < 10 else 0.15
            self.assertAlmostEqual(
                area, expected_area,
                delta=expected_area * tolerance
            )

    def test_create_circle_at_poles(self):
        """Test creating circles near the poles."""
        # Near North Pole (but not exactly at it to avoid singularities)
        north_center = (85, 0)
        circle_north = create_circular_geometry(north_center, 10)

        self.assertEqual(circle_north.geom_type, "Polygon")
        area_north = calculate_polygon_area(circle_north)
        self.assertGreater(area_north, 0)

        # Near South Pole
        south_center = (-85, 0)
        circle_south = create_circular_geometry(south_center, 10)

        self.assertEqual(circle_south.geom_type, "Polygon")
        area_south = calculate_polygon_area(circle_south)
        self.assertGreater(area_south, 0)

    def test_create_circle_at_date_line(self):
        """Test creating circles near the International Date Line."""
        # Near date line
        center = (0, 179.9)
        circle = create_circular_geometry(center, 50)

        self.assertEqual(circle.geom_type, "Polygon")
        area = calculate_polygon_area(circle)
        expected_area = math.pi * 50 * 50

        # Higher tolerance near date line
        self.assertAlmostEqual(area, expected_area, delta=expected_area * 0.2)

    def test_create_circle_zero_radius(self):
        """Test creating a circle with zero radius."""
        center = (35.9132, -79.0558)
        circle = create_circular_geometry(center, 0)

        # Should create a valid but tiny polygon
        self.assertEqual(circle.geom_type, "Polygon")
        area = calculate_polygon_area(circle)
        self.assertAlmostEqual(area, 0, places=5)


class TestExtractGeometryFromGeoJSON(TestCase):
    """Test extract_geometry_from_geojson function."""

    def test_extract_from_feature(self):
        """Test extracting geometry from a GeoJSON Feature."""
        feature = {
            "type": "Feature",
            "properties": {"name": "Test"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-122.5, 45.5],
                    [-122.4, 45.5],
                    [-122.4, 45.6],
                    [-122.5, 45.6],
                    [-122.5, 45.5]
                ]]
            }
        }

        geom = extract_geometry_from_geojson(feature)

        self.assertEqual(geom.geom_type, "Polygon")
        self.assertAlmostEqual(geom.bounds[0], -122.5)
        self.assertAlmostEqual(geom.bounds[1], 45.5)
        self.assertAlmostEqual(geom.bounds[2], -122.4)
        self.assertAlmostEqual(geom.bounds[3], 45.6)

    def test_extract_from_bare_geometry(self):
        """Test extracting from a bare GeoJSON geometry."""
        geometry = {
            "type": "Point",
            "coordinates": [-122.5, 45.5]
        }

        geom = extract_geometry_from_geojson(geometry)

        self.assertEqual(geom.geom_type, "Point")
        self.assertEqual(geom.x, -122.5)
        self.assertEqual(geom.y, 45.5)

    def test_extract_multipolygon(self):
        """Test extracting a MultiPolygon geometry."""
        multi = {
            "type": "MultiPolygon",
            "coordinates": [
                [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                [[[2, 2], [3, 2], [3, 3], [2, 3], [2, 2]]]
            ]
        }

        geom = extract_geometry_from_geojson(multi)

        self.assertEqual(geom.geom_type, "MultiPolygon")
        self.assertEqual(len(list(geom.geoms)), 2)

    def test_extract_linestring(self):
        """Test extracting a LineString geometry."""
        line = {
            "type": "LineString",
            "coordinates": [
                [-122.5, 45.5],
                [-122.4, 45.6],
                [-122.3, 45.7]
            ]
        }

        geom = extract_geometry_from_geojson(line)

        self.assertEqual(geom.geom_type, "LineString")
        self.assertEqual(len(geom.coords), 3)

    def test_extract_with_holes(self):
        """Test extracting a polygon with holes."""
        poly_with_hole = {
            "type": "Polygon",
            "coordinates": [
                # Exterior ring
                [[0, 0], [4, 0], [4, 4], [0, 4], [0, 0]],
                # Hole
                [[1, 1], [1, 3], [3, 3], [3, 1], [1, 1]]
            ]
        }

        geom = extract_geometry_from_geojson(poly_with_hole)

        self.assertEqual(geom.geom_type, "Polygon")
        self.assertEqual(len(list(geom.interiors)), 1)

        # Check area accounts for hole
        total_area = 4 * 4  # Exterior
        hole_area = 2 * 2    # Interior hole
        # Note: actual area will be in projected units
        exterior_poly = Polygon(poly_with_hole["coordinates"][0])
        hole_poly = Polygon(poly_with_hole["coordinates"][1])

        exterior_area = calculate_polygon_area(exterior_poly)
        hole_area_calc = calculate_polygon_area(hole_poly)
        geom_area = calculate_polygon_area(geom)

        # Area with hole should be less than exterior
        self.assertLess(geom_area, exterior_area)

    def test_extract_feature_collection_error(self):
        """Test that FeatureCollection raises appropriate error."""
        collection = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [0, 0]
                    }
                }
            ]
        }

        # Should raise an error as it's not a single geometry
        with self.assertRaises(Exception):
            extract_geometry_from_geojson(collection)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])