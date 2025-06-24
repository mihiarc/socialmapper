"""Property-based tests for coordinate validation using Hypothesis."""

import pytest
from hypothesis import given, strategies as st, assume
from pydantic import ValidationError
from socialmapper.util.coordinate_validation import (
    Coordinate,
    StrictCoordinate,
    validate_coordinate_point,
    validate_poi_coordinates,
    ValidationResult
)


class TestCoordinateValidation:
    """Property-based tests for coordinate validation functions."""

    @given(st.floats(min_value=-90.0, max_value=90.0))
    def test_valid_latitude_range(self, latitude: float):
        """Test that all values in valid latitude range are accepted."""
        assume(not (latitude != latitude))  # Exclude NaN
        # Test using Coordinate model
        coord = Coordinate(lat=latitude, lon=0.0)
        assert coord.lat == latitude

    @given(st.floats().filter(lambda x: x < -90.0 or x > 90.0))
    def test_invalid_latitude_range(self, latitude: float):
        """Test that values outside valid latitude range are rejected."""
        assume(not (latitude != latitude))  # Exclude NaN
        with pytest.raises(ValidationError):
            Coordinate(lat=latitude, lon=0.0)

    @given(st.floats(min_value=-180.0, max_value=180.0))
    def test_valid_longitude_range(self, longitude: float):
        """Test that all values in valid longitude range are accepted."""
        assume(not (longitude != longitude))  # Exclude NaN
        coord = Coordinate(lat=0.0, lon=longitude)
        assert coord.lon == longitude

    @given(st.floats().filter(lambda x: x < -180.0 or x > 180.0))
    def test_invalid_longitude_range(self, longitude: float):
        """Test that values outside valid longitude range are rejected."""
        assume(not (longitude != longitude))  # Exclude NaN
        with pytest.raises(ValidationError):
            Coordinate(lat=0.0, lon=longitude)

    @given(
        st.floats(min_value=-90.0, max_value=90.0),
        st.floats(min_value=-180.0, max_value=180.0)
    )
    def test_valid_coordinate_pairs(self, latitude: float, longitude: float):
        """Test that valid coordinate pairs are accepted."""
        assume(not (latitude != latitude or longitude != longitude))  # Exclude NaN
        coord = Coordinate(lat=latitude, lon=longitude)
        assert coord.lat == latitude
        assert coord.lon == longitude

    @given(
        st.one_of(
            st.tuples(
                st.floats().filter(lambda x: x < -90.0 or x > 90.0),
                st.floats(min_value=-180.0, max_value=180.0)
            ),
            st.tuples(
                st.floats(min_value=-90.0, max_value=90.0),
                st.floats().filter(lambda x: x < -180.0 or x > 180.0)
            )
        )
    )
    def test_invalid_coordinate_pairs(self, coords):
        """Test that invalid coordinate pairs are rejected."""
        latitude, longitude = coords
        assume(not (latitude != latitude or longitude != longitude))  # Exclude NaN
        with pytest.raises(ValidationError):
            Coordinate(lat=latitude, lon=longitude)

    def test_nan_coordinates_rejected(self):
        """Test that NaN coordinate values are rejected."""
        with pytest.raises(ValidationError):
            Coordinate(lat=float('nan'), lon=0.0)
        
        with pytest.raises(ValidationError):
            Coordinate(lat=0.0, lon=float('nan'))

    def test_infinity_coordinates_rejected(self):
        """Test that infinite coordinate values are rejected."""
        with pytest.raises(ValidationError):
            Coordinate(lat=float('inf'), lon=0.0)
        
        with pytest.raises(ValidationError):
            Coordinate(lat=float('-inf'), lon=0.0)
        
        with pytest.raises(ValidationError):
            Coordinate(lat=0.0, lon=float('inf'))
        
        with pytest.raises(ValidationError):
            Coordinate(lat=0.0, lon=float('-inf'))

    @given(
        st.floats(min_value=-90.0, max_value=90.0),
        st.floats(min_value=-180.0, max_value=180.0)
    )
    def test_coordinate_validation_idempotent(self, latitude: float, longitude: float):
        """Test that validating coordinates twice gives same result."""
        assume(not (latitude != latitude or longitude != longitude))  # Exclude NaN
        
        coord1 = Coordinate(lat=latitude, lon=longitude)
        coord2 = Coordinate(lat=latitude, lon=longitude)
        
        assert coord1.lat == coord2.lat
        assert coord1.lon == coord2.lon

    @given(
        st.lists(
            st.tuples(
                st.floats(min_value=-90.0, max_value=90.0),
                st.floats(min_value=-180.0, max_value=180.0)
            ),
            min_size=1,
            max_size=100
        )
    )
    def test_batch_coordinate_validation(self, coordinate_list):
        """Test batch validation of coordinates."""
        # Filter out NaN values
        valid_coords = [
            (lat, lon) for lat, lon in coordinate_list
            if not (lat != lat or lon != lon)
        ]
        
        if not valid_coords:
            return
        
        # All coordinates in the valid range should pass validation
        for lat, lon in valid_coords:
            coord = Coordinate(lat=lat, lon=lon)
            assert coord.lat == lat
            assert coord.lon == lon

    @given(
        st.floats(min_value=-90.0, max_value=90.0),
        st.floats(min_value=-180.0, max_value=180.0),
        st.integers(min_value=1, max_value=15)
    )
    def test_coordinate_precision_handling(self, latitude: float, longitude: float, precision: int):
        """Test that coordinate precision is handled correctly."""
        assume(not (latitude != latitude or longitude != longitude))  # Exclude NaN
        
        # Round coordinates to specified precision
        rounded_lat = round(latitude, precision)
        rounded_lon = round(longitude, precision)
        
        # Both original and rounded should be valid if in range
        coord1 = Coordinate(lat=latitude, lon=longitude)
        coord2 = Coordinate(lat=rounded_lat, lon=rounded_lon)
        
        assert coord1.lat == latitude
        assert coord2.lat == rounded_lat

    @given(st.text().filter(lambda x: not x.replace('-', '').replace('.', '').isdigit()))
    def test_string_coordinates_rejected(self, text_input: str):
        """Test that non-numeric string inputs are properly rejected."""
        with pytest.raises(ValidationError):
            Coordinate(lat=text_input, lon=0.0)
        
        with pytest.raises(ValidationError):
            Coordinate(lat=0.0, lon=text_input)

    def test_none_coordinates_rejected(self):
        """Test that None inputs are properly rejected."""
        with pytest.raises(ValidationError):
            Coordinate(lat=None, lon=0.0)
        
        with pytest.raises(ValidationError):
            Coordinate(lat=0.0, lon=None)

    @given(
        st.lists(
            st.dictionaries(
                st.sampled_from(["lat", "lon"]),
                st.floats(min_value=-90.0, max_value=90.0)
            ),
            min_size=1,
            max_size=10
        )
    )
    def test_poi_validation_function(self, poi_data_list):
        """Test POI validation with property-based testing."""
        # Ensure all POI entries have both lat and lon
        valid_poi_data = []
        for poi in poi_data_list:
            if "lat" in poi and "lon" in poi:
                # Ensure longitude is in valid range
                poi["lon"] = max(-180.0, min(180.0, poi["lon"]))
                valid_poi_data.append(poi)
        
        if not valid_poi_data:
            return
        
        result = validate_poi_coordinates(valid_poi_data)
        
        assert isinstance(result, ValidationResult)
        assert result.total_input == len(valid_poi_data)
        assert result.total_valid >= 0
        assert result.total_invalid >= 0
        assert result.total_valid + result.total_invalid == result.total_input

    def test_coordinate_to_point_conversion(self):
        """Test conversion of Coordinate to Shapely Point."""
        coord = Coordinate(lat=47.6062, lon=-122.3321)
        point = coord.to_point()
        
        assert point.x == coord.lon
        assert point.y == coord.lat

    @given(
        st.floats(min_value=-90.0, max_value=90.0),
        st.floats(min_value=-180.0, max_value=180.0)
    )
    def test_validate_coordinate_point_function(self, latitude: float, longitude: float):
        """Test the validate_coordinate_point utility function."""
        assume(not (latitude != latitude or longitude != longitude))  # Exclude NaN
        
        result = validate_coordinate_point(latitude, longitude, "test")
        
        assert result is not None
        assert isinstance(result, Coordinate)
        assert result.lat == latitude
        assert result.lon == longitude