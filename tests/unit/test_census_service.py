"""Unit tests for Census service components."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from socialmapper.census.services.census_service import CensusService
from socialmapper.census.domain.entities import CensusDataPoint, BlockGroupInfo
from socialmapper.census.infrastructure.cache import InMemoryCache


class TestCensusService:
    """Test cases for CensusService."""

    @pytest.fixture
    def mock_api_client(self):
        """Mock Census API client."""
        client = Mock()
        client.get_block_group_data.return_value = {
            "data": [["B01003_001E", "1250"]]
        }
        return client

    @pytest.fixture
    def mock_cache(self):
        """Mock cache implementation."""
        return InMemoryCache()

    @pytest.fixture
    def census_service(self, mock_api_client, mock_cache):
        """Census service with mocked dependencies."""
        return CensusService(
            api_client=mock_api_client,
            cache=mock_cache
        )

    def test_service_initialization(self, census_service):
        """Test service initializes correctly."""
        assert census_service is not None

    def test_get_demographics_success(self, census_service, sample_coordinates):
        """Test successful demographics retrieval."""
        # Mock the internal methods
        with patch.object(census_service, '_find_block_group') as mock_find:
            with patch.object(census_service, '_fetch_demographics') as mock_fetch:
                mock_find.return_value = BlockGroupInfo(
                    geoid="530330001001",
                    state="53",
                    county="033",
                    tract="000100",
                    block_group="1"
                )
                mock_fetch.return_value = CensusDataPoint(
                    geoid="530330001001",
                    total_population=1250,
                    median_income=75000
                )
                
                result = census_service.get_demographics(
                    latitude=sample_coordinates["latitude"],
                    longitude=sample_coordinates["longitude"]
                )
                
                assert result is not None
                assert result.total_population == 1250
                assert result.median_income == 75000

    def test_get_demographics_cache_hit(self, census_service, sample_coordinates, mock_cache):
        """Test demographics retrieval with cache hit."""
        # Pre-populate cache
        cache_key = f"demographics_{sample_coordinates['latitude']}_{sample_coordinates['longitude']}"
        cached_data = CensusDataPoint(
            geoid="530330001001",
            total_population=1250,
            median_income=75000
        )
        mock_cache.set(cache_key, cached_data)
        
        result = census_service.get_demographics(
            latitude=sample_coordinates["latitude"],
            longitude=sample_coordinates["longitude"]
        )
        
        assert result == cached_data

    def test_get_demographics_invalid_coordinates(self, census_service):
        """Test demographics with invalid coordinates."""
        with pytest.raises(ValueError, match="Invalid coordinates"):
            census_service.get_demographics(latitude=91.0, longitude=0.0)

        with pytest.raises(ValueError, match="Invalid coordinates"):
            census_service.get_demographics(latitude=0.0, longitude=181.0)

    @pytest.mark.asyncio
    async def test_async_get_demographics(self, mock_api_client, mock_cache, sample_coordinates):
        """Test async demographics retrieval."""
        # Create async version of service
        async_api_client = AsyncMock()
        async_api_client.get_block_group_data.return_value = {
            "data": [["B01003_001E", "1250"]]
        }
        
        from socialmapper.census.services.async_census_service import AsyncCensusService
        service = AsyncCensusService(
            api_client=async_api_client,
            cache=mock_cache
        )
        
        with patch.object(service, '_find_block_group') as mock_find:
            with patch.object(service, '_fetch_demographics') as mock_fetch:
                mock_find.return_value = BlockGroupInfo(
                    geoid="530330001001",
                    state="53",
                    county="033", 
                    tract="000100",
                    block_group="1"
                )
                mock_fetch.return_value = CensusDataPoint(
                    geoid="530330001001",
                    total_population=1250,
                    median_income=75000
                )
                
                result = await service.get_demographics(
                    latitude=sample_coordinates["latitude"],
                    longitude=sample_coordinates["longitude"]
                )
                
                assert result is not None
                assert result.total_population == 1250

    def test_batch_demographics(self, census_service):
        """Test batch demographics retrieval."""
        coordinates = [
            {"lat": 47.6062, "lon": -122.3321},
            {"lat": 47.6152, "lon": -122.3411},
            {"lat": 47.6205, "lon": -122.3501}
        ]
        
        with patch.object(census_service, 'get_demographics') as mock_get:
            mock_get.side_effect = [
                CensusDataPoint(geoid="1", total_population=1250, median_income=75000),
                CensusDataPoint(geoid="2", total_population=980, median_income=65000),
                CensusDataPoint(geoid="3", total_population=1340, median_income=85000)
            ]
            
            results = census_service.get_batch_demographics(coordinates)
            
            assert len(results) == 3
            assert all(isinstance(r, CensusDataPoint) for r in results)
            assert mock_get.call_count == 3

    def test_variable_mapping(self, census_service):
        """Test census variable mapping."""
        variables = census_service.get_available_variables()
        
        assert "total_population" in variables
        assert "median_income" in variables
        assert variables["total_population"] == "B01003_001E"
        assert variables["median_income"] == "B19013_001E"

    def test_error_handling_api_failure(self, census_service):
        """Test error handling when API fails."""
        with patch.object(census_service, '_fetch_demographics') as mock_fetch:
            mock_fetch.side_effect = Exception("API Error")
            
            with pytest.raises(Exception, match="API Error"):
                census_service.get_demographics(latitude=47.6062, longitude=-122.3321)

    @pytest.mark.benchmark
    def test_performance_single_request(self, census_service, benchmark, sample_coordinates):
        """Benchmark single demographics request."""
        with patch.object(census_service, 'get_demographics') as mock_get:
            mock_get.return_value = CensusDataPoint(
                geoid="530330001001",
                total_population=1250,
                median_income=75000
            )
            
            result = benchmark(
                census_service.get_demographics,
                latitude=sample_coordinates["latitude"],
                longitude=sample_coordinates["longitude"]
            )
            
            assert result is not None


class TestCensusDataPoint:
    """Test cases for CensusDataPoint entity."""

    def test_data_point_creation(self):
        """Test CensusDataPoint creation."""
        data_point = CensusDataPoint(
            geoid="530330001001",
            total_population=1250,
            median_income=75000
        )
        
        assert data_point.geoid == "530330001001"
        assert data_point.total_population == 1250
        assert data_point.median_income == 75000

    def test_data_point_validation(self):
        """Test CensusDataPoint validation."""
        with pytest.raises(ValueError, match="GEOID cannot be empty"):
            CensusDataPoint(geoid="", total_population=1250, median_income=75000)

        with pytest.raises(ValueError, match="Population cannot be negative"):
            CensusDataPoint(geoid="530330001001", total_population=-1, median_income=75000)

    def test_data_point_equality(self):
        """Test CensusDataPoint equality."""
        dp1 = CensusDataPoint(geoid="530330001001", total_population=1250, median_income=75000)
        dp2 = CensusDataPoint(geoid="530330001001", total_population=1250, median_income=75000)
        dp3 = CensusDataPoint(geoid="530330001002", total_population=1250, median_income=75000)
        
        assert dp1 == dp2
        assert dp1 != dp3

    def test_data_point_to_dict(self):
        """Test CensusDataPoint serialization."""
        data_point = CensusDataPoint(
            geoid="530330001001",
            total_population=1250,
            median_income=75000
        )
        
        result = data_point.to_dict()
        
        assert result["geoid"] == "530330001001"
        assert result["total_population"] == 1250
        assert result["median_income"] == 75000


class TestBlockGroupInfo:
    """Test cases for BlockGroupInfo entity."""

    def test_block_group_creation(self):
        """Test BlockGroupInfo creation."""
        bg_info = BlockGroupInfo(
            geoid="530330001001",
            state="53",
            county="033",
            tract="000100", 
            block_group="1"
        )
        
        assert bg_info.geoid == "530330001001"
        assert bg_info.state == "53"
        assert bg_info.county == "033"
        assert bg_info.tract == "000100"
        assert bg_info.block_group == "1"

    def test_block_group_validation(self):
        """Test BlockGroupInfo validation."""
        with pytest.raises(ValueError, match="Invalid state code"):
            BlockGroupInfo(
                geoid="530330001001",
                state="",
                county="033",
                tract="000100",
                block_group="1"
            )

    def test_block_group_fips_generation(self):
        """Test FIPS code generation."""
        bg_info = BlockGroupInfo(
            geoid="530330001001",
            state="53",
            county="033",
            tract="000100",
            block_group="1"
        )
        
        assert bg_info.county_fips == "53033"
        assert bg_info.tract_fips == "53033000100"