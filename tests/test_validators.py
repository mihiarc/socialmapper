"""Comprehensive tests for socialmapper.validators module.

Tests all validation functions:
- validate_coordinates
- validate_travel_time
- validate_travel_mode
- validate_export_format
- validate_report_format
- validate_location_input
"""

from unittest import TestCase

import pytest

from socialmapper.constants import (
    MAX_LATITUDE,
    MAX_LONGITUDE,
    MAX_TRAVEL_TIME,
    MIN_LATITUDE,
    MIN_LONGITUDE,
    MIN_TRAVEL_TIME,
    VALID_EXPORT_FORMATS,
    VALID_REPORT_FORMATS,
    VALID_TRAVEL_MODES,
)
from socialmapper.validators import (
    validate_coordinates,
    validate_export_format,
    validate_location_input,
    validate_report_format,
    validate_travel_mode,
    validate_travel_time,
)


class TestValidateCoordinates(TestCase):
    """Test validate_coordinates function."""

    def test_valid_coordinates(self):
        """Test validation of valid coordinates."""
        # Common US locations
        self.assertTrue(validate_coordinates(35.9132, -79.0558))  # Chapel Hill
        self.assertTrue(validate_coordinates(40.7128, -74.0060))  # NYC
        self.assertTrue(validate_coordinates(34.0522, -118.2437))  # LA
        self.assertTrue(validate_coordinates(41.8781, -87.6298))  # Chicago

        # Boundary cases (valid)
        self.assertTrue(validate_coordinates(MIN_LATITUDE, 0))
        self.assertTrue(validate_coordinates(MAX_LATITUDE, 0))
        self.assertTrue(validate_coordinates(0, MIN_LONGITUDE))
        self.assertTrue(validate_coordinates(0, MAX_LONGITUDE))

        # Edge of valid range
        self.assertTrue(validate_coordinates(-90, 0))
        self.assertTrue(validate_coordinates(90, 0))
        self.assertTrue(validate_coordinates(0, -180))
        self.assertTrue(validate_coordinates(0, 180))

    def test_invalid_coordinates(self):
        """Test validation of invalid coordinates."""
        # Latitude out of range
        self.assertFalse(validate_coordinates(91, 0))
        self.assertFalse(validate_coordinates(-91, 0))
        self.assertFalse(validate_coordinates(100, 0))
        self.assertFalse(validate_coordinates(-100, 0))

        # Longitude out of range
        self.assertFalse(validate_coordinates(0, 181))
        self.assertFalse(validate_coordinates(0, -181))
        self.assertFalse(validate_coordinates(0, 200))
        self.assertFalse(validate_coordinates(0, -200))

        # Both out of range
        self.assertFalse(validate_coordinates(91, 181))
        self.assertFalse(validate_coordinates(-91, -181))

    def test_extreme_coordinates(self):
        """Test validation at extreme coordinate values."""
        # North Pole
        self.assertTrue(validate_coordinates(90, 0))

        # South Pole
        self.assertTrue(validate_coordinates(-90, 0))

        # International Date Line
        self.assertTrue(validate_coordinates(0, 180))
        self.assertTrue(validate_coordinates(0, -180))

        # Prime Meridian and Equator
        self.assertTrue(validate_coordinates(0, 0))

    def test_coordinate_types(self):
        """Test validation with different numeric types."""
        # Integers
        self.assertTrue(validate_coordinates(40, -74))

        # Floats
        self.assertTrue(validate_coordinates(40.7, -74.0))

        # High precision
        self.assertTrue(validate_coordinates(40.712784, -74.006058))


