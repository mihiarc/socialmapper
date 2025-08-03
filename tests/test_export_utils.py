"""Tests for export utilities."""

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import Point

from socialmapper.export.utils import (
    estimate_data_size,
    generate_output_path,
    get_format_info,
    select_export_format,
    validate_export_data,
)


class TestEstimateDataSize:
    """Test data size estimation."""

    def test_dataframe_size_estimation(self):
        """Test size estimation for regular DataFrame."""
        # Create a DataFrame with known size
        data = pd.DataFrame({
            'col1': range(1000),
            'col2': ['string' * 10] * 1000,
            'col3': np.random.rand(1000)
        })

        size_mb = estimate_data_size(data)
        assert isinstance(size_mb, float)
        assert size_mb > 0

    def test_geodataframe_size_estimation(self):
        """Test size estimation for GeoDataFrame."""
        # Create a GeoDataFrame
        points = [Point(x, y) for x, y in zip(range(100), range(100), strict=False)]
        gdf = gpd.GeoDataFrame({
            'id': range(100),
            'value': np.random.rand(100)
        }, geometry=points)

        size_mb = estimate_data_size(gdf)
        assert isinstance(size_mb, float)
        assert size_mb > 0

    def test_empty_dataframe_size(self):
        """Test size estimation for empty DataFrame."""
        empty_df = pd.DataFrame()
        size_mb = estimate_data_size(empty_df)
        assert size_mb >= 0  # Should handle empty DataFrames

    def test_large_dataframe_size(self):
        """Test that larger DataFrames have larger estimated sizes."""
        small_df = pd.DataFrame({'col': range(100)})
        large_df = pd.DataFrame({'col': range(10000)})

        small_size = estimate_data_size(small_df)
        large_size = estimate_data_size(large_df)

        assert large_size > small_size


class TestGenerateOutputPath:
    """Test output path generation."""

    def test_default_path_generation(self):
        """Test default path generation."""
        path = generate_output_path()
        assert isinstance(path, Path)
        assert path.parent == Path("output")
        assert path.name == "census_data_export.csv"

    def test_custom_filename(self):
        """Test custom filename."""
        path = generate_output_path(base_filename="my_data")
        assert path.name == "my_data_export.csv"

    def test_custom_output_dir(self):
        """Test custom output directory."""
        path = generate_output_path(output_dir="custom/dir")
        assert path.parent == Path("custom/dir")

    def test_format_extensions(self):
        """Test different format extensions."""
        # CSV
        path = generate_output_path(format="csv")
        assert path.suffix == ".csv"

        # Parquet
        path = generate_output_path(format="parquet")
        assert path.suffix == ".parquet"

        # GeoParquet
        path = generate_output_path(format="geoparquet")
        assert path.suffix == ".geoparquet"

    def test_parquet_with_geometry(self):
        """Test that parquet with geometry becomes geoparquet."""
        path = generate_output_path(format="parquet", include_geometry=True)
        assert path.suffix == ".geoparquet"

    def test_directory_creation(self, tmp_path):
        """Test that directories are created."""
        output_dir = tmp_path / "new" / "nested" / "dir"
        path = generate_output_path(output_dir=str(output_dir))

        # Directory should be created
        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_unknown_format(self):
        """Test unknown format defaults to CSV."""
        path = generate_output_path(format="unknown")
        assert path.suffix == ".csv"


