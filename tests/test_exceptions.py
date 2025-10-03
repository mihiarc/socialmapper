"""Tests for custom exceptions."""

import pytest

from socialmapper.exceptions import (
    SocialMapperError,
    ValidationError,
    APIError,
    DataError,
    AnalysisError,
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
