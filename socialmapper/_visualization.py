"""Internal visualization utilities for SocialMapper."""

import io
import logging

import contextily as cx
import geopandas as gpd
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from matplotlib.patches import Patch
from pyproj import Transformer

from .constants import (
    BASEMAP_ALPHA,
    CHOROPLETH_ALPHA,
    CHOROPLETH_EDGE_COLOR,
    CHOROPLETH_EDGE_WIDTH,
    CRS_WEB_MERCATOR,
    CRS_WGS84_EPSG,
    DEFAULT_BASEMAP,
    DEFAULT_CATEGORICAL_CMAP,
    DEFAULT_CHOROPLETH_CMAP,
    DEFAULT_DIVERGING_CMAP,
    LABEL_BG_ALPHA,
    LABEL_BG_COLOR,
    LABEL_EDGE_COLOR,
    LABEL_FONTSIZE,
    LABEL_PAD,
    MAP_ACCENT_COLOR,
    MAP_DPI,
    MAP_FACECOLOR,
    MAP_FIGURE_SIZE,
    METERS_PER_KM,
    NORTH_ARROW_FONTSIZE,
    NORTH_ARROW_LINE_WIDTH,
    OVERLAY_BOUNDARY_COLOR,
    OVERLAY_BOUNDARY_STYLE,
    OVERLAY_BOUNDARY_WIDTH,
    OVERLAY_POINT_COLOR,
    OVERLAY_POINT_EDGE_COLOR,
    OVERLAY_POINT_EDGE_WIDTH,
    OVERLAY_POINT_SIZE,
    SCALE_BAR_LINE_WIDTH,
    SCALE_BAR_ROUND_THRESHOLD,
    STATS_BOX_ALPHA,
    STATS_BOX_BORDER_COLOR,
    STATS_BOX_FONT_FAMILY,
    STATS_BOX_FONTSIZE,
    TITLE_COLOR,
    TITLE_FONTSIZE,
)

logger = logging.getLogger(__name__)


