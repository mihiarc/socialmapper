"""Comprehensive tests for validators module."""

import pytest
from socialmapper.validators import (
    InputValidationError,
    _validate_coordinates_strict,
    validate_coordinates,
    validate_travel_time,
    validate_travel_mode,
    validate_export_format,
    validate_report_format,
    validate_location_input,
)


class TestCoordinateValidation:
    """Test coordinate validation functions."""

    def test_validate_coordinates_strict_valid(self):
        """Test strict coordinate validation with valid inputs."""
        lat, lon = _validate_coordinates_strict(45.5152, -122.6784)
        assert lat == 45.5152
        assert lon == -122.6784

    def test_validate_coordinates_strict_string_input(self):
        """Test strict validation accepts string coordinates."""
        lat, lon = _validate_coordinates_strict("45.5152", "-122.6784")
        assert lat == 45.5152
        assert lon == -122.6784

    def test_validate_coordinates_strict_integer_input(self):
        """Test strict validation accepts integer coordinates."""
        lat, lon = _validate_coordinates_strict(45, -122)
        assert lat == 45.0
        assert lon == -122.0

    def test_validate_coordinates_strict_invalid_latitude(self):
        """Test strict validation rejects invalid latitude."""
        with pytest.raises(InputValidationError, match="Invalid latitude"):
            _validate_coordinates_strict(91.0, 0.0)

        with pytest.raises(InputValidationError, match="Invalid latitude"):
            _validate_coordinates_strict(-91.0, 0.0)

    def test_validate_coordinates_strict_invalid_longitude(self):
        """Test strict validation rejects invalid longitude."""
        with pytest.raises(InputValidationError, match="Invalid longitude"):
            _validate_coordinates_strict(0.0, 181.0)

        with pytest.raises(InputValidationError, match="Invalid longitude"):
            _validate_coordinates_strict(0.0, -181.0)

    def test_validate_coordinates_strict_non_numeric(self):
        """Test strict validation rejects non-numeric values."""
        with pytest.raises(InputValidationError, match="must be numeric"):
            _validate_coordinates_strict("invalid", 0.0)

        with pytest.raises(InputValidationError, match="must be numeric"):
            _validate_coordinates_strict(0.0, "invalid")

    def test_validate_coordinates_strict_none(self):
        """Test strict validation rejects None values."""
        with pytest.raises(InputValidationError, match="must be numeric"):
            _validate_coordinates_strict(None, 0.0)

    def test_validate_coordinates_valid(self):
        """Test non-strict validation returns True for valid coords."""
        assert validate_coordinates(45.5152, -122.6784) is True
        assert validate_coordinates(0, 0) is True
        assert validate_coordinates(-90, -180) is True
        assert validate_coordinates(90, 180) is True

    def test_validate_coordinates_invalid(self):
        """Test non-strict validation returns False for invalid coords."""
        assert validate_coordinates(91.0, 0.0) is False
        assert validate_coordinates(-91.0, 0.0) is False
        assert validate_coordinates(0.0, 181.0) is False
        assert validate_coordinates(0.0, -181.0) is False


class TestTravelTimeValidation:
    """Test travel time validation."""

    def test_validate_travel_time_valid(self):
        """Test validation accepts valid travel times."""
        validate_travel_time(1)  # Minimum
        validate_travel_time(60)  # Common
        validate_travel_time(120)  # Maximum

    def test_validate_travel_time_too_low(self):
        """Test validation rejects travel time below minimum."""
        with pytest.raises(ValueError, match="Travel time must be between 1 and 120"):
            validate_travel_time(0)

        with pytest.raises(ValueError, match="Travel time must be between 1 and 120"):
            validate_travel_time(-1)

    def test_validate_travel_time_too_high(self):
        """Test validation rejects travel time above maximum."""
        with pytest.raises(ValueError, match="Travel time must be between 1 and 120"):
            validate_travel_time(121)

        with pytest.raises(ValueError, match="Travel time must be between 1 and 120"):
            validate_travel_time(500)


class TestTravelModeValidation:
    """Test travel mode validation."""

    def test_validate_travel_mode_valid(self):
        """Test validation accepts valid travel modes."""
        validate_travel_mode("drive")
        validate_travel_mode("walk")
        validate_travel_mode("bike")

    def test_validate_travel_mode_invalid(self):
        """Test validation rejects invalid travel modes."""
        with pytest.raises(ValueError, match="Travel mode must be one of"):
            validate_travel_mode("fly")

        with pytest.raises(ValueError, match="Travel mode must be one of"):
            validate_travel_mode("invalid")

        with pytest.raises(ValueError, match="Travel mode must be one of"):
            validate_travel_mode("DRIVE")  # Case sensitive


class TestExportFormatValidation:
    """Test export format validation."""

    def test_validate_export_format_valid(self):
        """Test validation accepts valid export formats."""
        validate_export_format("png")
        validate_export_format("pdf")
        validate_export_format("svg")
        validate_export_format("geojson")
        validate_export_format("shapefile")

    def test_validate_export_format_invalid(self):
        """Test validation rejects invalid export formats."""
        with pytest.raises(ValueError, match="Export format must be one of"):
            validate_export_format("jpg")

        with pytest.raises(ValueError, match="Export format must be one of"):
            validate_export_format("PNG")  # Case sensitive


class TestReportFormatValidation:
    """Test report format validation."""

    def test_validate_report_format_valid(self):
        """Test validation accepts valid report formats."""
        validate_report_format("html")
        validate_report_format("pdf")

    def test_validate_report_format_invalid(self):
        """Test validation rejects invalid report formats."""
        with pytest.raises(ValueError, match="Report format must be one of"):
            validate_report_format("docx")

        with pytest.raises(ValueError, match="Report format must be one of"):
            validate_report_format("CSV")  # Case sensitive


class TestLocationInputValidation:
    """Test location input validation."""

    def test_validate_location_input_polygon_only(self):
        """Test validation passes with polygon only."""
        validate_location_input(polygon={"type": "Polygon"}, location=None)

    def test_validate_location_input_location_only(self):
        """Test validation passes with location only."""
        validate_location_input(polygon=None, location=(45.5, -122.6))

    def test_validate_location_input_neither(self):
        """Test validation fails when neither is provided."""
        with pytest.raises(ValueError, match="Must provide either polygon or location"):
            validate_location_input(polygon=None, location=None)

    def test_validate_location_input_both(self):
        """Test validation fails when both are provided."""
        with pytest.raises(ValueError, match="Provide either polygon or location, not both"):
            validate_location_input(
                polygon={"type": "Polygon"},
                location=(45.5, -122.6)
            )

    def test_validate_location_input_defaults(self):
        """Test validation with default parameters."""
        with pytest.raises(ValueError, match="Must provide either polygon or location"):
            validate_location_input()
