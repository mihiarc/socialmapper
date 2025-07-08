"""Tests for census domain entities."""

import pytest
from datetime import datetime
from socialmapper.census.domain.entities import (
    CensusVariable,
    GeographicUnit,
    CensusDataPoint,
    BoundaryData,
    GeocodeResult,
    CensusRequest,
    BlockGroupInfo
)


class TestCensusVariable:
    """Test CensusVariable entity."""

    def test_census_variable_creation(self):
        """Test creating a CensusVariable."""
        var = CensusVariable(
            code="B01001_001E",
            name="Total Population",
            description="Total population count"
        )
        
        assert var.code == "B01001_001E"
        assert var.name == "Total Population"
        assert var.description == "Total population count"

    def test_census_variable_validation(self):
        """Test CensusVariable validation."""
        # Valid variable
        var = CensusVariable(
            code="B01001_001E",
            name="Total Population"
        )
        assert var.code == "B01001_001E"
        
        # Invalid - empty code
        with pytest.raises(ValueError, match="Census variable code must be a non-empty string"):
            CensusVariable(code="", name="Test")
        
        # Invalid - empty name
        with pytest.raises(ValueError, match="Census variable name must be a non-empty string"):
            CensusVariable(code="B01001_001E", name="")


class TestGeographicUnit:
    """Test GeographicUnit entity."""

    def test_geographic_unit_creation(self):
        """Test creating a GeographicUnit."""
        unit = GeographicUnit(
            geoid="060750201001",
            name="Block Group 1, Census Tract 201, San Francisco County, California",
            state_fips="06",
            county_fips="075",
            tract_code="020100",
            block_group_code="1"
        )
        
        assert unit.geoid == "060750201001"
        assert unit.state_fips == "06"
        assert unit.county_fips == "075"
        assert unit.tract_code == "020100"
        assert unit.block_group_code == "1"
        assert unit.name == "Block Group 1, Census Tract 201, San Francisco County, California"

    def test_geographic_unit_validation(self):
        """Test GeographicUnit validation."""
        # Valid unit
        unit = GeographicUnit(geoid="060750201001")
        assert unit.geoid == "060750201001"
        
        # Invalid - empty geoid
        with pytest.raises(ValueError, match="GEOID cannot be empty"):
            GeographicUnit(geoid="")


class TestCensusDataPoint:
    """Test CensusDataPoint entity."""

    def test_census_data_point_creation(self):
        """Test creating CensusDataPoint."""
        var = CensusVariable(code="B01001_001E", name="Total Population")
        data = CensusDataPoint(
            geoid="060750201001",
            variable=var,
            value=1234.0,
            year=2022
        )
        
        assert data.geoid == "060750201001"
        assert data.variable.code == "B01001_001E"
        assert data.value == 1234.0
        assert data.year == 2022
        assert data.margin_of_error is None

    def test_census_data_point_with_moe(self):
        """Test CensusDataPoint with margin of error."""
        var = CensusVariable(code="B01001_001E", name="Total Population")
        data = CensusDataPoint(
            geoid="060750201001",
            variable=var,
            value=1234.0,
            year=2022,
            margin_of_error=50.0
        )
        
        assert data.margin_of_error == 50.0


class TestGeocodeResult:
    """Test GeocodeResult entity."""

    def test_geocode_result_creation(self):
        """Test creating a GeocodeResult."""
        result = GeocodeResult(
            latitude=37.7749,
            longitude=-122.4194,
            state_fips="06",
            county_fips="075",
            block_group_geoid="060750201001",
            confidence=0.95
        )
        
        assert result.latitude == 37.7749
        assert result.longitude == -122.4194
        assert result.state_fips == "06"
        assert result.county_fips == "075"
        assert result.block_group_geoid == "060750201001"
        assert result.confidence == 0.95


class TestBlockGroupInfo:
    """Test BlockGroupInfo entity."""

    def test_block_group_info_creation(self):
        """Test creating a BlockGroupInfo."""
        info = BlockGroupInfo(
            state_fips="06",
            county_fips="075",
            tract="020100",
            block_group="1",
            geoid="060750201001"
        )
        
        assert info.geoid == "060750201001"
        assert info.state_fips == "06"
        assert info.county_fips == "075"
        assert info.tract == "020100"
        assert info.block_group == "1"
    
    def test_block_group_info_full_geoid(self):
        """Test BlockGroupInfo full_geoid property."""
        info = BlockGroupInfo(
            state_fips="06",
            county_fips="075",
            tract="020100",
            block_group="1"
        )
        
        assert info.full_geoid == "060750201001"