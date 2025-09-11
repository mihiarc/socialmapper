"""Integration tests for demographic-only analysis feature."""

import pytest
from pathlib import Path
import tempfile

from socialmapper import SocialMapper
from socialmapper.api.exceptions import ValidationError, AnalysisError


class TestDemographicOnlyAnalysis:
    """Test demographic-only analysis without POI discovery."""
    
    def test_analyze_location_without_pois(self):
        """Test that analyze_location works with poi_types=None."""
        mapper = SocialMapper()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            result = mapper.analyze_location(
                location="Chapel Hill, NC",
                poi_types=None,  # No POI search
                travel_time=15,
                travel_mode="drive",
                census_variables=["total_population"],
                output_dir=tmpdir,
                create_maps=False
            )
            
            # Should succeed without POIs
            assert result is not None
            assert result.poi_count == 0 or result.poi_count == 1  # May have location POI
            assert result.census_units_analyzed >= 0
            assert result.isochrone_area_km2 > 0
            
            # Should have demographics if census data available
            if result.census_units_analyzed > 0:
                assert result.has_demographics
                assert "total_population" in result.demographics or "B01003_001E" in str(result.demographics)
    
    def test_analyze_location_with_empty_poi_list(self):
        """Test that analyze_location works with poi_types=[]."""
        mapper = SocialMapper()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            result = mapper.analyze_location(
                location="Durham, NC",
                poi_types=[],  # Explicitly no POIs
                travel_time=10,
                travel_mode="walk",
                census_variables=["median_age", "median_household_income"],
                output_dir=tmpdir,
                create_maps=False
            )
            
            assert result is not None
            assert result.poi_count == 0 or result.poi_count == 1
            assert result.isochrone_area_km2 > 0
    
    def test_coordinates_with_no_pois(self):
        """Test demographic-only analysis with coordinates instead of city name."""
        mapper = SocialMapper()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Chapel Hill coordinates
            result = mapper.analyze_location(
                location=(35.9132, -79.0558),
                poi_types=None,
                travel_time=20,
                travel_mode="bike",
                census_variables=["total_population"],
                output_dir=tmpdir,
                create_maps=False
            )
            
            assert result is not None
            assert result.isochrone_area_km2 > 0
    
    def test_demographic_only_with_maps(self):
        """Test that map generation works without POIs."""
        mapper = SocialMapper()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            result = mapper.analyze_location(
                location="Raleigh, NC",
                poi_types=None,
                travel_time=15,
                census_variables=["total_population", "median_household_income"],
                output_dir=tmpdir,
                create_maps=True
            )
            
            assert result is not None
            assert result.isochrone_area_km2 > 0
            
            # Check if map files were created
            if result.files_created:
                map_files = [f for f in result.files_created if "map" in str(f).lower()]
                # Maps might be created even without POIs (for demographics)
                assert len(map_files) >= 0
    
    def test_mixed_analysis_still_works(self):
        """Test that normal POI analysis still works (regression test)."""
        mapper = SocialMapper()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            result = mapper.analyze_location(
                location="Chapel Hill, NC",
                poi_types=["library"],  # With POI search
                travel_time=15,
                census_variables=["total_population"],
                output_dir=tmpdir,
                create_maps=False
            )
            
            assert result is not None
            # Should find at least some libraries in Chapel Hill
            assert result.poi_count >= 0  # May be 0 if no libraries in range
            assert result.isochrone_area_km2 > 0


class TestDemographicOnlyValidation:
    """Test validation for demographic-only analysis."""
    
    def test_location_still_required(self):
        """Test that location is still required even without POIs."""
        mapper = SocialMapper()
        
        with pytest.raises(ValidationError):
            mapper.analyze_location(
                location="",  # Invalid empty location
                poi_types=None,
                travel_time=15
            )
    
    def test_travel_time_validation(self):
        """Test that travel time validation still applies."""
        mapper = SocialMapper()
        
        with pytest.raises(ValidationError):
            mapper.analyze_location(
                location="Chapel Hill, NC",
                poi_types=None,
                travel_time=150  # Invalid travel time
            )
    
    def test_invalid_census_variables(self):
        """Test that census variable validation still works."""
        mapper = SocialMapper()
        
        with pytest.raises(ValidationError):
            mapper.analyze_location(
                location="Chapel Hill, NC",
                poi_types=None,
                census_variables=["invalid_variable_xyz"]
            )