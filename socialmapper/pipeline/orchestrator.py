"""Pipeline orchestrator for the SocialMapper pipeline.

This module provides a class-based orchestrator that coordinates all pipeline stages.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from ..exceptions import (
    AnalysisError,
    DataProcessingError,
    ErrorSeverity,
    InvalidConfigurationError,
    InvalidTravelTimeError,
    NoDataFoundError,
)
from ..isochrone import TravelMode
from ..ui.console import get_logger, print_error, print_info
from ..util.error_handling import ErrorCollector, error_context, log_error
from .census import integrate_census_data
from .environment import setup_pipeline_environment
from .export import export_pipeline_outputs
from .extraction import extract_poi_data
from .isochrone import generate_isochrones
from .reporting import generate_final_report
from .validation import validate_poi_coordinates

logger = get_logger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for the pipeline orchestrator."""

    # POI configuration
    geocode_area: str | None = None
    state: str | None = None
    city: str | None = None
    poi_type: str | None = None
    poi_name: str | None = None
    additional_tags: dict | None = None
    custom_coords_path: str | None = None
    name_field: str | None = None
    type_field: str | None = None
    max_poi_count: int | None = None

    # Analysis configuration
    travel_time: int = 15
    travel_mode: str | TravelMode = TravelMode.DRIVE
    geographic_level: str = "block-group"
    census_variables: list[str] = field(default_factory=lambda: ["total_population"])
    api_key: str | None = None

    # Output configuration
    output_dir: str = "output"
    export_csv: bool = True
    export_isochrones: bool = False
    create_maps: bool = True

    def __post_init__(self):
        """Validate configuration after initialization."""
        self.validate()

    def validate(self):
        """Validate the configuration values."""
        from ..constants import MAX_TRAVEL_TIME, MIN_TRAVEL_TIME

        # Validate travel time
        if not MIN_TRAVEL_TIME <= self.travel_time <= MAX_TRAVEL_TIME:
            raise InvalidTravelTimeError(
                self.travel_time, MIN_TRAVEL_TIME, MAX_TRAVEL_TIME
            )

        # Validate POI configuration
        if not self.custom_coords_path:
            if not self.geocode_area and not (self.city and self.state):
                raise InvalidConfigurationError(
                    field="location",
                    value="None",
                    reason="Either geocode_area or city/state must be provided"
                )

            if not self.poi_type or not self.poi_name:
                raise InvalidConfigurationError(
                    field="POI",
                    value=f"type={self.poi_type}, name={self.poi_name}",
                    reason="Both poi_type and poi_name must be provided"
                )

        # Validate geographic level
        valid_levels = ["block-group", "tract", "county"]
        if self.geographic_level not in valid_levels:
            raise InvalidConfigurationError(
                field="geographic_level",
                value=self.geographic_level,
                reason=f"Must be one of: {', '.join(valid_levels)}"
            )


class PipelineStage:
    """Represents a single stage in the pipeline."""

    def __init__(self, name: str, function: Callable, description: str):
        self.name = name
        self.function = function
        self.description = description
        self.result = None
        self.error = None

    def execute(self, **kwargs) -> Any:
        """Execute the stage with error handling."""
        try:
            print_info(f"Starting: {self.description}")
            with error_context(f"Pipeline stage: {self.name}", stage=self.name):
                self.result = self.function(**kwargs)
            return self.result
        except Exception as e:
            self.error = e
            log_error(e, ErrorSeverity.ERROR, stage=self.name, description=self.description)
            raise