class TestValidateTravelTime(TestCase):
    """Test validate_travel_time function."""

    def test_valid_travel_times(self):
        """Test validation of valid travel times."""
        # Minimum valid time
        validate_travel_time(MIN_TRAVEL_TIME)

        # Maximum valid time
        validate_travel_time(MAX_TRAVEL_TIME)

        # Common values
        validate_travel_time(5)
        validate_travel_time(10)
        validate_travel_time(15)
        validate_travel_time(30)
        validate_travel_time(45)

        # All valid values
        for time in range(MIN_TRAVEL_TIME, MAX_TRAVEL_TIME + 1):
            validate_travel_time(time)

    def test_invalid_travel_times(self):
        """Test validation of invalid travel times."""
        # Below minimum
        with self.assertRaises(ValueError) as context:
            validate_travel_time(MIN_TRAVEL_TIME - 1)
        self.assertIn("Travel time must be between", str(context.exception))

        with self.assertRaises(ValueError):
            validate_travel_time(0)

        with self.assertRaises(ValueError):
            validate_travel_time(-5)

        # Above maximum
        with self.assertRaises(ValueError) as context:
            validate_travel_time(MAX_TRAVEL_TIME + 1)
        self.assertIn("Travel time must be between", str(context.exception))

        with self.assertRaises(ValueError):
            validate_travel_time(200)

        with self.assertRaises(ValueError):
            validate_travel_time(1000)

    def test_travel_time_error_messages(self):
        """Test error messages for invalid travel times."""
        with self.assertRaises(ValueError) as context:
            validate_travel_time(0)

        error_msg = str(context.exception)
        self.assertIn(str(MIN_TRAVEL_TIME), error_msg)
        self.assertIn(str(MAX_TRAVEL_TIME), error_msg)
        self.assertIn("0", error_msg)


class TestValidateTravelMode(TestCase):
    """Test validate_travel_mode function."""

    def test_valid_travel_modes(self):
        """Test validation of valid travel modes."""
        # All valid modes from constants
        for mode in VALID_TRAVEL_MODES:
            validate_travel_mode(mode)

        # Common modes
        validate_travel_mode("drive")
        validate_travel_mode("walk")
        validate_travel_mode("bike")

    def test_invalid_travel_modes(self):
        """Test validation of invalid travel modes."""
        invalid_modes = [
            "car",  # Should be "drive"
            "driving",  # Should be "drive"
            "walking",  # Should be "walk"
            "biking",  # Should be "bike"
            "transit",
            "fly",
            "run",
            "invalid",
            "",
            "DRIVE",  # Case sensitive
            "Walk",  # Case sensitive
        ]

        for mode in invalid_modes:
            with self.assertRaises(ValueError) as context:
                validate_travel_mode(mode)
            self.assertIn("Travel mode must be one of", str(context.exception))
            self.assertIn(mode, str(context.exception))

    def test_travel_mode_error_messages(self):
        """Test error messages for invalid travel modes."""
        with self.assertRaises(ValueError) as context:
            validate_travel_mode("invalid_mode")

        error_msg = str(context.exception)
        for valid_mode in VALID_TRAVEL_MODES:
            self.assertIn(valid_mode, error_msg)
        self.assertIn("invalid_mode", error_msg)


class TestValidateExportFormat(TestCase):
    """Test validate_export_format function."""

    def test_valid_export_formats(self):
        """Test validation of valid export formats."""
        # All valid formats from constants
        for format_type in VALID_EXPORT_FORMATS:
            validate_export_format(format_type)

        # Common formats
        if "html" in VALID_EXPORT_FORMATS:
            validate_export_format("html")
        if "png" in VALID_EXPORT_FORMATS:
            validate_export_format("png")
        if "json" in VALID_EXPORT_FORMATS:
            validate_export_format("json")

    def test_invalid_export_formats(self):
        """Test validation of invalid export formats."""
        invalid_formats = [
            "pdf",  # Might not be supported for maps
            "jpg",
            "jpeg",
            "svg",
            "xml",
            "txt",
            "invalid",
            "",
            "HTML",  # Case sensitive
            "Json",  # Case sensitive
        ]

        for format_type in invalid_formats:
            if format_type not in VALID_EXPORT_FORMATS:
                with self.assertRaises(ValueError) as context:
                    validate_export_format(format_type)
                self.assertIn("Export format must be one of", str(context.exception))
                self.assertIn(format_type, str(context.exception))

    def test_export_format_error_messages(self):
        """Test error messages for invalid export formats."""
        with self.assertRaises(ValueError) as context:
            validate_export_format("invalid_format")

        error_msg = str(context.exception)
        for valid_format in VALID_EXPORT_FORMATS:
            self.assertIn(valid_format, error_msg)
        self.assertIn("invalid_format", error_msg)


