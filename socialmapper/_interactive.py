"""Interactive map generation using Folium/Leaflet.

This module provides interactive HTML map generation as an alternative
to static matplotlib maps. Requires the 'interactive' optional
dependency: ``pip install socialmapper[interactive]``
"""

from __future__ import annotations

import logging
from html import escape
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import geopandas as gpd

from .constants import (
    OVERLAY_BOUNDARY_COLOR,
    OVERLAY_BOUNDARY_STYLE,
    OVERLAY_BOUNDARY_WIDTH,
)

logger = logging.getLogger(__name__)

# Mapping from our basemap names to folium tile layer names
_BASEMAP_TO_FOLIUM_TILES: dict[str, str] = {
    "CartoDB.Voyager": "cartodbvoyager",
    "CartoDB.Positron": "cartodbpositron",
    "CartoDB.DarkMatter": "CartoDB dark_matter",
    "OpenStreetMap.Mapnik": "OpenStreetMap",
}


def _ensure_folium():
    """Lazy-import folium with a helpful error message.

    Returns
    -------
    module
        The folium module.

    Raises
    ------
    ImportError
        If folium is not installed, with installation instructions.
    """
    try:
        import folium

        return folium
    except ImportError:
        raise ImportError(
            "The 'folium' package is required for interactive HTML maps. "
            "Install it with: pip install socialmapper[interactive]"
        ) from None


def generate_interactive_map(
    gdf: gpd.GeoDataFrame,
    column: str,
    title: str | None = None,
    save_path: str | None = None,
    basemap: str | None = "CartoDB.Voyager",
    overlay_boundary: gpd.GeoDataFrame | None = None,
    overlay_points: list[dict] | None = None,
    show_stats: bool = False,
    stats_dict: dict | None = None,
) -> str:
    """Generate an interactive Leaflet map via folium.

    Parameters
    ----------
    gdf : gpd.GeoDataFrame
        GeoDataFrame containing geometry and data to visualize.
    column : str
        Name of the column to visualize.
    title : str, optional
        Title to display on the map.
    save_path : str, optional
        File path to save the HTML. If None, returns HTML string.
    basemap : str, optional
        Basemap provider name. Default is 'CartoDB.Voyager'.
    overlay_boundary : gpd.GeoDataFrame, optional
        Boundary geometry to overlay (e.g., isochrone).
    overlay_points : list of dict, optional
        Point markers with 'lat', 'lon', and optional 'name'.
    show_stats : bool, optional
        Whether to display a statistics panel.
    stats_dict : dict, optional
        Custom statistics to display.

    Returns
    -------
    str
        HTML string of the interactive map.
    """
    folium = _ensure_folium()
    import branca.colormap as cm
    import numpy as np

    # Ensure WGS84 for Leaflet
    if gdf.crs is None:
        gdf_wgs = gdf.set_crs(epsg=4326)
    elif gdf.crs.to_epsg() != 4326:
        gdf_wgs = gdf.to_crs(epsg=4326)
    else:
        gdf_wgs = gdf

    # Determine map center and bounds
    bounds = gdf_wgs.total_bounds  # minx, miny, maxx, maxy
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    # Resolve tiles
    tiles = _BASEMAP_TO_FOLIUM_TILES.get(basemap, "cartodbvoyager") if basemap else "cartodbpositron"

    # Create map
    interactive_map = folium.Map(location=[center_lat, center_lon], tiles=tiles)

    # Fit bounds to data extent
    interactive_map.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    # Add choropleth layer
    _add_choropleth_layer(interactive_map, gdf_wgs, column, folium, cm, np)

    # Add overlay boundary
    if overlay_boundary is not None:
        _add_boundary_layer(interactive_map, overlay_boundary, folium)

    # Add overlay points
    if overlay_points:
        _add_marker_layer(interactive_map, overlay_points, folium)

    # Add title
    if title:
        _add_title_element(interactive_map, title)

    # Add stats panel
    if show_stats:
        _add_stats_panel(interactive_map, gdf_wgs, column, stats_dict)

    # Add layer control
    folium.LayerControl().add_to(interactive_map)

    # Generate HTML
    html_content = interactive_map.get_root().render()

    # Save if path provided
    if save_path:
        with open(save_path, "w", encoding="utf-8") as fh:
            fh.write(html_content)
        logger.info("Interactive map saved to %s", save_path)

    return html_content


