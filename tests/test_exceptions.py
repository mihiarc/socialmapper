"""Tests for custom exceptions."""

import pytest

from socialmapper.exceptions import (
    # Analysis exceptions
    AnalysisError,
    CensusAPIError,
    ConfigurationError,
    # Data exceptions
    DataProcessingError,
    ErrorCategory,
    ErrorContext,
    # Error metadata
    ErrorSeverity,
    # API exceptions
    ExternalAPIError,
    # File system exceptions
    FileSystemError,
    GeocodingError,
    InsufficientDataError,
    InvalidCensusVariableError,
    # Configuration exceptions
    InvalidConfigurationError,
    # Location exceptions
    InvalidLocationError,
    InvalidTravelTimeError,
    IsochroneGenerationError,
    MapGenerationError,
    MissingAPIKeyError,
    NetworkAnalysisError,
    NoDataFoundError,
    OSMAPIError,
    # Base exceptions
    SocialMapperError,
    ValidationError,
    # Visualization exceptions
    VisualizationError,
)


class TestExceptionHierarchy:
    """Test exception inheritance hierarchy."""

    def test_base_exception(self):
        """Test base SocialMapperError."""
        with pytest.raises(SocialMapperError) as exc_info:
            raise SocialMapperError("Base error")
        assert str(exc_info.value) == "Base error"

    def test_all_exceptions_inherit_from_base(self):
        """Test all custom exceptions inherit from SocialMapperError."""
        exceptions = [
            ConfigurationError,
            ValidationError,
            ExternalAPIError,
            DataProcessingError,
            AnalysisError,
            VisualizationError,
            FileSystemError
        ]

        for exc_class in exceptions:
            assert issubclass(exc_class, SocialMapperError)

    def test_api_exceptions_hierarchy(self):
        """Test API exception hierarchy."""
        assert issubclass(CensusAPIError, ExternalAPIError)
        assert issubclass(OSMAPIError, ExternalAPIError)
        assert issubclass(GeocodingError, ExternalAPIError)


class TestConfigurationExceptions:
    """Test configuration-related exceptions."""

    def test_configuration_error(self):
        """Test ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            raise ConfigurationError("Invalid config")
        assert "Invalid config" in str(exc_info.value)

    def test_invalid_configuration_error(self):
        """Test InvalidConfigurationError."""
        with pytest.raises(InvalidConfigurationError) as exc_info:
            raise InvalidConfigurationError(
                field="timeout",
                value=-1,
                reason="Timeout must be positive"
            )
        assert "timeout" in str(exc_info.value)
        assert "-1" in str(exc_info.value)
        assert "Timeout must be positive" in str(exc_info.value)
        assert isinstance(exc_info.value, ConfigurationError)

    def test_missing_api_key_error(self):
        """Test MissingAPIKeyError."""
        with pytest.raises(MissingAPIKeyError) as exc_info:
            raise MissingAPIKeyError("CENSUS_API_KEY")
        assert "CENSUS_API_KEY" in str(exc_info.value)
        assert isinstance(exc_info.value, ConfigurationError)


class TestValidationExceptions:
    """Test validation exceptions."""

    def test_validation_error(self):
        """Test ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Invalid input")
        assert "Invalid input" in str(exc_info.value)

    def test_invalid_location_error(self):
        """Test InvalidLocationError."""
        with pytest.raises(InvalidLocationError) as exc_info:
            raise InvalidLocationError("Invalid address")
        assert "Invalid address" in str(exc_info.value)
        assert isinstance(exc_info.value, ValidationError)

    def test_invalid_travel_time_error(self):
        """Test InvalidTravelTimeError."""
        with pytest.raises(InvalidTravelTimeError) as exc_info:
            raise InvalidTravelTimeError(150)
        assert isinstance(exc_info.value, ValidationError)
        assert "150" in str(exc_info.value)
        assert "between 1 and 60" in str(exc_info.value)

    def test_invalid_census_variable_error(self):
        """Test InvalidCensusVariableError."""
        with pytest.raises(InvalidCensusVariableError) as exc_info:
            raise InvalidCensusVariableError("INVALID_VAR")
        assert "INVALID_VAR" in str(exc_info.value)
        assert isinstance(exc_info.value, ValidationError)


