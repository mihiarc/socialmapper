"""Tests for SocialMapper exception hierarchy."""

import pytest

from socialmapper.exceptions import (
    AnalysisError,
    APIError,
    ConfigurationError,
    DataError,
    DataProcessingError,
    ExternalAPIError,
    FileSystemError,
    InvalidAPIResponseError,
    InvalidLocationError,
    InvalidPOICategoryError,
    MissingAPIKeyError,
    NetworkError,
    RateLimitError,
    SocialMapperError,
    ValidationError,
    VisualizationError,
)


class TestSocialMapperError:
    """Test base SocialMapperError."""

    def test_basic_error(self):
        error = SocialMapperError("Something went wrong")
        assert str(error) == "Something went wrong"

    def test_error_with_help_text(self):
        error = SocialMapperError(
            "Something went wrong",
            help_text="Try doing X instead"
        )
        assert "Something went wrong" in str(error)
        assert "Try doing X instead" in str(error)

    def test_help_text_attribute(self):
        error = SocialMapperError("Error", help_text="Help info")
        assert error.help_text == "Help info"

    def test_no_help_text_attribute(self):
        error = SocialMapperError("Error")
        assert error.help_text is None

    def test_catchable_as_exception(self):
        with pytest.raises(Exception):
            raise SocialMapperError("Test error")


class TestValidationError:
    """Test ValidationError."""

    def test_validation_error_inheritance(self):
        error = ValidationError("Invalid input")
        assert isinstance(error, SocialMapperError)

    def test_validation_error_message(self):
        error = ValidationError("Latitude must be between -90 and 90")
        assert "Latitude" in str(error)

    def test_catch_as_socialmapper_error(self):
        with pytest.raises(SocialMapperError):
            raise ValidationError("Test")


class TestAPIError:
    """Test APIError."""

    def test_api_error_inheritance(self):
        error = APIError("API call failed")
        assert isinstance(error, SocialMapperError)

    def test_api_error_message(self):
        error = APIError("Census API returned 403")
        assert "403" in str(error)


class TestDataError:
    """Test DataError."""

    def test_data_error_inheritance(self):
        error = DataError("No data found")
        assert isinstance(error, SocialMapperError)


class TestAnalysisError:
    """Test AnalysisError."""

    def test_analysis_error_inheritance(self):
        error = AnalysisError("Failed to generate isochrone")
        assert isinstance(error, SocialMapperError)


class TestMissingAPIKeyError:
    """Test MissingAPIKeyError."""

    def test_default_service(self):
        error = MissingAPIKeyError()
        assert "Census" in str(error)
        assert "API key not found" in str(error)

    def test_custom_service(self):
        error = MissingAPIKeyError(service="Mapbox")
        assert "Mapbox" in str(error)

    def test_help_text_included(self):
        error = MissingAPIKeyError()
        # Check help text contains guidance
        assert "api.census.gov" in str(error)
        assert "environment variable" in str(error).lower() or "CENSUS_API_KEY" in str(error)

    def test_inheritance(self):
        error = MissingAPIKeyError()
        assert isinstance(error, ValidationError)
        assert isinstance(error, SocialMapperError)


class TestInvalidLocationError:
    """Test InvalidLocationError."""

    def test_basic_location_error(self):
        error = InvalidLocationError("Nowhere, XX")
        assert "Nowhere, XX" in str(error)
        assert "Could not find location" in str(error)

    def test_with_suggestions(self):
        error = InvalidLocationError(
            "Portand, OR",
            suggestions=["Portland, OR", "Portland, ME"]
        )
        assert "Portland, OR" in str(error)
        assert "Did you mean" in str(error)

    def test_help_text_included(self):
        error = InvalidLocationError("Bad Location")
        # Check help text contains format guidance
        assert "City, State" in str(error)

    def test_inheritance(self):
        error = InvalidLocationError("Test")
        assert isinstance(error, ValidationError)
        assert isinstance(error, SocialMapperError)


class TestInvalidPOICategoryError:
    """Test InvalidPOICategoryError."""

    def test_invalid_category(self):
        error = InvalidPOICategoryError(
            "bad_category",
            valid_categories=["restaurant", "cafe", "library"]
        )
        assert "bad_category" in str(error)
        assert "Invalid POI category" in str(error)

    def test_lists_valid_categories(self):
        valid = ["restaurant", "cafe", "library"]
        error = InvalidPOICategoryError("invalid", valid_categories=valid)
        for cat in valid:
            assert cat in str(error)

    def test_inheritance(self):
        error = InvalidPOICategoryError("test", valid_categories=["a"])
        assert isinstance(error, ValidationError)
        assert isinstance(error, SocialMapperError)


