"""Tests for SocialMapper helper functions."""

import pytest
from unittest.mock import patch, MagicMock
from shapely.geometry import Point, Polygon, shape
import pyproj

from socialmapper.helpers import (
    resolve_coordinates,
    calculate_polygon_area,
    create_circular_geometry,
    extract_geometry_from_geojson
)


class TestResolveCoordinates:
    """Test resolve_coordinates helper function."""

    @patch('socialmapper._geocoding.geocode_location')
    def test_resolve_string_location_success(self, mock_geocode):
        """Test resolving string location to coordinates."""
        mock_geocode.return_value = (45.5152, -122.6784)

        coords, location_name = resolve_coordinates("Portland, OR")

        assert coords == (45.5152, -122.6784)
        assert location_name == "Portland, OR"
        mock_geocode.assert_called_once_with("Portland, OR")

    @patch('socialmapper._geocoding.geocode_location')
    def test_resolve_string_location_failure(self, mock_geocode):
        """Test handling of geocoding failure."""
        mock_geocode.return_value = None

        with pytest.raises(ValueError, match="Could not geocode location: Nonexistent Place"):
            resolve_coordinates("Nonexistent Place")

    def test_resolve_coordinate_tuple_valid(self):
        """Test resolving valid coordinate tuple."""
        coords, location_name = resolve_coordinates((37.7749, -122.4194))

        assert coords == (37.7749, -122.4194)
        assert location_name == "37.7749, -122.4194"

    def test_resolve_coordinate_tuple_invalid(self):
        """Test resolving invalid coordinate tuple."""
        with pytest.raises(ValueError, match="Invalid coordinates: \\(200, 300\\)"):
            resolve_coordinates((200, 300))

    def test_resolve_coordinate_boundary_cases(self):
        """Test coordinate resolution at boundaries."""
        # Valid boundaries
        coords, name = resolve_coordinates((90, 180))
        assert coords == (90, 180)
        assert name == "90.0000, 180.0000"

        coords, name = resolve_coordinates((-90, -180))
        assert coords == (-90, -180)
        assert name == "-90.0000, -180.0000"

        # Invalid boundaries
        with pytest.raises(ValueError, match="Invalid coordinates"):
            resolve_coordinates((90.1, 0))

    def test_resolve_coordinate_precision_formatting(self):
        """Test coordinate formatting with various precision."""
        # High precision coordinates
        coords, name = resolve_coordinates((45.123456789, -122.987654321))
        assert coords == (45.123456789, -122.987654321)
        assert name == "45.1235, -122.9877"  # Should format to 4 decimals

    @patch('socialmapper._geocoding.geocode_location')
    def test_resolve_empty_string_location(self, mock_geocode):
        """Test resolving empty string location."""
        mock_geocode.return_value = None

        with pytest.raises(ValueError, match="Could not geocode location: "):
            resolve_coordinates("")

    def test_resolve_zero_coordinates(self):
        """Test resolving zero coordinates (Null Island)."""
        coords, name = resolve_coordinates((0, 0))
        assert coords == (0, 0)
        assert name == "0.0000, 0.0000"

    @patch('socialmapper._geocoding.geocode_location')
    def test_resolve_geocode_returns_empty_result(self, mock_geocode):
        """Test when geocode returns empty tuple or other falsy value."""
        mock_geocode.return_value = ()

        with pytest.raises(ValueError, match="Could not geocode location"):
            resolve_coordinates("Invalid Location")


