"""Tests for custom exceptions."""

import pytest

from socialmapper.exceptions import (
    SocialMapperError,
    ValidationError,
    APIError,
    DataError,
    AnalysisError,
    # Helpful specific exceptions
    MissingAPIKeyError,
    InvalidLocationError,
    InvalidPOICategoryError,
    NetworkError,
    RateLimitError,
    InvalidAPIResponseError,
    # Legacy aliases
    ConfigurationError,
    ExternalAPIError,
    DataProcessingError,
    FileSystemError,
    VisualizationError,
)


class TestExceptionHierarchy:
    """Test exception inheritance hierarchy."""

    def test_base_exception(self):
        """Test base SocialMapperError."""
        with pytest.raises(SocialMapperError) as exc_info:
            raise SocialMapperError("Base error")
        assert str(exc_info.value) == "Base error"

    def test_all_core_exceptions_inherit_from_base(self):
        """Test all custom exceptions inherit from SocialMapperError."""
        core_exceptions = [
            ValidationError,
            APIError,
            DataError,
            AnalysisError,
        ]

        for exc_class in core_exceptions:
            assert issubclass(exc_class, SocialMapperError)

    def test_legacy_aliases_work(self):
        """Test legacy exception aliases still work."""
        # These should all be aliases to core exceptions
        assert ConfigurationError == ValidationError
        assert ExternalAPIError == APIError
        assert DataProcessingError == DataError
        assert FileSystemError == SocialMapperError
        assert VisualizationError == SocialMapperError