def generate_choropleth_map(
    gdf: gpd.GeoDataFrame,
    column: str,
    title: str | None = None,
    save_path: str | None = None,
    output_format: str = "png",
    basemap: str | None = DEFAULT_BASEMAP,
    cmap: str | None = None,
    overlay_boundary: gpd.GeoDataFrame | None = None,
    overlay_points: list[dict] | None = None,
    show_stats: bool = False,
    stats_dict: dict | None = None,
) -> bytes | None:
    """
    Generate a choropleth map from geographic data with enhanced styling.

    Creates a choropleth map visualization with automatic color scheme
    selection based on data type (numeric sequential/diverging or
    categorical). Supports contextily basemaps, overlay layers for
    boundaries and points, and optional statistics annotations.

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
    output_format : str, optional
        Output image format ('png', 'pdf', or 'svg'), by default 'png'.
    basemap : str, optional
        Basemap provider name. Options include:
        - 'CartoDB.Voyager' (default): Clean, light basemap
        - 'CartoDB.Positron': Minimal, grayscale basemap
        - 'CartoDB.DarkMatter': Dark theme basemap
        - None: No basemap (plain white background)
    cmap : str, optional
        Matplotlib colormap name. If None, auto-selects based on data:
        - Sequential numeric: 'YlGnBu'
        - Diverging numeric: 'RdBu_r'
        - Categorical: 'Set3'
    overlay_boundary : gpd.GeoDataFrame, optional
        GeoDataFrame with boundary geometry to overlay (e.g., isochrone).
        Displayed as dashed red line.
    overlay_points : list of dict, optional
        List of point markers to overlay. Each dict must have:
        - 'lat': Latitude
        - 'lon': Longitude
        - 'name' (optional): Label for the point
    show_stats : bool, optional
        Whether to display a statistics box, by default False.
    stats_dict : dict, optional
        Custom statistics to display. If None and show_stats is True,
        basic statistics are calculated from the data column.

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

    >>> # With basemap and overlays
    >>> generate_choropleth_map(
    ...     gdf, 'median_income',
    ...     title='Income Distribution',
    ...     basemap='CartoDB.Positron',
    ...     overlay_boundary=isochrone_gdf,
    ...     overlay_points=[{'lat': 45.5, 'lon': -122.6, 'name': 'Origin'}],
    ...     show_stats=True,
    ...     save_path='income_map.png'
    ... )
    """
    # Determine if we need Web Mercator projection (for basemap)
    use_basemap = basemap is not None

    # Prepare the GeoDataFrame
    if use_basemap:
        # Reproject to Web Mercator for basemap compatibility
        gdf_plot = gdf.to_crs(CRS_WEB_MERCATOR)
    else:
        gdf_plot = gdf.copy()

    # Create figure and axis
    fig, ax = plt.subplots(1, 1, figsize=MAP_FIGURE_SIZE)
    fig.set_facecolor(MAP_FACECOLOR)

    try:
        # Remove axis frame but keep for scale bar calculation
        ax.set_axis_off()

        # Get data for coloring
        data = gdf[column].values

        # Handle empty data
        if len(data) == 0:
            logger.warning("No data in column '%s', rendering blank map", column)
            gdf_plot.plot(
                ax=ax,
                color='lightgray',
                edgecolor=CHOROPLETH_EDGE_COLOR,
                linewidth=CHOROPLETH_EDGE_WIDTH,
                alpha=CHOROPLETH_ALPHA,
            )
            valid_data = data
        # Handle missing data
        elif isinstance(data[0], int | float):
            valid_data = data[~np.isnan(data)]
        else:
            valid_data = data

        # Determine colormap
        if cmap is not None:
            selected_cmap = cmap
        elif len(valid_data) == 0:
            selected_cmap = None
        elif isinstance(valid_data[0], int | float):
            vmin, vmax = valid_data.min(), valid_data.max()
            if vmin < 0 and vmax > 0:
                selected_cmap = DEFAULT_DIVERGING_CMAP
            else:
                selected_cmap = DEFAULT_CHOROPLETH_CMAP
        else:
            selected_cmap = DEFAULT_CATEGORICAL_CMAP

        # Plot the choropleth (skip if empty data already rendered above)
        if len(data) > 0:
            if len(valid_data) == 0:
                logger.warning("No valid data in column '%s'", column)
                gdf_plot.plot(
                    ax=ax,
                    color='lightgray',
                    edgecolor=CHOROPLETH_EDGE_COLOR,
                    linewidth=CHOROPLETH_EDGE_WIDTH,
                    alpha=CHOROPLETH_ALPHA,
                )
            elif isinstance(valid_data[0], int | float):
                # Numeric data - use gradient
                vmin, vmax = valid_data.min(), valid_data.max()

                if vmin < 0 and vmax > 0:
                    # Diverging data
                    norm = mcolors.TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)
                else:
                    # Sequential data
                    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)

                # Plot choropleth with enhanced styling
                gdf_plot.plot(
                    column=column,
                    ax=ax,
                    cmap=selected_cmap,
                    norm=norm,
                    edgecolor=CHOROPLETH_EDGE_COLOR,
                    linewidth=CHOROPLETH_EDGE_WIDTH,
                    alpha=CHOROPLETH_ALPHA,
                    legend=True,
                    legend_kwds={
                        'label': column.replace('_', ' ').title(),
                        'orientation': 'vertical',
                        'shrink': 0.8,
                        'format': mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'),
                    }
                )
            else:
                # Categorical data
                unique_values = gdf[column].unique()
                n_colors = len(unique_values)

                # Create color map
                colors = plt.cm.get_cmap(selected_cmap)(np.linspace(0, 1, n_colors))
                color_map = {val: colors[i] for i, val in enumerate(unique_values)}

                # Plot with categorical colors
                gdf_plot_cat = gdf_plot.copy()
                gdf_plot_cat['_plot_color'] = gdf[column].map(color_map)
                gdf_plot_cat.plot(
                    ax=ax,
                    color=gdf_plot_cat['_plot_color'],
                    edgecolor=CHOROPLETH_EDGE_COLOR,
                    linewidth=CHOROPLETH_EDGE_WIDTH,
                    alpha=CHOROPLETH_ALPHA,
                )

                # Add legend
                patches = [
                    Patch(color=color, label=str(val))
                    for val, color in color_map.items()
                ]
                ax.legend(
                    handles=patches,
                    loc='best',
                    title=column.replace('_', ' ').title()
                )

        # Add basemap if requested
        if use_basemap:
            try:
                provider = _get_basemap_provider(basemap)
                cx.add_basemap(ax, source=provider, alpha=BASEMAP_ALPHA, zorder=-1)
            except Exception as e:
                logger.warning("Could not add basemap: %s", e)

        # Add overlay boundary if provided
        if overlay_boundary is not None:
            _add_overlay_boundary(ax, overlay_boundary, use_basemap)

        # Add overlay points if provided
        if overlay_points:
            _add_overlay_points(ax, overlay_points, use_basemap)

        # Add stats box if requested
        if show_stats:
            _add_stats_box(ax, gdf, column, stats_dict)

        # Add title
        if title:
            plt.title(
                title,
                fontsize=TITLE_FONTSIZE,
                fontweight='bold',
                color=TITLE_COLOR,
                pad=20,
            )

        # Add north arrow (using original CRS extent for proper positioning)
        add_north_arrow(ax)

        # Add scale bar (using plot GeoDataFrame for proper units)
        add_scale_bar(ax, gdf_plot, use_web_mercator=use_basemap)

        # Layout
        plt.tight_layout(pad=1.5)

        # Save or return bytes
        if save_path:
            plt.savefig(
                save_path, format=output_format, dpi=MAP_DPI,
                bbox_inches='tight', facecolor=fig.get_facecolor(),
            )
            plt.close(fig)
            logger.info("Map saved to %s", save_path)
            return None
        else:
            # Return as bytes
            buf = io.BytesIO()
            plt.savefig(
                buf, format=output_format, dpi=MAP_DPI,
                bbox_inches='tight', facecolor=fig.get_facecolor(),
            )
            plt.close(fig)
            buf.seek(0)
            return buf.read()
    except Exception:
        plt.close(fig)
        raise


