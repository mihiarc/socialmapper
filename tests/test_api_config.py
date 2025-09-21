"""Tests for SocialMapper API configuration objects."""

import pytest
from unittest.mock import Mock
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from socialmapper.api_config import (
    IsochroneConfig,
    CensusConfig,
    PoiConfig,
    MapConfig,
    MultipleAnalysisConfig,
    ReportConfig
)


class TestIsochroneConfig:
    """Test IsochroneConfig dataclass validation and initialization."""

    def test_valid_initialization_string_location(self):
        """Test valid config with string location."""
        config = IsochroneConfig("Portland, OR", 20, "drive")

        assert config.location == "Portland, OR"
        assert config.travel_time == 20
        assert config.travel_mode == "drive"

    def test_valid_initialization_coordinates(self):
        """Test valid config with coordinate tuple."""
        config = IsochroneConfig((45.5152, -122.6784), 15, "walk")

        assert config.location == (45.5152, -122.6784)
        assert config.travel_time == 15
        assert config.travel_mode == "walk"

    def test_default_values(self):
        """Test default parameter values."""
        config = IsochroneConfig("Seattle, WA")

        assert config.travel_time == 15
        assert config.travel_mode == "drive"

    def test_all_valid_travel_modes(self):
        """Test all valid travel mode options."""
        valid_modes = ["drive", "walk", "bike"]

        for mode in valid_modes:
            config = IsochroneConfig("Test City", 10, mode)
            assert config.travel_mode == mode

    def test_travel_time_validation_minimum(self):
        """Test travel time validation at minimum boundary."""
        # Valid minimum
        config = IsochroneConfig("Test", 1)
        assert config.travel_time == 1

        # Invalid below minimum
        with pytest.raises(ValueError, match="Travel time must be between 1 and 120"):
            IsochroneConfig("Test", 0)

    def test_travel_time_validation_maximum(self):
        """Test travel time validation at maximum boundary."""
        # Valid maximum
        config = IsochroneConfig("Test", 120)
        assert config.travel_time == 120

        # Invalid above maximum
        with pytest.raises(ValueError, match="Travel time must be between 1 and 120"):
            IsochroneConfig("Test", 121)

    def test_travel_time_validation_negative(self):
        """Test travel time validation with negative values."""
        with pytest.raises(ValueError, match="Travel time must be between 1 and 120"):
            IsochroneConfig("Test", -5)

    def test_travel_time_validation_extreme(self):
        """Test travel time validation with extreme values."""
        with pytest.raises(ValueError, match="Travel time must be between 1 and 120"):
            IsochroneConfig("Test", 9999)

    def test_invalid_travel_mode(self):
        """Test validation of invalid travel modes."""
        invalid_modes = ["fly", "swim", "teleport", "drive_fast", ""]

        for mode in invalid_modes:
            with pytest.raises(ValueError, match="Travel mode must be"):
                IsochroneConfig("Test", 15, mode)

    def test_travel_mode_case_sensitivity(self):
        """Test that travel mode validation is case sensitive."""
        with pytest.raises(ValueError, match="Travel mode must be"):
            IsochroneConfig("Test", 15, "DRIVE")

        with pytest.raises(ValueError, match="Travel mode must be"):
            IsochroneConfig("Test", 15, "Walk")


class TestCensusConfig:
    """Test CensusConfig dataclass."""

    def test_valid_initialization_dict_location(self):
        """Test valid config with dictionary location."""
        geojson_dict = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-122.4194, 37.7749]}
        }
        config = CensusConfig(geojson_dict, ["population"], 2022)

        assert config.location == geojson_dict
        assert config.variables == ["population"]
        assert config.year == 2022

    def test_valid_initialization_list_location(self):
        """Test valid config with list of GEOIDs."""
        geoids = ["060750201001", "060750201002"]
        config = CensusConfig(geoids, ["median_income", "median_age"])

        assert config.location == geoids
        assert config.variables == ["median_income", "median_age"]
        assert config.year == 2023  # Default

    def test_valid_initialization_tuple_location(self):
        """Test valid config with coordinate tuple."""
        coords = (40.7128, -74.0060)
        config = CensusConfig(coords, ["B01003_001E"])

        assert config.location == coords
        assert config.variables == ["B01003_001E"]

    def test_default_year(self):
        """Test default year value."""
        config = CensusConfig([], ["population"])
        assert config.year == 2023

    def test_multiple_variables(self):
        """Test configuration with multiple census variables."""
        variables = [
            "population", "median_income", "median_age",
            "housing_units", "poverty_rate"
        ]
        config = CensusConfig((0, 0), variables, 2020)

        assert config.variables == variables
        assert len(config.variables) == 5

    def test_empty_variables_list(self):
        """Test configuration with empty variables list."""
        config = CensusConfig((0, 0), [])
        assert config.variables == []

    def test_census_codes_variables(self):
        """Test configuration with census variable codes."""
        census_codes = ["B01003_001E", "B19013_001E", "B01002_001E"]
        config = CensusConfig((0, 0), census_codes)

        assert config.variables == census_codes


