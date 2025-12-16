"""Internal visualization utilities for SocialMapper."""

import io
import logging

import geopandas as gpd
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

from .constants import (
    CRS_WGS84_EPSG,
    METERS_PER_KM,
    SCALE_BAR_ROUND_THRESHOLD,
)

logger = logging.getLogger(__name__)


def generate_choropleth_map(
    gdf: gpd.GeoDataFrame,
    column: str,
    title: str | None = None,
    save_path: str | None = None,
    format: str = "png"
) -> bytes | None:
    """
    Generate a choropleth map from geographic data with auto styling.

    Creates a choropleth map visualization with automatic color scheme
    selection based on data type (numeric sequential/diverging or
    categorical). Includes north arrow and scale bar for reference.

    Parameters
    ----------
    gdf : gpd.GeoDataFrame
        GeoDataFrame containing geometry and data to visualize.
    column : str
        Name of the column in the GeoDataFrame to visualize.
    title : str, optional
        Title to display on the map, by default None.
    save_path : str, optional
        File path to save the map. If None, returns bytes, by default
        None.
    format : str, optional
        Output image format ('png', 'pdf', or 'svg'), by default 'png'.

    Returns
    -------
    bytes or None
        Image bytes if save_path is None, otherwise None after saving.

    Examples
    --------
    >>> import geopandas as gpd
    >>> gdf = gpd.read_file('census_tracts.geojson')
    >>> img_bytes = generate_choropleth_map(
    ...     gdf, 'population', title='Population by Tract'
    ... )

    >>> # Save to file instead
    >>> generate_choropleth_map(
    ...     gdf, 'median_income',
    ...     title='Income Distribution',
    ...     save_path='income_map.png'
    ... )
    """
    # Create figure and axis
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))

    # Remove axis
    ax.set_axis_off()

    # Get data for coloring
    data = gdf[column].values

    # Handle missing data
    valid_data = data[~np.isnan(data)] if isinstance(data[0], int | float) else data

    if len(valid_data) == 0:
        logger.warning(f"No valid data in column '{column}'")
        # Plot with single color
        gdf.plot(ax=ax, color='lightgray', edgecolor='black', linewidth=0.5)
    # Determine color scheme based on data
    elif isinstance(valid_data[0], int | float):
        # Numeric data - use gradient
        vmin, vmax = valid_data.min(), valid_data.max()

        # Choose colormap
        if vmin < 0 and vmax > 0:
            # Diverging data
            cmap = 'RdBu_r'
            norm = mcolors.TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)
        else:
            # Sequential data
            cmap = 'YlOrRd'
            norm = mcolors.Normalize(vmin=vmin, vmax=vmax)

        # Plot choropleth
        gdf.plot(
            column=column,
            ax=ax,
            cmap=cmap,
            norm=norm,
            edgecolor='black',
            linewidth=0.5,
            legend=True,
            legend_kwds={
                'label': column.replace('_', ' ').title(),
                'orientation': 'vertical',
                'shrink': 0.8
            }
        )
    else:
        # Categorical data
        unique_values = gdf[column].unique()
        n_colors = len(unique_values)

        # Create color map
        colors = plt.cm.Set3(np.linspace(0, 1, n_colors))
        color_map = {val: colors[i] for i, val in enumerate(unique_values)}

        # Plot with categorical colors
        gdf['color'] = gdf[column].map(color_map)
        gdf.plot(ax=ax, color=gdf['color'], edgecolor='black', linewidth=0.5)

        # Add legend
        patches = [Patch(color=color, label=str(val)) for val, color in color_map.items()]
        ax.legend(handles=patches, loc='best', title=column.replace('_', ' ').title())

    # Add title
    if title:
        plt.title(title, fontsize=16, fontweight='bold', pad=20)

    # Add north arrow
    add_north_arrow(ax)

    # Add scale bar
    add_scale_bar(ax, gdf)

    # Adjust layout
    plt.tight_layout()

    # Save or return bytes
    if save_path:
        plt.savefig(save_path, format=format, dpi=150, bbox_inches='tight')
        plt.close()
        logger.info(f"Map saved to {save_path}")
        return None
    else:
        # Return as bytes
        buf = io.BytesIO()
        plt.savefig(buf, format=format, dpi=150, bbox_inches='tight')
        plt.close()
        buf.seek(0)
        return buf.read()


def add_north_arrow(ax):
    """
    Add a north arrow indicator to the map in the upper right corner.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Matplotlib axis object to add the north arrow to.

    Examples
    --------
    >>> import matplotlib.pyplot as plt
    >>> fig, ax = plt.subplots()
    >>> add_north_arrow(ax)
    """
    # Get axis bounds
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    # Position in upper right
    x = xlim[0] + (xlim[1] - xlim[0]) * 0.95
    y = ylim[0] + (ylim[1] - ylim[0]) * 0.95

    # Draw arrow
    arrow_length = (ylim[1] - ylim[0]) * 0.05
    ax.annotate(
        'N',
        xy=(x, y),
        xytext=(x, y - arrow_length),
        arrowprops={
            "arrowstyle": '->,head_width=0.3,head_length=0.3',
            "lw": 2,
            "color": 'black'
        },
        ha='center',
        va='bottom',
        fontsize=14,
        fontweight='bold'
    )


