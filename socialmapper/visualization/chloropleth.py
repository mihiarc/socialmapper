"""Choropleth map creation for socialmapper outputs."""

import contextlib
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import geopandas as gpd
import mapclassify
import matplotlib.pyplot as plt

try:
    import contextily as ctx

    CONTEXTILY_AVAILABLE = True
except ImportError:
    CONTEXTILY_AVAILABLE = False

from .config import (
    DEFAULT_FIGSIZE,
    DEFAULT_DPI,
    DEFAULT_CMAP,
    DEFAULT_CLASSIFICATION,
    DEFAULT_N_CLASSES,
    DEFAULT_EDGE_COLOR,
    DEFAULT_EDGE_WIDTH,
    DEFAULT_ALPHA,
    DEFAULT_MISSING_COLOR,
    DEFAULT_LEGEND_LOC,
    DEFAULT_LEGEND_FONTSIZE,
    DEFAULT_LEGEND_FMT,
)
from .utils import add_north_arrow, add_scale_bar


class MapType(str, Enum):
    """Types of choropleth maps supported."""

    DEMOGRAPHIC = "demographic"
    DISTANCE = "distance"
    ACCESSIBILITY = "accessibility"
    COMPOSITE = "composite"


class ChoroplethMap:
    """Create professional static choropleth maps from socialmapper data.

    Simplified interface using direct parameters instead of config objects.
    """

    def __init__(
        self,
        figsize: tuple[float, float] = DEFAULT_FIGSIZE,
        dpi: int = DEFAULT_DPI,
        cmap: str = DEFAULT_CMAP,
        classification: str = DEFAULT_CLASSIFICATION,
        n_classes: int = DEFAULT_N_CLASSES,
        **kwargs
    ):
        """Initialize choropleth map creator with direct parameters.

        Parameters
        ----------
        figsize : tuple, optional
            Figure size (width, height)
        dpi : int, optional
            Resolution for saved images
        cmap : str, optional
            Matplotlib colormap name (e.g., 'viridis', 'YlOrRd', 'Blues')
        classification : str, optional
            Mapclassify scheme (e.g., 'quantiles', 'fisher_jenks')
        n_classes : int, optional
            Number of classification bins
        **kwargs
            Additional parameters passed to plotting functions
        """
        self.figsize = figsize
        self.dpi = dpi
        self.cmap = cmap
        self.classification = classification
        self.n_classes = n_classes
        self.kwargs = kwargs

        self._fig = None
        self._ax = None
        self._gdf = None
        self._classifier = None

    def create_map(
        self,
        gdf: gpd.GeoDataFrame,
        column: str,
        map_type: MapType = MapType.DEMOGRAPHIC,
        poi_gdf: gpd.GeoDataFrame | None = None,
        isochrone_gdf: gpd.GeoDataFrame | None = None,
        title: str | None = None,
        legend: bool = True,
        add_basemap: bool = True,
        **kwargs,
    ) -> tuple[plt.Figure, plt.Axes]:
        """Create a choropleth map from a GeoDataFrame.

        Parameters
        ----------
        gdf : GeoDataFrame
            GeoDataFrame with data to map
        column : str
            Column name to visualize
        map_type : MapType, optional
            Type of map to create
        poi_gdf : GeoDataFrame, optional
            POI locations to overlay
        isochrone_gdf : GeoDataFrame, optional
            Isochrone boundaries to overlay
        title : str, optional
            Map title
        legend : bool, optional
            Whether to show legend
        add_basemap : bool, optional
            Whether to add contextily basemap
        **kwargs
            Additional parameters override instance defaults

        Returns
        -------
        fig : Figure
            Matplotlib figure object
        ax : Axes
            Matplotlib axes object
        """
        # Merge kwargs with instance defaults
        params = {**self.kwargs, **kwargs}

        # Store data
        self._gdf = gdf.copy()

        # Simplify geometries if requested
        if params.get('simplify_tolerance'):
            self._gdf["geometry"] = self._gdf.geometry.simplify(
                tolerance=params['simplify_tolerance']
            )

        # Create figure and axes
        figsize = params.get('figsize', self.figsize)
        facecolor = params.get('facecolor', 'white')
        edgecolor = params.get('edgecolor', 'none')

        self._fig, self._ax = plt.subplots(
            1, 1, figsize=figsize, facecolor=facecolor, edgecolor=edgecolor
        )

        # Remove axes for cleaner look
        self._ax.set_axis_off()

        # Create the base choropleth
        self._create_choropleth(column, legend=legend, **params)

        # Add basemap after choropleth
        if add_basemap and CONTEXTILY_AVAILABLE:
            self._add_basemap(**params)

        # Add overlays based on map type
        if map_type == MapType.ACCESSIBILITY and isochrone_gdf is not None:
            self._add_isochrone_overlay(isochrone_gdf)

        if poi_gdf is not None:
            self._add_poi_overlay(poi_gdf)

        # Add map elements
        if title:
            self._add_title(title, **params)
        self._add_north_arrow(**params)
        self._add_scale_bar(**params)
        self._add_attribution(**params)

        # Tight layout
        plt.tight_layout()

        return self._fig, self._ax

    def _create_choropleth(self, column: str, legend: bool = True, **kwargs) -> None:
        """Create the base choropleth layer."""
        if column not in self._gdf.columns:
            raise ValueError(f"Column '{column}' not found in GeoDataFrame")

        # Handle missing data and Census API error codes
        self._gdf = self._gdf.copy()
        census_error_codes = [-666666666, -999999999, -888888888, -555555555]
        error_mask = self._gdf[column].isin(census_error_codes)
        missing_mask = self._gdf[column].isna() | error_mask
        self._gdf.loc[error_mask, column] = None

        # Create classifier for non-missing data
        valid_data = self._gdf[~missing_mask][column]

        if len(valid_data) > 0:
            classification = kwargs.get('classification', self.classification)
            n_classes = kwargs.get('n_classes', self.n_classes)

            # Handle defined_interval scheme
            if classification == "defined_interval":
                classification = "quantiles"  # Fallback

            try:
                self._classifier = mapclassify.classify(
                    valid_data, scheme=classification, k=n_classes
                )
            except Exception:
                # Fallback to quantiles
                self._classifier = mapclassify.classify(
                    valid_data, scheme="quantiles", k=n_classes
                )

        # Get styling parameters
        cmap = kwargs.get('cmap', self.cmap)
        edge_color = kwargs.get('edge_color', DEFAULT_EDGE_COLOR)
        edge_width = kwargs.get('edge_width', DEFAULT_EDGE_WIDTH)
        alpha = kwargs.get('alpha', DEFAULT_ALPHA)
        missing_color = kwargs.get('missing_color', DEFAULT_MISSING_COLOR)

        # Plot choropleth
        plot_kwargs = {
            'column': column,
            'ax': self._ax,
            'scheme': kwargs.get('classification', self.classification),
            'k': kwargs.get('n_classes', self.n_classes),
            'cmap': cmap,
            'edgecolor': edge_color,
            'linewidth': edge_width,
            'alpha': alpha,
            'missing_kwds': {'color': missing_color, 'label': 'No data'},
            'zorder': 3,
        }

        if legend and self._classifier:
            legend_kwds = {
                'loc': kwargs.get('legend_loc', DEFAULT_LEGEND_LOC),
                'title': kwargs.get('legend_title') or self._format_column_name(column),
                'fontsize': kwargs.get('legend_fontsize', DEFAULT_LEGEND_FONTSIZE),
                'fmt': kwargs.get('legend_fmt', DEFAULT_LEGEND_FMT),
            }
            plot_kwargs['legend'] = True
            plot_kwargs['legend_kwds'] = legend_kwds
        else:
            plot_kwargs['legend'] = False

        self._gdf.plot(**plot_kwargs)

    def _format_column_name(self, column: str) -> str:
        """Format column name for display."""
        if column.startswith("B") and "_" in column:
            return "Census Variable"

        formatted = column.replace("_", " ").title()
        replacements = {
            "Km": "km", "Miles": "miles", "Poi": "POI",
            "Id": "ID", "Fips": "FIPS"
        }

        for old, new in replacements.items():
            formatted = formatted.replace(old, new)

        return formatted

    def _add_isochrone_overlay(self, isochrone_gdf: gpd.GeoDataFrame) -> None:
        """Add isochrone boundaries as overlay."""
        isochrone_gdf.boundary.plot(
            ax=self._ax,
            color="red",
            linewidth=2,
            alpha=0.7,
            label="Travel time boundary",
            zorder=4,
        )

    def _add_poi_overlay(self, poi_gdf: gpd.GeoDataFrame) -> None:
        """Add POI locations as overlay."""
        if "tags" in poi_gdf.columns and "amenity" in poi_gdf.columns:
            for amenity_type, group in poi_gdf.groupby("amenity"):
                group.plot(
                    ax=self._ax,
                    color="teal",
                    markersize=80,
                    marker="o",
                    edgecolor="gold",
                    linewidth=2,
                    label=amenity_type.title(),
                    zorder=5,
                )
        else:
            poi_gdf.plot(
                ax=self._ax,
                color="teal",
                markersize=80,
                marker="o",
                edgecolor="gold",
                linewidth=2,
                label="Points of Interest",
                zorder=5,
            )

        # Add legend for overlays if any exist
        if len(self._ax.get_legend_handles_labels()[0]) > 0:
            self._ax.legend(
                loc="upper left", frameon=True, fancybox=True,
                shadow=True, fontsize=10
            )

    def _add_title(self, title: str, **kwargs) -> None:
        """Add title to the map."""
        self._ax.set_title(
            title,
            fontsize=kwargs.get('title_fontsize', 16),
            fontweight=kwargs.get('title_fontweight', 'bold'),
            pad=kwargs.get('title_pad', 20),
        )

    def _add_north_arrow(self, **kwargs) -> None:
        """Add north arrow to the map."""
        if kwargs.get('north_arrow', True):
            with contextlib.suppress(Exception):
                add_north_arrow(
                    self._ax,
                    location=kwargs.get('north_arrow_location', 'upper right'),
                    scale=kwargs.get('north_arrow_scale', 0.5),
                )

    def _add_scale_bar(self, **kwargs) -> None:
        """Add scale bar to the map."""
        if kwargs.get('scale_bar', True):
            with contextlib.suppress(Exception):
                add_scale_bar(
                    self._ax,
                    location=kwargs.get('scale_bar_location', 'lower right'),
                    length_fraction=kwargs.get('scale_bar_length_fraction', 0.25),
                    box_alpha=kwargs.get('scale_bar_box_alpha', 0.8),
                    font_size=kwargs.get('scale_bar_font_size', 10),
                )

    def _add_basemap(self, **kwargs) -> None:
        """Add contextily basemap to the map."""
        if not CONTEXTILY_AVAILABLE:
            return

        try:
            # Ensure data is in Web Mercator for contextily
            if self._gdf.crs != "EPSG:3857":
                gdf_mercator = self._gdf.to_crs("EPSG:3857")
            else:
                gdf_mercator = self._gdf

            # Prepare zoom parameter
            zoom_param = {}
            basemap_zoom = kwargs.get('basemap_zoom', 'auto')
            if basemap_zoom != "auto":
                if isinstance(basemap_zoom, int):
                    zoom_param["zoom"] = min(max(basemap_zoom, 0), 19)

            # Add basemap
            ctx.add_basemap(
                self._ax,
                crs=gdf_mercator.crs,
                source=kwargs.get('basemap_source', 'OpenStreetMap.Mapnik'),
                alpha=kwargs.get('basemap_alpha', 0.6),
                attribution=kwargs.get('basemap_attribution'),
                zorder=0,
                **zoom_param,
            )

        except Exception as e:
            print(f"⚠️ Failed to add basemap: {e}")

    def _add_attribution(self, **kwargs) -> None:
        """Add attribution text to the map."""
        attribution = kwargs.get(
            'attribution',
            "Data: US Census Bureau, OpenStreetMap | Analysis: SocialMapper"
        )

        if attribution:
            fontsize = kwargs.get('attribution_fontsize', 9)
            color = kwargs.get('attribution_color', 'gray')

            # Left side attribution
            plt.figtext(
                0.02, 0.02, attribution,
                fontsize=fontsize, style="italic", color=color, ha="left"
            )

            # Right side date
            date_text = f"Created: {datetime.now().strftime('%Y-%m-%d')}"
            plt.figtext(
                0.98, 0.02, date_text,
                fontsize=fontsize, style="italic", color=color, ha="right"
            )

    def save(
        self,
        filepath: str | Path,
        format: str | None = None,
        dpi: int | None = None,
        **kwargs
    ) -> None:
        """Save the map to file.

        Parameters
        ----------
        filepath : str or Path
            Path to save the map
        format : str, optional
            Output format (png, pdf, svg). If None, inferred from filepath
        dpi : int, optional
            DPI for raster formats. If None, uses instance default
        **kwargs
            Additional savefig parameters
        """
        if self._fig is None:
            raise ValueError("No map has been created yet. Call create_map first.")

        filepath = Path(filepath)

        # Infer format from extension if not provided
        if format is None:
            format = filepath.suffix.lstrip(".") or "png"

        # Use instance DPI if not provided
        if dpi is None:
            dpi = self.dpi

        # Save figure
        save_params = {
            'format': format,
            'dpi': dpi,
            'bbox_inches': kwargs.get('bbox_inches', 'tight'),
            'pad_inches': kwargs.get('pad_inches', 0.1),
            'facecolor': kwargs.get('facecolor', 'white'),
            'edgecolor': kwargs.get('edgecolor', 'none'),
        }

        self._fig.savefig(filepath, **save_params)

    @classmethod
    def create_demographic_map(
        cls,
        gdf: gpd.GeoDataFrame,
        demographic_column: str,
        title: str | None = None,
        **kwargs
    ) -> tuple[plt.Figure, plt.Axes]:
        """
        Create a demographic choropleth map with sensible defaults.

        Parameters
        ----------
        gdf : GeoDataFrame
            GeoDataFrame with census data
        demographic_column : str
            Column to visualize
        title : str, optional
            Map title
        **kwargs
            Additional parameters

        Returns
        -------
        fig : Figure
            Matplotlib figure object
        ax : Axes
            Matplotlib axes object
        """
        mapper = cls(cmap=kwargs.pop('cmap', 'Blues'), **kwargs)
        title = title or f"Distribution of {demographic_column}"
        return mapper.create_map(
            gdf, demographic_column,
            map_type=MapType.DEMOGRAPHIC,
            title=title,
            **kwargs
        )

    @classmethod
    def create_distance_map(
        cls,
        gdf: gpd.GeoDataFrame,
        distance_column: str = "travel_distance_km",
        poi_gdf: gpd.GeoDataFrame | None = None,
        title: str | None = None,
        **kwargs,
    ) -> tuple[plt.Figure, plt.Axes]:
        """
        Create a distance-based choropleth map with sensible defaults.

        Parameters
        ----------
        gdf : GeoDataFrame
            GeoDataFrame with distance data
        distance_column : str, optional
            Distance column to visualize
        poi_gdf : GeoDataFrame, optional
            POI locations
        title : str, optional
            Map title
        **kwargs
            Additional parameters

        Returns
        -------
        fig : Figure
            Matplotlib figure object
        ax : Axes
            Matplotlib axes object
        """
        mapper = cls(
            cmap=kwargs.pop('cmap', 'YlOrRd'),
            classification=kwargs.pop('classification', 'fisher_jenks'),
            **kwargs
        )

        title = title or "Travel Distance Analysis"
        legend_kwds = kwargs.pop('legend_kwds', {})
        legend_kwds.setdefault('title', 'Distance (km)')
        legend_kwds.setdefault('fmt', '{:.1f}')

        return mapper.create_map(
            gdf,
            distance_column,
            map_type=MapType.DISTANCE,
            poi_gdf=poi_gdf,
            title=title,
            legend_title=legend_kwds.get('title'),
            legend_fmt=legend_kwds.get('fmt'),
            **kwargs,
        )

    @classmethod
    def create_accessibility_map(
        cls,
        gdf: gpd.GeoDataFrame,
        column: str,
        poi_gdf: gpd.GeoDataFrame | None = None,
        isochrone_gdf: gpd.GeoDataFrame | None = None,
        title: str | None = None,
        **kwargs,
    ) -> tuple[plt.Figure, plt.Axes]:
        """
        Create an accessibility-focused map with sensible defaults.

        Parameters
        ----------
        gdf : GeoDataFrame
            GeoDataFrame with data
        column : str
            Column to visualize
        poi_gdf : GeoDataFrame, optional
            POI locations
        isochrone_gdf : GeoDataFrame, optional
            Isochrone boundaries
        title : str, optional
            Map title
        **kwargs
            Additional parameters

        Returns
        -------
        fig : Figure
            Matplotlib figure object
        ax : Axes
            Matplotlib axes object
        """
        mapper = cls(
            cmap=kwargs.pop('cmap', 'viridis'),
            **kwargs
        )

        title = title or "Accessibility Analysis"
        return mapper.create_map(
            gdf,
            column,
            map_type=MapType.ACCESSIBILITY,
            poi_gdf=poi_gdf,
            isochrone_gdf=isochrone_gdf,
            title=title,
            alpha=kwargs.get('alpha', 0.8),
            **kwargs,
        )
