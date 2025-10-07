"""Utility functions for map visualization."""

import geopandas as gpd
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.offsetbox import AnchoredOffsetbox, DrawingArea, HPacker, TextArea
from matplotlib.patches import FancyBboxPatch, Polygon

# Scale bar formatting constants
KM_TO_M_THRESHOLD = 1
KM_FORMAT_THRESHOLD = 10


def add_north_arrow(
    ax: plt.Axes,
    location: str = "upper right",
    scale: float = 0.5,
    arrow_color: str = "black",
    text_color: str = "black",
    fontsize: int = 12,
) -> None:
    """
    Add a north arrow indicator to a map visualization.

    Creates a decorative north arrow with customizable position,
    size, and colors. Falls back to simple text arrow if rendering
    fails.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Matplotlib axes object to add the north arrow to.
    location : str, optional
        Position on the map. Options: 'upper right', 'upper left',
        'lower left', 'lower right', 'center', etc. By default
        'upper right'.
    scale : float, optional
        Size multiplier for the arrow, by default 0.5.
    arrow_color : str, optional
        Color of the arrow shape, by default 'black'.
    text_color : str, optional
        Color of the 'N' text, by default 'black'.
    fontsize : int, optional
        Font size for the 'N' text, by default 12.

    Examples
    --------
    >>> import matplotlib.pyplot as plt
    >>> fig, ax = plt.subplots()
    >>> add_north_arrow(ax, location='upper left', scale=0.8)
    """
    try:
        # Create drawing area
        arrow_size = 40 * scale
        da = DrawingArea(arrow_size, arrow_size * 1.5)

        # Create arrow shape
        arrow_verts = [
            (arrow_size * 0.5, 0),  # Bottom point
            (arrow_size * 0.3, arrow_size * 0.5),  # Left side
            (arrow_size * 0.4, arrow_size * 0.5),  # Left inner
            (arrow_size * 0.4, arrow_size * 0.8),  # Left stem
            (arrow_size * 0.6, arrow_size * 0.8),  # Right stem
            (arrow_size * 0.6, arrow_size * 0.5),  # Right inner
            (arrow_size * 0.7, arrow_size * 0.5),  # Right side
            (arrow_size * 0.5, 0),  # Back to bottom
        ]

        arrow = Polygon(arrow_verts, closed=True, color=arrow_color)
        da.add_artist(arrow)

        # Create text
        TextArea(
            "N",
            textprops={
                "color": text_color,
                "fontsize": fontsize * scale,
                "fontweight": "bold",
                "ha": "center",
                "va": "center",
            },
        )

        # Pack arrow and text
        box = HPacker(children=[da], pad=0, sep=0)

        # Convert location string to numeric code
        loc_dict = {
            "upper right": 1,
            "upper left": 2,
            "lower left": 3,
            "lower right": 4,
            "right": 5,
            "center left": 6,
            "center right": 7,
            "lower center": 8,
            "upper center": 9,
            "center": 10,
        }
        loc_code = loc_dict.get(location, 1)

        # Create anchored box
        anchored_box = AnchoredOffsetbox(
            loc=loc_code,
            child=box,
            pad=0.4,
            frameon=False,
            bbox_to_anchor=(1, 1),
            bbox_transform=ax.transAxes,
        )

        ax.add_artist(anchored_box)

    except Exception:
        # Fallback: Simple text-based north arrow
        x_pos = 0.95 if "right" in location else 0.05
        y_pos = 0.95 if "upper" in location else 0.05
        ha = "right" if "right" in location else "left"
        va = "top" if "upper" in location else "bottom"

        ax.text(
            x_pos,
            y_pos,
            "N\n↑",
            transform=ax.transAxes,
            fontsize=fontsize,
            fontweight="bold",
            ha=ha,
            va=va,
            bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.8},
        )