def _get_basemap_provider(basemap: str):
    """
    Get the contextily basemap provider from a string name.

    Parameters
    ----------
    basemap : str
        Basemap provider name (e.g., 'CartoDB.Voyager').

    Returns
    -------
    contextily provider
        The provider object for the requested basemap.
    """
    # Handle common basemap names
    basemap_mapping = {
        'CartoDB.Voyager': cx.providers.CartoDB.Voyager,
        'CartoDB.Positron': cx.providers.CartoDB.Positron,
        'CartoDB.DarkMatter': cx.providers.CartoDB.DarkMatter,
        'OpenStreetMap.Mapnik': cx.providers.OpenStreetMap.Mapnik,
        'Stamen.Toner': cx.providers.Stadia.StamenToner,
        'Stamen.TonerLite': cx.providers.Stadia.StamenTonerLite,
        'Stamen.Watercolor': cx.providers.Stadia.StamenWatercolor,
    }

    if basemap in basemap_mapping:
        return basemap_mapping[basemap]

    # Try to parse as Provider.Style format
    if '.' in basemap:
        parts = basemap.split('.')
        try:
            provider = getattr(cx.providers, parts[0])
            return getattr(provider, parts[1])
        except AttributeError:
            pass

    # Default to CartoDB Voyager
    logger.warning("Unknown basemap '%s', using CartoDB.Voyager", basemap)
    return cx.providers.CartoDB.Voyager


