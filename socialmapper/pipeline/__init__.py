"""
Pipeline package for SocialMapper.

This package contains modular components for the SocialMapper ETL pipeline.
Each module focuses on a specific responsibility following the Single Responsibility Principle.
"""

from .census import integrate_census_data
from .environment import setup_pipeline_environment
from .export import export_pipeline_outputs
from .extraction import extract_poi_data, parse_custom_coordinates
from .helpers import convert_poi_to_geodataframe, setup_directory
from .isochrone import generate_isochrones
from .orchestrator import PipelineConfig, PipelineOrchestrator
from .reporting import generate_final_report
from .validation import validate_poi_coordinates

__all__ = [
    "setup_pipeline_environment",
    "extract_poi_data",
    "parse_custom_coordinates",
    "validate_poi_coordinates",
    "generate_isochrones",
    "integrate_census_data",
    "export_pipeline_outputs",
    "generate_final_report",
    "PipelineOrchestrator",
    "PipelineConfig",
    "convert_poi_to_geodataframe",
    "setup_directory",
]
