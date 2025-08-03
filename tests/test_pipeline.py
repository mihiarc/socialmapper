"""Tests for pipeline modules."""


from socialmapper.pipeline import (
    PipelineConfig,
    PipelineOrchestrator,
    export_pipeline_outputs,
    extract_poi_data,
    generate_isochrones,
    integrate_census_data,
    parse_custom_coordinates,
    setup_directory,
    validate_poi_coordinates,
)


class TestPipelineConfig:
    """Test PipelineConfig class."""

    def test_pipeline_config_dataclass(self):
        """Test PipelineConfig as a dataclass."""
        config = PipelineConfig(
            geocode_area="San Francisco, CA",
            poi_type="amenity",
            poi_name="library",
            travel_time=15,
            travel_mode="walk"
        )

        assert config.geocode_area == "San Francisco, CA"
        assert config.poi_type == "amenity"
        assert config.poi_name == "library"
        assert config.travel_time == 15
        assert config.travel_mode == "walk"

    def test_pipeline_config_defaults(self):
        """Test pipeline config default values."""
        config = PipelineConfig(
            geocode_area="San Francisco, CA",
            poi_type="amenity",
            poi_name="library"
        )

        # Check defaults
        assert config.travel_time == 15
        assert config.geographic_level == "block-group"
        assert config.output_dir == "output"
        assert config.export_csv is True
        assert config.create_maps is True


class TestPipelineValidation:
    """Test pipeline validation functions."""

    def test_has_validate_function(self):
        """Test that validate_poi_coordinates exists."""
        assert callable(validate_poi_coordinates)

    def test_has_parse_function(self):
        """Test that parse_custom_coordinates exists."""
        assert callable(parse_custom_coordinates)


class TestPipelineEnvironment:
    """Test pipeline environment setup."""

    def test_has_setup_directory(self):
        """Test that setup_directory exists."""
        assert callable(setup_directory)


class TestPipelineOrchestrator:
    """Test PipelineOrchestrator class."""

    def test_orchestrator_initialization(self):
        """Test creating orchestrator with config."""
        config = PipelineConfig(
            geocode_area="Boston, MA",
            poi_type="amenity",
            poi_name="park"
        )

        orchestrator = PipelineOrchestrator(config)

        assert orchestrator.config == config
        assert hasattr(orchestrator, 'run')

    def test_orchestrator_has_run_method(self):
        """Test that orchestrator has run method."""
        config = PipelineConfig(
            geocode_area="Boston, MA",
            poi_type="amenity",
            poi_name="park"
        )
        orchestrator = PipelineOrchestrator(config)

        assert hasattr(orchestrator, 'run')
        assert callable(orchestrator.run)


class TestPipelineFunctions:
    """Test pipeline functions exist."""

    def test_extract_poi_data_exists(self):
        """Test extract_poi_data function exists."""
        assert callable(extract_poi_data)

    def test_generate_isochrones_exists(self):
        """Test generate_isochrones function exists."""
        assert callable(generate_isochrones)

    def test_integrate_census_data_exists(self):
        """Test integrate_census_data function exists."""
        assert callable(integrate_census_data)

    def test_export_pipeline_outputs_exists(self):
        """Test export_pipeline_outputs function exists."""
        assert callable(export_pipeline_outputs)