def _add_overlay_boundary(
    ax,
    boundary_gdf: gpd.GeoDataFrame,
    use_web_mercator: bool
) -> None:
    """
    Add a boundary overlay to the map.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes to add the boundary to.
    boundary_gdf : gpd.GeoDataFrame
        GeoDataFrame with the boundary geometry.
    use_web_mercator : bool
        Whether to reproject to Web Mercator.
    """
    try:
        if use_web_mercator:
            boundary_plot = boundary_gdf.to_crs(CRS_WEB_MERCATOR)
        else:
            boundary_plot = boundary_gdf

        # Plot just the boundary (not filled)
        boundary_plot.boundary.plot(
            ax=ax,
            color=OVERLAY_BOUNDARY_COLOR,
            linewidth=OVERLAY_BOUNDARY_WIDTH,
            linestyle=OVERLAY_BOUNDARY_STYLE,
            zorder=3
        )
    except Exception as e:
        logger.warning("Could not add overlay boundary: %s", e)


def _add_overlay_points(
    ax,
    points: list[dict],
    use_web_mercator: bool
) -> None:
    """
    Add point markers to the map.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes to add points to.
    points : list of dict
        List of point dictionaries with 'lat', 'lon', and optional 'name'.
    use_web_mercator : bool
        Whether to transform coordinates to Web Mercator.
    """
    try:
        if use_web_mercator:
            transformer = Transformer.from_crs(
                'EPSG:4326',
                CRS_WEB_MERCATOR,
                always_xy=True
            )

        for point in points:
            if 'lat' not in point or 'lon' not in point:
                continue

            if use_web_mercator:
                x, y = transformer.transform(point['lon'], point['lat'])
            else:
                x, y = point['lon'], point['lat']

            # Plot the marker
            ax.scatter(
                x, y,
                c=OVERLAY_POINT_COLOR,
                s=OVERLAY_POINT_SIZE,
                zorder=5,
                edgecolors=OVERLAY_POINT_EDGE_COLOR,
                linewidths=OVERLAY_POINT_EDGE_WIDTH
            )

            # Add label if name is provided
            if 'name' in point:
                ax.annotate(
                    point['name'],
                    (x, y),
                    xytext=(10, 10),
                    textcoords='offset points',
                    fontsize=LABEL_FONTSIZE,
                    fontweight='bold',
                    zorder=6,
                    bbox={
                        'boxstyle': f'round,pad={LABEL_PAD}',
                        'facecolor': LABEL_BG_COLOR,
                        'alpha': LABEL_BG_ALPHA,
                        'edgecolor': LABEL_EDGE_COLOR,
                    },
                )
    except Exception as e:
        logger.warning("Could not add overlay points: %s", e)


def _add_stats_box(
    ax,
    gdf: gpd.GeoDataFrame,
    column: str,
    stats_dict: dict | None
) -> None:
    """
    Add a statistics box to the map.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes to add the stats box to.
    gdf : gpd.GeoDataFrame
        The GeoDataFrame with data.
    column : str
        The column being visualized.
    stats_dict : dict, optional
        Custom statistics to display. If None, calculates basic stats.
    """
    try:
        if stats_dict is not None:
            stats = stats_dict
        else:
            # Calculate basic statistics
            data = gdf[column]
            if data.dtype in ['int64', 'float64']:
                stats = {
                    'Count': len(data),
                    'Min': f'{data.min():.1f}',
                    'Max': f'{data.max():.1f}',
                    'Mean': f'{data.mean():.1f}',
                    'Median': f'{data.median():.1f}',
                }
            else:
                value_counts = data.value_counts()
                stats = {
                    'Count': len(data),
                    'Unique': len(value_counts),
                    'Top': str(value_counts.index[0]) if len(value_counts) > 0 else 'N/A',
                }

        # Format stats text
        stats_text = '\n'.join(f'{k}: {v}' for k, v in stats.items())

        # Add text box
        props = dict(
            boxstyle='round,pad=0.5',
            facecolor='white',
            alpha=STATS_BOX_ALPHA,
            edgecolor=STATS_BOX_BORDER_COLOR,
        )
        ax.text(
            0.02, 0.98,
            stats_text,
            transform=ax.transAxes,
            fontsize=STATS_BOX_FONTSIZE,
            verticalalignment='top',
            bbox=props,
            family=STATS_BOX_FONT_FAMILY,
            zorder=10
        )
    except Exception as e:
        logger.warning("Could not add stats box: %s", e)


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
            "lw": NORTH_ARROW_LINE_WIDTH,
            "color": MAP_ACCENT_COLOR,
        },
        ha='center',
        va='bottom',
        fontsize=NORTH_ARROW_FONTSIZE,
        fontweight='bold',
        color=MAP_ACCENT_COLOR,
    )