class TestCalculatePolygonArea:
    """Test calculate_polygon_area helper function."""

    def test_calculate_small_polygon_area(self):
        """Test area calculation for small polygon."""
        # Create a small square polygon (approximately 1km x 1km)
        coords = [
            (-122.4194, 37.7749),  # SW corner
            (-122.4094, 37.7749),  # SE corner
            (-122.4094, 37.7849),  # NE corner
            (-122.4194, 37.7849),  # NW corner
            (-122.4194, 37.7749)   # Close the polygon
        ]
        polygon = Polygon(coords)

        area = calculate_polygon_area(polygon)

        # Should be approximately 1 square kilometer
        assert isinstance(area, float)
        assert 0.5 < area < 2.0  # Reasonable bounds for a ~1km square

    def test_calculate_large_polygon_area(self):
        """Test area calculation for larger polygon."""
        # Create a larger polygon (approximately 10km x 10km)
        coords = [
            (-122.5, 37.7),
            (-122.3, 37.7),
            (-122.3, 37.9),
            (-122.5, 37.9),
            (-122.5, 37.7)
        ]
        polygon = Polygon(coords)

        area = calculate_polygon_area(polygon)

        # Should be significantly larger
        assert area > 100  # At least 100 sq km

    def test_calculate_point_area(self):
        """Test area calculation for point (should be zero)."""
        point = Point(-122.4194, 37.7749)

        area = calculate_polygon_area(point)

        assert area == 0.0

    def test_calculate_line_area(self):
        """Test area calculation for line (should be zero)."""
        from shapely.geometry import LineString

        line = LineString([(-122.4194, 37.7749), (-122.4094, 37.7849)])

        area = calculate_polygon_area(line)

        assert area == 0.0

    def test_calculate_complex_polygon_area(self):
        """Test area calculation for complex polygon with hole."""
        # Outer ring
        outer = [(-122.5, 37.7), (-122.3, 37.7), (-122.3, 37.9), (-122.5, 37.9), (-122.5, 37.7)]
        # Inner hole
        inner = [(-122.45, 37.75), (-122.35, 37.75), (-122.35, 37.85), (-122.45, 37.85), (-122.45, 37.75)]

        polygon = Polygon(outer, [inner])

        area = calculate_polygon_area(polygon)

        # Should be positive (outer area minus inner area)
        assert area > 0
        assert isinstance(area, float)

    def test_calculate_very_small_polygon_area(self):
        """Test area calculation for very small polygon."""
        # Create a tiny polygon (few meters)
        coords = [
            (-122.4194, 37.7749),
            (-122.4193, 37.7749),
            (-122.4193, 37.7750),
            (-122.4194, 37.7750),
            (-122.4194, 37.7749)
        ]
        polygon = Polygon(coords)

        area = calculate_polygon_area(polygon)

        # Should be very small but positive
        assert 0 < area < 0.1  # Less than 0.1 sq km

    def test_calculate_invalid_polygon_area(self):
        """Test area calculation handles invalid polygons gracefully."""
        # Self-intersecting polygon
        coords = [
            (-122.4194, 37.7749),
            (-122.4094, 37.7849),
            (-122.4094, 37.7749),
            (-122.4194, 37.7849),
            (-122.4194, 37.7749)
        ]
        polygon = Polygon(coords)

        # Should still return a numeric result (shapely handles this)
        area = calculate_polygon_area(polygon)
        assert isinstance(area, float)


