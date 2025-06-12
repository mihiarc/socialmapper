"""
Pipeline package for SocialMapper.

This package contains modular components for the SocialMapper ETL pipeline.
Each module focuses on a specific responsibility following the Single Responsibility Principle.
"""

from .environment import setup_pipeline_environment
from .extraction import extract_poi_data, parse_custom_coordinates
from .validation import validate_poi_coordinates
from .isochrone import generate_isochrones
from .census import integrate_census_data
from .export import export_pipeline_outputs
from .reporting import generate_final_report
from .orchestrator import PipelineOrchestrator
from .helpers import convert_poi_to_geodataframe, setup_directory

__all__ = [
    'setup_pipeline_environment',
    'extract_poi_data',
    'parse_custom_coordinates',
    'validate_poi_coordinates',
    'generate_isochrones',
    'integrate_census_data',
    'export_pipeline_outputs',
    'generate_final_report',
    'PipelineOrchestrator',
    'convert_poi_to_geodataframe',
    'setup_directory'
]