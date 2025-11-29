"""Tests for SocialMapper validators."""

import pytest
from shapely.geometry import Point

from socialmapper.exceptions import ValidationError
from socialmapper.validators import (
    _validate_coordinates_strict,
    prevalidate_for_pyproj,
    validate_coordinates,
    validate_export_format,
    validate_location_input,
    validate_poi_data,
    validate_report_format,
    validate_travel_mode,
    validate_travel_time,
)


class TestValidateCoordinatesStrict:
    """Test _validate_coordinates_strict function."""

    def test_valid_coordinates(self, valid_coordinates_list):
        for lat, lon in valid_coordinates_list:
            result_lat, result_lon = _validate_coordinates_strict(lat, lon)
            assert result_lat == lat
            assert result_lon == lon

    def test_invalid_latitude_too_high(self):
        with pytest.raises(ValidationError, match="Invalid latitude"):
            _validate_coordinates_strict(91, 0)

    def test_invalid_latitude_too_low(self):
        with pytest.raises(ValidationError, match="Invalid latitude"):
            _validate_coordinates_strict(-91, 0)

    def test_invalid_longitude_too_high(self):
        with pytest.raises(ValidationError, match="Invalid longitude"):
            _validate_coordinates_strict(0, 181)

    def test_invalid_longitude_too_low(self):
        with pytest.raises(ValidationError, match="Invalid longitude"):
            _validate_coordinates_strict(0, -181)

    def test_boundary_values(self):
        # Test exact boundary values
        _validate_coordinates_strict(90, 180)
        _validate_coordinates_strict(-90, -180)
        _validate_coordinates_strict(90, -180)
        _validate_coordinates_strict(-90, 180)

    def test_string_coordinates(self):
        lat, lon = _validate_coordinates_strict("45.5", "-122.6")
        assert lat == 45.5
        assert lon == -122.6

    def test_integer_coordinates(self):
        lat, lon = _validate_coordinates_strict(45, -122)
        assert lat == 45.0
        assert lon == -122.0

    def test_non_numeric_raises(self):
        with pytest.raises(ValidationError, match="must be numeric"):
            _validate_coordinates_strict("abc", 0)

        with pytest.raises(ValidationError, match="must be numeric"):
            _validate_coordinates_strict(0, "xyz")

    def test_none_values_raise(self):
        with pytest.raises(ValidationError, match="must be numeric"):
            _validate_coordinates_strict(None, 0)


class TestValidateCoordinates:
    """Test validate_coordinates function (returns bool)."""

    def test_valid_coordinates_return_true(self, valid_coordinates_list):
        for lat, lon in valid_coordinates_list:
            assert validate_coordinates(lat, lon) is True

    def test_invalid_coordinates_return_false(self, invalid_coordinates_list):
        for lat, lon in invalid_coordinates_list:
            assert validate_coordinates(lat, lon) is False


class TestValidateTravelTime:
    """Test validate_travel_time function."""

    def test_valid_travel_times(self):
        # Should not raise
        validate_travel_time(1)
        validate_travel_time(15)
        validate_travel_time(60)
        validate_travel_time(120)

    def test_minimum_boundary(self):
        validate_travel_time(1)  # Should pass

        with pytest.raises(ValueError, match="Travel time must be between"):
            validate_travel_time(0)

    def test_maximum_boundary(self):
        validate_travel_time(120)  # Should pass

        with pytest.raises(ValueError, match="Travel time must be between"):
            validate_travel_time(121)

    def test_negative_travel_time(self):
        with pytest.raises(ValueError, match="Travel time must be between"):
            validate_travel_time(-5)


class TestValidateTravelMode:
    """Test validate_travel_mode function."""

    def test_valid_modes(self):
        # Should not raise
        validate_travel_mode("drive")
        validate_travel_mode("walk")
        validate_travel_mode("bike")

    def test_invalid_mode(self):
        with pytest.raises(ValueError, match="Travel mode must be one of"):
            validate_travel_mode("fly")

        with pytest.raises(ValueError, match="Travel mode must be one of"):
            validate_travel_mode("car")

        with pytest.raises(ValueError, match="Travel mode must be one of"):
            validate_travel_mode("transit")

    def test_case_sensitive(self):
        with pytest.raises(ValueError):
            validate_travel_mode("Drive")

        with pytest.raises(ValueError):
            validate_travel_mode("WALK")


class TestValidateExportFormat:
    """Test validate_export_format function."""

    def test_valid_formats(self):
        # Should not raise
        validate_export_format("png")
        validate_export_format("pdf")
        validate_export_format("svg")
        validate_export_format("geojson")
        validate_export_format("shapefile")

    def test_invalid_format(self):
        with pytest.raises(ValueError, match="Export format must be one of"):
            validate_export_format("jpeg")

        with pytest.raises(ValueError, match="Export format must be one of"):
            validate_export_format("tiff")

        with pytest.raises(ValueError, match="Export format must be one of"):
            validate_export_format("csv")

    def test_case_sensitive(self):
        with pytest.raises(ValueError):
            validate_export_format("PNG")


