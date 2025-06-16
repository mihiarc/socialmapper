"""Utility functions for map visualization."""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.offsetbox import AnchoredOffsetbox, DrawingArea, HPacker, TextArea
from matplotlib.patches import FancyBboxPatch, Polygon


def add_north_arrow(
    ax: plt.Axes,
    location: str = "upper right",
    scale: float = 0.5,
    arrow_color: str = "black",
    text_color: str = "black",
    fontsize: int = 12,
) -> None:
    """Add a north arrow to the map.

    Args:
        ax: Matplotlib axes object
        location: Location of the north arrow
        scale: Scale factor for arrow size
        arrow_color: Color of the arrow
        text_color: Color of the 'N' text
        fontsize: Font size for 'N' text
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
        text = TextArea(
            "N",
            textprops=dict(
                color=text_color,
                fontsize=fontsize * scale,
                fontweight="bold",
                ha="center",
                va="center",
            ),
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
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
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
    """Add a scale bar to the map.

    Note: This is a simplified scale bar. For accurate scale bars,
    use matplotlib-scalebar package or cartopy.

    Args:
        ax: Matplotlib axes object
        location: Location of the scale bar
        length_fraction: Fraction of axes width for scale bar
        height_fraction: Fraction of axes height for scale bar
        box_alpha: Alpha value for background box
        font_size: Font size for scale text
        color: Color of scale bar and text
        box_color: Background box color
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
    if scale_km < 1:
        scale_text = f"{int(scale_km * 1000)} m"
    elif scale_km < 10:
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
    """Format number for display with thousands separator.

    Args:
        value: Number to format
        decimals: Number of decimal places

    Returns:
        Formatted string
    """
    if pd.isna(value):
        return "N/A"

    if decimals == 0:
        return f"{int(value):,}"
    else:
        return f"{value:,.{decimals}f}"


def get_color_ramp(cmap_name: str, n_colors: int, reverse: bool = False) -> list:
    """Get a list of colors from a colormap.

    Args:
        cmap_name: Name of the matplotlib colormap
        n_colors: Number of colors to extract
        reverse: Whether to reverse the color order

    Returns:
        List of color hex strings
    """
    cmap = plt.get_cmap(cmap_name)
    colors = [cmap(i / (n_colors - 1)) for i in range(n_colors)]

    if reverse:
        colors = colors[::-1]

    # Convert to hex
    hex_colors = [f"#{int(color[0] * 255):02x}{int(color[1] * 255):02x}{int(color[2] * 255):02x}" for color in colors]

    return hex_colors


def calculate_map_extent(
    gdf: "gpd.GeoDataFrame", buffer_factor: float = 0.1
) -> tuple[float, float, float, float]:
    """Calculate appropriate map extent with buffer.

    Args:
        gdf: GeoDataFrame to calculate extent for
        buffer_factor: Buffer to add around data (fraction of extent)

    Returns:
        Tuple of (xmin, xmax, ymin, ymax)
    """
    bounds = gdf.total_bounds  # minx, miny, maxx, maxy
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]

    buffer_x = width * buffer_factor
    buffer_y = height * buffer_factor

    return (bounds[0] - buffer_x, bounds[2] + buffer_x, bounds[1] - buffer_y, bounds[3] + buffer_y)


def validate_geodataframe(gdf: "gpd.GeoDataFrame") -> None:
    """Validate that a GeoDataFrame is suitable for mapping.

    Args:
        gdf: GeoDataFrame to validate

    Raises:
        ValueError: If GeoDataFrame is invalid
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
