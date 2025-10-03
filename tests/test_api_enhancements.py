"""Tests for enhanced API features."""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon

from socialmapper.api import (
    create_map,
    get_poi,
    analyze_multiple_pois,
    import_poi_csv,
    generate_report
)


class TestCreateMapEnhancements:
    """Test enhanced create_map function."""

    def test_export_formats_png(self):
        """Test PNG export format."""
        # Create sample data
        data = [
            {"geometry": Point(0, 0).__geo_interface__, "value": 10},
            {"geometry": Point(1, 1).__geo_interface__, "value": 20}
        ]

        with patch('socialmapper._visualization.generate_choropleth_map') as mock_map:
            mock_map.return_value = b'fake_png_data'

            result = create_map(data, "value", export_format="png")

            assert result == b'fake_png_data'
            mock_map.assert_called_once()
            # Check that format parameter was passed
            assert mock_map.call_args[1]['format'] == 'png'

    def test_export_format_geojson(self):
        """Test GeoJSON export format."""
        data = [
            {"geometry": Point(0, 0).__geo_interface__, "value": 10},
            {"geometry": Point(1, 1).__geo_interface__, "value": 20}
        ]

        result = create_map(data, "value", export_format="geojson")

        assert isinstance(result, dict)
        assert "features" in result
        assert len(result["features"]) == 2

    def test_export_format_shapefile_requires_path(self):
        """Test that shapefile export requires save_path."""
        data = [{"geometry": Point(0, 0).__geo_interface__, "value": 10}]

        with pytest.raises(ValueError, match="save_path is required for shapefile export"):
            create_map(data, "value", export_format="shapefile")

    @patch('geopandas.GeoDataFrame.to_file')
    def test_export_format_shapefile_with_path(self, mock_to_file):
        """Test shapefile export with path."""
        data = [{"geometry": Point(0, 0).__geo_interface__, "value": 10}]

        result = create_map(data, "value", save_path="/tmp/test.shp", export_format="shapefile")

        assert result is None
        mock_to_file.assert_called_once()
        assert mock_to_file.call_args[0][0] == Path("/tmp/test.shp")
        assert mock_to_file.call_args[1]['driver'] == 'ESRI Shapefile'

    def test_invalid_export_format(self):
        """Test invalid export format raises error."""
        data = [{"geometry": Point(0, 0).__geo_interface__, "value": 10}]

        with pytest.raises(ValueError, match="Export format must be one of"):
            create_map(data, "value", export_format="invalid")


class TestGetPOIEnhancements:
    """Test enhanced get_poi function."""

    @patch('socialmapper._osm.query_pois')
    @patch('socialmapper._geocoding.geocode_location')
    def test_validate_coords_true(self, mock_geocode, mock_query):
        """Test POI validation when enabled."""
        mock_geocode.return_value = (37.7749, -122.4194)
        mock_query.return_value = [
            {"name": "Valid POI", "lat": 37.7749, "lon": -122.4194},
            {"name": "Invalid POI", "lat": 200, "lon": -300},  # Invalid coords
            {"name": "Null Island", "lat": 0, "lon": 0}  # Often invalid
        ]

        result = get_poi("San Francisco, CA", validate_coords=True)

        # Should only return valid POI
        assert len(result) == 1
        assert result[0]["name"] == "Valid POI"

    @patch('socialmapper._osm.query_pois')
    @patch('socialmapper._geocoding.geocode_location')
    def test_validate_coords_false(self, mock_geocode, mock_query):
        """Test POI validation when disabled."""
        mock_geocode.return_value = (37.7749, -122.4194)
        mock_query.return_value = [
            {"name": "Valid POI", "lat": 37.7749, "lon": -122.4194},
            {"name": "Invalid POI", "lat": 200, "lon": -300}
        ]

        result = get_poi("San Francisco, CA", validate_coords=False)

        # Should return all POIs
        assert len(result) == 2


