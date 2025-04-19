"""
Tests for the fetch_walmart_locations module.
"""
import pytest
import json
import pandas as pd
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
from scripts.core.fetch_walmart_locations import load_bbox, get_walmart_stores


class TestFetchWalmartLocations:
    """Tests for the fetch_walmart_locations module."""

    @patch('scripts.core.fetch_walmart_locations.open', new_callable=mock_open, 
           read_data='{"north": 38.5, "south": 36.5, "east": -99.0, "west": -102.0}')
    def test_load_bbox(self, mock_file, test_config):
        """Test that the load_bbox function returns the correct dictionary."""
        bbox = load_bbox(test_config)
        
        assert isinstance(bbox, dict)
        assert 'north' in bbox
        assert 'south' in bbox
        assert 'east' in bbox
        assert 'west' in bbox
        assert bbox['north'] == 38.5
        assert bbox['south'] == 36.5
        assert bbox['east'] == -99.0
        assert bbox['west'] == -102.0

    @patch('scripts.core.fetch_walmart_locations.load_bbox')
    @patch('scripts.core.fetch_walmart_locations.overpy.Overpass')
    def test_get_walmart_stores(self, mock_overpass, mock_load_bbox, test_config):
        """Test that get_walmart_stores returns a DataFrame with Walmart locations."""
        # Setup mocks
        mock_load_bbox.return_value = {
            'north': 38.5, 
            'south': 36.5, 
            'east': -99.0, 
            'west': -102.0
        }
        
        # Mock Overpass API instance
        mock_api = MagicMock()
        mock_overpass.return_value = mock_api
        
        # Create a mock result with nodes and ways
        mock_result = MagicMock()
        
        # Mock nodes (points)
        mock_node1 = MagicMock()
        mock_node1.id = 123456789
        mock_node1.lat = "37.5678"
        mock_node1.lon = "-101.2345"
        mock_node1.tags = {
            'name': 'Walmart Supercenter',
            'brand': 'Walmart',
            'addr:street': 'Main Street',
            'addr:housenumber': '123',
            'addr:city': 'Garden City',
            'addr:state': 'KS',
            'addr:postcode': '67846',
            'phone': '+1-555-123-4567',
            'website': 'https://www.walmart.com/store/1234',
            'opening_hours': '24/7'
        }
        
        mock_node2 = MagicMock()
        mock_node2.id = 987654321
        mock_node2.lat = "37.2345"
        mock_node2.lon = "-100.5678"
        mock_node2.tags = {
            'name': 'Walmart',
            'brand': 'Walmart',
            'addr:street': 'Commerce Road',
            'addr:housenumber': '456',
            'addr:city': 'Dodge City',
            'addr:state': 'KS',
            'addr:postcode': '67801',
            'phone': '+1-555-987-6543',
            'website': 'https://www.walmart.com/store/5678',
            'opening_hours': '8:00-22:00'
        }
        
        # Mock a way (building)
        mock_way = MagicMock()
        mock_way.id = 123123123
        
        # Mock nodes for the way
        way_node1 = MagicMock()
        way_node1.lat = "36.9876"
        way_node1.lon = "-100.1234"
        
        way_node2 = MagicMock()
        way_node2.lat = "36.9878"
        way_node2.lon = "-100.1236"
        
        way_node3 = MagicMock()
        way_node3.lat = "36.9874"
        way_node3.lon = "-100.1238"
        
        way_node4 = MagicMock()
        way_node4.lat = "36.9872"
        way_node4.lon = "-100.1232"
        
        mock_way.nodes = [way_node1, way_node2, way_node3, way_node4]
        
        mock_way.tags = {
            'name': 'Walmart Neighborhood Market',
            'brand': 'Walmart',
            'addr:street': 'Center Avenue',
            'addr:housenumber': '789',
            'addr:city': 'Liberal',
            'addr:state': 'KS',
            'addr:postcode': '67901',
            'phone': '+1-555-789-0123',
            'website': 'https://www.walmart.com/store/9012',
            'opening_hours': '6:00-23:00'
        }
        
        # Assign nodes and ways to the mock result
        mock_result.nodes = [mock_node1, mock_node2]
        mock_result.ways = [mock_way]
        
        # Configure the mock API to return our mock result
        mock_api.query.return_value = mock_result
        
        # Call the function
        result_df = get_walmart_stores(test_config)
        
        # Assertions
        assert isinstance(result_df, pd.DataFrame)
        assert not result_df.empty
        assert len(result_df) == 3  # 2 nodes + 1 way
        
        # Check if the DataFrame has the expected columns
        expected_columns = ['name', 'brand', 'state', 'city', 'address', 'postcode', 
                            'lat', 'lon', 'phone', 'website', 'opening_hours', 'type', 'id']
        for col in expected_columns:
            assert col in result_df.columns
        
        # Check if the data was processed correctly
        assert 'Walmart Supercenter' in result_df['name'].values
        assert 'KS' in result_df['state'].values
        assert 'Garden City' in result_df['city'].values
        
        # Verify the API was called with the correct query
        mock_api.query.assert_called_once()
        query_arg = mock_api.query.call_args[0][0]
        assert 'node["shop"]["brand"="Walmart"]' in query_arg
        assert 'way["shop"]["brand"="Walmart"]' in query_arg
        assert '36.5' in query_arg  # South
        assert '38.5' in query_arg  # North
        assert '-102.0' in query_arg  # West
        assert '-99.0' in query_arg  # East

    @patch('scripts.core.fetch_walmart_locations.overpy.Overpass')
    @patch('scripts.core.fetch_walmart_locations.load_bbox')
    def test_get_walmart_stores_retry_logic(self, mock_load_bbox, mock_overpass, test_config):
        """Test that the retry logic works when the API call fails."""
        # Setup mocks
        mock_load_bbox.return_value = {
            'north': 38.5, 
            'south': 36.5, 
            'east': -99.0, 
            'west': -102.0
        }
        
        # Mock Overpass API instance that fails on first call but succeeds on second
        mock_api = MagicMock()
        mock_overpass.return_value = mock_api
        
        # First call raises exception, second succeeds
        mock_api.query.side_effect = [
            Exception("API timeout"),
            MagicMock(nodes=[], ways=[])  # Empty result on second call
        ]
        
        # Call the function
        with patch('scripts.core.fetch_walmart_locations.time.sleep') as mock_sleep:
            result_df = get_walmart_stores(test_config)
        
        # Verify API was called twice
        assert mock_api.query.call_count == 2
        
        # Verify sleep was called once between retries
        mock_sleep.assert_called_once()
        
        # Result should be an empty DataFrame since we returned no nodes or ways
        assert isinstance(result_df, pd.DataFrame)
        assert result_df.empty

    @patch('scripts.core.fetch_walmart_locations.overpy.Overpass')
    @patch('scripts.core.fetch_walmart_locations.load_bbox')
    def test_get_walmart_stores_empty_result(self, mock_load_bbox, mock_overpass, test_config):
        """Test handling of empty results from the API."""
        # Setup mocks
        mock_load_bbox.return_value = {
            'north': 38.5, 
            'south': 36.5, 
            'east': -99.0, 
            'west': -102.0
        }
        
        # Mock Overpass API instance that returns empty result
        mock_api = MagicMock()
        mock_overpass.return_value = mock_api
        
        # Create a mock result with no nodes or ways
        mock_result = MagicMock()
        mock_result.nodes = []
        mock_result.ways = []
        
        # Configure the mock API to return our empty mock result
        mock_api.query.return_value = mock_result
        
        # Call the function
        result_df = get_walmart_stores(test_config)
        
        # Check we get an empty DataFrame
        assert isinstance(result_df, pd.DataFrame)
        assert result_df.empty 