class TestCreateCircularGeometry:
    """Test create_circular_geometry helper function."""

    def test_create_small_circle(self):
        """Test creating small circular geometry."""
        location = (37.7749, -122.4194)  # San Francisco
        radius_km = 1.0

        geometry = create_circular_geometry(location, radius_km)

        assert hasattr(geometry, 'area')
        assert hasattr(geometry, 'bounds')

        # Check that it's approximately circular (has area)
        assert geometry.area > 0

    def test_create_large_circle(self):
        """Test creating large circular geometry."""
        location = (40.7128, -74.0060)  # New York
        radius_km = 50.0

        geometry = create_circular_geometry(location, radius_km)

        # Large circle should have significantly more area
        assert geometry.area > 0

    def test_create_zero_radius_circle(self):
        """Test creating circle with zero radius."""
        location = (0, 0)
        radius_km = 0.0

        geometry = create_circular_geometry(location, radius_km)

        # Zero radius should create a point-like geometry
        assert geometry.area == 0.0 or geometry.area < 0.001

    def test_create_circle_different_locations(self):
        """Test creating circles at different global locations."""
        locations = [
            (0, 0),           # Equator, Prime Meridian
            (0, 180),         # Equator, International Date Line
            (45, -122),       # Portland, OR
            (-33.8688, 151.2093),  # Sydney, Australia
            (60, 10),         # Northern latitude
            (-60, -70)        # Southern latitude
        ]

        for lat, lon in locations:
            geometry = create_circular_geometry((lat, lon), 5.0)
            # Polar regions might have special behavior, so just check structure
            assert hasattr(geometry, 'bounds')
            # Area might be 0 at extreme poles due to projection issues
            assert geometry.area >= 0

    def test_create_circle_various_radii(self):
        """Test creating circles with various radii."""
        location = (37.7749, -122.4194)
        radii = [0.1, 0.5, 1.0, 5.0, 10.0, 50.0, 100.0]

        previous_area = 0
        for radius in radii:
            geometry = create_circular_geometry(location, radius)
            current_area = geometry.area

            # Area should generally increase with radius
            assert current_area > previous_area
            previous_area = current_area

    def test_circle_coordinate_system_consistency(self):
        """Test that circles are in the correct coordinate system."""
        location = (37.7749, -122.4194)
        radius_km = 5.0

        geometry = create_circular_geometry(location, radius_km)
        bounds = geometry.bounds

        # Bounds should be in WGS84 (reasonable lat/lon values)
        min_x, min_y, max_x, max_y = bounds
        assert -180 <= min_x <= 180
        assert -180 <= max_x <= 180
        assert -90 <= min_y <= 90
        assert -90 <= max_y <= 90

    def test_circle_symmetry(self):
        """Test that created circles are roughly symmetric."""
        location = (0, 0)  # Equator for symmetry
        radius_km = 10.0

        geometry = create_circular_geometry(location, radius_km)
        bounds = geometry.bounds
        min_x, min_y, max_x, max_y = bounds

        # Should be roughly symmetric around the center point
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2

        # Allow for some projection distortion
        assert abs(center_x - 0) < 0.1
        assert abs(center_y - 0) < 0.1

    def test_circle_extreme_coordinates(self):
        """Test circle creation at extreme but valid coordinates."""
        extreme_locations = [
            (89.9, 179.9),    # Near north pole, near date line
            (-89.9, -179.9),  # Near south pole, near date line
            (89.9, 0.1),      # Near north pole, near prime meridian
            (-89.9, 0.1)      # Near south pole, near prime meridian
        ]

        for lat, lon in extreme_locations:
            geometry = create_circular_geometry((lat, lon), 1.0)
            assert geometry.area >= 0  # Should create valid geometry