def add_scale_bar(ax, gdf: gpd.GeoDataFrame, use_web_mercator: bool = False):
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
    use_web_mercator : bool, optional
        Whether the map is in Web Mercator projection. Affects scale
        calculation, by default False.

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

        # For Web Mercator, the scale is in meters
        if use_web_mercator:
            # Round to nice number in meters
            if scale_length > METERS_PER_KM:
                # Round to nearest km
                scale_length_km = round(scale_length / METERS_PER_KM)
                scale_length = scale_length_km * METERS_PER_KM
                label = f"{scale_length_km} km"
            else:
                # Round to nice meter value
                nice_values = [100, 200, 500, 1000]
                scale_length = min(nice_values, key=lambda x: abs(x - scale_length))
                label = f"{int(scale_length)} m"
        else:
            # Round to nice number (degrees or projected units)
            if scale_length > 1:
                scale_length = round(scale_length)
            elif scale_length > SCALE_BAR_ROUND_THRESHOLD:
                scale_length = round(scale_length, 1)
            else:
                scale_length = round(scale_length, 2)

            # Determine units and label
            if gdf.crs and gdf.crs.to_epsg() == CRS_WGS84_EPSG:
                # Degrees - convert to km
                # Rough approximation at middle latitude
                mid_lat = (bounds[1] + bounds[3]) / 2
                km_per_degree = 111 * np.cos(np.radians(mid_lat))
                distance_km = scale_length * km_per_degree

                if distance_km >= 1:
                    label = f"{distance_km:.0f} km"
                else:
                    label = f"{distance_km * METERS_PER_KM:.0f} m"
            elif scale_length >= METERS_PER_KM:
                label = f"{scale_length / METERS_PER_KM:.0f} km"
            else:
                label = f"{scale_length:.0f} m"

        # Position in lower left
        x_start = bounds[0] + width * 0.05
        y = bounds[1] + (bounds[3] - bounds[1]) * 0.05
        x_end = x_start + scale_length

        # Draw scale bar
        bar_color = MAP_ACCENT_COLOR
        lw = SCALE_BAR_LINE_WIDTH
        ax.plot([x_start, x_end], [y, y], color=bar_color, linewidth=lw)
        if use_web_mercator:
            tick_height = (bounds[3] - bounds[1]) * 0.01
        else:
            tick_height = scale_length * 0.01
        ax.plot(
            [x_start, x_start], [y - tick_height, y + tick_height],
            color=bar_color, linewidth=lw,
        )
        ax.plot(
            [x_end, x_end], [y - tick_height, y + tick_height],
            color=bar_color, linewidth=lw,
        )

        # Add label
        ax.text(
            (x_start + x_end) / 2,
            y - tick_height * 2,
            label,
            ha='center',
            va='top',
            fontsize=10,
            color=bar_color,
        )

    except (ValueError, TypeError, AttributeError) as e:
        logger.debug("Could not add scale bar: %s", e)


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
    plt.savefig(buf, format='png', dpi=MAP_DPI, bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return buf.read()