class TestPoiConfig:
    """Test PoiConfig dataclass."""

    def test_valid_initialization_string_location(self):
        """Test valid config with string location."""
        config = PoiConfig("Chicago, IL", ["restaurant"], 20, 50, False)

        assert config.location == "Chicago, IL"
        assert config.categories == ["restaurant"]
        assert config.travel_time == 20
        assert config.limit == 50
        assert config.validate_coords is False

    def test_valid_initialization_coordinates(self):
        """Test valid config with coordinate tuple."""
        config = PoiConfig((41.8781, -87.6298))

        assert config.location == (41.8781, -87.6298)
        assert config.categories is None  # Default
        assert config.travel_time is None  # Default
        assert config.limit == 100  # Default
        assert config.validate_coords is True  # Default

    def test_default_values(self):
        """Test all default parameter values."""
        config = PoiConfig("Test Location")

        assert config.categories is None
        assert config.travel_time is None
        assert config.limit == 100
        assert config.validate_coords is True

    def test_categories_list(self):
        """Test POI categories configuration."""
        categories = ["restaurant", "cafe", "bar", "fast_food"]
        config = PoiConfig("Test", categories=categories)

        assert config.categories == categories

    def test_travel_time_optional(self):
        """Test optional travel time parameter."""
        # None (uses radius instead)
        config1 = PoiConfig("Test", travel_time=None)
        assert config1.travel_time is None

        # Specific time
        config2 = PoiConfig("Test", travel_time=30)
        assert config2.travel_time == 30

    def test_limit_boundaries(self):
        """Test POI limit parameter boundaries."""
        # Small limit
        config1 = PoiConfig("Test", limit=1)
        assert config1.limit == 1

        # Large limit
        config2 = PoiConfig("Test", limit=1000)
        assert config2.limit == 1000

    def test_validation_flag_options(self):
        """Test coordinate validation flag options."""
        config_true = PoiConfig("Test", validate_coords=True)
        config_false = PoiConfig("Test", validate_coords=False)

        assert config_true.validate_coords is True
        assert config_false.validate_coords is False


class TestMapConfig:
    """Test MapConfig dataclass."""

    def test_valid_initialization_list_data(self):
        """Test valid config with list data."""
        data = [{"geometry": Point(0, 0), "value": 10}]
        config = MapConfig(data, "value", "Test Map", "/tmp/test.png", "png")

        assert config.data == data
        assert config.column == "value"
        assert config.title == "Test Map"
        assert config.save_path == "/tmp/test.png"
        assert config.export_format == "png"

    def test_valid_initialization_dataframe(self):
        """Test valid config with pandas DataFrame."""
        df = pd.DataFrame({"value": [1, 2, 3], "geometry": [Point(i, i) for i in range(3)]})
        config = MapConfig(df, "value")

        assert config.data is df
        assert config.column == "value"

    def test_valid_initialization_geodataframe(self):
        """Test valid config with geopandas GeoDataFrame."""
        gdf = gpd.GeoDataFrame({"value": [1, 2]}, geometry=[Point(0, 0), Point(1, 1)])
        config = MapConfig(gdf, "value")

        assert config.data is gdf

    def test_default_values(self):
        """Test default parameter values."""
        config = MapConfig([], "test_column")

        assert config.title is None
        assert config.save_path is None
        assert config.export_format == "png"

    def test_export_format_options(self):
        """Test various export format options."""
        formats = ["png", "pdf", "svg", "geojson", "shapefile"]

        for fmt in formats:
            config = MapConfig([], "col", export_format=fmt)
            assert config.export_format == fmt


class TestMultipleAnalysisConfig:
    """Test MultipleAnalysisConfig dataclass."""

    def test_valid_initialization_string_locations(self):
        """Test valid config with string locations."""
        locations = ["Portland, OR", "Seattle, WA", "San Francisco, CA"]
        config = MultipleAnalysisConfig(locations, 20, "bike", ["population"], False)

        assert config.locations == locations
        assert config.travel_time == 20
        assert config.travel_mode == "bike"
        assert config.variables == ["population"]
        assert config.compare is False

    def test_valid_initialization_coordinate_locations(self):
        """Test valid config with coordinate locations."""
        locations = [(45.5152, -122.6784), (47.6062, -122.3321)]
        config = MultipleAnalysisConfig(locations)

        assert config.locations == locations
        assert config.travel_time == 15  # Default
        assert config.travel_mode == "drive"  # Default

    def test_mixed_location_types(self):
        """Test config with mixed location types."""
        locations = ["Portland, OR", (47.6062, -122.3321)]
        config = MultipleAnalysisConfig(locations)

        assert config.locations == locations

    def test_default_values(self):
        """Test default parameter values."""
        config = MultipleAnalysisConfig(["Test"])

        assert config.travel_time == 15
        assert config.travel_mode == "drive"
        assert config.variables == ["population"]  # Set by __post_init__
        assert config.compare is True

    def test_post_init_variables_default(self):
        """Test __post_init__ sets default variables when None."""
        config = MultipleAnalysisConfig(["Test"], variables=None)
        assert config.variables == ["population"]

        # Should not override explicit empty list
        config2 = MultipleAnalysisConfig(["Test"], variables=[])
        assert config2.variables == []

    def test_multiple_variables(self):
        """Test configuration with multiple variables."""
        variables = ["population", "median_income", "housing_units"]
        config = MultipleAnalysisConfig(["Test"], variables=variables)

        assert config.variables == variables

    def test_single_location_list(self):
        """Test configuration with single location in list."""
        config = MultipleAnalysisConfig(["Single Location"])
        assert len(config.locations) == 1

    def test_empty_locations_list(self):
        """Test configuration with empty locations list."""
        config = MultipleAnalysisConfig([])
        assert config.locations == []