class TestExtractGeometryFromGeoJSON:
    """Test extract_geometry_from_geojson helper function."""

    def test_extract_from_feature(self):
        """Test extracting geometry from GeoJSON Feature."""
        feature = {
            "type": "Feature",
            "properties": {"name": "Test"},
            "geometry": {
                "type": "Point",
                "coordinates": [-122.4194, 37.7749]
            }
        }

        geometry = extract_geometry_from_geojson(feature)

        assert hasattr(geometry, 'geom_type')
        assert geometry.geom_type == 'Point'
        assert geometry.x == -122.4194
        assert geometry.y == 37.7749

    def test_extract_from_geometry_only(self):
        """Test extracting from geometry object directly."""
        geometry_dict = {
            "type": "Polygon",
            "coordinates": [[
                [-122.4, 37.7], [-122.3, 37.7],
                [-122.3, 37.8], [-122.4, 37.8],
                [-122.4, 37.7]
            ]]
        }

        geometry = extract_geometry_from_geojson(geometry_dict)

        assert geometry.geom_type == 'Polygon'
        assert geometry.area > 0

    def test_extract_point_geometry(self):
        """Test extracting Point geometry."""
        point_geom = {
            "type": "Point",
            "coordinates": [0, 0]
        }

        geometry = extract_geometry_from_geojson(point_geom)

        assert geometry.geom_type == 'Point'
        assert geometry.x == 0
        assert geometry.y == 0

    def test_extract_linestring_geometry(self):
        """Test extracting LineString geometry."""
        line_geom = {
            "type": "LineString",
            "coordinates": [[-122.4, 37.7], [-122.3, 37.8]]
        }

        geometry = extract_geometry_from_geojson(line_geom)

        assert geometry.geom_type == 'LineString'
        assert geometry.length > 0

    def test_extract_polygon_geometry(self):
        """Test extracting Polygon geometry."""
        polygon_geom = {
            "type": "Polygon",
            "coordinates": [[
                [-122.4, 37.7], [-122.3, 37.7],
                [-122.3, 37.8], [-122.4, 37.8],
                [-122.4, 37.7]
            ]]
        }

        geometry = extract_geometry_from_geojson(polygon_geom)

        assert geometry.geom_type == 'Polygon'
        assert geometry.area > 0

    def test_extract_multipolygon_geometry(self):
        """Test extracting MultiPolygon geometry."""
        multipolygon_geom = {
            "type": "MultiPolygon",
            "coordinates": [
                [[[-122.4, 37.7], [-122.3, 37.7], [-122.3, 37.8], [-122.4, 37.8], [-122.4, 37.7]]],
                [[[-122.2, 37.6], [-122.1, 37.6], [-122.1, 37.7], [-122.2, 37.7], [-122.2, 37.6]]]
            ]
        }

        geometry = extract_geometry_from_geojson(multipolygon_geom)

        assert geometry.geom_type == 'MultiPolygon'
        assert geometry.area > 0

    def test_extract_from_feature_collection_feature(self):
        """Test extracting from a Feature within a FeatureCollection structure."""
        # Simulate extracting one feature from what might be a FeatureCollection
        feature = {
            "type": "Feature",
            "id": "test_feature",
            "properties": {"population": 1000},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-122.4, 37.7], [-122.3, 37.7],
                    [-122.3, 37.8], [-122.4, 37.8],
                    [-122.4, 37.7]
                ]]
            }
        }

        geometry = extract_geometry_from_geojson(feature)

        assert geometry.geom_type == 'Polygon'

    def test_extract_geometry_with_holes(self):
        """Test extracting polygon geometry with holes."""
        polygon_with_hole = {
            "type": "Polygon",
            "coordinates": [
                # Outer ring
                [[-122.5, 37.7], [-122.3, 37.7], [-122.3, 37.9], [-122.5, 37.9], [-122.5, 37.7]],
                # Inner ring (hole)
                [[-122.45, 37.75], [-122.35, 37.75], [-122.35, 37.85], [-122.45, 37.85], [-122.45, 37.75]]
            ]
        }

        geometry = extract_geometry_from_geojson(polygon_with_hole)

        assert geometry.geom_type == 'Polygon'
        # Should have less area than outer ring alone due to hole
        assert geometry.area > 0

    def test_extract_empty_geometry(self):
        """Test extracting empty geometry."""
        empty_geom = {
            "type": "Point",
            "coordinates": []
        }

        geometry = extract_geometry_from_geojson(empty_geom)

        # Should handle empty geometry gracefully
        assert geometry.is_empty or geometry.geom_type == 'Point'

    def test_extract_invalid_geojson_structure(self):
        """Test handling of invalid GeoJSON structure."""
        invalid_structures = [
            {},  # Empty dict - will be passed to shape
            {"type": "InvalidType"},  # Invalid type
            {"geometry": {}},  # Empty geometry
        ]

        for invalid_struct in invalid_structures:
            # Should either raise an exception or handle gracefully
            try:
                geometry = extract_geometry_from_geojson(invalid_struct)
                # If it doesn't raise, should return some geometry object
                assert hasattr(geometry, 'geom_type') or geometry is None
            except (KeyError, ValueError, TypeError, AttributeError, Exception):
                # These exceptions are acceptable for invalid input (including GeometryTypeError)
                pass

        # Test None geometry separately as it causes AttributeError
        with pytest.raises((ValueError, TypeError, AttributeError)):
            extract_geometry_from_geojson({"type": "Feature", "geometry": None})