class TestValidationErrors:
    """Test validation exceptions."""

    def test_validation_error(self):
        """Test ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Invalid input")
        assert "Invalid input" in str(exc_info.value)

    def test_configuration_error_alias(self):
        """Test ConfigurationError is alias for ValidationError."""
        with pytest.raises(ValidationError):
            raise ConfigurationError("Invalid config")


class TestAPIErrors:
    """Test API-related exceptions."""

    def test_api_error(self):
        """Test APIError."""
        with pytest.raises(APIError) as exc_info:
            raise APIError("API failed")
        assert "API failed" in str(exc_info.value)

    def test_external_api_error_alias(self):
        """Test ExternalAPIError is alias for APIError."""
        with pytest.raises(APIError):
            raise ExternalAPIError("External API failed")


class TestDataErrors:
    """Test data-related exceptions."""

    def test_data_error(self):
        """Test DataError."""
        with pytest.raises(DataError) as exc_info:
            raise DataError("Processing failed")
        assert "Processing failed" in str(exc_info.value)

    def test_data_processing_error_alias(self):
        """Test DataProcessingError is alias for DataError."""
        with pytest.raises(DataError):
            raise DataProcessingError("Processing failed")


class TestAnalysisErrors:
    """Test analysis exceptions."""

    def test_analysis_error(self):
        """Test AnalysisError."""
        with pytest.raises(AnalysisError) as exc_info:
            raise AnalysisError("Analysis failed")
        assert "Analysis failed" in str(exc_info.value)


class TestCatchAll:
    """Test catching all library errors with base exception."""

    def test_catch_validation_error(self):
        """Test catching ValidationError with SocialMapperError."""
        with pytest.raises(SocialMapperError):
            raise ValidationError("Invalid input")

    def test_catch_api_error(self):
        """Test catching APIError with SocialMapperError."""
        with pytest.raises(SocialMapperError):
            raise APIError("API failed")

    def test_catch_data_error(self):
        """Test catching DataError with SocialMapperError."""
        with pytest.raises(SocialMapperError):
            raise DataError("Processing failed")

    def test_catch_analysis_error(self):
        """Test catching AnalysisError with SocialMapperError."""
        with pytest.raises(SocialMapperError):
            raise AnalysisError("Analysis failed")


class TestHelpfulExceptions:
    """Test helpful specific exceptions with guidance."""

    def test_missing_api_key_error(self):
        """Test MissingAPIKeyError provides helpful guidance."""
        with pytest.raises(MissingAPIKeyError) as exc_info:
            raise MissingAPIKeyError("Census")

        error_msg = str(exc_info.value)
        assert "Census API key not found" in error_msg
        assert "https://api.census.gov/data/key_signup.html" in error_msg
        assert "CENSUS_API_KEY" in error_msg
        assert "socialmapper-keys" in error_msg

    def test_missing_api_key_error_inherits_from_validation_error(self):
        """Test MissingAPIKeyError inherits from ValidationError."""
        assert issubclass(MissingAPIKeyError, ValidationError)
        with pytest.raises(ValidationError):
            raise MissingAPIKeyError()

    def test_invalid_location_error(self):
        """Test InvalidLocationError provides helpful suggestions."""
        with pytest.raises(InvalidLocationError) as exc_info:
            raise InvalidLocationError("Fake City, XX")

        error_msg = str(exc_info.value)
        assert "Could not find location: 'Fake City, XX'" in error_msg
        assert "City, State" in error_msg
        assert "Portland, OR" in error_msg

    def test_invalid_location_error_with_suggestions(self):
        """Test InvalidLocationError with custom suggestions."""
        with pytest.raises(InvalidLocationError) as exc_info:
            raise InvalidLocationError(
                "Portlnd",
                suggestions=["Portland, OR", "Portland, ME"]
            )

        error_msg = str(exc_info.value)
        assert "Did you mean one of these?" in error_msg
        assert "Portland, OR" in error_msg
        assert "Portland, ME" in error_msg

    def test_invalid_poi_category_error(self):
        """Test InvalidPOICategoryError lists valid categories."""
        valid_categories = ["food_and_drink", "shopping", "education"]

        with pytest.raises(InvalidPOICategoryError) as exc_info:
            raise InvalidPOICategoryError("invalid_cat", valid_categories)

        error_msg = str(exc_info.value)
        assert "Invalid POI category: 'invalid_cat'" in error_msg
        assert "food_and_drink" in error_msg
        assert "shopping" in error_msg
        assert "education" in error_msg
        assert "get_poi" in error_msg

    def test_network_error(self):
        """Test NetworkError provides troubleshooting help."""
        with pytest.raises(NetworkError) as exc_info:
            raise NetworkError("Census API", "Connection timeout")

        error_msg = str(exc_info.value)
        assert "Network error connecting to Census API" in error_msg
        assert "Connection timeout" in error_msg
        assert "internet connection" in error_msg
        assert "Try again" in error_msg

    def test_network_error_inherits_from_api_error(self):
        """Test NetworkError inherits from APIError."""
        assert issubclass(NetworkError, APIError)
        with pytest.raises(APIError):
            raise NetworkError("Test Service")

    def test_rate_limit_error(self):
        """Test RateLimitError provides rate limiting guidance."""
        with pytest.raises(RateLimitError) as exc_info:
            raise RateLimitError("Census API", retry_after=60)

        error_msg = str(exc_info.value)
        assert "Rate limit exceeded for Census API" in error_msg
        assert "Retry after: 60 seconds" in error_msg
        assert "Add delays between requests" in error_msg
        assert "caching" in error_msg

    def test_invalid_api_response_error_403(self):
        """Test InvalidAPIResponseError with 403 status."""
        with pytest.raises(InvalidAPIResponseError) as exc_info:
            raise InvalidAPIResponseError("Census API", status_code=403)

        error_msg = str(exc_info.value)
        assert "Invalid response from Census API (HTTP 403)" in error_msg
        assert "Invalid or missing API key" in error_msg

    def test_invalid_api_response_error_404(self):
        """Test InvalidAPIResponseError with 404 status."""
        with pytest.raises(InvalidAPIResponseError) as exc_info:
            raise InvalidAPIResponseError(
                "Census API",
                status_code=404,
                details="Resource not found"
            )

        error_msg = str(exc_info.value)
        assert "HTTP 404" in error_msg
        assert "Resource not found" in error_msg
        assert "Check location or identifier" in error_msg

    def test_invalid_api_response_error_500(self):
        """Test InvalidAPIResponseError with 500 status."""
        with pytest.raises(InvalidAPIResponseError) as exc_info:
            raise InvalidAPIResponseError("Census API", status_code=500)

        error_msg = str(exc_info.value)
        assert "HTTP 500" in error_msg
        assert "server error" in error_msg
        assert "Try again later" in error_msg