def add_scale_bar(ax, gdf):
    """
    Add a scale bar to the map in the lower left corner.

    Automatically calculates appropriate scale based on map extent and
    converts units based on coordinate reference system. Displays
    distance in kilometers or meters as appropriate.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Matplotlib axis object to add the scale bar to.
    gdf : gpd.GeoDataFrame
        GeoDataFrame used to determine map extent and CRS for scale
        calculation.

    Examples
    --------
    >>> import geopandas as gpd
    >>> import matplotlib.pyplot as plt
    >>> gdf = gpd.read_file('boundaries.geojson')
    >>> fig, ax = plt.subplots()
    >>> gdf.plot(ax=ax)
    >>> add_scale_bar(ax, gdf)
    """
    try:

        # Get bounds
        bounds = gdf.total_bounds  # minx, miny, maxx, maxy
        width = bounds[2] - bounds[0]

        # Estimate scale bar length (roughly 1/5 of map width)
        scale_length = width / 5

        # Round to nice number
        if scale_length > 1:
            scale_length = round(scale_length)
        elif scale_length > SCALE_BAR_ROUND_THRESHOLD:
            scale_length = round(scale_length, 1)
        else:
            scale_length = round(scale_length, 2)

        # Position in lower left
        x_start = bounds[0] + width * 0.05
        y = bounds[1] + (bounds[3] - bounds[1]) * 0.05
        x_end = x_start + scale_length

        # Draw scale bar
        ax.plot([x_start, x_end], [y, y], 'k-', linewidth=3)
        ax.plot([x_start, x_start], [y - scale_length*0.01, y + scale_length*0.01], 'k-', linewidth=3)
        ax.plot([x_end, x_end], [y - scale_length*0.01, y + scale_length*0.01], 'k-', linewidth=3)

        # Determine units and label
        if gdf.crs and gdf.crs.to_epsg() == CRS_WGS84_EPSG:
            # Degrees - convert to km
            # Rough approximation at middle latitude
            mid_lat = (bounds[1] + bounds[3]) / 2
            km_per_degree = 111 * np.cos(np.radians(mid_lat))
            distance_km = scale_length * km_per_degree

            label = f"{distance_km:.0f} km" if distance_km >= 1 else f"{distance_km*METERS_PER_KM:.0f} m"
        # Assume meters
        elif scale_length >= METERS_PER_KM:
            label = f"{scale_length/METERS_PER_KM:.0f} km"
        else:
            label = f"{scale_length:.0f} m"

        # Add label
        ax.text(
            (x_start + x_end) / 2,
            y - scale_length * 0.02,
            label,
            ha='center',
            va='top',
            fontsize=10
        )

    except (ValueError, TypeError, AttributeError) as e:
        logger.debug(f"Could not add scale bar: {e}")


def create_simple_map(data: list, title: str | None = None) -> bytes:
    """
    Create a simple scatter plot map from a list of point locations.

    Generates a basic map visualization showing points with optional
    labels. Returns image as PNG bytes for embedding or serving via API.

    Parameters
    ----------
    data : list of dict
        List of location dictionaries. Each dict must contain 'lat' and
        'lon' keys. Optional 'name' key adds point labels.
    title : str, optional
        Title to display on the map, by default None.

    Returns
    -------
    bytes
        PNG image data as bytes.

    Examples
    --------
    >>> locations = [
    ...     {'lat': 42.3601, 'lon': -71.0589, 'name': 'Boston'},
    ...     {'lat': 40.7128, 'lon': -74.0060, 'name': 'New York'}
    ... ]
    >>> img_bytes = create_simple_map(locations, 'Major Cities')
    """
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))

    # Extract coordinates
    lons = [d['lon'] for d in data]
    lats = [d['lat'] for d in data]

    # Plot points
    ax.scatter(lons, lats, c='red', s=50, alpha=0.6, edgecolors='black', linewidth=1)

    # Add labels if names provided
    for item in data:
        if 'name' in item:
            ax.annotate(
                item['name'],
                (item['lon'], item['lat']),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=8,
                alpha=0.7
            )

    # Set limits with padding
    lon_range = max(lons) - min(lons)
    lat_range = max(lats) - min(lats)
    padding = 0.1

    ax.set_xlim(min(lons) - lon_range * padding, max(lons) + lon_range * padding)
    ax.set_ylim(min(lats) - lat_range * padding, max(lats) + lat_range * padding)

    # Labels
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')

    if title:
        ax.set_title(title, fontsize=14, fontweight='bold')

    # Grid
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    # Return as bytes
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return buf.read()
