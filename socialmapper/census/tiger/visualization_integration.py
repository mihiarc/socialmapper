"""Integration between TIGER geometry client and visualization module."""

import logging
from typing import Dict, List, Optional, Tuple, Union

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

from ...visualization import ChoroplethMap, ColorScheme, MapConfig
from .client import TigerGeometryClient
from .models import GeographyLevel, GeometryQuery, GeometryResult

logger = logging.getLogger(__name__)


class TigerVisualizationHelper:
    """Helper class for visualizing TIGER geometries."""
    
    def __init__(self, tiger_client: Optional[TigerGeometryClient] = None):
        """Initialize with optional TIGER client."""
        self.tiger_client = tiger_client or TigerGeometryClient()
    
    def create_county_map(
        self,
        state_fips: str,
        census_data: Optional[pd.DataFrame] = None,
        value_column: Optional[str] = None,
        map_config: Optional[MapConfig] = None,
    ) -> Union[ChoroplethMap, Tuple[plt.Figure, plt.Axes]]:
        """Create a choropleth map of counties with optional census data.
        
        Args:
            state_fips: State FIPS code
            census_data: DataFrame with GEOID column and value columns
            value_column: Column to visualize (if census_data provided)
            map_config: Map configuration
            
        Returns:
            ChoroplethMap instance
        """
        # Fetch county geometries
        result = self.tiger_client.fetch_counties(state_fips=state_fips)
        gdf = result.geodataframe
        
        # Merge with census data if provided
        if census_data is not None and value_column is not None:
            gdf = gdf.merge(census_data, on="GEOID", how="left")
        
        # Create default config if not provided
        if map_config is None:
            state_name = gdf.iloc[0]["NAME"].split(",")[1].strip() if len(gdf) > 0 else state_fips
            map_config = MapConfig(
                title=f"{state_name} Counties",
                figsize=(12, 10),
                show_legend=True,
                show_north_arrow=True,
                show_scale_bar=True,
            )
        
        # Create choropleth
        choropleth = ChoroplethMap(config=map_config)
        
        # Store the data for later use
        choropleth._gdf = gdf
        choropleth._value_column = value_column
        
        return choropleth
    
    def create_block_group_map(
        self,
        state_fips: str,
        county_fips: str,
        census_data: Optional[pd.DataFrame] = None,
        value_column: Optional[str] = None,
        map_config: Optional[MapConfig] = None,
    ) -> ChoroplethMap:
        """Create a choropleth map of block groups with optional census data.
        
        Args:
            state_fips: State FIPS code
            county_fips: County FIPS code
            census_data: DataFrame with GEOID column and value columns
            value_column: Column to visualize (if census_data provided)
            map_config: Map configuration
            
        Returns:
            ChoroplethMap instance
        """
        # Fetch block group geometries
        result = self.tiger_client.fetch_block_groups(
            state_fips=state_fips,
            county_fips=county_fips,
        )
        gdf = result.geodataframe
        
        # Merge with census data if provided
        if census_data is not None and value_column is not None:
            gdf = gdf.merge(census_data, on="GEOID", how="left")
        
        # Create default config if not provided
        if map_config is None:
            map_config = MapConfig(
                title=f"Block Groups - {state_fips}{county_fips}",
                figsize=(12, 10),
                show_legend=True,
                show_north_arrow=True,
                show_scale_bar=True,
            )
        
        # Create choropleth
        choropleth = ChoroplethMap(config=map_config)
        
        # Store the data for later use
        choropleth._gdf = gdf
        choropleth._value_column = value_column
        
        return choropleth
    
    def create_zcta_map(
        self,
        zcta_codes: Optional[List[str]] = None,
        zcta_prefix: Optional[str] = None,
        census_data: Optional[pd.DataFrame] = None,
        value_column: Optional[str] = None,
        map_config: Optional[MapConfig] = None,
    ) -> ChoroplethMap:
        """Create a choropleth map of ZCTAs with optional census data.
        
        Args:
            zcta_codes: Specific ZCTA codes to include
            zcta_prefix: ZCTA prefix to filter by
            census_data: DataFrame with GEOID column and value columns
            value_column: Column to visualize (if census_data provided)
            map_config: Map configuration
            
        Returns:
            ChoroplethMap instance
        """
        # Fetch ZCTA geometries
        result = self.tiger_client.fetch_zctas(
            zcta_codes=zcta_codes,
            zcta_prefix=zcta_prefix,
        )
        gdf = result.geodataframe
        
        # Merge with census data if provided
        if census_data is not None and value_column is not None:
            gdf = gdf.merge(census_data, on="GEOID", how="left")
        
        # Create default config if not provided
        if map_config is None:
            title = "ZCTAs"
            if zcta_prefix:
                title += f" - {zcta_prefix}xxx"
            map_config = MapConfig(
                title=title,
                figsize=(12, 10),
                show_legend=True,
                show_north_arrow=True,
                show_scale_bar=True,
            )
        
        # Create choropleth
        choropleth = ChoroplethMap(config=map_config)
        
        # Store the data for later use
        choropleth._gdf = gdf
        choropleth._value_column = value_column
        
        return choropleth
    
    def create_multi_level_map(
        self,
        queries: List[Tuple[GeographyLevel, GeometryQuery]],
        layer_styles: Optional[Dict[GeographyLevel, dict]] = None,
        map_config: Optional[MapConfig] = None,
    ) -> ChoroplethMap:
        """Create a map with multiple geography levels.
        
        Args:
            queries: List of (level, query) tuples
            layer_styles: Dict mapping geography levels to style dicts
            map_config: Map configuration
            
        Returns:
            ChoroplethMap instance with base layer
        """
        if not queries:
            raise ValueError("At least one query is required")
        
        # Default styles for each level
        default_styles = {
            GeographyLevel.STATE: {"color": "lightgray", "edgecolor": "black", "linewidth": 2},
            GeographyLevel.COUNTY: {"color": "lightblue", "edgecolor": "darkblue", "linewidth": 1.5},
            GeographyLevel.TRACT: {"color": "lightgreen", "edgecolor": "darkgreen", "linewidth": 1},
            GeographyLevel.BLOCK_GROUP: {"color": "lightyellow", "edgecolor": "orange", "linewidth": 0.5},
            GeographyLevel.ZCTA: {"color": "lightcoral", "edgecolor": "darkred", "linewidth": 1},
        }
        
        # Merge with provided styles
        if layer_styles:
            default_styles.update(layer_styles)
        
        # Fetch all geometries
        gdfs = []
        for level, query in queries:
            try:
                result = self.tiger_client.fetch_geometries(query)
                gdf = result.geodataframe.copy()
                gdf["geography_level"] = level.value
                gdfs.append(gdf)
            except Exception as e:
                logger.warning(f"Failed to fetch {level.value}: {e}")
        
        if not gdfs:
            raise ValueError("No geometries could be fetched")
        
        # Use the first layer as base
        base_gdf = gdfs[0]
        
        # Create default config if not provided
        if map_config is None:
            map_config = MapConfig(
                title="Multi-Level Geography Map",
                figsize=(14, 10),
                show_legend=False,  # Complex to show legend for multiple layers
                show_north_arrow=True,
                show_scale_bar=True,
            )
        
        # Create base choropleth
        choropleth = ChoroplethMap(config=map_config)
        choropleth._gdf = base_gdf
        choropleth._value_column = None  # No values for multi-level
        
        # Store additional layers for custom rendering
        choropleth._additional_layers = gdfs[1:] if len(gdfs) > 1 else []
        choropleth._layer_styles = default_styles
        
        return choropleth