class PipelineOrchestrator:
    """Orchestrates the SocialMapper pipeline execution.

    This class provides a clean interface for running the pipeline with
    better error handling, stage management, and extensibility.
    """

    def __init__(self, config: PipelineConfig):
        """Initialize the orchestrator with configuration.

        Args:
            config: Pipeline configuration object
        """
        self.config = config
        self.stages: list[PipelineStage] = []
        self.results: dict[str, Any] = {}
        self.stage_outputs: dict[str, Any] = {}

        # Define pipeline stages
        self._define_stages()

    def _define_stages(self):
        """Define the pipeline stages."""
        stages = [
            PipelineStage("setup", self._setup_environment, "Setting up pipeline environment"),
            PipelineStage("extract", self._extract_poi_data, "Extracting POI data"),
            PipelineStage("validate", self._validate_coordinates, "Validating POI coordinates"),
            PipelineStage("isochrone", self._generate_isochrones, "Generating isochrones"),
            PipelineStage("census", self._integrate_census, "Integrating census data"),
            PipelineStage("export", self._export_outputs, "Exporting results"),
        ]

        # Add mapping stage if enabled
        if self.config.create_maps:
            stages.append(PipelineStage("maps", self._generate_maps, "Creating maps"))

        stages.append(PipelineStage("report", self._generate_report, "Generating final report"))

        self.stages = stages

    def _setup_environment(self) -> dict[str, str]:
        """Setup pipeline environment."""
        return setup_pipeline_environment(
            output_dir=self.config.output_dir,
            export_csv=self.config.export_csv,
            export_isochrones=self.config.export_isochrones,
            create_maps=self.config.create_maps,
        )

    def _extract_poi_data(self) -> tuple[dict[str, Any], str, list[str], bool]:
        """Extract POI data."""
        return extract_poi_data(
            custom_coords_path=self.config.custom_coords_path,
            geocode_area=self.config.geocode_area,
            state=self.config.state,
            city=self.config.city,
            poi_type=self.config.poi_type,
            poi_name=self.config.poi_name,
            additional_tags=self.config.additional_tags,
            name_field=self.config.name_field,
            type_field=self.config.type_field,
            max_poi_count=self.config.max_poi_count,
        )

    def _validate_coordinates(self) -> None:
        """Validate POI coordinates."""
        poi_data = self.stage_outputs["extract"][0]
        validate_poi_coordinates(poi_data)

    def _generate_isochrones(self):
        """Generate isochrones."""
        poi_data = self.stage_outputs["extract"][0]
        state_abbreviations = self.stage_outputs["extract"][2]

        # Convert travel_mode string to TravelMode enum if needed
        travel_mode = self.config.travel_mode
        if isinstance(travel_mode, str):
            travel_mode = TravelMode.from_string(travel_mode)

        return generate_isochrones(
            poi_data=poi_data,
            travel_time=self.config.travel_time,
            state_abbreviations=state_abbreviations,
            travel_mode=travel_mode,
        )

    def _integrate_census(self):
        """Integrate census data."""
        poi_data = self.stage_outputs["extract"][0]
        state_abbreviations = self.stage_outputs["extract"][2]
        isochrone_gdf = self.stage_outputs["isochrone"]

        return integrate_census_data(
            isochrone_gdf=isochrone_gdf,
            census_variables=self.config.census_variables,
            api_key=self.config.api_key,
            poi_data=poi_data,
            geographic_level=self.config.geographic_level,
            state_abbreviations=state_abbreviations,
        )

    def _export_outputs(self):
        """Export pipeline outputs."""
        poi_data = self.stage_outputs["extract"][0]
        base_filename = self.stage_outputs["extract"][1]
        isochrone_gdf = self.stage_outputs["isochrone"]
        census_data_gdf = self.stage_outputs["census"][1]
        census_codes = self.stage_outputs["census"][2]
        directories = self.stage_outputs["setup"]

        return export_pipeline_outputs(
            census_data_gdf=census_data_gdf,
            poi_data=poi_data,
            isochrone_gdf=isochrone_gdf,
            base_filename=base_filename,
            travel_time=self.config.travel_time,
            directories=directories,
            export_csv=self.config.export_csv,
            census_codes=census_codes,
            geographic_level=self.config.geographic_level,
        )

    def _generate_maps(self):
        """Generate maps from pipeline outputs."""
        from .map import generate_pipeline_maps

        poi_data = self.stage_outputs["extract"][0]
        base_filename = self.stage_outputs["extract"][1]
        isochrone_gdf = self.stage_outputs["isochrone"]
        census_data_gdf = self.stage_outputs["census"][1]
        census_codes = self.stage_outputs["census"][2]
        directories = self.stage_outputs["setup"]

        return generate_pipeline_maps(
            census_data_gdf=census_data_gdf,
            poi_data=poi_data,
            isochrone_gdf=isochrone_gdf,
            directories=directories,
            base_filename=base_filename,
            travel_time=self.config.travel_time,
            census_codes=census_codes,
            geographic_level=self.config.geographic_level,
        )

    def _generate_report(self):
        """Generate final report."""
        poi_data = self.stage_outputs["extract"][0]
        base_filename = self.stage_outputs["extract"][1]
        sampled_pois = self.stage_outputs["extract"][3]
        result_files = self.stage_outputs["export"]

        return generate_final_report(
            poi_data=poi_data,
            sampled_pois=sampled_pois,
            result_files=result_files,
            base_filename=base_filename,
            travel_time=self.config.travel_time,
        )

    def run(self, skip_on_error: bool = False) -> dict[str, Any]:
        """Execute the pipeline.

        Args:
            skip_on_error: Whether to skip failed stages and continue

        Returns:
            Dictionary containing all pipeline results
        """
        error_collector = ErrorCollector()

        for stage in self.stages:
            try:
                result = stage.execute()
                self.stage_outputs[stage.name] = result

            except NoDataFoundError as e:
                # Handle no data found - might be acceptable
                if skip_on_error:
                    print_error(f"Stage '{stage.name}' found no data: {e!s}")
                    print_info("Continuing with next stage...")
                    error_collector.warnings.append((stage.name, e))
                    continue
                else:
                    self._handle_stage_error(stage.name, e)
                    raise AnalysisError(
                        f"Pipeline failed at stage '{stage.name}': No data found",
                        cause=e,
                        stage=stage.name,
                        completed_stages=list(self.stage_outputs.keys())
                    ).with_operation("pipeline_execution")

            except Exception as e:
                if skip_on_error:
                    print_error(f"Stage '{stage.name}' failed: {e!s}")
                    print_info("Continuing with next stage...")
                    error_collector.errors.append((stage.name, e))
                    continue
                else:
                    self._handle_stage_error(stage.name, e)
                    # Wrap non-SocialMapper errors
                    if not hasattr(e, 'context'):
                        raise DataProcessingError(
                            f"Pipeline failed at stage '{stage.name}': {e!s}",
                            cause=e,
                            stage=stage.name,
                            completed_stages=list(self.stage_outputs.keys()),
                            config=self.config.__dict__
                        ).with_operation("pipeline_execution")
                    raise

        # Check if we had critical errors
        if error_collector.has_errors and not skip_on_error:
            error_collector.raise_if_errors("Pipeline execution failed with errors")

        # Compile final results
        return self._compile_results()

    def _handle_stage_error(self, stage_name: str, error: Exception):
        """Handle errors that occur during stage execution."""
        error_context = {
            "stage": stage_name,
            "config": self.config.__dict__,
            "completed_stages": list(self.stage_outputs.keys()),
        }

        logger.error(f"Pipeline failed at stage '{stage_name}'", extra=error_context)

        # Could add error recovery logic here

    def _compile_results(self) -> dict[str, Any]:
        """Compile all stage outputs into final result."""
        # Get the report which contains the main results
        result = self.stage_outputs.get("report", {})

        # Add POI data if available (needed for API client to calculate poi_count)
        if "extract" in self.stage_outputs:
            poi_data = self.stage_outputs["extract"][0]
            result["pois"] = poi_data.get("pois", [])

        # Add processed data for backward compatibility
        if "isochrone" in self.stage_outputs:
            result["isochrones"] = self.stage_outputs["isochrone"]

        if "census" in self.stage_outputs:
            geographic_units_gdf, census_data_gdf, _ = self.stage_outputs["census"]
            result["geographic_units"] = geographic_units_gdf
            result["block_groups"] = geographic_units_gdf  # Backward compatibility
            result["census_data"] = census_data_gdf

        # Add maps if available
        if "maps" in self.stage_outputs:
            result["maps"] = self.stage_outputs["maps"]

        return result

    def get_stage_output(self, stage_name: str) -> Any:
        """Get the output of a specific stage.

        Args:
            stage_name: Name of the stage

        Returns:
            Output of the stage or None if not executed
        """
        return self.stage_outputs.get(stage_name)

    def get_failed_stages(self) -> list[str]:
        """Get list of failed stages."""
        return [stage.name for stage in self.stages if stage.error is not None]