class TestNetworkError:
    """Test NetworkError."""

    def test_basic_network_error(self):
        error = NetworkError("Census API")
        assert "Census API" in str(error)
        assert "Network error" in str(error)

    def test_with_original_error(self):
        error = NetworkError(
            "Overpass API",
            original_error="Connection refused"
        )
        assert "Connection refused" in str(error)

    def test_with_retry_suggestion(self):
        error = NetworkError("API", retry_suggested=True)
        error_str = str(error).lower()
        assert "try again" in error_str or "retry" in error_str

    def test_without_retry_suggestion(self):
        error = NetworkError("API", retry_suggested=False)
        # Should not suggest retry
        error_str = str(error).lower()
        # Still provides troubleshooting, just not retry
        assert "troubleshooting" in error_str.lower() or "check" in error_str.lower()

    def test_inheritance(self):
        error = NetworkError("Test")
        assert isinstance(error, APIError)
        assert isinstance(error, SocialMapperError)


class TestRateLimitError:
    """Test RateLimitError."""

    def test_basic_rate_limit_error(self):
        error = RateLimitError("Census API")
        assert "Rate limit" in str(error)
        assert "Census API" in str(error)

    def test_with_retry_after(self):
        error = RateLimitError("API", retry_after=30)
        assert "30" in str(error)

    def test_help_text_included(self):
        error = RateLimitError("API")
        # Check help text contains rate limiting tips
        assert "delay" in str(error).lower() or "batch" in str(error).lower()

    def test_inheritance(self):
        error = RateLimitError("Test")
        assert isinstance(error, APIError)
        assert isinstance(error, SocialMapperError)


class TestInvalidAPIResponseError:
    """Test InvalidAPIResponseError."""

    def test_basic_invalid_response(self):
        error = InvalidAPIResponseError("Census API")
        assert "Invalid response" in str(error)
        assert "Census API" in str(error)

    def test_with_status_code(self):
        error = InvalidAPIResponseError("API", status_code=403)
        assert "403" in str(error)

    def test_403_help_text(self):
        error = InvalidAPIResponseError("API", status_code=403)
        assert "API key" in str(error).lower() or "permission" in str(error).lower()

    def test_404_help_text(self):
        error = InvalidAPIResponseError("API", status_code=404)
        assert "not found" in str(error).lower()

    def test_500_help_text(self):
        error = InvalidAPIResponseError("API", status_code=500)
        assert "server" in str(error).lower()

    def test_with_details(self):
        error = InvalidAPIResponseError(
            "API",
            status_code=400,
            details="Missing required field: location"
        )
        assert "Missing required field" in str(error)

    def test_inheritance(self):
        error = InvalidAPIResponseError("Test")
        assert isinstance(error, APIError)
        assert isinstance(error, SocialMapperError)


class TestLegacyAliases:
    """Test legacy exception aliases for backward compatibility."""

    def test_configuration_error_alias(self):
        assert ConfigurationError is ValidationError

    def test_external_api_error_alias(self):
        assert ExternalAPIError is APIError

    def test_data_processing_error_alias(self):
        assert DataProcessingError is DataError

    def test_file_system_error_alias(self):
        assert FileSystemError is SocialMapperError

    def test_visualization_error_alias(self):
        assert VisualizationError is SocialMapperError


class TestExceptionHierarchy:
    """Test the exception hierarchy structure."""

    def test_all_inherit_from_base(self):
        exceptions = [
            ValidationError("test"),
            APIError("test"),
            DataError("test"),
            AnalysisError("test"),
            MissingAPIKeyError(),
            InvalidLocationError("test"),
            InvalidPOICategoryError("test", ["a"]),
            NetworkError("test"),
            RateLimitError("test"),
            InvalidAPIResponseError("test"),
        ]
        for exc in exceptions:
            assert isinstance(exc, SocialMapperError)

    def test_catch_all_with_base(self):
        """Verify all exceptions can be caught with base class."""
        def raise_exception(exc):
            raise exc

        exceptions_to_test = [
            ValidationError("test"),
            APIError("test"),
            DataError("test"),
            AnalysisError("test"),
            MissingAPIKeyError(),
            InvalidLocationError("test"),
            InvalidPOICategoryError("test", ["a"]),
            NetworkError("test"),
            RateLimitError("test"),
            InvalidAPIResponseError("test"),
        ]

        for exc in exceptions_to_test:
            with pytest.raises(SocialMapperError):
                raise_exception(exc)

    def test_specific_catch(self):
        """Test catching specific exception types."""
        with pytest.raises(MissingAPIKeyError):
            raise MissingAPIKeyError()

        with pytest.raises(ValidationError):
            raise MissingAPIKeyError()

        with pytest.raises(NetworkError):
            raise NetworkError("API")

        with pytest.raises(APIError):
            raise NetworkError("API")
