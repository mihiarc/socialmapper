"""Utility functions for the Streamlit application."""

from .cache import (
    clear_analysis_cache,
    clear_specific_cache,
    get_census_variables,
    get_map_base_config,
    get_poi_types,
    load_census_data,
    run_cached_analysis,
    run_analysis_with_progress,
    validate_coordinates,
)
from .formatters import (
    format_census_variable,
    format_currency,
    format_distance,
    format_number,
    format_percentage,
    format_time,
)
from .progress import (
    ProgressTracker,
    animated_progress,
    multi_progress,
    progress_context,
    progress_with_eta,
    show_progress,
)
from .theme import (
    apply_theme_class,
    get_current_theme,
    get_map_style,
    get_theme_colors,
    theme_info_box,
    theme_metric_card,
)

__all__ = [
    # Cache utilities
    "clear_analysis_cache",
    "clear_specific_cache", 
    "get_census_variables",
    "get_map_base_config",
    "get_poi_types",
    "load_census_data",
    "run_cached_analysis",
    "run_analysis_with_progress",
    "validate_coordinates",
    # Formatters
    "format_census_variable",
    "format_currency",
    "format_distance",
    "format_number",
    "format_percentage",
    "format_time",
    # Progress utilities
    "ProgressTracker",
    "animated_progress", 
    "multi_progress",
    "progress_context",
    "progress_with_eta",
    "show_progress",
    # Theme utilities
    "apply_theme_class",
    "get_current_theme",
    "get_map_style",
    "get_theme_colors",
    "theme_info_box",
    "theme_metric_card",
]