def add_scale_bar(
    ax: plt.Axes,
    location: str = "lower right",
    length_fraction: float = 0.25,
    height_fraction: float = 0.01,
    box_alpha: float = 0.8,
    font_size: int = 10,
    color: str = "black",
    box_color: str = "white",
) -> None:
    """
    Add a simplified scale bar to a map visualization.

    Creates an approximate scale bar with distance estimation. For
    accurate scale bars with proper projection support, use the
    matplotlib-scalebar package or cartopy instead.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Matplotlib axes object to add the scale bar to.
    location : str, optional
        Position on the map. Options: 'lower right', 'lower left',
        'upper right', etc. By default 'lower right'.
    length_fraction : float, optional
        Scale bar length as fraction of axes width, by default 0.25.
    height_fraction : float, optional
        Scale bar height as fraction of axes height, by default 0.01.
    box_alpha : float, optional
        Transparency of background box (0-1), by default 0.8.
    font_size : int, optional
        Font size for distance label, by default 10.
    color : str, optional
        Color of scale bar and text, by default 'black'.
    box_color : str, optional
        Background box color, by default 'white'.

    Examples
    --------
    >>> import matplotlib.pyplot as plt
    >>> fig, ax = plt.subplots()
    >>> add_scale_bar(ax, location='lower left', length_fraction=0.3)

    Notes
    -----
    Scale distance uses rough approximation (1 degree ≈ 111 km).
    Results may be inaccurate for non-geographic projections.
    """
    # Get axis limits
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()

    # Calculate scale bar dimensions
    axes_width = x_max - x_min
    axes_height = y_max - y_min
    scale_length = axes_width * length_fraction
    scale_height = axes_height * height_fraction

    # Determine position based on location
    padding = 0.02  # Padding from edges
    if "lower" in location:
        y_pos = y_min + (axes_height * padding)
    else:
        y_pos = y_max - (axes_height * padding) - scale_height

    if "right" in location:
        x_pos = x_max - (axes_width * padding) - scale_length
    elif "left" in location:
        x_pos = x_min + (axes_width * padding)
    else:  # center
        x_pos = x_min + (axes_width - scale_length) / 2

    # Create scale bar
    scale_bar = mpatches.Rectangle(
        (x_pos, y_pos), scale_length, scale_height, facecolor=color, edgecolor=color
    )
    ax.add_patch(scale_bar)

    # Add background box
    box_padding = scale_height * 2
    background = FancyBboxPatch(
        (x_pos - box_padding, y_pos - box_padding),
        scale_length + 2 * box_padding,
        scale_height + 4 * box_padding,
        boxstyle="round,pad=0.1",
        facecolor=box_color,
        edgecolor="none",
        alpha=box_alpha,
        zorder=4,
    )
    ax.add_patch(background)

    # Estimate scale distance (this is approximate without proper projection)
    # For more accurate scale bars, use the actual CRS and projection
    scale_km = scale_length * 111  # Very rough approximation (1 degree ≈ 111 km)

    # Format scale text
    if scale_km < KM_TO_M_THRESHOLD:
        scale_text = f"{int(scale_km * 1000)} m"
    elif scale_km < KM_FORMAT_THRESHOLD:
        scale_text = f"{scale_km:.1f} km"
    else:
        scale_text = f"{int(scale_km)} km"

    # Add scale text
    ax.text(
        x_pos + scale_length / 2,
        y_pos + scale_height + box_padding,
        scale_text,
        fontsize=font_size,
        ha="center",
        va="bottom",
        color=color,
        zorder=5,
    )


def format_number(value: int | float, decimals: int = 0) -> str:
    """
    Format numeric values with thousands separators for display.

    Handles missing values (NaN) and formats integers or floats with
    commas for readability.

    Parameters
    ----------
    value : int or float
        Number to format for display.
    decimals : int, optional
        Number of decimal places to show, by default 0.

    Returns
    -------
    str
        Formatted string with thousands separators, or 'N/A' for NaN.

    Examples
    --------
    >>> format_number(1234567)
    '1,234,567'

    >>> format_number(1234.5678, decimals=2)
    '1,234.57'

    >>> import pandas as pd
    >>> format_number(pd.NA)
    'N/A'
    """
    if pd.isna(value):
        return "N/A"

    if decimals == 0:
        return f"{int(value):,}"
    else:
        return f"{value:,.{decimals}f}"


