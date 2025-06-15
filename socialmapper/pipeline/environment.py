"""
Environment setup for the SocialMapper pipeline.

This module handles directory creation, environment configuration,
and initialization of tracking systems.
"""

from pathlib import Path
from typing import Dict

from ..util import PathSecurityError, sanitize_path
from ..util.invalid_data_tracker import reset_global_tracker


def setup_directory(output_dir: str = "output") -> str:
    """
    Create a single output directory.

    Args:
        output_dir: Path to the output directory

    Returns:
        The output directory path

    Raises:
        PathSecurityError: If the path is invalid or unsafe
    """
    try:
        # Sanitize the output directory path
        safe_output_dir = sanitize_path(output_dir, allow_absolute=True)
        safe_output_dir.mkdir(parents=True, exist_ok=True)
        return str(safe_output_dir)
    except PathSecurityError as e:
        raise PathSecurityError(f"Invalid output directory: {e}")


def setup_pipeline_environment(
    output_dir: str, export_csv: bool, export_isochrones: bool, create_maps: bool = True
) -> Dict[str, str]:
    """
    Set up the pipeline environment and create necessary directories.

    Args:
        output_dir: Base output directory
        export_csv: Whether CSV export is enabled
        export_isochrones: Whether isochrone export is enabled
        create_maps: Whether map export is enabled

    Returns:
        Dictionary of created directory paths
    """
    # Create base output directory
    setup_directory(output_dir)

    directories = {"base": output_dir}

    # Create subdirectories only for enabled outputs
    if export_csv:
        # Create csv subdirectory directly
        csv_path = Path(output_dir) / "csv"
        csv_path.mkdir(exist_ok=True)
        directories["csv"] = str(csv_path)

    if export_isochrones:
        # Create isochrones subdirectory directly
        isochrones_path = Path(output_dir) / "isochrones"
        isochrones_path.mkdir(exist_ok=True)
        directories["isochrones"] = str(isochrones_path)

    if create_maps:
        # Create maps subdirectory directly
        maps_path = Path(output_dir) / "maps"
        maps_path.mkdir(exist_ok=True)
        directories["maps"] = str(maps_path)

    # Initialize invalid data tracker for this session
    reset_global_tracker(output_dir)

    return directories
