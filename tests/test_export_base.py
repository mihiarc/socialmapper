"""Tests for export base classes and configuration."""

from pathlib import Path

import pytest

from socialmapper.export.base import (
    BaseExporter,
    DataPreparationError,
    DataPrepConfig,
    ExportError,
    FormatNotSupportedError,
)


class TestDataPrepConfig:
    """Test DataPrepConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = DataPrepConfig()

        # Check preferred column order
        assert isinstance(config.preferred_column_order, list)
        assert "census_block_group" in config.preferred_column_order
        assert "poi_name" in config.preferred_column_order
        assert "total_population" in config.preferred_column_order

        # Check excluded columns
        assert isinstance(config.excluded_columns, list)
        assert "geometry" in config.excluded_columns
        assert "GEOID" in config.excluded_columns

        # Check deduplication columns
        assert isinstance(config.deduplication_columns, list)
        assert "census_block_group" in config.deduplication_columns
        assert "poi_name" in config.deduplication_columns

        # Check aggregation rules
        assert isinstance(config.deduplication_agg_rules, dict)
        assert config.deduplication_agg_rules["distance_miles"] == "min"
        assert config.deduplication_agg_rules["travel_time_minutes"] == "min"

    def test_custom_config(self):
        """Test custom configuration."""
        custom_order = ["custom_col1", "custom_col2"]
        custom_excluded = ["exclude1", "exclude2"]

        config = DataPrepConfig(
            preferred_column_order=custom_order,
            excluded_columns=custom_excluded
        )

        assert config.preferred_column_order == custom_order
        assert config.excluded_columns == custom_excluded

    def test_config_independence(self):
        """Test that configs are independent."""
        config1 = DataPrepConfig()
        config2 = DataPrepConfig()

        # Modify config1
        config1.preferred_column_order.append("new_column")

        # config2 should not be affected
        assert "new_column" not in config2.preferred_column_order


class MockExporter(BaseExporter):
    """Mock exporter for testing base class."""

    def export(self, data, output_path, **kwargs):
        """Mock export implementation."""
        validated_path = self.validate_output_path(output_path)
        return str(validated_path)

    def get_file_extension(self):
        """Return mock file extension."""
        return ".mock"

    def supports_geometry(self):
        """Mock geometry support."""
        return False


class TestBaseExporter:
    """Test BaseExporter abstract base class."""

    def test_initialization(self):
        """Test exporter initialization."""
        # With default config
        exporter = MockExporter()
        assert isinstance(exporter.config, DataPrepConfig)

        # With custom config
        custom_config = DataPrepConfig(
            preferred_column_order=["col1", "col2"]
        )
        exporter = MockExporter(config=custom_config)
        assert exporter.config == custom_config

    def test_validate_output_path(self, tmp_path):
        """Test output path validation."""
        exporter = MockExporter()

        # Test with string path
        output_path = str(tmp_path / "output.txt")
        validated = exporter.validate_output_path(output_path)
        assert isinstance(validated, Path)
        assert validated.suffix == ".mock"

        # Test with Path object
        output_path = tmp_path / "output.mock"
        validated = exporter.validate_output_path(output_path)
        assert validated == output_path

        # Test directory creation
        nested_path = tmp_path / "nested" / "dir" / "output.mock"
        validated = exporter.validate_output_path(nested_path)
        assert validated.parent.exists()

    def test_abstract_methods(self):
        """Test that abstract methods must be implemented."""
        # Cannot instantiate BaseExporter directly
        with pytest.raises(TypeError):
            BaseExporter()

        # Mock exporter should work
        exporter = MockExporter()
        assert exporter.get_file_extension() == ".mock"
        assert exporter.supports_geometry() is False


class TestExportExceptions:
    """Test export exception hierarchy."""

    def test_export_error(self):
        """Test base ExportError."""
        with pytest.raises(ExportError) as exc_info:
            raise ExportError("Test error")
        assert str(exc_info.value) == "Test error"

    def test_data_preparation_error(self):
        """Test DataPreparationError."""
        with pytest.raises(DataPreparationError) as exc_info:
            raise DataPreparationError("Data prep failed")
        assert str(exc_info.value) == "Data prep failed"
        assert isinstance(exc_info.value, ExportError)

    def test_format_not_supported_error(self):
        """Test FormatNotSupportedError."""
        with pytest.raises(FormatNotSupportedError) as exc_info:
            raise FormatNotSupportedError("Format XYZ not supported")
        assert str(exc_info.value) == "Format XYZ not supported"
        assert isinstance(exc_info.value, ExportError)

    def test_exception_hierarchy(self):
        """Test exception inheritance."""
        # All custom exceptions should inherit from ExportError
        assert issubclass(DataPreparationError, ExportError)
        assert issubclass(FormatNotSupportedError, ExportError)

        # ExportError should inherit from Exception
        assert issubclass(ExportError, Exception)
