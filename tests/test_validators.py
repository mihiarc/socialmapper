"""Tests for SocialMapper input validation functions."""

import pytest

from socialmapper.validators import (
    validate_coordinates,
    validate_travel_time,
    validate_travel_mode,
    validate_export_format,
    validate_location_input
)


class TestValidateCoordinates:
    """Test coordinate validation function."""

    def test_valid_coordinates_center(self):
        """Test valid coordinates at center of ranges."""
        assert validate_coordinates(0.0, 0.0) is True
        assert validate_coordinates(45.5, -122.6) is True

    def test_valid_coordinates_boundaries(self):
        """Test valid coordinates at exact boundaries."""
        # Latitude boundaries
        assert validate_coordinates(90.0, 0.0) is True
        assert validate_coordinates(-90.0, 0.0) is True

        # Longitude boundaries
        assert validate_coordinates(0.0, 180.0) is True
        assert validate_coordinates(0.0, -180.0) is True

        # All corners
        assert validate_coordinates(90.0, 180.0) is True
        assert validate_coordinates(90.0, -180.0) is True
        assert validate_coordinates(-90.0, 180.0) is True
        assert validate_coordinates(-90.0, -180.0) is True

    def test_invalid_coordinates_latitude_high(self):
        """Test invalid coordinates with latitude too high."""
        assert validate_coordinates(90.1, 0.0) is False
        assert validate_coordinates(100.0, 0.0) is False
        assert validate_coordinates(180.0, 0.0) is False

    def test_invalid_coordinates_latitude_low(self):
        """Test invalid coordinates with latitude too low."""
        assert validate_coordinates(-90.1, 0.0) is False
        assert validate_coordinates(-100.0, 0.0) is False
        assert validate_coordinates(-180.0, 0.0) is False

    def test_invalid_coordinates_longitude_high(self):
        """Test invalid coordinates with longitude too high."""
        assert validate_coordinates(0.0, 180.1) is False
        assert validate_coordinates(0.0, 200.0) is False
        assert validate_coordinates(0.0, 360.0) is False

    def test_invalid_coordinates_longitude_low(self):
        """Test invalid coordinates with longitude too low."""
        assert validate_coordinates(0.0, -180.1) is False
        assert validate_coordinates(0.0, -200.0) is False
        assert validate_coordinates(0.0, -360.0) is False

    def test_invalid_coordinates_both_invalid(self):
        """Test coordinates with both latitude and longitude invalid."""
        assert validate_coordinates(200.0, 300.0) is False
        assert validate_coordinates(-200.0, -300.0) is False

    def test_coordinates_precision(self):
        """Test coordinate validation with high precision."""
        # Very precise valid coordinates
        assert validate_coordinates(89.999999, 179.999999) is True
        assert validate_coordinates(-89.999999, -179.999999) is True

        # Just barely invalid
        assert validate_coordinates(90.000001, 0.0) is False
        assert validate_coordinates(0.0, 180.000001) is False

    def test_coordinates_extreme_precision(self):
        """Test coordinates with extreme decimal precision."""
        lat = 45.123456789012345
        lon = -122.987654321098765
        assert validate_coordinates(lat, lon) is True

    def test_coordinates_zero_handling(self):
        """Test coordinate validation handles zeros correctly."""
        assert validate_coordinates(0.0, 0.0) is True
        assert validate_coordinates(-0.0, -0.0) is True

    def test_coordinates_type_handling(self):
        """Test that function handles different numeric types."""
        # Integers
        assert validate_coordinates(45, -122) is True
        assert validate_coordinates(91, 0) is False

        # Floats
        assert validate_coordinates(45.5, -122.6) is True

        # Mixed types
        assert validate_coordinates(45, -122.6) is True
        assert validate_coordinates(45.5, -122) is True


class TestValidateTravelTime:
    """Test travel time validation function."""

    def test_valid_travel_time_boundaries(self):
        """Test valid travel times at boundaries."""
        # Should not raise
        validate_travel_time(1)
        validate_travel_time(120)

    def test_valid_travel_time_middle(self):
        """Test valid travel times in middle range."""
        valid_times = [5, 10, 15, 20, 30, 45, 60, 90]

        for time in valid_times:
            validate_travel_time(time)  # Should not raise

    def test_invalid_travel_time_zero(self):
        """Test invalid travel time of zero."""
        with pytest.raises(ValueError, match="Travel time must be between 1 and 120"):
            validate_travel_time(0)

    def test_invalid_travel_time_negative(self):
        """Test invalid negative travel times."""
        invalid_times = [-1, -5, -10, -100]

        for time in invalid_times:
            with pytest.raises(ValueError, match="Travel time must be between 1 and 120"):
                validate_travel_time(time)

    def test_invalid_travel_time_high(self):
        """Test invalid travel times above maximum."""
        invalid_times = [121, 150, 200, 500, 1000]

        for time in invalid_times:
            with pytest.raises(ValueError, match="Travel time must be between 1 and 120"):
                validate_travel_time(time)

    def test_travel_time_error_message_format(self):
        """Test that error messages contain the actual invalid value."""
        with pytest.raises(ValueError) as excinfo:
            validate_travel_time(150)

        assert "150" in str(excinfo.value)
        assert "Travel time must be between 1 and 120 minutes" in str(excinfo.value)