class TestSelectExportFormat:
    """Test export format selection."""

    def test_manual_format_preference(self):
        """Test that manual preference is respected."""
        # Should return preference regardless of data characteristics
        assert select_export_format(1.0, False, "csv") == "csv"
        assert select_export_format(1000.0, True, "parquet") == "parquet"
        assert select_export_format(0.1, False, "geoparquet") == "geoparquet"

    def test_auto_format_with_geometry(self):
        """Test auto format selection with geometry."""
        # Should always return geoparquet for geometry data
        assert select_export_format(0.1, True, "auto") == "geoparquet"
        assert select_export_format(50.0, True, "auto") == "geoparquet"
        assert select_export_format(200.0, True, "auto") == "geoparquet"

    def test_auto_format_by_size(self):
        """Test auto format selection based on size."""
        # Small data (< 10 MB) -> CSV
        assert select_export_format(5.0, False, "auto") == "csv"

        # Medium data (10-100 MB) -> Parquet
        assert select_export_format(50.0, False, "auto") == "parquet"

        # Large data (> 100 MB) -> Parquet
        assert select_export_format(150.0, False, "auto") == "parquet"

    def test_edge_cases(self):
        """Test edge cases for size thresholds."""
        # The logic is:
        # - if data_size_mb > 100: parquet
        # - elif data_size_mb > 10: parquet
        # - else: csv

        # Exactly at thresholds
        assert select_export_format(10.0, False, "auto") == "csv"  # 10.0 is not > 10
        assert select_export_format(100.0, False, "auto") == "parquet"  # 100.0 is not > 100, but is > 10

        # Just above thresholds
        assert select_export_format(10.01, False, "auto") == "parquet"  # 10.01 > 10
        assert select_export_format(100.01, False, "auto") == "parquet"  # 100.01 > 100

        # Just below thresholds
        assert select_export_format(9.99, False, "auto") == "csv"  # 9.99 < 10
        assert select_export_format(99.99, False, "auto") == "parquet"  # 99.99 > 10


class TestValidateExportData:
    """Test data validation."""

    def test_valid_dataframe(self):
        """Test validation of valid DataFrame."""
        df = pd.DataFrame({'col': [1, 2, 3]})
        # Should not raise
        validate_export_data(df)

    def test_valid_geodataframe(self):
        """Test validation of valid GeoDataFrame."""
        points = [Point(0, 0), Point(1, 1)]
        gdf = gpd.GeoDataFrame({'id': [1, 2]}, geometry=points)
        # Should not raise
        validate_export_data(gdf)

    def test_none_data(self):
        """Test validation of None data."""
        with pytest.raises(ValueError, match="Export data cannot be None"):
            validate_export_data(None)

    def test_invalid_type(self):
        """Test validation of invalid data type."""
        with pytest.raises(ValueError, match="Export data must be DataFrame"):
            validate_export_data([1, 2, 3])

    def test_empty_dataframe(self):
        """Test validation of empty DataFrame (should warn but not raise)."""
        empty_df = pd.DataFrame()
        # Should not raise, just warn
        validate_export_data(empty_df)


class TestGetFormatInfo:
    """Test format information retrieval."""

    def test_csv_info(self):
        """Test CSV format info."""
        info = get_format_info("csv")
        assert info["name"] == "CSV"
        assert info["supports_geometry"] is False
        assert info["compression"] is False
        assert "Excel" in info["best_for"]

    def test_parquet_info(self):
        """Test Parquet format info."""
        info = get_format_info("parquet")
        assert info["name"] == "Parquet"
        assert info["supports_geometry"] is False
        assert info["compression"] is True
        assert "Large datasets" in info["best_for"]

    def test_geoparquet_info(self):
        """Test GeoParquet format info."""
        info = get_format_info("geoparquet")
        assert info["name"] == "GeoParquet"
        assert info["supports_geometry"] is True
        assert info["compression"] is True
        assert "Geospatial" in info["best_for"]

    def test_unknown_format_info(self):
        """Test unknown format info."""
        info = get_format_info("unknown")
        assert info["name"] == "UNKNOWN"
        assert info["description"] == "Unknown format"
        assert info["supports_geometry"] is False
        assert info["compression"] is False

    def test_all_formats_have_required_fields(self):
        """Test that all formats have required fields."""
        required_fields = ["name", "description", "supports_geometry", "compression", "best_for"]

        for format_name in ["csv", "parquet", "geoparquet", "unknown"]:
            info = get_format_info(format_name)
            for field in required_fields:
                assert field in info, f"Format {format_name} missing field {field}"
