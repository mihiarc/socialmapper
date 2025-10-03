"""Tests for the new simplified SocialMapper API v2.0."""

import pytest
import os
from unittest.mock import patch, MagicMock
from socialmapper import (
    create_isochrone,
    get_census_blocks,
    get_census_data,
    create_map,
    get_poi
)


class TestCreateIsochrone:
    """Test the create_isochrone function."""
    
    def test_valid_city_name(self):
        """Test isochrone creation with city name."""
        result = create_isochrone("Seattle, WA", travel_time=15)
        
        assert result["type"] == "Feature"
        assert "geometry" in result
        assert result["geometry"]["type"] == "Polygon"
        assert result["properties"]["location"] == "Seattle, WA"
        assert result["properties"]["travel_time"] == 15
        assert result["properties"]["travel_mode"] == "drive"
        assert "area_sq_km" in result["properties"]
    
    def test_valid_coordinates(self):
        """Test isochrone creation with coordinates."""
        result = create_isochrone((47.6062, -122.3321), travel_time=10)
        
        assert result["type"] == "Feature"
        assert "geometry" in result
        assert result["properties"]["travel_time"] == 10
    
    def test_different_travel_modes(self):
        """Test all supported travel modes."""
        for mode in ["drive", "walk", "bike"]:
            result = create_isochrone("Portland, OR", travel_time=15, travel_mode=mode)
            assert result["properties"]["travel_mode"] == mode
    
    def test_invalid_travel_time(self):
        """Test validation of travel time bounds."""
        with pytest.raises(ValueError, match="Travel time must be between 1 and 120"):
            create_isochrone("Seattle, WA", travel_time=0)
        
        with pytest.raises(ValueError, match="Travel time must be between 1 and 120"):
            create_isochrone("Seattle, WA", travel_time=150)
    
    def test_invalid_travel_mode(self):
        """Test validation of travel mode."""
        with pytest.raises(ValueError, match="Travel mode must be"):
            create_isochrone("Seattle, WA", travel_mode="fly")
    
    def test_invalid_coordinates(self):
        """Test validation of coordinate bounds."""
        from socialmapper.exceptions import ValidationError

        with pytest.raises(ValidationError, match="Invalid coordinates"):
            create_isochrone((100, 200), travel_time=15)

        with pytest.raises(ValidationError, match="Invalid coordinates"):
            create_isochrone((-91, 0), travel_time=15)


class TestGetPOI:
    """Test the get_poi function."""
    
    def test_basic_poi_search(self):
        """Test basic POI search."""
        pois = get_poi("Portland, OR", limit=5)
        
        assert isinstance(pois, list)
        assert len(pois) <= 5
        
        if pois:  # If we got results
            poi = pois[0]
            assert "name" in poi
            assert "category" in poi
            assert "lat" in poi
            assert "lon" in poi
            assert "distance_km" in poi
    
    def test_poi_with_categories(self):
        """Test POI search with category filtering."""
        pois = get_poi(
            location=(37.7749, -122.4194),
            categories=["restaurant", "cafe"],
            limit=10
        )
        
        assert isinstance(pois, list)
        assert len(pois) <= 10
        
        # Check that results are sorted by distance
        if len(pois) > 1:
            distances = [p["distance_km"] for p in pois]
            assert distances == sorted(distances)
    
    def test_poi_with_travel_time(self):
        """Test POI search within travel time boundary."""
        pois = get_poi(
            location="Denver, CO",
            travel_time=10,
            limit=20
        )
        
        assert isinstance(pois, list)
        assert len(pois) <= 20


