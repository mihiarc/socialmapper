"""
Tests for the process_walmart_locations module.
"""
import pytest
import json
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Point, Polygon
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
from scripts.core.process_walmart_locations import (
    load_raw_locations, 
    load_county_boundaries,
    filter_by_county_intersection,
    extract_services_from_name,
    are_same_location,
    consolidate_locations
)


class TestProcessWalmartLocations:
    """Tests for the process_walmart_locations module."""

    @pytest.fixture
    def sample_walmart_df(self):
        """Create a sample DataFrame of Walmart locations."""
        return pd.DataFrame({
            'name': ['Walmart Supercenter', 'Walmart Neighborhood Market', 'Walmart'],
            'brand': ['Walmart', 'Walmart', 'Walmart'],
            'state': ['KS', 'KS', 'OK'],
            'city': ['Garden City', 'Liberal', 'Beaver'],
            'address': ['123 Main St', '456 Center Ave', '789 Commerce Blvd'],
            'postcode': ['67846', '67901', '73932'],
            'lat': [37.5678, 36.9876, 36.8123],
            'lon': [-101.2345, -100.1234, -100.5678],
            'phone': ['+1-555-123-4567', '+1-555-789-0123', '+1-555-987-6543'],
            'website': ['https://www.walmart.com/store/1234', 
                      'https://www.walmart.com/store/5678',
                      'https://www.walmart.com/store/9012'],
            'opening_hours': ['24/7', '6:00-23:00', '7:00-22:00'],
            'type': ['node', 'way', 'node'],
            'id': [123456789, 987654321, 567891234]
        })

    @pytest.fixture
    def sample_counties_gdf(self):
        """Create a sample GeoDataFrame of county boundaries."""
        # Create two polygons representing counties
        county1 = Polygon([
            (-101.5, 37.0),  # Southwest
            (-101.5, 38.0),  # Northwest
            (-100.5, 38.0),  # Northeast
            (-100.5, 37.0),  # Southeast
            (-101.5, 37.0)   # Back to Southwest to close the polygon
        ])
        
        county2 = Polygon([
            (-100.5, 36.5),  # Southwest
            (-100.5, 37.5),  # Northwest
            (-99.5, 37.5),   # Northeast
            (-99.5, 36.5),   # Southeast
            (-100.5, 36.5)   # Back to Southwest to close the polygon
        ])
        
        gdf = gpd.GeoDataFrame(
            {
                'NAME': ['County1', 'County2'],
                'STATE': ['20', '20'],  # FIPS code for Kansas
                'GEOID': ['20001', '20003'],
                'geometry': [county1, county2]
            },
            crs="EPSG:4326"
        )
        return gdf

    @patch('scripts.core.process_walmart_locations.pd.read_csv')
    def test_load_raw_locations(self, mock_read_csv, test_config):
        """Test loading raw Walmart locations from CSV."""
        # Setup mock
        mock_df = pd.DataFrame({
            'name': ['Walmart Supercenter', 'Walmart Neighborhood Market'],
            'lat': [37.5678, 36.9876],
            'lon': [-101.2345, -100.1234]
        })
        mock_read_csv.return_value = mock_df
        
        # Call function
        result = load_raw_locations(test_config)
        
        # Verify mock was called with the correct path
        mock_read_csv.assert_called_once()
        file_arg = mock_read_csv.call_args[0][0]
        assert 'walmart_stores_bbox.csv' in str(file_arg)
        
        # Verify result
        pd.testing.assert_frame_equal(result, mock_df)

    @patch('scripts.core.process_walmart_locations.gpd.read_file')
    def test_load_county_boundaries(self, mock_read_file, test_config, sample_counties_gdf):
        """Test loading county boundaries from GeoJSON."""
        # Setup mock
        mock_read_file.return_value = sample_counties_gdf
        
        # Call function
        result = load_county_boundaries(test_config)
        
        # Verify mock was called with the correct path
        mock_read_file.assert_called_once()
        file_arg = mock_read_file.call_args[0][0]
        assert 'county_boundaries.geojson' in str(file_arg)
        
        # Verify result
        assert isinstance(result, gpd.GeoDataFrame)
        assert result.equals(sample_counties_gdf)

    def test_filter_by_county_intersection(self, sample_walmart_df, sample_counties_gdf):
        """Test filtering Walmart locations by county intersection."""
        # Call function
        filtered_df, filtered_count = filter_by_county_intersection(sample_walmart_df, sample_counties_gdf)
        
        # Verify results
        assert isinstance(filtered_df, pd.DataFrame)
        assert isinstance(filtered_count, int)
        
        # The first store should be in County1, and the second store should be in County2
        # The third store should be outside any county
        assert len(filtered_df) == 2  # Only 2 of 3 stores are within counties
        assert filtered_count == 1  # 1 store was filtered out
        
        # Check that the right stores were kept
        assert 'Garden City' in filtered_df['city'].values
        assert 'Liberal' in filtered_df['city'].values
        assert 'Beaver' not in filtered_df['city'].values

    def test_extract_services_from_name(self):
        """Test extracting services from Walmart location names."""
        # Test various names
        test_cases = [
            ('Walmart Supercenter', {'Supercenter'}),
            ('Walmart Neighborhood Market', {'Neighborhood Market'}),
            ('Walmart Supercenter with Pharmacy', {'Supercenter', 'Pharmacy'}),
            ('Walmart with Fuel Station', {'Fuel Station'}),
            ('Walmart', {'General Store'}),
            ('Walmart Auto Care Center', {'Auto Care'}),
            ('Walmart Supercenter with Gas Station and Pharmacy', {'Supercenter', 'Fuel Station', 'Pharmacy'}),
            ('Neighborhood Walmart with Vision and Money Services', {'Neighborhood Market', 'Vision Center', 'Money Services'})
        ]
        
        for name, expected_services in test_cases:
            services = extract_services_from_name(name)
            assert services == expected_services, f"Failed for '{name}'"

    def test_are_same_location(self):
        """Test checking if two lat/lon pairs represent the same location."""
        # Test cases
        test_cases = [
            # Same exact location
            (37.5678, -101.2345, 37.5678, -101.2345, True),
            
            # Just under threshold distance (100m)
            (37.5678, -101.2345, 37.5678, -101.2354, True),  # ~80m apart
            
            # Just over threshold distance
            (37.5678, -101.2345, 37.5678, -101.2366, False),  # ~180m apart
            
            # Significantly different locations
            (37.5678, -101.2345, 36.9876, -100.1234, False)
        ]
        
        for lat1, lon1, lat2, lon2, expected_result in test_cases:
            result = are_same_location(lat1, lon1, lat2, lon2)
            assert result == expected_result, f"Failed for ({lat1}, {lon1}) and ({lat2}, {lon2})"
            
        # Test with custom threshold
        assert are_same_location(37.5678, -101.2345, 37.5678, -101.2366, threshold_km=0.2)  # ~180m with 200m threshold

    def test_consolidate_locations(self, sample_walmart_df):
        """Test consolidating Walmart locations that are physically the same place."""
        # Create test data with some duplicates
        test_df = pd.DataFrame({
            'name': [
                'Walmart Supercenter',                   # Regular store
                'Walmart Neighborhood Market',           # Regular store
                'Walmart',                               # Regular store
                'Walmart Supercenter with Pharmacy',     # Duplicate of first store
                'Walmart with Gas Station'               # Duplicate of third store
            ],
            'brand': ['Walmart'] * 5,
            'state': ['KS', 'KS', 'OK', 'KS', 'OK'],
            'city': ['Garden City', 'Liberal', 'Beaver', 'Garden City', 'Beaver'],
            'address': [
                '123 Main St', '456 Center Ave', '789 Commerce Blvd', 
                '123 Main St', '789 Commerce Blvd'
            ],
            'postcode': ['67846', '67901', '73932', '67846', '73932'],
            'lat': [37.5678, 36.9876, 36.8123, 37.5679, 36.8124],  # Slightly different coordinates for duplicates
            'lon': [-101.2345, -100.1234, -100.5678, -101.2346, -100.5677],
            'phone': ['+1-555-123-4567'] * 5,
            'website': ['https://www.walmart.com/store/1234'] * 5,
            'opening_hours': ['24/7'] * 5,
            'type': ['node'] * 5,
            'id': [123456789, 987654321, 567891234, 111111111, 222222222]
        })
        
        # Call consolidate_locations
        result_df = consolidate_locations(test_df)
        
        # Verify results
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == 3  # Should consolidate to 3 unique locations
        
        # Check that the first location has services from both Supercenter and Pharmacy
        supercenter_row = result_df[result_df['name'] == 'Walmart Supercenter'].iloc[0]
        assert 'Pharmacy' in supercenter_row['services']
        assert supercenter_row['location_count'] == 2
        
        # Check that the third location has services from both General Store and Fuel Station
        walmart_row = result_df[result_df['name'] == 'Walmart'].iloc[0]
        assert 'Fuel Station' in walmart_row['services']
        assert walmart_row['location_count'] == 2
        
        # Check that Neighborhood Market is still a single location
        neighborhood_row = result_df[result_df['name'] == 'Walmart Neighborhood Market'].iloc[0]
        assert neighborhood_row['location_count'] == 1

    def test_consolidate_locations_with_no_duplicates(self, sample_walmart_df):
        """Test consolidating locations when there are no duplicates."""
        # Call consolidate_locations with sample data that has no duplicates
        result_df = consolidate_locations(sample_walmart_df)
        
        # Verify results
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == 3  # Should still have 3 locations
        
        # Check that all location_count values are 1
        assert (result_df['location_count'] == 1).all() 