class TestAnalyzeMultiplePOIs:
    """Test analyze_multiple_pois function."""

    @patch('socialmapper.api.get_census_data')
    @patch('socialmapper.api.create_isochrone')
    def test_basic_analysis(self, mock_iso, mock_census):
        """Test basic multi-POI analysis."""
        mock_iso.return_value = {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
            "properties": {"location": "Test", "travel_time": 15, "travel_mode": "drive", "area_sq_km": 10}
        }
        mock_census.return_value = {
            "12345": {"population": 1000},
            "67890": {"population": 2000}
        }

        result = analyze_multiple_pois(
            ["Location 1", "Location 2"],
            travel_time=15,
            variables=["population"]
        )

        assert "locations" in result
        assert len(result["locations"]) == 2
        assert "metadata" in result
        assert result["metadata"]["travel_time"] == 15

    @patch('socialmapper.api.get_census_data')
    @patch('socialmapper.api.create_isochrone')
    def test_comparison_enabled(self, mock_iso, mock_census):
        """Test multi-POI analysis with comparison."""
        mock_iso.return_value = {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
            "properties": {"location": "Test", "travel_time": 15, "travel_mode": "drive", "area_sq_km": 10}
        }

        # Different census data for each location
        mock_census.side_effect = [
            {"12345": {"population": 1000}},
            {"67890": {"population": 2000}}
        ]

        result = analyze_multiple_pois(
            ["Location 1", "Location 2"],
            compare=True,
            variables=["population"]
        )

        assert "comparison" in result
        assert "population" in result["comparison"]
        assert "ranked" in result["comparison"]["population"]

    def test_single_location_no_comparison(self):
        """Test that single location doesn't produce comparison."""
        with patch('socialmapper.api.create_isochrone'), \
             patch('socialmapper.api.get_census_data'):

            result = analyze_multiple_pois(["Single Location"], compare=True)

            assert "comparison" not in result or result["comparison"] == {}


class TestImportPOICSV:
    """Test import_poi_csv function."""

    def test_import_basic_csv(self, tmp_path):
        """Test importing basic CSV file."""
        # Create test CSV
        csv_file = tmp_path / "test_pois.csv"
        csv_content = """name,latitude,longitude,type
Store A,37.7749,-122.4194,retail
Store B,37.7849,-122.4094,retail
"""
        csv_file.write_text(csv_content)

        result = import_poi_csv(str(csv_file))

        assert len(result) == 2
        assert result[0]["name"] == "Store A"
        assert result[0]["lat"] == 37.7749
        assert result[0]["lon"] == -122.4194
        assert result[0]["type"] == "retail"

    def test_import_csv_custom_columns(self, tmp_path):
        """Test importing CSV with custom column names."""
        csv_file = tmp_path / "test_pois.csv"
        csv_content = """business_name,lat,lng,category,address
Shop X,40.7128,-74.0060,food,123 Main St
Shop Y,40.7228,-73.9960,food,456 Oak Ave
"""
        csv_file.write_text(csv_content)

        result = import_poi_csv(
            str(csv_file),
            name_field="business_name",
            lat_field="lat",
            lon_field="lng",
            type_field="category"
        )

        assert len(result) == 2
        assert result[0]["name"] == "Shop X"
        assert result[0]["type"] == "food"
        assert result[0]["tags"]["address"] == "123 Main St"

    def test_import_csv_invalid_coords(self, tmp_path):
        """Test that invalid coordinates are filtered."""
        csv_file = tmp_path / "test_pois.csv"
        csv_content = """name,latitude,longitude,type
Valid,37.7749,-122.4194,retail
Invalid,200,-300,retail
Also Valid,40.7128,-74.0060,retail
"""
        csv_file.write_text(csv_content)

        result = import_poi_csv(str(csv_file))

        assert len(result) == 2  # Only valid coordinates
        assert result[0]["name"] == "Valid"
        assert result[1]["name"] == "Also Valid"

    def test_import_nonexistent_file(self):
        """Test error for nonexistent file."""
        with pytest.raises(FileNotFoundError):
            import_poi_csv("/nonexistent/file.csv")


class TestGenerateReport:
    """Test generate_report function."""

    def test_generate_html_report(self):
        """Test HTML report generation."""
        analysis_data = {
            "isochrone": {
                "properties": {
                    "location": "Test City",
                    "travel_time": 15,
                    "travel_mode": "drive",
                    "area_sq_km": 25.5
                }
            },
            "census_data": {
                "12345": {"population": 1000, "median_income": 50000}
            }
        }

        result = generate_report(analysis_data, format="html")

        assert isinstance(result, str)
        assert "<html>" in result.lower()
        assert "Test City" in result
        assert "15 min" in result

    def test_generate_pdf_report(self):
        """Test PDF report generation (simplified)."""
        analysis_data = {"test": "data"}

        result = generate_report(analysis_data, format="pdf")

        # Since PDF generation is simplified, it returns bytes
        assert isinstance(result, bytes)

    def test_invalid_format(self):
        """Test invalid report format."""
        with pytest.raises(ValueError, match="Report format must be one of"):
            generate_report({}, format="invalid")
