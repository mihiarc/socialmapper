#!/usr/bin/env python3
"""Tests for polygon-based census functions.

Verifies that census functions work with any polygon geometry,
not just isochrones.
"""

import pytest
import geopandas as gpd
from shapely.geometry import Polygon, Point
import pandas as pd
from unittest.mock import Mock, patch

from socialmapper.census import (
    get_census_data_for_polygon,
    get_demographics_for_polygon,
    get_block_groups_for_polygon,
    identify_states_counties,
    geocode_point,
    normalize_variables
)


class TestPolygonCensusFunctions:
    """Test census functions with various polygon types."""
    
    def test_get_census_data_for_polygon_with_isochrone(self):
        """Test with isochrone polygon (existing use case)."""
        # Create a sample isochrone-like polygon
        polygon = Polygon([
            (-78.65, 35.78),
            (-78.64, 35.78),
            (-78.64, 35.79),
            (-78.65, 35.79),
            (-78.65, 35.78)
        ])
        
        gdf = gpd.GeoDataFrame([1], geometry=[polygon], crs="EPSG:4326")
        
        with patch('socialmapper.census.get_block_groups_for_polygon') as mock_bg:
            # Mock block groups
            mock_bg.return_value = gpd.GeoDataFrame({
                'GEOID': ['37183010100'],
                'geometry': [polygon]
            })
            
            with patch('socialmapper.census.CensusClient.get_data') as mock_data:
                # Mock census data
                mock_data.return_value = pd.DataFrame({
                    'GEOID': ['37183010100'],
                    'B01003_001E': [1000]
                })
                
                result = get_census_data_for_polygon(
                    gdf,
                    variables=['B01003_001E']
                )
                
                assert not result.empty
                assert 'B01003_001E' in result.columns
                assert result['B01003_001E'].sum() == 1000
    
    def test_get_census_data_for_polygon_with_custom_polygon(self):
        """Test with custom polygon from GIS tools."""
        # Create a custom study area polygon
        custom_polygon = Polygon([
            (-79.0, 35.9),
            (-78.9, 35.9),
            (-78.9, 36.0),
            (-79.0, 36.0),
            (-79.0, 35.9)
        ])
        
        gdf = gpd.GeoDataFrame([1], geometry=[custom_polygon], crs="EPSG:4326")
        
        with patch('socialmapper.census.get_block_groups_for_polygon') as mock_bg:
            # Mock block groups
            mock_bg.return_value = gpd.GeoDataFrame({
                'GEOID': ['37183010200', '37183010300'],
                'geometry': [custom_polygon, custom_polygon]
            })
            
            with patch('socialmapper.census.CensusClient.get_data') as mock_data:
                # Mock census data
                mock_data.return_value = pd.DataFrame({
                    'GEOID': ['37183010200', '37183010300'],
                    'B01003_001E': [2000, 3000]
                })
                
                result = get_census_data_for_polygon(
                    gdf,
                    variables=['B01003_001E']
                )
                
                assert not result.empty
                assert len(result) == 2
                assert result['B01003_001E'].sum() == 5000
    
    def test_get_demographics_for_polygon(self):
        """Test demographic summary for any polygon."""
        polygon = Polygon([
            (-78.65, 35.78),
            (-78.64, 35.78),
            (-78.64, 35.79),
            (-78.65, 35.79),
            (-78.65, 35.78)
        ])
        
        gdf = gpd.GeoDataFrame([1], geometry=[polygon], crs="EPSG:4326")
        
        with patch('socialmapper.census.get_census_data') as mock_census:
            # Mock census data response
            mock_census.return_value = pd.DataFrame({
                'B01003_001E': [1000, 2000],  # Total population
                'B19013_001E': [50000, 60000],  # Median income
                'B01002_001E': [35, 40],  # Median age
            })
            
            demographics = get_demographics_for_polygon(gdf)
            
            assert demographics is not None
            # Check that function was called with correct parameters
            mock_census.assert_called_once()
            call_args = mock_census.call_args
            assert call_args[0][0] is gdf  # First arg is the polygon
    
    def test_identify_states_counties_with_different_crs(self):
        """Test CRS handling in identify_states_counties."""
        # Create polygon in Web Mercator (EPSG:3857)
        polygon = Polygon([
            (-8745000, 4260000),
            (-8744000, 4260000),
            (-8744000, 4261000),
            (-8745000, 4261000),
            (-8745000, 4260000)
        ])
        
        gdf = gpd.GeoDataFrame([1], geometry=[polygon], crs="EPSG:3857")
        
        with patch('socialmapper.census.geocode_point') as mock_geocode:
            mock_geocode.return_value = {
                'state_fips': '37',
                'county_fips': '183',
                'tract': '010100',
                'block_group': '1'
            }
            
            result = identify_states_counties(gdf)
            
            # Should have converted to WGS84 for geocoding
            assert result == [('37', '183')]
            
            # Check that geocode was called with lat/lon in reasonable range
            call_args = mock_geocode.call_args[0]
            lat, lon = call_args[0], call_args[1]
            assert -90 <= lat <= 90
            assert -180 <= lon <= 180
    
    def test_normalize_variables(self):
        """Test variable name normalization."""
        variables = [
            'total_population',
            'median_household_income',
            'B01003_001E',  # Already normalized
            'unknown_variable'
        ]
        
        normalized = normalize_variables(variables)
        
        assert normalized[0] == 'B01003_001E'  # total_population
        assert normalized[1] == 'B19013_001E'  # median_household_income
        assert normalized[2] == 'B01003_001E'  # Already correct
        assert normalized[3] == 'unknown_variable'  # Keep unknown as-is
    
    def test_empty_polygon_handling(self):
        """Test handling of polygons with no census data."""
        # Create a small polygon that might not contain block groups
        tiny_polygon = Polygon([
            (-78.6382, 35.7796),
            (-78.6381, 35.7796),
            (-78.6381, 35.7797),
            (-78.6382, 35.7797),
            (-78.6382, 35.7796)
        ])
        
        gdf = gpd.GeoDataFrame([1], geometry=[tiny_polygon], crs="EPSG:4326")
        
        with patch('socialmapper.census.get_block_groups_for_polygon') as mock_bg:
            # Mock empty block groups
            mock_bg.return_value = gpd.GeoDataFrame()
            
            result = get_census_data_for_polygon(
                gdf,
                variables=['B01003_001E']
            )
            
            assert result.empty
    
    def test_polygon_from_file(self):
        """Test that polygon from external file works."""
        # Simulate loading a polygon from a shapefile/GeoJSON
        external_polygon = Polygon([
            (-78.7, 35.7),
            (-78.6, 35.7),
            (-78.6, 35.8),
            (-78.7, 35.8),
            (-78.7, 35.7)
        ])
        
        # This would typically come from gpd.read_file()
        gdf = gpd.GeoDataFrame(
            {'name': ['Study Area'], 'id': [1]},
            geometry=[external_polygon],
            crs="EPSG:4326"
        )
        
        with patch('socialmapper.census.get_block_groups_for_polygon') as mock_bg:
            mock_bg.return_value = gpd.GeoDataFrame({
                'GEOID': ['37183010400'],
                'geometry': [external_polygon]
            })
            
            with patch('socialmapper.census.CensusClient.get_data') as mock_data:
                mock_data.return_value = pd.DataFrame({
                    'GEOID': ['37183010400'],
                    'B01003_001E': [5000]
                })
                
                result = get_census_data_for_polygon(
                    gdf,
                    variables=['B01003_001E']
                )
                
                assert not result.empty
                assert result['B01003_001E'].sum() == 5000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])