class TestValidateReportFormat(TestCase):
    """Test validate_report_format function."""

    def test_valid_report_formats(self):
        """Test validation of valid report formats."""
        # All valid formats from constants
        for format_type in VALID_REPORT_FORMATS:
            validate_report_format(format_type)

        # Common formats
        if "html" in VALID_REPORT_FORMATS:
            validate_report_format("html")
        if "pdf" in VALID_REPORT_FORMATS:
            validate_report_format("pdf")
        if "markdown" in VALID_REPORT_FORMATS:
            validate_report_format("markdown")

    def test_invalid_report_formats(self):
        """Test validation of invalid report formats."""
        invalid_formats = [
            "doc",
            "docx",
            "txt",
            "xml",
            "json",  # Might not be a report format
            "csv",  # Might not be a report format
            "invalid",
            "",
            "HTML",  # Case sensitive
            "PDF",  # Case sensitive
        ]

        for format_type in invalid_formats:
            if format_type not in VALID_REPORT_FORMATS:
                with self.assertRaises(ValueError) as context:
                    validate_report_format(format_type)
                self.assertIn("Report format must be one of", str(context.exception))
                self.assertIn(format_type, str(context.exception))

    def test_report_format_error_messages(self):
        """Test error messages for invalid report formats."""
        with self.assertRaises(ValueError) as context:
            validate_report_format("invalid_format")

        error_msg = str(context.exception)
        for valid_format in VALID_REPORT_FORMATS:
            self.assertIn(valid_format, error_msg)
        self.assertIn("invalid_format", error_msg)


class TestValidateLocationInput(TestCase):
    """Test validate_location_input function."""

    def test_valid_polygon_only(self):
        """Test validation with only polygon provided."""
        # Valid: polygon provided, location is None
        polygon = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}
        validate_location_input(polygon=polygon, location=None)

        # Valid: polygon provided, location not specified
        validate_location_input(polygon=polygon)

        # Different polygon types
        validate_location_input(polygon={"type": "Feature", "geometry": {"type": "Polygon"}})
        validate_location_input(polygon={"geometry": {"type": "MultiPolygon"}})

    def test_valid_location_only(self):
        """Test validation with only location provided."""
        # Valid: location provided, polygon is None
        location = (35.9132, -79.0558)
        validate_location_input(polygon=None, location=location)

        # Valid: location provided, polygon not specified
        validate_location_input(location=location)

        # Different location formats
        validate_location_input(location=(40.7128, -74.0060))
        validate_location_input(location=[34.0522, -118.2437])
        validate_location_input(location="Chapel Hill, NC")

    def test_neither_provided(self):
        """Test validation when neither polygon nor location is provided."""
        with self.assertRaises(ValueError) as context:
            validate_location_input()
        self.assertIn("Must provide either polygon or location", str(context.exception))

        with self.assertRaises(ValueError) as context:
            validate_location_input(polygon=None, location=None)
        self.assertIn("Must provide either polygon or location", str(context.exception))

    def test_both_provided(self):
        """Test validation when both polygon and location are provided."""
        polygon = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}
        location = (35.9132, -79.0558)

        with self.assertRaises(ValueError) as context:
            validate_location_input(polygon=polygon, location=location)
        self.assertIn("Provide either polygon or location, not both", str(context.exception))

    def test_edge_cases(self):
        """Test edge cases for location input validation."""
        # Empty polygon dict should be valid (polygon is not None)
        validate_location_input(polygon={})

        # Empty location tuple should be valid (location is not None)
        validate_location_input(location=())

        # False values should be treated as provided
        validate_location_input(polygon=False)
        validate_location_input(location=False)

        # Zero values should be treated as provided
        validate_location_input(polygon=0)
        validate_location_input(location=0)

        # Empty string should be treated as provided
        validate_location_input(location="")

    def test_error_messages(self):
        """Test error messages are clear and helpful."""
        # Test neither provided error
        with self.assertRaises(ValueError) as context:
            validate_location_input()

        error_msg = str(context.exception)
        self.assertIn("polygon", error_msg.lower())
        self.assertIn("location", error_msg.lower())
        self.assertIn("either", error_msg.lower())

        # Test both provided error
        with self.assertRaises(ValueError) as context:
            validate_location_input(polygon={"type": "Polygon"}, location=(0, 0))

        error_msg = str(context.exception)
        self.assertIn("polygon", error_msg.lower())
        self.assertIn("location", error_msg.lower())
        self.assertIn("not both", error_msg.lower())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])