class TestAPIExceptions:
    """Test API-related exceptions."""

    def test_external_api_error(self):
        """Test ExternalAPIError."""
        with pytest.raises(ExternalAPIError) as exc_info:
            raise ExternalAPIError("API failed")
        assert "API failed" in str(exc_info.value)

    def test_census_api_error(self):
        """Test CensusAPIError."""
        with pytest.raises(CensusAPIError) as exc_info:
            raise CensusAPIError("Census API error", status_code=500)
        assert "Census API error" in str(exc_info.value)
        assert isinstance(exc_info.value, ExternalAPIError)

    def test_osm_api_error(self):
        """Test OSMAPIError."""
        with pytest.raises(OSMAPIError) as exc_info:
            raise OSMAPIError("OSM query failed")
        assert "OSM query failed" in str(exc_info.value)

    def test_geocoding_error(self):
        """Test GeocodingError."""
        with pytest.raises(GeocodingError) as exc_info:
            raise GeocodingError("Could not geocode address")
        assert "Could not geocode address" in str(exc_info.value)


class TestDataExceptions:
    """Test data-related exceptions."""

    def test_data_processing_error(self):
        """Test DataProcessingError."""
        with pytest.raises(DataProcessingError) as exc_info:
            raise DataProcessingError("Processing failed")
        assert "Processing failed" in str(exc_info.value)

    def test_no_data_found_error(self):
        """Test NoDataFoundError."""
        with pytest.raises(NoDataFoundError) as exc_info:
            raise NoDataFoundError("No census data")
        assert "No census data" in str(exc_info.value)
        assert isinstance(exc_info.value, DataProcessingError)

    def test_insufficient_data_error(self):
        """Test InsufficientDataError."""
        with pytest.raises(InsufficientDataError) as exc_info:
            raise InsufficientDataError(required=10, found=3)
        assert "Need at least 10" in str(exc_info.value)
        assert "only found 3" in str(exc_info.value)
        assert isinstance(exc_info.value, DataProcessingError)


class TestAnalysisExceptions:
    """Test analysis exceptions."""

    def test_analysis_error(self):
        """Test AnalysisError."""
        with pytest.raises(AnalysisError) as exc_info:
            raise AnalysisError("Analysis failed")
        assert "Analysis failed" in str(exc_info.value)

    def test_network_analysis_error(self):
        """Test NetworkAnalysisError."""
        with pytest.raises(NetworkAnalysisError) as exc_info:
            raise NetworkAnalysisError("Network analysis failed")
        assert "Network analysis failed" in str(exc_info.value)
        assert isinstance(exc_info.value, AnalysisError)

    def test_isochrone_generation_error(self):
        """Test IsochroneGenerationError."""
        with pytest.raises(IsochroneGenerationError) as exc_info:
            raise IsochroneGenerationError("Could not generate isochrone")
        assert "Could not generate isochrone" in str(exc_info.value)
        assert isinstance(exc_info.value, AnalysisError)


class TestVisualizationExceptions:
    """Test visualization exceptions."""

    def test_visualization_error(self):
        """Test VisualizationError."""
        with pytest.raises(VisualizationError) as exc_info:
            raise VisualizationError("Viz failed")
        assert "Viz failed" in str(exc_info.value)

    def test_map_generation_error(self):
        """Test MapGenerationError."""
        with pytest.raises(MapGenerationError) as exc_info:
            raise MapGenerationError("Could not create map")
        assert "Could not create map" in str(exc_info.value)
        assert isinstance(exc_info.value, VisualizationError)


class TestErrorMetadata:
    """Test error metadata enums and classes."""

    def test_error_severity(self):
        """Test ErrorSeverity enum."""
        assert hasattr(ErrorSeverity, 'INFO')
        assert hasattr(ErrorSeverity, 'WARNING')
        assert hasattr(ErrorSeverity, 'ERROR')
        assert hasattr(ErrorSeverity, 'CRITICAL')

    def test_error_category(self):
        """Test ErrorCategory enum."""
        assert hasattr(ErrorCategory, 'CONFIGURATION')
        assert hasattr(ErrorCategory, 'VALIDATION')
        assert hasattr(ErrorCategory, 'EXTERNAL_API')
        assert hasattr(ErrorCategory, 'DATA_PROCESSING')

    def test_error_context(self):
        """Test ErrorContext class."""
        context = ErrorContext(
            operation="test_operation",
            severity=ErrorSeverity.ERROR
        )
        assert context.operation == "test_operation"
        assert context.severity == ErrorSeverity.ERROR
