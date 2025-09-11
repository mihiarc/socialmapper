"""Tests for convenience API functions."""

import pytest
from unittest.mock import patch, MagicMock
import tempfile
from pathlib import Path

from socialmapper.api.convenience import (
    quick_analysis,
    analyze_libraries,
    analyze_schools,
    analyze_hospitals,
    analyze_parks,
    discover_food_access,
    discover_healthcare_access,
    compare_locations,
    analyze_custom_pois
)
from socialmapper.api.exceptions import ValidationError


class TestQuickAnalysis:
    """Test the quick_analysis convenience function."""
    
    @patch('socialmapper.api.convenience.SocialMapper')
    def test_quick_analysis_basic(self, mock_mapper_class):
        """Test basic quick_analysis functionality."""
        # Setup mock
        mock_mapper = MagicMock()
        mock_mapper_class.return_value = mock_mapper
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            'poi_count': 5,
            'census_units_analyzed': 10,
            'demographics': {'total_population': 50000}
        }
        mock_mapper.analyze_location.return_value = mock_result
        
        # Call function
        result = quick_analysis(
            location="Portland, OR",
            poi_search="amenity:library",
            travel_time=20
        )
        
        # Verify
        assert result['poi_count'] == 5
        mock_mapper.analyze_location.assert_called_once()
        call_args = mock_mapper.analyze_location.call_args
        assert call_args.kwargs['location'] == "Portland, OR"
        assert call_args.kwargs['poi_types'] == ['library']
        assert call_args.kwargs['travel_time'] == 20
    
    @patch('socialmapper.api.convenience.SocialMapper')
    def test_quick_analysis_simple_poi_search(self, mock_mapper_class):
        """Test quick_analysis with simple POI search (no colon)."""
        mock_mapper = MagicMock()
        mock_mapper_class.return_value = mock_mapper
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {'poi_count': 3}
        mock_mapper.analyze_location.return_value = mock_result
        
        result = quick_analysis(
            location="Seattle, WA",
            poi_search="school"
        )
        
        call_args = mock_mapper.analyze_location.call_args
        assert call_args.kwargs['poi_types'] == ['school']


class TestAnalyzePresets:
    """Test the preset analysis functions."""
    
    @patch('socialmapper.api.convenience.SocialMapper')
    def test_analyze_libraries(self, mock_mapper_class):
        """Test analyze_libraries preset function."""
        mock_mapper = MagicMock()
        mock_mapper_class.return_value = mock_mapper
        mock_result = MagicMock()
        mock_mapper.analyze_location.return_value = mock_result
        
        result = analyze_libraries(
            location="San Francisco, CA",
            travel_time=20,
            travel_mode="walk"
        )
        
        assert result == mock_result
        call_args = mock_mapper.analyze_location.call_args
        assert call_args.kwargs['location'] == "San Francisco, CA"
        assert call_args.kwargs['poi_types'] == ['library']
        assert call_args.kwargs['travel_time'] == 20
        assert call_args.kwargs['travel_mode'] == "walk"
        # Should include education-related census variables
        assert 'census_variables' in call_args.kwargs
        assert 'education_bachelors_plus' in call_args.kwargs['census_variables']
    
    @patch('socialmapper.api.convenience.SocialMapper')
    def test_analyze_schools(self, mock_mapper_class):
        """Test analyze_schools preset function."""
        mock_mapper = MagicMock()
        mock_mapper_class.return_value = mock_mapper
        mock_result = MagicMock()
        mock_mapper.analyze_location.return_value = mock_result
        
        result = analyze_schools(
            location="Chapel Hill, NC",
            include_demographics=True
        )
        
        call_args = mock_mapper.analyze_location.call_args
        assert call_args.kwargs['poi_types'] == ['school']
        assert 'census_variables' in call_args.kwargs
        assert 'children_under_18' in call_args.kwargs['census_variables']
    
    @patch('socialmapper.api.convenience.SocialMapper')
    def test_analyze_hospitals(self, mock_mapper_class):
        """Test analyze_hospitals preset function."""
        mock_mapper = MagicMock()
        mock_mapper_class.return_value = mock_mapper
        mock_result = MagicMock()
        mock_mapper.analyze_location.return_value = mock_result
        
        result = analyze_hospitals(
            location="Durham, NC"
        )
        
        call_args = mock_mapper.analyze_location.call_args
        assert call_args.kwargs['poi_types'] == ['hospital']
        # Default travel time for hospitals should be 30 minutes
        assert call_args.kwargs['travel_time'] == 30
        # Should include health-related census variables
        assert 'seniors_65_plus' in call_args.kwargs['census_variables']
    
    @patch('socialmapper.api.convenience.SocialMapper')
    def test_analyze_parks(self, mock_mapper_class):
        """Test analyze_parks preset function."""
        mock_mapper = MagicMock()
        mock_mapper_class.return_value = mock_mapper
        mock_result = MagicMock()
        mock_mapper.analyze_location.return_value = mock_result
        
        result = analyze_parks(
            location="Raleigh, NC"
        )
        
        call_args = mock_mapper.analyze_location.call_args
        assert call_args.kwargs['poi_types'] == ['park']
        # Default travel mode for parks should be walk
        assert call_args.kwargs['travel_mode'] == "walk"
    
    @patch('socialmapper.api.convenience.SocialMapper')
    def test_analyze_without_demographics(self, mock_mapper_class):
        """Test preset functions with include_demographics=False."""
        mock_mapper = MagicMock()
        mock_mapper_class.return_value = mock_mapper
        mock_result = MagicMock()
        mock_mapper.analyze_location.return_value = mock_result
        
        result = analyze_libraries(
            location="Test City, NC",
            include_demographics=False
        )
        
        call_args = mock_mapper.analyze_location.call_args
        assert call_args.kwargs['census_variables'] is None


