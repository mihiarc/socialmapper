"""Tests for API result types and data models."""

from pathlib import Path

import pytest
from pydantic import ValidationError as PydanticValidationError

from socialmapper.api_result_types import (
    CensusBlock,
    CensusDataResult,
    DiscoveredPOI,
    IsochroneResult,
    MapResult,
    NearbyPOIResult,
    ReportResult,
)


class TestDiscoveredPOI:
    """Test DiscoveredPOI model."""

    def test_basic_poi_creation(self):
        poi = DiscoveredPOI(
            osm_id=12345,
            name="Test Library",
            category="library",
            latitude=45.5152,
            longitude=-122.6784,
            distance_meters=500.0
        )
        assert poi.osm_id == 12345
        assert poi.name == "Test Library"
        assert poi.category == "library"
        assert poi.latitude == 45.5152
        assert poi.longitude == -122.6784
        assert poi.distance_meters == 500.0

    def test_poi_optional_fields(self):
        poi = DiscoveredPOI(
            osm_id=12345,
            category="restaurant",
            latitude=45.5,
            longitude=-122.6,
            distance_meters=100.0,
            subcategory="italian",
            travel_time_minutes=5.0,
            tags={"cuisine": "italian"},
            address="123 Main St"
        )
        assert poi.subcategory == "italian"
        assert poi.travel_time_minutes == 5.0
        assert poi.tags == {"cuisine": "italian"}
        assert poi.address == "123 Main St"

    def test_poi_default_values(self):
        poi = DiscoveredPOI(
            osm_id=1,
            category="cafe",
            latitude=0,
            longitude=0,
            distance_meters=0
        )
        assert poi.name is None
        assert poi.subcategory is None
        assert poi.travel_time_minutes is None
        assert poi.tags == {}
        assert poi.address is None


class TestNearbyPOIResult:
    """Test NearbyPOIResult model."""

    def test_nearby_poi_result_creation(self):
        result = NearbyPOIResult(
            origin={"latitude": 45.5152, "longitude": -122.6784},
            travel_time_minutes=15,
            travel_mode="drive",
            discovered_pois=[],
            total_pois=0
        )
        assert result.origin["latitude"] == 45.5152
        assert result.travel_time_minutes == 15
        assert result.travel_mode == "drive"

    def test_nearby_poi_result_with_pois(self):
        poi = DiscoveredPOI(
            osm_id=1,
            category="library",
            latitude=45.5,
            longitude=-122.6,
            distance_meters=500
        )
        result = NearbyPOIResult(
            origin={"latitude": 45.5152, "longitude": -122.6784},
            travel_time_minutes=10,
            travel_mode="walk",
            discovered_pois=[poi],
            total_pois=1,
            categories_found=["library"]
        )
        assert len(result.discovered_pois) == 1
        assert result.total_pois == 1
        assert "library" in result.categories_found


class TestCensusDataResult:
    """Test CensusDataResult model."""

    def test_census_data_result_polygon(self):
        result = CensusDataResult(
            data={"060750201001": {"population": 2543}},
            location_type="polygon",
            query_info={"year": 2023}
        )
        assert result.location_type == "polygon"
        assert result.data["060750201001"]["population"] == 2543

    def test_census_data_result_geoids(self):
        result = CensusDataResult(
            data={
                "410510100001": {"population": 1000},
                "410510100002": {"population": 2000}
            },
            location_type="geoids"
        )
        assert result.location_type == "geoids"
        assert len(result.data) == 2

    def test_census_data_result_point(self):
        result = CensusDataResult(
            data={"410510100001": {"median_income": 75000}},
            location_type="point"
        )
        assert result.location_type == "point"

    def test_census_data_result_invalid_location_type(self):
        with pytest.raises(PydanticValidationError):
            CensusDataResult(
                data={},
                location_type="invalid"
            )


class TestMapResult:
    """Test MapResult model."""

    def test_map_result_png_with_bytes(self):
        result = MapResult(
            format="png",
            image_data=b"fake_image_bytes",
            metadata={"column": "population"}
        )
        assert result.format == "png"
        assert result.image_data == b"fake_image_bytes"

    def test_map_result_geojson_with_dict(self):
        result = MapResult(
            format="geojson",
            geojson_data={"type": "FeatureCollection", "features": []},
            metadata={"column": "income"}
        )
        assert result.format == "geojson"
        assert result.geojson_data["type"] == "FeatureCollection"

    def test_map_result_with_file_path(self):
        result = MapResult(
            format="shapefile",
            file_path=Path("/tmp/output.shp"),
            metadata={"num_features": 10}
        )
        assert result.format == "shapefile"
        assert result.file_path == Path("/tmp/output.shp")

    def test_map_result_invalid_format(self):
        with pytest.raises(PydanticValidationError):
            MapResult(format="invalid")


class TestIsochroneResult:
    """Test IsochroneResult model."""

    def test_isochrone_result_creation(self):
        geometry = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}
        result = IsochroneResult(
            geometry=geometry,
            location="Portland, OR",
            travel_time=15,
            travel_mode="drive",
            area_sq_km=125.4
        )
        assert result.location == "Portland, OR"
        assert result.travel_time == 15
        assert result.travel_mode == "drive"
        assert result.area_sq_km == 125.4

    def test_isochrone_to_geojson(self):
        geometry = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}
        result = IsochroneResult(
            geometry=geometry,
            location="Seattle, WA",
            travel_time=20,
            travel_mode="walk",
            area_sq_km=50.0
        )
        geojson = result.to_geojson()
        assert geojson["type"] == "Feature"
        assert geojson["geometry"] == geometry
        assert geojson["properties"]["location"] == "Seattle, WA"
        assert geojson["properties"]["travel_time"] == 20
        assert geojson["properties"]["travel_mode"] == "walk"
        assert geojson["properties"]["area_sq_km"] == 50.0


class TestCensusBlock:
    """Test CensusBlock model."""

    def test_census_block_creation(self):
        block = CensusBlock(
            geoid="530330051001",
            state_fips="53",
            county_fips="033",
            tract="005100",
            block_group="1",
            geometry={"type": "Polygon", "coordinates": []},
            area_sq_km=2.34
        )
        assert block.geoid == "530330051001"
        assert block.state_fips == "53"
        assert block.county_fips == "033"
        assert block.tract == "005100"
        assert block.block_group == "1"
        assert block.area_sq_km == 2.34


class TestReportResult:
    """Test ReportResult model."""

    def test_html_report_result(self):
        result = ReportResult(
            format="html",
            content="<html><body>Report</body></html>",
            metadata={"generated_at": "2025-01-05"}
        )
        assert result.format == "html"
        assert "<html>" in result.content

    def test_pdf_report_result(self):
        result = ReportResult(
            format="pdf",
            content=b"%PDF-1.4",
            file_path=Path("/reports/analysis.pdf"),
            metadata={"pages": 5}
        )
        assert result.format == "pdf"
        assert isinstance(result.content, bytes)
        assert result.file_path.name == "analysis.pdf"