def visualize_tiger_with_census(
    geography_level: GeographyLevel,
    geography_query: GeometryQuery,
    census_data: pd.DataFrame,
    value_column: str,
    map_title: Optional[str] = None,
    color_scheme: ColorScheme = ColorScheme.VIRIDIS,
) -> ChoroplethMap:
    """Convenience function to visualize TIGER geometries with census data.
    
    Args:
        geography_level: Geography level to fetch
        geography_query: Query parameters
        census_data: DataFrame with GEOID column and value columns
        value_column: Column to visualize
        map_title: Optional map title
        color_scheme: Color scheme for the map
        
    Returns:
        ChoroplethMap instance
    """
    # Fetch geometries
    client = TigerGeometryClient()
    result = client.fetch_geometries(geography_query)
    
    # Merge with census data
    gdf = result.geodataframe.merge(census_data, on="GEOID", how="left")
    
    # Create map config
    if map_title is None:
        map_title = f"{geography_level.value.title()} - {value_column}"
    
    config = MapConfig(
        title=map_title,
        color_scheme=color_scheme,
        figsize=(12, 10),
        show_legend=True,
        show_north_arrow=True,
        show_scale_bar=True,
    )
    
    # Create and return choropleth
    choropleth = ChoroplethMap(config=config)
    choropleth._gdf = gdf
    choropleth._value_column = value_column
    return choropleth


def create_comparison_maps(
    geography_level: GeographyLevel,
    geography_query: GeometryQuery,
    census_data: pd.DataFrame,
    value_columns: List[str],
    titles: Optional[List[str]] = None,
    shared_colormap: bool = True,
) -> List[ChoroplethMap]:
    """Create multiple maps for comparing different variables.
    
    Args:
        geography_level: Geography level to fetch
        geography_query: Query parameters
        census_data: DataFrame with GEOID column and value columns
        value_columns: List of columns to visualize
        titles: Optional list of titles for each map
        shared_colormap: Whether to use the same color scale across maps
        
    Returns:
        List of ChoroplethMap instances
    """
    # Fetch geometries once
    client = TigerGeometryClient()
    result = client.fetch_geometries(geography_query)
    
    # Merge with census data
    gdf = result.geodataframe.merge(census_data, on="GEOID", how="left")
    
    # Determine shared vmin/vmax if requested
    vmin, vmax = None, None
    if shared_colormap:
        all_values = pd.concat([gdf[col] for col in value_columns if col in gdf.columns])
        vmin = all_values.min()
        vmax = all_values.max()
    
    # Create maps
    maps = []
    for i, column in enumerate(value_columns):
        title = titles[i] if titles and i < len(titles) else f"{geography_level.value.title()} - {column}"
        
        config = MapConfig(
            title=title,
            figsize=(10, 8),
            show_legend=True,
            show_north_arrow=True,
            show_scale_bar=True,
        )
        
        choropleth = ChoroplethMap(config=config)
        choropleth._gdf = gdf
        choropleth._value_column = column
        
        # Store vmin/vmax for consistent coloring
        if shared_colormap:
            choropleth._vmin = vmin
            choropleth._vmax = vmax
        
        maps.append(choropleth)
    
    return maps