def get_color_ramp(cmap_name: str, n_colors: int, reverse: bool = False) -> list:
    """
    Extract evenly-spaced colors from a matplotlib colormap.

    Generates a discrete color palette by sampling from a continuous
    colormap. Returns colors as hex strings for easy use in plots.

    Parameters
    ----------
    cmap_name : str
        Name of the matplotlib colormap (e.g., 'viridis', 'coolwarm',
        'RdYlBu').
    n_colors : int
        Number of discrete colors to extract from the colormap.
    reverse : bool, optional
        Whether to reverse the color order, by default False.

    Returns
    -------
    list of str
        List of color hex strings (e.g., ['#440154', '#31688e']).

    Examples
    --------
    >>> colors = get_color_ramp('viridis', 5)
    >>> len(colors)
    5
    >>> colors[0].startswith('#')
    True

    >>> colors = get_color_ramp('RdYlBu', 3, reverse=True)
    >>> len(colors)
    3
    """
    cmap = plt.get_cmap(cmap_name)
    colors = [cmap(i / (n_colors - 1)) for i in range(n_colors)]

    if reverse:
        colors.reverse()

    # Convert to hex
    hex_colors = [
        f"#{int(color[0] * 255):02x}{int(color[1] * 255):02x}{int(color[2] * 255):02x}"
        for color in colors
    ]

    return hex_colors


def calculate_map_extent(
    gdf: gpd.GeoDataFrame, buffer_factor: float = 0.1
) -> tuple[float, float, float, float]:
    """
    Calculate map extent with buffer around geographic data.

    Adds proportional padding around the bounding box of a
    GeoDataFrame to prevent features from touching map edges.

    Parameters
    ----------
    gdf : gpd.GeoDataFrame
        GeoDataFrame to calculate extent for.
    buffer_factor : float, optional
        Proportional buffer to add around data as fraction of extent
        dimensions, by default 0.1 (10% padding).

    Returns
    -------
    tuple of float
        Map extent as (xmin, xmax, ymin, ymax).

    Examples
    --------
    >>> import geopandas as gpd
    >>> gdf = gpd.read_file('data.geojson')
    >>> extent = calculate_map_extent(gdf, buffer_factor=0.15)
    >>> xmin, xmax, ymin, ymax = extent
    """
    bounds = gdf.total_bounds  # minx, miny, maxx, maxy
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]

    buffer_x = width * buffer_factor
    buffer_y = height * buffer_factor

    return (bounds[0] - buffer_x, bounds[2] + buffer_x, bounds[1] - buffer_y, bounds[3] + buffer_y)


def validate_geodataframe(gdf: gpd.GeoDataFrame) -> None:
    """
    Validate GeoDataFrame suitability for map visualization.

    Checks for common issues: empty data, missing geometries, no CRS
    definition, and invalid geometries that could cause rendering
    failures.

    Parameters
    ----------
    gdf : gpd.GeoDataFrame
        GeoDataFrame to validate before visualization.

    Raises
    ------
    ValueError
        If GeoDataFrame is empty, has all null geometries, lacks a
        CRS, or contains invalid geometries.

    Examples
    --------
    >>> import geopandas as gpd
    >>> gdf = gpd.read_file('valid_data.geojson')
    >>> validate_geodataframe(gdf)  # No exception

    >>> empty_gdf = gpd.GeoDataFrame()
    >>> validate_geodataframe(empty_gdf)  # Raises ValueError
    Traceback (most recent call last):
        ...
    ValueError: GeoDataFrame is empty
    """
    if gdf.empty:
        raise ValueError("GeoDataFrame is empty")

    if gdf.geometry.isna().all():
        raise ValueError("All geometries are null")

    if not gdf.crs:
        raise ValueError("GeoDataFrame has no CRS defined")

    # Check for invalid geometries
    invalid_geoms = ~gdf.geometry.is_valid
    if invalid_geoms.any():
        n_invalid = invalid_geoms.sum()
        raise ValueError(f"GeoDataFrame contains {n_invalid} invalid geometries")