def _add_choropleth_layer(
    interactive_map,
    gdf: gpd.GeoDataFrame,
    column: str,
    folium,
    cm,
    np,
) -> None:
    """Add a choropleth GeoJson layer with tooltip and colormap.

    Parameters
    ----------
    interactive_map : folium.Map
        The map to add the layer to.
    gdf : gpd.GeoDataFrame
        Data with geometry and column to visualize.
    column : str
        Column name to color by.
    folium : module
        The folium module.
    cm : module
        branca.colormap module.
    np : module
        numpy module.
    """
    data = gdf[column]
    is_numeric = data.dtype.kind in ("i", "f")

    if is_numeric:
        valid_data = data.dropna()
        vmin = float(valid_data.min())
        vmax = float(valid_data.max())

        # Create a linear colormap using YlGnBu colors
        colormap = cm.LinearColormap(
            colors=["#ffffcc", "#a1dab4", "#41b6c4", "#2c7fb8", "#253494"],
            vmin=vmin,
            vmax=vmax,
            caption=column.replace("_", " ").title(),
        )
        colormap.add_to(interactive_map)

        def style_function(feature):
            value = feature["properties"].get(column)
            if value is None or (isinstance(value, float) and np.isnan(value)):
                fill_color = "lightgray"
            else:
                fill_color = colormap(value)
            return {
                "fillColor": fill_color,
                "color": "#cccccc",
                "weight": 0.4,
                "fillOpacity": 0.85,
            }
    else:
        # Categorical - assign colors from a palette
        unique_values = list(data.unique())
        palette = [
            "#66c2a5", "#fc8d62", "#8da0cb", "#e78ac3",
            "#a6d854", "#ffd92f", "#e5c494", "#b3b3b3",
        ]
        color_map = {
            val: palette[i % len(palette)]
            for i, val in enumerate(unique_values)
        }

        def style_function(feature):
            value = feature["properties"].get(column)
            return {
                "fillColor": color_map.get(value, "lightgray"),
                "color": "#cccccc",
                "weight": 0.4,
                "fillOpacity": 0.85,
            }

    # Auto-detect tooltip fields (exclude geometry)
    tooltip_fields = [
        col for col in gdf.columns
        if col != "geometry" and not col.startswith("_")
    ]
    tooltip_aliases = [col.replace("_", " ").title() for col in tooltip_fields]

    def highlight_function(feature):
        return {
            "weight": 2,
            "color": "#333333",
            "fillOpacity": 0.95,
        }

    geojson_layer = folium.GeoJson(
        gdf.__geo_interface__,
        name="Choropleth",
        style_function=style_function,
        highlight_function=highlight_function,
        tooltip=folium.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=tooltip_aliases,
            localize=True,
            sticky=False,
            style="""
                background-color: #fafafa;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 6px 10px;
                font-family: sans-serif;
                font-size: 13px;
            """,
        ),
    )
    geojson_layer.add_to(interactive_map)


def _add_boundary_layer(
    interactive_map,
    boundary_gdf: gpd.GeoDataFrame,
    folium,
) -> None:
    """Add a dashed boundary overlay layer.

    Parameters
    ----------
    interactive_map : folium.Map
        The map to add the layer to.
    boundary_gdf : gpd.GeoDataFrame
        GeoDataFrame with boundary geometry.
    folium : module
        The folium module.
    """
    if boundary_gdf.crs is None:
        boundary_wgs = boundary_gdf.set_crs(epsg=4326)
    elif boundary_gdf.crs.to_epsg() != 4326:
        boundary_wgs = boundary_gdf.to_crs(epsg=4326)
    else:
        boundary_wgs = boundary_gdf

    # Convert dash style: matplotlib "--" -> Leaflet dash array
    dash_array = "8 6" if OVERLAY_BOUNDARY_STYLE == "--" else None

    folium.GeoJson(
        boundary_wgs.__geo_interface__,
        name="Boundary",
        style_function=lambda _: {
            "fillColor": "transparent",
            "fillOpacity": 0,
            "color": OVERLAY_BOUNDARY_COLOR,
            "weight": OVERLAY_BOUNDARY_WIDTH,
            "dashArray": dash_array,
        },
    ).add_to(interactive_map)


