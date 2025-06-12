"""
Pipeline orchestrator for the SocialMapper pipeline.

This module provides a class-based orchestrator that coordinates all pipeline stages.
"""

from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
import logging

from .environment import setup_pipeline_environment
from .extraction import extract_poi_data
from .validation import validate_poi_coordinates
from .isochrone import generate_isochrones
from .census import integrate_census_data
from .export import export_pipeline_outputs
from .reporting import generate_final_report
from ..ui.rich_console import print_error, print_info


logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for the pipeline orchestrator."""
    # POI configuration
    geocode_area: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    poi_type: Optional[str] = None
    poi_name: Optional[str] = None
    additional_tags: Optional[Dict] = None
    custom_coords_path: Optional[str] = None
    name_field: Optional[str] = None
    type_field: Optional[str] = None
    max_poi_count: Optional[int] = None
    
    # Analysis configuration
    travel_time: int = 15
    geographic_level: str = "block-group"
    census_variables: List[str] = field(default_factory=lambda: ["total_population"])
    api_key: Optional[str] = None
    
    # Output configuration
    output_dir: str = "output"
    export_csv: bool = True
    export_maps: bool = False
    export_isochrones: bool = False
    use_interactive_maps: bool = True
    map_backend: str = "plotly"


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
            self.result = self.function(**kwargs)
            return self.result
        except Exception as e:
            self.error = e
            logger.error(f"Stage '{self.name}' failed: {str(e)}")
            raise


class PipelineOrchestrator:
    """
    Orchestrates the SocialMapper pipeline execution.
    
    This class provides a clean interface for running the pipeline with
    better error handling, stage management, and extensibility.
    """
    
    def __init__(self, config: PipelineConfig):
        """
        Initialize the orchestrator with configuration.
        
        Args:
            config: Pipeline configuration object
        """
        self.config = config
        self.stages: List[PipelineStage] = []
        self.results: Dict[str, Any] = {}
        self.stage_outputs: Dict[str, Any] = {}
        
        # Define pipeline stages
        self._define_stages()
        
    def _define_stages(self):
        """Define the pipeline stages."""
        self.stages = [
            PipelineStage(
                "setup",
                self._setup_environment,
                "Setting up pipeline environment"
            ),
            PipelineStage(
                "extract",
                self._extract_poi_data,
                "Extracting POI data"
            ),
            PipelineStage(
                "validate",
                self._validate_coordinates,
                "Validating POI coordinates"
            ),
            PipelineStage(
                "isochrone",
                self._generate_isochrones,
                "Generating isochrones"
            ),
            PipelineStage(
                "census",
                self._integrate_census,
                "Integrating census data"
            ),
            PipelineStage(
                "export",
                self._export_outputs,
                "Exporting results"
            ),
            PipelineStage(
                "report",
                self._generate_report,
                "Generating final report"
            )
        ]
    
    def _setup_environment(self) -> Dict[str, str]:
        """Setup pipeline environment."""
        return setup_pipeline_environment(
            output_dir=self.config.output_dir,
            export_csv=self.config.export_csv,
            export_maps=self.config.export_maps,
            export_isochrones=self.config.export_isochrones
        )
    
    def _extract_poi_data(self) -> Tuple[Dict[str, Any], str, List[str], bool]:
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
            max_poi_count=self.config.max_poi_count
        )
    
    def _validate_coordinates(self) -> None:
        """Validate POI coordinates."""
        poi_data = self.stage_outputs['extract'][0]
        validate_poi_coordinates(poi_data)
    
    def _generate_isochrones(self):
        """Generate isochrones."""
        poi_data = self.stage_outputs['extract'][0]
        state_abbreviations = self.stage_outputs['extract'][2]
        
        return generate_isochrones(
            poi_data=poi_data,
            travel_time=self.config.travel_time,
            state_abbreviations=state_abbreviations
        )
    
    def _integrate_census(self):
        """Integrate census data."""
        poi_data = self.stage_outputs['extract'][0]
        isochrone_gdf = self.stage_outputs['isochrone']
        
        return integrate_census_data(
            isochrone_gdf=isochrone_gdf,
            census_variables=self.config.census_variables,
            api_key=self.config.api_key,
            poi_data=poi_data,
            geographic_level=self.config.geographic_level
        )
    
    def _export_outputs(self):
        """Export pipeline outputs."""
        poi_data = self.stage_outputs['extract'][0]
        base_filename = self.stage_outputs['extract'][1]
        isochrone_gdf = self.stage_outputs['isochrone']
        census_data_gdf = self.stage_outputs['census'][1]
        census_codes = self.stage_outputs['census'][2]
        directories = self.stage_outputs['setup']
        
        return export_pipeline_outputs(
            census_data_gdf=census_data_gdf,
            poi_data=poi_data,
            isochrone_gdf=isochrone_gdf,
            base_filename=base_filename,
            travel_time=self.config.travel_time,
            directories=directories,
            export_csv=self.config.export_csv,
            export_maps=self.config.export_maps,
            use_interactive_maps=self.config.use_interactive_maps,
            census_codes=census_codes,
            geographic_level=self.config.geographic_level
        )
    
    def _generate_report(self):
        """Generate final report."""
        poi_data = self.stage_outputs['extract'][0]
        base_filename = self.stage_outputs['extract'][1]
        sampled_pois = self.stage_outputs['extract'][3]
        result_files = self.stage_outputs['export']
        
        return generate_final_report(
            poi_data=poi_data,
            sampled_pois=sampled_pois,
            result_files=result_files,
            base_filename=base_filename,
            travel_time=self.config.travel_time
        )
    
    def run(self, skip_on_error: bool = False) -> Dict[str, Any]:
        """
        Execute the pipeline.
        
        Args:
            skip_on_error: Whether to skip failed stages and continue
            
        Returns:
            Dictionary containing all pipeline results
        """
        for stage in self.stages:
            try:
                result = stage.execute()
                self.stage_outputs[stage.name] = result
                
            except Exception as e:
                if skip_on_error:
                    print_error(f"Stage '{stage.name}' failed: {str(e)}")
                    print_info("Continuing with next stage...")
                    continue
                else:
                    self._handle_stage_error(stage.name, e)
                    raise
        
        # Compile final results
        return self._compile_results()
    
    def _handle_stage_error(self, stage_name: str, error: Exception):
        """Handle errors that occur during stage execution."""
        error_context = {
            'stage': stage_name,
            'config': self.config.__dict__,
            'completed_stages': list(self.stage_outputs.keys())
        }
        
        logger.error(f"Pipeline failed at stage '{stage_name}'", extra=error_context)
        
        # Could add error recovery logic here
        
    def _compile_results(self) -> Dict[str, Any]:
        """Compile all stage outputs into final result."""
        # Get the report which contains the main results
        result = self.stage_outputs.get('report', {})
        
        # Add processed data for backward compatibility
        if 'isochrone' in self.stage_outputs:
            result['isochrones'] = self.stage_outputs['isochrone']
            
        if 'census' in self.stage_outputs:
            geographic_units_gdf, census_data_gdf, _ = self.stage_outputs['census']
            result['geographic_units'] = geographic_units_gdf
            result['block_groups'] = geographic_units_gdf  # Backward compatibility
            result['census_data'] = census_data_gdf
        
        return result
    
    def get_stage_output(self, stage_name: str) -> Any:
        """
        Get the output of a specific stage.
        
        Args:
            stage_name: Name of the stage
            
        Returns:
            Output of the stage or None if not executed
        """
        return self.stage_outputs.get(stage_name)
    
    def get_failed_stages(self) -> List[str]:
        """Get list of failed stages."""
        return [stage.name for stage in self.stages if stage.error is not None]