class TestGetCensusBlocks:
    """Test the get_census_blocks function."""
    
    def test_blocks_from_point_and_radius(self):
        """Test getting blocks from a point and radius."""
        blocks = get_census_blocks(
            location=(40.7128, -74.0060),
            radius_km=1
        )
        
        assert isinstance(blocks, list)
        
        if blocks:  # If we got results
            block = blocks[0]
            assert "geoid" in block
            assert "geometry" in block
            assert "area_sq_km" in block
            assert len(block["geoid"]) == 12  # Standard GEOID length
    
    def test_blocks_from_polygon(self):
        """Test getting blocks from a polygon."""
        # Create a small isochrone first
        iso = create_isochrone((37.7749, -122.4194), travel_time=5)
        
        blocks = get_census_blocks(polygon=iso)
        
        assert isinstance(blocks, list)
    
    def test_invalid_inputs(self):
        """Test validation of input parameters."""
        with pytest.raises(ValueError, match="Must provide either polygon or location"):
            get_census_blocks()
        
        with pytest.raises(ValueError, match="Provide either polygon or location, not both"):
            get_census_blocks(
                polygon={"type": "Feature"},
                location=(40, -74)
            )


class TestGetCensusData:
    """Test the get_census_data function."""
    
    def test_census_data_for_point(self):
        """Test getting census data for a single point."""
        data = get_census_data(
            location=(39.7392, -104.9903),
            variables=["population"],
            year=2022
        )
        
        assert isinstance(data, dict)
        # Data might be empty if Census API fails
    
    def test_census_data_for_geoids(self):
        """Test getting census data for specific GEOIDs."""
        # Use a known GEOID (example from California)
        data = get_census_data(
            location=["060750201001"],
            variables=["population", "median_income"],
            year=2022
        )
        
        assert isinstance(data, dict)
    
    def test_variable_name_normalization(self):
        """Test that human-readable variable names are normalized."""
        # This should work with both formats
        data1 = get_census_data(
            location=(40.7128, -74.0060),
            variables=["population"]
        )
        
        data2 = get_census_data(
            location=(40.7128, -74.0060),
            variables=["B01003_001E"]
        )
        
        assert isinstance(data1, dict)
        assert isinstance(data2, dict)


class TestCreateMap:
    """Test the create_map function."""
    
    @patch('matplotlib.pyplot.savefig')
    def test_create_map_from_list(self, mock_savefig):
        """Test creating a map from a list of dicts."""
        data = [
            {
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[-122.4, 37.7], [-122.4, 37.8], [-122.3, 37.8], [-122.3, 37.7], [-122.4, 37.7]]]
                },
                "population": 1000
            },
            {
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[-122.3, 37.7], [-122.3, 37.8], [-122.2, 37.8], [-122.2, 37.7], [-122.3, 37.7]]]
                },
                "population": 2000
            }
        ]
        
        # Should return bytes when no save_path
        result = create_map(data, "population", title="Test Map")
        assert isinstance(result, bytes)
    
    def test_create_map_invalid_column(self):
        """Test error when column doesn't exist."""
        data = [{"geometry": {"type": "Polygon", "coordinates": []}, "value": 100}]
        
        with pytest.raises(ValueError, match="Column 'nonexistent' not found"):
            create_map(data, "nonexistent")


class TestBoundaryConditions:
    """Test boundary conditions and edge cases."""
    
    def test_extreme_coordinates(self):
        """Test with extreme but valid coordinates."""
        # Near north pole (just an example, may not have real data)
        result = create_isochrone((89, 0), travel_time=5)
        assert result["type"] == "Feature"
        
        # Near south pole
        result = create_isochrone((-89, 0), travel_time=5)
        assert result["type"] == "Feature"
        
        # International date line
        result = create_isochrone((0, 179.9), travel_time=5)
        assert result["type"] == "Feature"
    
    def test_minimum_maximum_travel_times(self):
        """Test with minimum and maximum allowed travel times."""
        # Minimum
        result = create_isochrone("Chicago, IL", travel_time=1)
        assert result["properties"]["travel_time"] == 1
        
        # Maximum
        result = create_isochrone("Chicago, IL", travel_time=120)
        assert result["properties"]["travel_time"] == 120
    
    def test_empty_poi_results(self):
        """Test handling of locations with no POIs."""
        # Use a remote location that might have no POIs
        pois = get_poi((70, -150), limit=5)  # Arctic Ocean
        assert isinstance(pois, list)
        # Should return empty list or very few results