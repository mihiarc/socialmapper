"""
Tests for the fetch_county_boundaries module.
"""
import pytest
import json
import pandas as pd
from unittest.mock import patch, MagicMock
from pathlib import Path
from scripts.core.fetch_county_boundaries import load_study_area, get_county_boundaries


class TestFetchCountyBoundaries:
    """Tests for the fetch_county_boundaries module."""

    def test_load_study_area(self, test_config):
        """Test that the load_study_area function returns a dictionary."""
        with patch('scripts.core.fetch_county_boundaries.Config', return_value=test_config):
            study_area = load_study_area()
            assert isinstance(study_area, dict)
            assert 'states' in study_area
            assert 'counties' in study_area

    @patch('scripts.core.fetch_county_boundaries.load_study_area')
    @patch('scripts.core.fetch_county_boundaries.requests.get')
    def test_get_county_boundaries(self, mock_get, mock_load_study_area, test_config, temp_dir):
        """Test that get_county_boundaries returns a DataFrame and bbox."""
        # Mock study area
        mock_study_area = {
            'states': [
                {'name': 'Georgia', 'abbr': 'GA'},
            ],
            'counties': {
                'Georgia': [
                    {'name': 'Fulton', 'fips': '13121'},
                    {'name': 'DeKalb', 'fips': '13089'}
                ]
            }
        }
        mock_load_study_area.return_value = mock_study_area
        
        # Mock the response from the Census API
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        # Create a sample GeoJSON response
        geojson_data = {
            'type': 'FeatureCollection',
            'features': [
                {
                    'type': 'Feature',
                    'properties': {
                        'GEOID': '13121',  # Fulton County
                        'NAME': 'Fulton',
                        'STATE': '13',
                        'STUSPS': 'GA',
                        'STATEFP': '13',
                        'COUNTYFP': '121',
                        'ALAND': 1335423423,
                        'AWATER': 42534534
                    },
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': [
                            [
                                [-84.5, 33.5],
                                [-84.5, 34.0],
                                [-84.0, 34.0],
                                [-84.0, 33.5],
                                [-84.5, 33.5]
                            ]
                        ]
                    }
                },
                {
                    'type': 'Feature',
                    'properties': {
                        'GEOID': '13089',  # DeKalb County
                        'NAME': 'DeKalb',
                        'STATE': '13',
                        'STUSPS': 'GA',
                        'STATEFP': '13',
                        'COUNTYFP': '089',
                        'ALAND': 1299423423,
                        'AWATER': 32534534
                    },
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': [
                            [
                                [-84.2, 33.6],
                                [-84.2, 33.9],
                                [-83.8, 33.9],
                                [-83.8, 33.6],
                                [-84.2, 33.6]
                            ]
                        ]
                    }
                }
            ]
        }
        
        mock_response.json.return_value = geojson_data
        mock_get.return_value = mock_response
        
        # Call the function with our mocked response
        counties_df, bbox = get_county_boundaries(test_config)
        
        # Verify the function called requests.get with the right parameters
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        base_url = args[0]
        params = kwargs.get('params', {})
        
        assert "tigerweb.geo.census.gov" in base_url
        assert "GEOID IN" in params['where']
        assert "13121" in params['where']
        assert "13089" in params['where']
        
        # Verify the DataFrame returned has the expected columns
        assert isinstance(counties_df, pd.DataFrame)
        assert 'GEOID' in counties_df.columns
        assert 'NAME' in counties_df.columns
        assert 'STATE' in counties_df.columns
        
        # Verify the bbox is properly calculated
        assert isinstance(bbox, dict)
        assert 'north' in bbox
        assert 'south' in bbox
        assert 'east' in bbox
        assert 'west' in bbox
        
        # Check that files were saved
        county_data_dir = Path(test_config.get_path('data.input.county_data'))
        assert (county_data_dir / 'county_boundaries.geojson').exists()
        assert (county_data_dir / 'study_area_bbox.json').exists()
        assert (county_data_dir / 'county_metadata.csv').exists()
        
        # Verify the saved bbox
        with open(county_data_dir / 'study_area_bbox.json', 'r') as f:
            saved_bbox = json.load(f)
            assert saved_bbox['north'] > 33.9  # Should include buffer
            assert saved_bbox['south'] < 33.5  # Should include buffer
            assert saved_bbox['east'] > -83.8  # Should include buffer
            assert saved_bbox['west'] < -84.5  # Should include buffer

    @patch('scripts.core.fetch_county_boundaries.load_study_area')
    @patch('scripts.core.fetch_county_boundaries.requests.get')
    def test_get_county_boundaries_error(self, mock_get, mock_load_study_area, test_config):
        """Test that get_county_boundaries handles errors correctly."""
        # Mock study area
        mock_study_area = {
            'states': [
                {'name': 'Georgia', 'abbr': 'GA'},
            ],
            'counties': {
                'Georgia': [
                    {'name': 'Fulton', 'fips': '13121'},
                    {'name': 'DeKalb', 'fips': '13089'}
                ]
            }
        }
        mock_load_study_area.return_value = mock_study_area
        
        # Mock error response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        # Check that it raises an exception
        with pytest.raises(Exception, match="Error fetching county boundaries"):
            get_county_boundaries(test_config)

    @patch('scripts.core.fetch_county_boundaries.load_study_area')
    @patch('scripts.core.fetch_county_boundaries.requests.get')
    def test_get_county_boundaries_missing_counties(self, mock_get, mock_load_study_area, test_config):
        """Test that get_county_boundaries handles missing counties correctly."""
        # Mock study area
        mock_study_area = {
            'states': [
                {'name': 'Georgia', 'abbr': 'GA'},
            ],
            'counties': {
                'Georgia': [
                    {'name': 'Fulton', 'fips': '13121'},
                    {'name': 'DeKalb', 'fips': '13089'}
                ]
            }
        }
        mock_load_study_area.return_value = mock_study_area
        
        # Mock successful response but with missing counties
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        # Create GeoJSON with only one county
        geojson_data = {
            'type': 'FeatureCollection',
            'features': [
                {
                    'type': 'Feature',
                    'properties': {
                        'GEOID': '13121',  # Only Fulton County
                        'NAME': 'Fulton',
                        'STATE': '13',
                        'STUSPS': 'GA',
                        'STATEFP': '13',
                        'COUNTYFP': '121',
                        'ALAND': 1335423423,
                        'AWATER': 42534534
                    },
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': [
                            [
                                [-84.5, 33.5],
                                [-84.5, 34.0],
                                [-84.0, 34.0],
                                [-84.0, 33.5],
                                [-84.5, 33.5]
                            ]
                        ]
                    }
                }
            ]
        }
        
        mock_response.json.return_value = geojson_data
        mock_get.return_value = mock_response
        
        # This should run without error but print a warning
        with patch('builtins.print') as mock_print:
            counties_df, bbox = get_county_boundaries(test_config)
            
            # Verify that warnings were printed
            mock_print.assert_any_call("\nWARNING: Missing configured counties:")
            
            # Check that we have only one county in the DataFrame
            assert len(counties_df) == 1
            assert counties_df['GEOID'].iloc[0] == '13121' 