def _add_marker_layer(
    interactive_map,
    points: list[dict],
    folium,
) -> None:
    """Add point markers with popups to the map.

    Parameters
    ----------
    interactive_map : folium.Map
        The map to add markers to.
    points : list of dict
        Point dicts with 'lat', 'lon', and optional 'name'.
    folium : module
        The folium module.
    """
    feature_group = folium.FeatureGroup(name="Points")

    for point in points:
        if "lat" not in point or "lon" not in point:
            continue

        label = point.get("name", "")
        popup_text = label or f"{point['lat']:.4f}, {point['lon']:.4f}"

        folium.Marker(
            location=[point["lat"], point["lon"]],
            popup=folium.Popup(popup_text, max_width=200),
            tooltip=label or None,
            icon=folium.Icon(color="pink", icon="info-sign"),
        ).add_to(feature_group)

    feature_group.add_to(interactive_map)


def _add_title_element(interactive_map, title: str) -> None:
    """Add a floating title element centered at the top of the map.

    Parameters
    ----------
    interactive_map : folium.Map
        The map to add the title to.
    title : str
        Title text to display.
    """
    from branca.element import Element

    title_html = f"""
    <div style="
        position: fixed;
        top: 12px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 1000;
        background-color: rgba(250, 250, 250, 0.92);
        padding: 8px 20px;
        border-radius: 6px;
        border: 1px solid #d0d0d0;
        font-family: sans-serif;
        font-size: 18px;
        font-weight: bold;
        color: #1a1a2e;
        box-shadow: 0 1px 4px rgba(0,0,0,0.1);
        pointer-events: none;
    ">{escape(title)}</div>
    """

    interactive_map.get_root().html.add_child(Element(title_html))


def _add_stats_panel(
    interactive_map,
    gdf: gpd.GeoDataFrame,
    column: str,
    stats_dict: dict[str, Any] | None,
) -> None:
    """Add a floating statistics panel to the bottom-left of the map.

    Parameters
    ----------
    interactive_map : folium.Map
        The map to add the panel to.
    gdf : gpd.GeoDataFrame
        Data for computing statistics.
    column : str
        Column being visualized.
    stats_dict : dict, optional
        Custom statistics. If None, computes basic stats.
    """
    from branca.element import Element

    if stats_dict is not None:
        stats = stats_dict
    else:
        data = gdf[column]
        if data.dtype.kind in ("i", "f"):
            stats = {
                "Count": f"{len(data):,}",
                "Min": f"{data.min():,.1f}",
                "Max": f"{data.max():,.1f}",
                "Mean": f"{data.mean():,.1f}",
                "Median": f"{data.median():,.1f}",
            }
        else:
            value_counts = data.value_counts()
            stats = {
                "Count": f"{len(data):,}",
                "Unique": f"{len(value_counts):,}",
                "Top": str(value_counts.index[0]) if len(value_counts) > 0 else "N/A",
            }

    # Build table rows
    rows = "".join(
        f"<tr><td style='padding:2px 8px;font-weight:600;'>{escape(str(k))}</td>"
        f"<td style='padding:2px 8px;'>{escape(str(v))}</td></tr>"
        for k, v in stats.items()
    )

    stats_html = f"""
    <div style="
        position: fixed;
        bottom: 30px;
        left: 12px;
        z-index: 1000;
        background-color: rgba(255, 255, 255, 0.95);
        padding: 10px 14px;
        border-radius: 6px;
        border: 1px solid #d0d0d0;
        font-family: sans-serif;
        font-size: 13px;
        color: #333;
        box-shadow: 0 1px 4px rgba(0,0,0,0.1);
    ">
        <table>{rows}</table>
    </div>
    """

    interactive_map.get_root().html.add_child(Element(stats_html))