class TestValidateTravelMode:
    """Test travel mode validation function."""

    def test_valid_travel_modes(self):
        """Test all valid travel modes."""
        valid_modes = ["drive", "walk", "bike"]

        for mode in valid_modes:
            validate_travel_mode(mode)  # Should not raise

    def test_invalid_travel_modes(self):
        """Test various invalid travel modes."""
        invalid_modes = [
            "fly", "swim", "run", "car", "driving", "walking", "biking",
            "transit", "public_transport", "helicopter", "boat"
        ]

        for mode in invalid_modes:
            with pytest.raises(ValueError, match="Travel mode must be"):
                validate_travel_mode(mode)

    def test_travel_mode_case_sensitivity(self):
        """Test that travel mode validation is case sensitive."""
        invalid_cases = ["DRIVE", "WALK", "BIKE", "Drive", "Walk", "Bike"]

        for mode in invalid_cases:
            with pytest.raises(ValueError, match="Travel mode must be"):
                validate_travel_mode(mode)

    def test_travel_mode_whitespace_handling(self):
        """Test travel mode validation with whitespace."""
        invalid_modes = [" drive", "walk ", " bike ", "drive\n", "\twalk"]

        for mode in invalid_modes:
            with pytest.raises(ValueError, match="Travel mode must be"):
                validate_travel_mode(mode)

    def test_empty_travel_mode(self):
        """Test empty travel mode string."""
        with pytest.raises(ValueError, match="Travel mode must be"):
            validate_travel_mode("")

    def test_travel_mode_error_message_format(self):
        """Test that error messages contain the actual invalid value."""
        with pytest.raises(ValueError) as excinfo:
            validate_travel_mode("fly")

        assert "fly" in str(excinfo.value)
        assert "['drive', 'walk', 'bike']" in str(excinfo.value)


class TestValidateExportFormat:
    """Test export format validation function."""

    def test_valid_export_formats(self):
        """Test all valid export formats."""
        valid_formats = ["png", "pdf", "svg", "geojson", "shapefile"]

        for fmt in valid_formats:
            validate_export_format(fmt)  # Should not raise

    def test_invalid_export_formats(self):
        """Test various invalid export formats."""
        invalid_formats = [
            "jpg", "jpeg", "gif", "bmp", "tiff", "webp",
            "doc", "docx", "txt", "csv", "xlsx", "html",
            "kml", "kmz", "gml", "json"
        ]

        for fmt in invalid_formats:
            with pytest.raises(ValueError, match="Export format must be one of"):
                validate_export_format(fmt)

    def test_export_format_case_sensitivity(self):
        """Test that export format validation is case sensitive."""
        invalid_cases = ["PNG", "PDF", "SVG", "GEOJSON", "SHAPEFILE"]

        for fmt in invalid_cases:
            with pytest.raises(ValueError, match="Export format must be one of"):
                validate_export_format(fmt)

    def test_export_format_with_dots(self):
        """Test export formats with file extensions."""
        invalid_formats = [".png", ".pdf", ".svg", ".geojson", ".shp"]

        for fmt in invalid_formats:
            with pytest.raises(ValueError, match="Export format must be one of"):
                validate_export_format(fmt)

    def test_empty_export_format(self):
        """Test empty export format string."""
        with pytest.raises(ValueError, match="Export format must be one of"):
            validate_export_format("")

    def test_export_format_whitespace(self):
        """Test export format with whitespace."""
        invalid_formats = [" png", "pdf ", " svg ", "geojson\n", "\tpng"]

        for fmt in invalid_formats:
            with pytest.raises(ValueError, match="Export format must be one of"):
                validate_export_format(fmt)

    def test_export_format_error_message_content(self):
        """Test that error message contains valid formats list."""
        with pytest.raises(ValueError) as excinfo:
            validate_export_format("invalid")

        error_message = str(excinfo.value)
        assert "invalid" in error_message
        assert "png" in error_message
        assert "pdf" in error_message
        assert "svg" in error_message
        assert "geojson" in error_message
        assert "shapefile" in error_message