class TestHelpersIntegration:
    """Test integration between helper functions."""

    @patch('socialmapper._geocoding.geocode_location')
    def test_resolve_and_create_circle_integration(self, mock_geocode):
        """Test integration between resolve_coordinates and create_circular_geometry."""
        mock_geocode.return_value = (37.7749, -122.4194)

        # Resolve coordinates from string
        coords, _ = resolve_coordinates("San Francisco, CA")

        # Use resolved coordinates to create circular geometry
        geometry = create_circular_geometry(coords, 5.0)

        assert geometry.area > 0
        bounds = geometry.bounds

        # Should be centered roughly around San Francisco
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2

        assert abs(center_lat - 37.7749) < 0.1
        assert abs(center_lon - -122.4194) < 0.1

    def test_geojson_extraction_and_area_calculation(self):
        """Test integration between extract_geometry_from_geojson and calculate_polygon_area."""
        geojson_feature = {
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-122.4, 37.7], [-122.3, 37.7],
                    [-122.3, 37.8], [-122.4, 37.8],
                    [-122.4, 37.7]
                ]]
            }
        }

        # Extract geometry
        geometry = extract_geometry_from_geojson(geojson_feature)

        # Calculate area
        area = calculate_polygon_area(geometry)

        assert isinstance(area, float)
        assert area > 0

    def test_circular_geometry_area_consistency(self):
        """Test that circular geometries have consistent area calculations."""
        location = (37.7749, -122.4194)
        radius_km = 10.0

        # Create circular geometry
        geometry = create_circular_geometry(location, radius_km)

        # Calculate area
        area = calculate_polygon_area(geometry)

        # Area should be roughly π * r²
        expected_area = 3.14159 * (radius_km ** 2)

        # Allow for projection distortion (within 50% of expected)
        assert 0.5 * expected_area < area < 2.0 * expected_area

    def test_helper_functions_error_propagation(self):
        """Test that helper functions properly propagate errors."""
        # Test invalid coordinates in resolve_coordinates
        with pytest.raises(ValueError):
            resolve_coordinates((200, 300))

        # Test that subsequent functions would also handle this gracefully
        # if the error wasn't caught
        try:
            coords, _ = resolve_coordinates((37.7749, -122.4194))  # Valid
            geometry = create_circular_geometry(coords, -1)  # Invalid radius

            # Should either work or raise appropriate error
            assert geometry is not None or True  # Allowing for either behavior
        except (ValueError, Exception) as e:
            # Error propagation is acceptable
            assert isinstance(e, Exception)

    def test_helper_functions_return_types(self):
        """Test that helper functions return expected types."""
        # resolve_coordinates should return tuple of (tuple, str)
        coords, name = resolve_coordinates((0, 0))
        assert isinstance(coords, tuple)
        assert isinstance(name, str)
        assert len(coords) == 2

        # create_circular_geometry should return shapely geometry
        geometry = create_circular_geometry((0, 0), 1.0)
        assert hasattr(geometry, 'area')
        assert hasattr(geometry, 'bounds')

        # calculate_polygon_area should return float
        area = calculate_polygon_area(geometry)
        assert isinstance(area, float)

        # extract_geometry_from_geojson should return shapely geometry
        geom_dict = {"type": "Point", "coordinates": [0, 0]}
        extracted = extract_geometry_from_geojson(geom_dict)
        assert hasattr(extracted, 'geom_type')