class TestReportConfig:
    """Test ReportConfig dataclass."""

    def test_valid_initialization(self):
        """Test valid config initialization."""
        data = {"test": "data", "analysis": {"results": [1, 2, 3]}}
        config = ReportConfig(data, "pdf", "detailed", False)

        assert config.analysis_data == data
        assert config.format == "pdf"
        assert config.template == "detailed"
        assert config.include_maps is False

    def test_default_values(self):
        """Test default parameter values."""
        config = ReportConfig({})

        assert config.format == "html"
        assert config.template == "default"
        assert config.include_maps is True

    def test_valid_html_format(self):
        """Test valid HTML format configuration."""
        config = ReportConfig({}, format="html")
        assert config.format == "html"

    def test_valid_pdf_format(self):
        """Test valid PDF format configuration."""
        config = ReportConfig({}, format="pdf")
        assert config.format == "pdf"

    def test_invalid_format_validation(self):
        """Test validation of invalid report formats."""
        invalid_formats = ["doc", "txt", "xml", "json", "csv"]

        for fmt in invalid_formats:
            with pytest.raises(ValueError, match="Report format must be one of"):
                ReportConfig({}, format=fmt)

    def test_case_sensitive_format_validation(self):
        """Test that format validation is case sensitive."""
        with pytest.raises(ValueError, match="Report format must be one of"):
            ReportConfig({}, format="HTML")

        with pytest.raises(ValueError, match="Report format must be one of"):
            ReportConfig({}, format="PDF")

    def test_template_options(self):
        """Test various template options."""
        templates = ["default", "detailed", "summary", "custom"]

        for template in templates:
            config = ReportConfig({}, template=template)
            assert config.template == template

    def test_include_maps_boolean(self):
        """Test include_maps boolean options."""
        config_true = ReportConfig({}, include_maps=True)
        config_false = ReportConfig({}, include_maps=False)

        assert config_true.include_maps is True
        assert config_false.include_maps is False

    def test_complex_analysis_data(self):
        """Test configuration with complex analysis data."""
        complex_data = {
            "isochrones": [{"id": 1}, {"id": 2}],
            "census_data": {"123": {"pop": 1000}},
            "pois": [{"name": "Store", "lat": 45.5, "lon": -122.6}],
            "metadata": {"timestamp": "2023-01-01", "version": "2.0"}
        }

        config = ReportConfig(complex_data)
        assert config.analysis_data == complex_data

    def test_empty_analysis_data(self):
        """Test configuration with empty analysis data."""
        config = ReportConfig({})
        assert config.analysis_data == {}


class TestConfigIntegration:
    """Test integration between configuration objects."""

    def test_config_objects_independence(self):
        """Test that config objects don't interfere with each other."""
        iso_config = IsochroneConfig("Test", 10, "walk")
        census_config = CensusConfig((0, 0), ["pop"])
        poi_config = PoiConfig("Test", limit=50)

        # Modify one config
        iso_config.travel_time = 20

        # Others should be unaffected
        assert census_config.year == 2023
        assert poi_config.limit == 50

    def test_config_serialization_readiness(self):
        """Test that configs contain serializable data."""
        import json

        configs = [
            IsochroneConfig("Test", 15, "drive"),
            CensusConfig((0, 0), ["pop"], 2023),
            PoiConfig("Test", ["food"], 10, 100, True),
            MapConfig([{"test": "data"}], "test", "Title", "/tmp/test.png", "png"),
            MultipleAnalysisConfig(["Test"], 15, "drive", ["pop"], True),
            ReportConfig({"data": "test"}, "html", "default", True)
        ]

        for config in configs:
            # This should not raise an exception for serializable data
            try:
                vars_dict = vars(config)
                # Remove non-serializable data for this test
                serializable_dict = {k: v for k, v in vars_dict.items()
                                   if not isinstance(v, (pd.DataFrame, gpd.GeoDataFrame))}
                json.dumps(serializable_dict, default=str)
            except (TypeError, ValueError) as e:
                pytest.fail(f"Config {type(config).__name__} contains non-serializable data: {e}")