class TestValidateLocationInput:
    """Test location input validation function."""

    def test_valid_polygon_only(self):
        """Test valid input with polygon only."""
        polygon = {"type": "Feature", "geometry": {"type": "Polygon"}}

        validate_location_input(polygon=polygon, location=None)  # Should not raise

    def test_valid_location_only(self):
        """Test valid input with location only."""
        location = (45.5, -122.6)

        validate_location_input(polygon=None, location=location)  # Should not raise

    def test_both_none_invalid(self):
        """Test that providing neither polygon nor location is invalid."""
        with pytest.raises(ValueError, match="Must provide either polygon or location"):
            validate_location_input(polygon=None, location=None)

    def test_both_provided_invalid(self):
        """Test that providing both polygon and location is invalid."""
        polygon = {"type": "Feature"}
        location = (45.5, -122.6)

        with pytest.raises(ValueError, match="Provide either polygon or location, not both"):
            validate_location_input(polygon=polygon, location=location)

    def test_polygon_various_types(self):
        """Test validation with various polygon types."""
        valid_polygons = [
            {"type": "Feature"},
            {"type": "Polygon"},
            {"geometry": {"type": "Polygon"}},
            {},  # Empty dict is still valid for this validator
            {"custom": "data"}
        ]

        for polygon in valid_polygons:
            validate_location_input(polygon=polygon, location=None)  # Should not raise

    def test_location_various_types(self):
        """Test validation with various location types."""
        valid_locations = [
            (0, 0),
            (45.5, -122.6),
            (-90, -180),
            (90, 180)
        ]

        for location in valid_locations:
            validate_location_input(polygon=None, location=location)  # Should not raise

    def test_falsy_values_handling(self):
        """Test handling of falsy values that are not None."""
        # Empty dict is considered as provided (not None)
        with pytest.raises(ValueError, match="Provide either polygon or location, not both"):
            validate_location_input(polygon={}, location=(0, 0))

        # Empty tuple is considered as provided
        with pytest.raises(ValueError, match="Provide either polygon or location, not both"):
            validate_location_input(polygon={"test": "data"}, location=())

    def test_default_parameters(self):
        """Test default parameter behavior."""
        # Both default to None
        with pytest.raises(ValueError, match="Must provide either polygon or location"):
            validate_location_input()

    def test_explicit_none_vs_default(self):
        """Test explicit None vs default parameter behavior."""
        location = (45.5, -122.6)

        # These should behave identically
        validate_location_input(polygon=None, location=location)
        validate_location_input(location=location)  # polygon defaults to None


class TestValidationIntegration:
    """Test integration between validation functions."""

    def test_coordinate_validation_consistency(self):
        """Test that coordinate validation is consistent across functions."""
        # These coordinates should be invalid everywhere they're checked
        invalid_coords = [(200, 300), (-200, -300), (91, 0), (0, 181)]

        for lat, lon in invalid_coords:
            assert validate_coordinates(lat, lon) is False

    def test_validation_functions_independence(self):
        """Test that validation functions don't interfere with each other."""
        # Call all validation functions with valid inputs
        validate_coordinates(45.5, -122.6)
        validate_travel_time(15)
        validate_travel_mode("drive")
        validate_export_format("png")
        validate_location_input(polygon={"test": "data"}, location=None)

        # Should still work after other validations
        validate_coordinates(0, 0)
        assert validate_coordinates(200, 300) is False

    def test_error_message_clarity(self):
        """Test that error messages are clear and specific."""
        validation_tests = [
            (lambda: validate_travel_time(0), "Travel time must be between 1 and 120"),
            (lambda: validate_travel_mode("fly"), "Travel mode must be"),
            (lambda: validate_export_format("jpg"), "Export format must be one of"),
            (lambda: validate_location_input(), "Must provide either polygon or location")
        ]

        for test_func, expected_text in validation_tests:
            with pytest.raises(ValueError) as excinfo:
                test_func()
            assert expected_text in str(excinfo.value)

    def test_validation_performance(self):
        """Test that validation functions perform reasonably on repeated calls."""
        import time

        # Test coordinate validation performance
        start_time = time.time()
        for _ in range(1000):
            validate_coordinates(45.5, -122.6)
        coord_time = time.time() - start_time

        # Should complete 1000 validations quickly (< 1 second)
        assert coord_time < 1.0

        # Test other validations
        start_time = time.time()
        for _ in range(1000):
            validate_travel_time(15)
            validate_travel_mode("drive")
            validate_export_format("png")
        other_time = time.time() - start_time

        assert other_time < 1.0