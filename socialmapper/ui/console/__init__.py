#!/usr/bin/env python3
"""Rich Console Package for SocialMapper.

This package provides a centralized Rich console for consistent beautiful
output throughout the SocialMapper application.
"""

# Core console and basic formatting
from .core import (
    clear_console_state,
    console,
    print_banner,
    print_divider,
    print_error,
    print_info,
    print_json,
    print_panel,
    print_statistics,
    print_step,
    print_success,
    print_warning,
    status,
    status_spinner,
)

# Domain-specific display functions
from .domain import (
    log_census_integration_start,
    log_export_start,
    log_isochrone_generation_start,
    log_poi_processing_start,
    print_census_variables_table,
    print_file_summary,
    print_performance_summary,
    print_poi_summary_table,
)

# Logging utilities
from .logging import get_logger, setup_rich_logging

# Progress tracking
from .progress import RichProgressWrapper, progress_bar, rich_tqdm

# Table creation utilities
from .tables import (
    create_data_table,
    create_performance_table,
    create_rich_panel,
    print_table,
)

# For backward compatibility - expose tqdm-compatible wrapper at package level
tqdm = rich_tqdm

__all__ = [
    "RichProgressWrapper",
    "clear_console_state",
    # Core
    "console",
    # Tables
    "create_data_table",
    "create_performance_table",
    "create_rich_panel",
    "get_logger",
    "log_census_integration_start",
    "log_export_start",
    "log_isochrone_generation_start",
    "log_poi_processing_start",
    "print_banner",
    # Domain
    "print_census_variables_table",
    "print_divider",
    "print_error",
    "print_file_summary",
    "print_info",
    "print_json",
    "print_panel",
    "print_performance_summary",
    "print_poi_summary_table",
    "print_statistics",
    "print_step",
    "print_success",
    "print_table",
    "print_warning",
    # Progress
    "progress_bar",
    "rich_tqdm",
    # Logging
    "setup_rich_logging",
    "status",
    "status_spinner",
    "tqdm",
]
