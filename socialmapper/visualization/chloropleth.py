"""Chloropleth map creation for socialmapper outputs."""

from enum import Enum
from typing import Optional, Union, Dict, Any, Tuple, List
from pathlib import Path
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colorbar import ColorbarBase
from matplotlib.colors import Normalize
from mpl_toolkits.axes_grid1 import make_axes_locatable
import geopandas as gpd
import pandas as pd
import numpy as np
import mapclassify

from .config import MapConfig, ColorScheme, ClassificationScheme, LegendConfig
from .utils import add_north_arrow, add_scale_bar, format_number


class MapType(str, Enum):
    """Types of choropleth maps supported."""
    
    DEMOGRAPHIC = "demographic"
    DISTANCE = "distance"
    ACCESSIBILITY = "accessibility"
    COMPOSITE = "composite"


class ChoroplethMap:
    """Create professional static choropleth maps from socialmapper data."""
    
    def __init__(self, config: Optional[MapConfig] = None):
        """Initialize choropleth map creator.
        
        Args:
            config: Map configuration object. If None, uses defaults.
        """
        self.config = config or MapConfig()
        self._fig = None
        self._ax = None
        self._gdf = None
        self._classifier = None
        
    def create_map(
        self,
        gdf: gpd.GeoDataFrame,
        column: str,
        map_type: MapType = MapType.DEMOGRAPHIC,
        poi_gdf: Optional[gpd.GeoDataFrame] = None,
        isochrone_gdf: Optional[gpd.GeoDataFrame] = None,
        config_overrides: Optional[Dict[str, Any]] = None,
    ) -> Tuple[plt.Figure, plt.Axes]:
        """Create a choropleth map from a GeoDataFrame.
        
        Args:
            gdf: GeoDataFrame with data to map
            column: Column name to visualize
            map_type: Type of map to create
            poi_gdf: Optional POI locations to overlay
            isochrone_gdf: Optional isochrone boundaries to overlay
            config_overrides: Optional config overrides for this map
            
        Returns:
            Tuple of (Figure, Axes) objects
        """
        # Apply config overrides if provided
        if config_overrides:
            config_dict = self.config.model_dump()
            config_dict.update(config_overrides)
            self.config = MapConfig(**config_dict)
        
        # Store data
        self._gdf = gdf.copy()
        
        # Simplify geometries if requested
        if self.config.simplify_tolerance:
            self._gdf["geometry"] = self._gdf.geometry.simplify(
                tolerance=self.config.simplify_tolerance
            )
        
        # Create figure and axes
        self._fig, self._ax = plt.subplots(
            1, 1, 
            figsize=self.config.figsize,
            facecolor=self.config.facecolor,
            edgecolor=self.config.edgecolor
        )
        
        # Remove axes for cleaner look
        self._ax.set_axis_off()
        
        # Create the base choropleth
        self._create_choropleth(column)
        
        # Add overlays based on map type
        if map_type == MapType.ACCESSIBILITY and isochrone_gdf is not None:
            self._add_isochrone_overlay(isochrone_gdf)
        
        if poi_gdf is not None:
            self._add_poi_overlay(poi_gdf)
        
        # Add map elements
        self._add_title()
        self._add_north_arrow()
        self._add_scale_bar()
        self._add_attribution()
        
        # Tight layout
        plt.tight_layout()
        
        return self._fig, self._ax
    
    def _create_choropleth(self, column: str) -> None:
        """Create the base choropleth layer."""
        # Check if column exists
        if column not in self._gdf.columns:
            raise ValueError(f"Column '{column}' not found in GeoDataFrame")
        
        # Handle missing data
        self._gdf = self._gdf.copy()
        missing_mask = self._gdf[column].isna()
        
        # Create classifier for non-missing data
        valid_data = self._gdf[~missing_mask][column]
        
        if len(valid_data) > 0:
            # Create classification
            if self.config.classification_scheme == ClassificationScheme.DEFINED_INTERVAL:
                # For defined interval, we need to specify intervals
                # Using quantiles as fallback
                scheme = "quantiles"
            else:
                scheme = self.config.classification_scheme.value
            
            try:
                self._classifier = mapclassify.classify(
                    valid_data,
                    scheme=scheme,
                    k=self.config.n_classes
                )
            except Exception as e:
                # Fallback to quantiles if classification fails
                self._classifier = mapclassify.classify(
                    valid_data,
                    scheme="quantiles",
                    k=self.config.n_classes
                )
        
        # Plot choropleth
        if self.config.legend and self._classifier:
            # Create custom legend
            legend_kwds = self._create_legend_kwds(column)
            
            self._gdf.plot(
                column=column,
                ax=self._ax,
                scheme=self.config.classification_scheme.value,
                k=self.config.n_classes,
                cmap=self.config.color_scheme.value,
                edgecolor=self.config.edge_color,
                linewidth=self.config.edge_width,
                alpha=self.config.alpha,
                missing_kwds={
                    "color": self.config.missing_color,
                    "label": "No data"
                },
                legend=True,
                legend_kwds=legend_kwds
            )
        else:
            # Plot without legend
            self._gdf.plot(
                column=column,
                ax=self._ax,
                scheme=self.config.classification_scheme.value,
                k=self.config.n_classes,
                cmap=self.config.color_scheme.value,
                edgecolor=self.config.edge_color,
                linewidth=self.config.edge_width,
                alpha=self.config.alpha,
                missing_kwds={
                    "color": self.config.missing_color
                }
            )
    
    def _create_legend_kwds(self, column: str) -> Dict[str, Any]:
        """Create legend keyword arguments."""
        legend_config = self.config.legend_config
        
        legend_kwds = {
            "loc": legend_config.loc,
            "title": legend_config.title or self._format_column_name(column),
            "fontsize": legend_config.fontsize,
            "title_fontsize": legend_config.title_fontsize,
            "frameon": legend_config.frameon,
            "fancybox": legend_config.fancybox,
            "shadow": legend_config.shadow,
            "borderpad": legend_config.borderpad,
            "columnspacing": legend_config.columnspacing,
            "fmt": legend_config.fmt,
        }
        
        if legend_config.bbox_to_anchor:
            legend_kwds["bbox_to_anchor"] = legend_config.bbox_to_anchor
        
        # Don't pass custom labels - let geopandas handle it
        if legend_config.labels:
            legend_kwds["labels"] = legend_config.labels
        
        return legend_kwds
    
    def _format_legend_labels(self, classifier) -> List[str]:
        """Format legend labels based on classifier bins."""
        labels = []
        fmt = self.config.legend_config.fmt
        
        # Get the bins from the classifier
        bins = list(classifier.bins)
        n_classes = len(bins) - 1
        
        for i in range(n_classes):
            lower = bins[i]
            upper = bins[i + 1]
            
            if i == 0:
                # First class
                label = f"≤ {fmt.format(upper)}"
            elif i == n_classes - 1:
                # Last class
                label = f"> {fmt.format(lower)}"
            else:
                # Middle classes
                label = f"{fmt.format(lower)} - {fmt.format(upper)}"
            labels.append(label)
        
        return labels
    
    def _format_column_name(self, column: str) -> str:
        """Format column name for display."""
        # Handle common census variable patterns
        if column.startswith("B") and "_" in column:
            return "Census Variable"
        
        # Handle snake_case
        formatted = column.replace("_", " ").title()
        
        # Handle specific cases
        replacements = {
            "Km": "km",
            "Miles": "miles",
            "Poi": "POI",
            "Id": "ID",
            "Fips": "FIPS"
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
            label="Travel time boundary"
        )
    
    def _add_poi_overlay(self, poi_gdf: gpd.GeoDataFrame) -> None:
        """Add POI locations as overlay."""
        # Determine POI type from data if available
        if "tags" in poi_gdf.columns:
            # Group by amenity type if available
            if "amenity" in poi_gdf.columns:
                for amenity_type, group in poi_gdf.groupby("amenity"):
                    group.plot(
                        ax=self._ax,
                        color="darkred",
                        markersize=100,
                        marker="*",
                        label=amenity_type.title(),
                        zorder=5
                    )
            else:
                poi_gdf.plot(
                    ax=self._ax,
                    color="darkred",
                    markersize=100,
                    marker="*",
                    label="Points of Interest",
                    zorder=5
                )
        else:
            poi_gdf.plot(
                ax=self._ax,
                color="darkred",
                markersize=100,
                marker="*",
                label="Points of Interest",
                zorder=5
            )
        
        # Add legend for overlays if any exist
        if len(self._ax.get_legend_handles_labels()[0]) > 0:
            self._ax.legend(
                loc="upper left",
                frameon=True,
                fancybox=True,
                shadow=True,
                fontsize=10
            )
    
    def _add_title(self) -> None:
        """Add title to the map."""
        if self.config.title:
            self._ax.set_title(
                self.config.title,
                fontsize=self.config.title_fontsize,
                fontweight=self.config.title_fontweight,
                pad=self.config.title_pad
            )
    
    def _add_north_arrow(self) -> None:
        """Add north arrow to the map."""
        if self.config.north_arrow:
            try:
                add_north_arrow(
                    self._ax,
                    location=self.config.north_arrow_location,
                    scale=self.config.north_arrow_scale
                )
            except Exception:
                # If north arrow fails, continue without it
                pass
    
    def _add_scale_bar(self) -> None:
        """Add scale bar to the map."""
        if self.config.scale_bar:
            try:
                add_scale_bar(
                    self._ax,
                    location=self.config.scale_bar_location,
                    length_fraction=self.config.scale_bar_length_fraction,
                    box_alpha=self.config.scale_bar_box_alpha,
                    font_size=self.config.scale_bar_font_size
                )
            except Exception:
                # If scale bar fails, continue without it
                pass
    
    def _add_attribution(self) -> None:
        """Add attribution text to the map."""
        if self.config.attribution:
            # Left side attribution
            plt.figtext(
                0.02,
                0.02,
                self.config.attribution,
                fontsize=self.config.attribution_fontsize,
                style="italic",
                color=self.config.attribution_color,
                ha="left"
            )
            
            # Right side date
            date_text = f"Created: {datetime.now().strftime('%Y-%m-%d')}"
            plt.figtext(
                0.98,
                0.02,
                date_text,
                fontsize=self.config.attribution_fontsize,
                style="italic",
                color=self.config.attribution_color,
                ha="right"
            )
    
    def save(
        self,
        filepath: Union[str, Path],
        format: Optional[str] = None,
        dpi: Optional[int] = None
    ) -> None:
        """Save the map to file.
        
        Args:
            filepath: Path to save the map
            format: Output format (png, pdf, svg). If None, inferred from filepath
            dpi: DPI for raster formats. If None, uses config default
        """
        if self._fig is None:
            raise ValueError("No map has been created yet. Call create_map first.")
        
        filepath = Path(filepath)
        
        # Infer format from extension if not provided
        if format is None:
            format = filepath.suffix.lstrip(".") or "png"
        
        # Use config DPI if not provided
        if dpi is None:
            dpi = self.config.dpi
        
        # Save figure
        self._fig.savefig(
            filepath,
            format=format,
            dpi=dpi,
            bbox_inches=self.config.bbox_inches,
            pad_inches=self.config.pad_inches,
            facecolor=self.config.facecolor,
            edgecolor=self.config.edgecolor
        )
    
    @classmethod
    def create_demographic_map(
        cls,
        gdf: gpd.GeoDataFrame,
        demographic_column: str,
        title: Optional[str] = None,
        **kwargs
    ) -> Tuple[plt.Figure, plt.Axes]:
        """Convenience method to create a demographic choropleth map.
        
        Args:
            gdf: GeoDataFrame with census data
            demographic_column: Column to visualize
            title: Map title
            **kwargs: Additional config overrides
            
        Returns:
            Tuple of (Figure, Axes) objects
        """
        config_overrides = {
            "title": title or f"Distribution of {demographic_column}",
            "color_scheme": ColorScheme.BLUES,
            **kwargs
        }
        
        mapper = cls()
        return mapper.create_map(
            gdf,
            demographic_column,
            map_type=MapType.DEMOGRAPHIC,
            config_overrides=config_overrides
        )
    
    @classmethod
    def create_distance_map(
        cls,
        gdf: gpd.GeoDataFrame,
        distance_column: str = "travel_distance_km",
        poi_gdf: Optional[gpd.GeoDataFrame] = None,
        title: Optional[str] = None,
        **kwargs
    ) -> Tuple[plt.Figure, plt.Axes]:
        """Convenience method to create a distance-based choropleth map.
        
        Args:
            gdf: GeoDataFrame with distance data
            distance_column: Distance column to visualize
            poi_gdf: Optional POI locations
            title: Map title
            **kwargs: Additional config overrides
            
        Returns:
            Tuple of (Figure, Axes) objects
        """
        config_overrides = {
            "title": title or "Travel Distance Analysis",
            "color_scheme": ColorScheme.YLORD,
            "classification_scheme": ClassificationScheme.FISHER_JENKS,
            **kwargs
        }
        
        # Update legend format for distances
        if "legend_config" not in config_overrides:
            config_overrides["legend_config"] = LegendConfig(
                title="Distance (km)",
                fmt="{:.1f}"
            )
        
        mapper = cls()
        return mapper.create_map(
            gdf,
            distance_column,
            map_type=MapType.DISTANCE,
            poi_gdf=poi_gdf,
            config_overrides=config_overrides
        )
    
    @classmethod
    def create_accessibility_map(
        cls,
        gdf: gpd.GeoDataFrame,
        column: str,
        poi_gdf: Optional[gpd.GeoDataFrame] = None,
        isochrone_gdf: Optional[gpd.GeoDataFrame] = None,
        title: Optional[str] = None,
        **kwargs
    ) -> Tuple[plt.Figure, plt.Axes]:
        """Convenience method to create an accessibility-focused map.
        
        Args:
            gdf: GeoDataFrame with data
            column: Column to visualize
            poi_gdf: Optional POI locations
            isochrone_gdf: Optional isochrone boundaries
            title: Map title
            **kwargs: Additional config overrides
            
        Returns:
            Tuple of (Figure, Axes) objects
        """
        config_overrides = {
            "title": title or "Accessibility Analysis",
            "color_scheme": ColorScheme.VIRIDIS,
            "alpha": 0.8,
            **kwargs
        }
        
        mapper = cls()
        return mapper.create_map(
            gdf,
            column,
            map_type=MapType.ACCESSIBILITY,
            poi_gdf=poi_gdf,
            isochrone_gdf=isochrone_gdf,
            config_overrides=config_overrides
        )