class TestValidateReportFormat:
    """Test validate_report_format function."""

    def test_valid_formats(self):
        # Should not raise
        validate_report_format("html")
        validate_report_format("pdf")

    def test_invalid_format(self):
        with pytest.raises(ValueError, match="Report format must be one of"):
            validate_report_format("docx")

        with pytest.raises(ValueError, match="Report format must be one of"):
            validate_report_format("markdown")


class TestValidateLocationInput:
    """Test validate_location_input function."""

    def test_polygon_only(self):
        # Should not raise
        validate_location_input(polygon={"type": "Polygon"})

    def test_location_only(self):
        # Should not raise
        validate_location_input(location=(45.5, -122.6))

    def test_neither_provided(self):
        with pytest.raises(ValueError, match="Must provide either polygon or location"):
            validate_location_input()

    def test_both_provided(self):
        with pytest.raises(ValueError, match="not both"):
            validate_location_input(
                polygon={"type": "Polygon"},
                location=(45.5, -122.6)
            )


class TestValidatePOIData:
    """Test validate_poi_data function."""

    def test_valid_lat_lon_format(self):
        pois = [
            {"lat": 45.5152, "lon": -122.6784, "name": "Test"},
            {"lat": 35.7796, "lon": -78.6382, "name": "Test2"}
        ]
        result = validate_poi_data(pois)
        assert len(result) == 2

    def test_valid_latitude_longitude_format(self):
        pois = [
            {"latitude": 45.5152, "longitude": -122.6784}
        ]
        result = validate_poi_data(pois)
        assert len(result) == 1
        # Should standardize to lat/lon
        assert "lat" in result[0]
        assert "lon" in result[0]

    def test_valid_coordinates_array_format(self):
        pois = [
            {"coordinates": [-122.6784, 45.5152]}  # GeoJSON order: lon, lat
        ]
        result = validate_poi_data(pois)
        assert len(result) == 1

    def test_valid_geometry_format(self):
        pois = [
            {"geometry": {"type": "Point", "coordinates": [-122.6784, 45.5152]}}
        ]
        result = validate_poi_data(pois)
        assert len(result) == 1

    def test_empty_list_raises(self):
        with pytest.raises(ValueError, match="No valid POI coordinates"):
            validate_poi_data([])

    def test_all_invalid_raises(self):
        pois = [
            {"lat": 200, "lon": 0},  # Invalid lat
            {"lat": 0, "lon": 300},  # Invalid lon
            {"name": "No coords"}    # Missing coords
        ]
        with pytest.raises(ValueError, match="No valid POI coordinates"):
            validate_poi_data(pois)

    def test_mixed_valid_invalid(self):
        pois = [
            {"lat": 45.5, "lon": -122.6},  # Valid
            {"lat": 200, "lon": 0},         # Invalid
            {"lat": 35.7, "lon": -78.6}    # Valid
        ]
        result = validate_poi_data(pois)
        assert len(result) == 2

    def test_preserves_extra_fields(self):
        pois = [
            {"lat": 45.5, "lon": -122.6, "name": "Library", "category": "library"}
        ]
        result = validate_poi_data(pois)
        assert result[0]["name"] == "Library"
        assert result[0]["category"] == "library"


class TestPrevalidateForPyproj:
    """Test prevalidate_for_pyproj function."""

    def test_valid_dict_list(self):
        data = [{"lat": 45.5, "lon": -122.6}]
        is_valid, errors = prevalidate_for_pyproj(data)
        assert is_valid is True
        assert len(errors) == 0

    def test_valid_point_list(self):
        data = [Point(-122.6, 45.5), Point(-78.6, 35.7)]
        is_valid, errors = prevalidate_for_pyproj(data)
        assert is_valid is True
        assert len(errors) == 0

    def test_empty_data(self):
        is_valid, errors = prevalidate_for_pyproj([])
        assert is_valid is False
        assert "Empty data" in errors[0]

    def test_invalid_coordinates_in_dict(self):
        data = [{"lat": 200, "lon": 0}]
        is_valid, errors = prevalidate_for_pyproj(data)
        assert is_valid is False

    def test_invalid_point_coordinates(self):
        # Point with invalid coordinates
        data = [Point(0, 200)]  # lat=200 is invalid
        is_valid, errors = prevalidate_for_pyproj(data)
        assert is_valid is False
        assert len(errors) > 0

    def test_unsupported_type(self):
        is_valid, errors = prevalidate_for_pyproj("not a list")
        assert is_valid is False
        assert "Unsupported data type" in errors[0]

    def test_unsupported_item_type(self):
        data = [123, 456]  # List of ints instead of dicts/Points
        is_valid, errors = prevalidate_for_pyproj(data)
        assert is_valid is False
