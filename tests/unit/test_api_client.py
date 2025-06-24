"""Unit tests for API client components."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from socialmapper.api.client import SocialMapperClient
from socialmapper.api.builder import SocialMapperBuilder
from socialmapper.api.result_types import Ok, Err


class TestSocialMapperClient:
    """Test cases for SocialMapperClient."""

    @pytest.fixture
    def mock_config(self) -> Dict[str, Any]:
        """Mock configuration for client."""
        return {
            "census_api_key": "test_key",
            "cache_enabled": True,
            "travel_mode": "walk",
            "travel_time": 15
        }

    def test_client_initialization(self, mock_config):
        """Test client initializes correctly."""
        with patch("socialmapper.api.client.SocialMapperClient._validate_config") as mock_validate:
            client = SocialMapperClient(config=mock_config)
            assert client is not None
            mock_validate.assert_called_once()

    def test_client_context_manager(self, mock_config):
        """Test client works as context manager."""
        with patch("socialmapper.api.client.SocialMapperClient._validate_config"):
            with SocialMapperClient(config=mock_config) as client:
                assert client is not None

    def test_poi_query_success(self, mock_config, mock_osm_response):
        """Test successful POI query."""
        with patch("socialmapper.api.client.SocialMapperClient._validate_config"):
            with patch("socialmapper.api.client.SocialMapperClient._execute_poi_query") as mock_execute:
                mock_execute.return_value = Ok(mock_osm_response)
                
                client = SocialMapperClient(config=mock_config)
                result = client.poi_query("library")
                
                assert result.is_ok()
                data = result.unwrap()
                assert "elements" in data

    def test_poi_query_failure(self, mock_config):
        """Test POI query failure handling."""
        with patch("socialmapper.api.client.SocialMapperClient._validate_config"):
            with patch("socialmapper.api.client.SocialMapperClient._execute_poi_query") as mock_execute:
                mock_execute.return_value = Err("API Error")
                
                client = SocialMapperClient(config=mock_config)
                result = client.poi_query("library")
                
                assert result.is_err()
                assert result.unwrap_err() == "API Error"

    @pytest.mark.asyncio
    async def test_async_poi_query(self, mock_config, mock_osm_response):
        """Test async POI query."""
        with patch("socialmapper.api.async_client.AsyncSocialMapperClient._validate_config"):
            with patch("socialmapper.api.async_client.AsyncSocialMapperClient._execute_poi_query") as mock_execute:
                mock_execute.return_value = Ok(mock_osm_response)
                
                from socialmapper.api.async_client import AsyncSocialMapperClient
                client = AsyncSocialMapperClient(config=mock_config)
                result = await client.poi_query("library")
                
                assert result.is_ok()


class TestSocialMapperBuilder:
    """Test cases for SocialMapperBuilder."""

    def test_builder_initialization(self):
        """Test builder initializes with defaults."""
        builder = SocialMapperBuilder()
        assert builder is not None

    def test_builder_poi_query(self):
        """Test builder POI query configuration."""
        builder = SocialMapperBuilder()
        result = builder.poi_query("library")
        assert result is builder  # Check fluent interface

    def test_builder_travel_mode(self):
        """Test builder travel mode configuration."""
        builder = SocialMapperBuilder()
        result = builder.set_travel_mode("bike")
        assert result is builder

    def test_builder_travel_time(self):
        """Test builder travel time configuration."""
        builder = SocialMapperBuilder()
        result = builder.set_travel_time(20)
        assert result is builder

    def test_builder_build_and_run(self):
        """Test builder build and run functionality."""
        with patch("socialmapper.api.builder.SocialMapperBuilder._create_client") as mock_create:
            mock_client = Mock()
            mock_client.run.return_value = Ok({"data": "test"})
            mock_create.return_value = mock_client
            
            builder = SocialMapperBuilder()
            result = builder.poi_query("library").build().run()
            
            assert result.is_ok()
            mock_create.assert_called_once()

    def test_builder_invalid_travel_mode(self):
        """Test builder with invalid travel mode."""
        builder = SocialMapperBuilder()
        with pytest.raises(ValueError, match="Invalid travel mode"):
            builder.set_travel_mode("invalid_mode")

    def test_builder_invalid_travel_time(self):
        """Test builder with invalid travel time."""
        builder = SocialMapperBuilder()
        with pytest.raises(ValueError, match="Travel time must be positive"):
            builder.set_travel_time(-5)


class TestResultTypes:
    """Test cases for Result types."""

    def test_ok_result(self):
        """Test Ok result type."""
        result = Ok("success")
        assert result.is_ok()
        assert not result.is_err()
        assert result.unwrap() == "success"

    def test_err_result(self):
        """Test Err result type."""
        result = Err("error")
        assert result.is_err()
        assert not result.is_ok()
        assert result.unwrap_err() == "error"

    def test_ok_unwrap_err_raises(self):
        """Test that unwrap_err on Ok raises exception."""
        result = Ok("success")
        with pytest.raises(ValueError, match="Called unwrap_err on Ok"):
            result.unwrap_err()

    def test_err_unwrap_raises(self):
        """Test that unwrap on Err raises exception."""
        result = Err("error")
        with pytest.raises(ValueError, match="Called unwrap on Err"):
            result.unwrap()

    def test_result_map(self):
        """Test Result map functionality."""
        result = Ok(5)
        mapped = result.map(lambda x: x * 2)
        assert mapped.is_ok()
        assert mapped.unwrap() == 10

        err_result = Err("error")
        mapped_err = err_result.map(lambda x: x * 2)
        assert mapped_err.is_err()
        assert mapped_err.unwrap_err() == "error"

    def test_result_map_err(self):
        """Test Result map_err functionality."""
        result = Err("error")
        mapped = result.map_err(lambda x: f"Mapped: {x}")
        assert mapped.is_err()
        assert mapped.unwrap_err() == "Mapped: error"

        ok_result = Ok(5)
        mapped_ok = ok_result.map_err(lambda x: f"Mapped: {x}")
        assert mapped_ok.is_ok()
        assert mapped_ok.unwrap() == 5