class TestDiscoverFunctions:
    """Test the discovery convenience functions."""
    
    @patch('socialmapper.api.convenience.SocialMapper')
    def test_discover_food_access(self, mock_mapper_class):
        """Test discover_food_access function."""
        mock_mapper = MagicMock()
        mock_mapper_class.return_value = mock_mapper
        mock_result = MagicMock()
        mock_mapper.discover_nearby_pois.return_value = mock_result
        
        result = discover_food_access(
            location="Chapel Hill, NC",
            travel_time=15
        )
        
        assert result == mock_result
        call_args = mock_mapper.discover_nearby_pois.call_args
        assert call_args.kwargs['location'] == "Chapel Hill, NC"
        assert call_args.kwargs['travel_time'] == 15
        assert "food_and_drink" in call_args.kwargs['poi_categories']
        assert "shopping" in call_args.kwargs['poi_categories']
    
    @patch('socialmapper.api.convenience.SocialMapper')
    def test_discover_healthcare_access(self, mock_mapper_class):
        """Test discover_healthcare_access function."""
        mock_mapper = MagicMock()
        mock_mapper_class.return_value = mock_mapper
        mock_result = MagicMock()
        mock_mapper.discover_nearby_pois.return_value = mock_result
        
        result = discover_healthcare_access(
            location="Durham, NC"
        )
        
        call_args = mock_mapper.discover_nearby_pois.call_args
        assert call_args.kwargs['travel_time'] == 30  # Default for healthcare
        assert "healthcare" in call_args.kwargs['poi_categories']


class TestCompareLocations:
    """Test the compare_locations function."""
    
    @patch('socialmapper.api.convenience.SocialMapper')
    def test_compare_locations_success(self, mock_mapper_class):
        """Test comparing multiple locations."""
        mock_mapper = MagicMock()
        mock_mapper_class.return_value = mock_mapper
        
        # Create different mock results for each location
        mock_results = []
        for i in range(3):
            mock_result = MagicMock()
            mock_result.poi_count = i + 1
            mock_results.append(mock_result)
        
        mock_mapper.analyze_location.side_effect = mock_results
        
        locations = ["Portland, OR", "Seattle, WA", "San Francisco, CA"]
        results = compare_locations(
            locations=locations,
            poi_types=["library"],
            travel_time=15
        )
        
        assert len(results) == 3
        assert "Portland, OR" in results
        assert "Seattle, WA" in results
        assert "San Francisco, CA" in results
        assert mock_mapper.analyze_location.call_count == 3
    
    @patch('socialmapper.api.convenience.SocialMapper')
    def test_compare_locations_partial_failure(self, mock_mapper_class, capsys):
        """Test that compare_locations continues on partial failure."""
        mock_mapper = MagicMock()
        mock_mapper_class.return_value = mock_mapper
        
        # Make second location fail
        mock_result1 = MagicMock()
        mock_result3 = MagicMock()
        mock_mapper.analyze_location.side_effect = [
            mock_result1,
            Exception("Network error"),
            mock_result3
        ]
        
        locations = ["City1, ST", "City2, ST", "City3, ST"]
        results = compare_locations(
            locations=locations,
            poi_types=["school"]
        )
        
        # Should have results for 2 cities, not 3
        assert len(results) == 2
        assert "City1, ST" in results
        assert "City3, ST" in results
        assert "City2, ST" not in results
        
        # Check that error was printed
        captured = capsys.readouterr()
        assert "Analysis failed for City2, ST" in captured.out


class TestAnalyzeCustomPOIs:
    """Test the analyze_custom_pois legacy function."""
    
    @patch('socialmapper.api.convenience.SocialMapper')
    def test_analyze_custom_pois(self, mock_mapper_class):
        """Test analyze_custom_pois legacy compatibility function."""
        mock_mapper = MagicMock()
        mock_mapper_class.return_value = mock_mapper
        mock_result = MagicMock()
        mock_mapper.analyze_custom_pois.return_value = mock_result
        
        with tempfile.NamedTemporaryFile(suffix='.csv') as tmp:
            result = analyze_custom_pois(
                poi_file=tmp.name,
                travel_time=20,
                census_variables=["total_population"]
            )
            
            assert result == mock_result
            call_args = mock_mapper.analyze_custom_pois.call_args
            assert call_args.kwargs['poi_file'] == tmp.name
            assert call_args.kwargs['travel_time'] == 20
            assert call_args.kwargs['census_variables'] == ["total_population"]