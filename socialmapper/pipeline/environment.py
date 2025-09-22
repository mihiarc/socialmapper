"""Environment setup for the SocialMapper pipeline.

This module handles directory creation, environment configuration,
and initialization of tracking systems.
"""

from pathlib import Path

from ..util import PathSecurityError, sanitize_path
from ..util.invalid_data_tracker import reset_global_tracker


def setup_directory(output_dir: str = "output") -> str:
    """
    Create and validate an output directory.

    Ensures the directory path is safe from security vulnerabilities
    and creates it if it doesn't exist.

    Parameters
    ----------
    output_dir : str, optional
        Path to the output directory, by default "output".

    Returns
    -------
    str
        The sanitized output directory path.

    Raises
    ------
    PathSecurityError
        If the path contains unsafe components like '..' traversal
        or other security risks.

    Examples
    --------
    >>> output_path = setup_directory("results/analysis")
    >>> print(output_path)
    results/analysis

    >>> # Unsafe paths are rejected
    >>> setup_directory("../../../etc")  # doctest: +SKIP
    PathSecurityError: Invalid output directory
    """
    try:
        # Sanitize the output directory path
        safe_output_dir = sanitize_path(output_dir, allow_absolute=True)
        safe_output_dir.mkdir(parents=True, exist_ok=True)
        return str(safe_output_dir)
    except PathSecurityError as e:
        raise PathSecurityError(f"Invalid output directory: {e}") from e


def setup_pipeline_environment(
    output_dir: str, export_csv: bool, export_isochrones: bool, create_maps: bool = True
) -> dict[str, str]:
    """
    Set up the pipeline environment with necessary directories.

    Creates a structured directory hierarchy based on the export
    requirements and resets tracking systems for a clean pipeline run.

    Parameters
    ----------
    output_dir : str
        Base output directory for all pipeline outputs.
    export_csv : bool
        Whether CSV export is enabled, creates census_data subdirectory.
    export_isochrones : bool
        Whether isochrone export is enabled, creates isochrones subdirectory.
    create_maps : bool, optional
        Whether map export is enabled, creates maps subdirectory,
        by default True.

    Returns
    -------
    dict of str
        Dictionary mapping directory types to their paths:
        - 'base': Base output directory
        - 'census_data': CSV export directory (if enabled)
        - 'isochrones': Isochrone export directory (if enabled)
        - 'maps': Map export directory (if enabled)

    Notes
    -----
    This function also resets the global invalid data tracker to ensure
    clean state for the pipeline run.

    Examples
    --------
    >>> dirs = setup_pipeline_environment(
    ...     "output", export_csv=True, export_isochrones=False
    ... )
    >>> print(dirs["base"])
    output
    >>> "census_data" in dirs
    True
    >>> "isochrones" in dirs
    False
    """
    # Create base output directory
    setup_directory(output_dir)

    directories = {"base": output_dir}

    # Create subdirectories only for enabled outputs
    if export_csv:
        # Create census_data subdirectory for CSV files
        census_data_path = Path(output_dir) / "census_data"
        census_data_path.mkdir(exist_ok=True)
        directories["census_data"] = str(census_data_path)

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
