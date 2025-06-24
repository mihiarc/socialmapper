"""Snapshot tests for export format outputs using Syrupy."""

import pytest
import pandas as pd
import geopandas as gpd
from pathlib import Path
from unittest.mock import patch

from socialmapper.export.formats.csv import CSVExporter
from socialmapper.export.formats.geoparquet import GeoParquetExporter


@pytest.mark.unit
class TestExportFormatSnapshots:
    """Snapshot tests for export format consistency."""

    def test_csv_export_format(self, snapshot, sample_census_data, temp_dir):
        """Test CSV export format remains consistent."""
        exporter = CSVExporter()
        output_path = temp_dir / "test_export.csv"
        
        # Export the data
        exporter.export(sample_census_data, output_path)
        
        # Read back the exported data for snapshot comparison
        exported_data = pd.read_csv(output_path)
        
        # Convert to dict for consistent snapshot format
        snapshot_data = {
            "columns": list(exported_data.columns),
            "dtypes": {col: str(dtype) for col, dtype in exported_data.dtypes.items()},
            "shape": exported_data.shape,
            "sample_rows": exported_data.head(3).to_dict(orient="records")
        }
        
        assert snapshot_data == snapshot

    def test_geoparquet_export_format(self, snapshot, sample_geodataframe, temp_dir):
        """Test GeoParquet export format remains consistent."""
        exporter = GeoParquetExporter()
        output_path = temp_dir / "test_export.geoparquet"
        
        # Export the data
        exporter.export(sample_geodataframe, output_path)
        
        # Read back the exported data for snapshot comparison
        exported_gdf = gpd.read_parquet(output_path)
        
        # Convert to dict for consistent snapshot format
        snapshot_data = {
            "columns": list(exported_gdf.columns),
            "crs": str(exported_gdf.crs) if exported_gdf.crs else None,
            "geometry_type": exported_gdf.geometry.geom_type.iloc[0] if not exported_gdf.empty else None,
            "shape": exported_gdf.shape,
            "dtypes": {col: str(dtype) for col, dtype in exported_gdf.dtypes.items() if col != "geometry"}
        }
        
        assert snapshot_data == snapshot

    def test_census_data_processing_output(self, snapshot, sample_census_data):
        """Test census data processing output format."""
        # Simulate data processing
        processed_data = sample_census_data.copy()
        processed_data["population_density"] = processed_data["B01003_001E"] / 1000  # Mock density calculation
        processed_data["housing_total"] = processed_data["B25003_002E"] + processed_data["B25003_003E"]
        
        # Create snapshot of processed structure
        snapshot_data = {
            "columns": list(processed_data.columns),
            "calculated_fields": ["population_density", "housing_total"],
            "sample_calculations": {
                "first_row_density": float(processed_data["population_density"].iloc[0]),
                "first_row_housing": int(processed_data["housing_total"].iloc[0])
            },
            "dtypes": {col: str(dtype) for col, dtype in processed_data.dtypes.items() if col != "geometry"}
        }
        
        assert snapshot_data == snapshot

    def test_poi_query_response_format(self, snapshot, mock_osm_response):
        """Test POI query response format remains consistent."""
        # Process the mock response as the system would
        processed_elements = []
        for element in mock_osm_response["elements"]:
            processed_element = {
                "id": element["id"],
                "name": element["tags"].get("name", "Unknown"),
                "amenity": element["tags"].get("amenity", "Unknown"),
                "coordinates": [element["lat"], element["lon"]],
                "has_address": "addr:street" in element["tags"]
            }
            processed_elements.append(processed_element)
        
        snapshot_data = {
            "total_elements": len(processed_elements),
            "elements": processed_elements,
            "element_types": list({elem["amenity"] for elem in processed_elements})
        }
        
        assert snapshot_data == snapshot

    def test_isochrone_generation_output(self, snapshot, sample_isochrone_polygon):
        """Test isochrone generation output format."""
        # Simulate isochrone processing
        isochrone_data = {
            "area_km2": sample_isochrone_polygon.area * 111000,  # Rough conversion to km²
            "perimeter_km": sample_isochrone_polygon.length * 111,  # Rough conversion to km
            "bounds": list(sample_isochrone_polygon.bounds),
            "geometry_type": sample_isochrone_polygon.geom_type,
            "is_valid": sample_isochrone_polygon.is_valid,
            "coordinate_count": len(list(sample_isochrone_polygon.exterior.coords))
        }
        
        assert isochrone_data == snapshot

    def test_error_response_format(self, snapshot):
        """Test error response format consistency."""
        # Simulate different types of errors
        error_responses = {
            "api_error": {
                "type": "APIError",
                "message": "Census API returned 500",
                "code": "API_SERVER_ERROR",
                "timestamp": "2025-01-01T00:00:00Z"
            },
            "validation_error": {
                "type": "ValidationError", 
                "message": "Invalid coordinates: latitude must be between -90 and 90",
                "code": "INVALID_COORDINATES",
                "details": {"latitude": 91.0, "longitude": -122.3321}
            },
            "timeout_error": {
                "type": "TimeoutError",
                "message": "Request timed out after 30 seconds",
                "code": "REQUEST_TIMEOUT"
            }
        }
        
        assert error_responses == snapshot

    def test_configuration_serialization(self, snapshot):
        """Test configuration serialization format."""
        # Simulate configuration data
        config_data = {
            "travel_mode": "walk",
            "travel_time": 15,
            "geographic_level": "block_group",
            "census_variables": [
                "B01003_001E",  # Total population
                "B19013_001E",  # Median household income
                "B25003_002E",  # Owner occupied housing
                "B25003_003E"   # Renter occupied housing
            ],
            "cache_enabled": True,
            "api_timeout": 30,
            "max_retries": 3
        }
        
        assert config_data == snapshot

    def test_progress_reporting_format(self, snapshot):
        """Test progress reporting format consistency."""
        # Simulate progress data
        progress_data = {
            "current_step": "Fetching POI data",
            "step_number": 2,
            "total_steps": 5,
            "percentage": 40.0,
            "estimated_time_remaining": 120,  # seconds
            "details": {
                "pois_found": 15,
                "geocoding_complete": True,
                "isochrone_generated": False
            }
        }
        
        assert progress_data == snapshot

    def test_map_generation_metadata(self, snapshot, sample_coordinates):
        """Test map generation metadata format."""
        # Simulate map metadata
        map_metadata = {
            "center_coordinates": [sample_coordinates["latitude"], sample_coordinates["longitude"]],
            "zoom_level": 12,
            "map_size": [800, 600],
            "layers": ["basemap", "isochrones", "pois", "census_boundaries"],
            "style": "openstreetmap",
            "generated_at": "2025-01-01T00:00:00Z",
            "file_format": "png",
            "dpi": 300
        }
        
        assert map_metadata == snapshot