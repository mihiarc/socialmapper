"""Integration of visualization module with socialmapper pipeline."""

from pathlib import Path
from typing import Dict, List, Optional, Union

import geopandas as gpd
import matplotlib.pyplot as plt

from .chloropleth import ChoroplethMap, MapType
from .config import ClassificationScheme, ColorScheme, MapConfig


class VisualizationPipeline:
    """Integrate choropleth mapping into the socialmapper pipeline."""
    
    def __init__(self, output_dir: Union[str, Path]):
        """Initialize visualization pipeline.
        
        Args:
            output_dir: Directory to save map outputs
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def create_maps_from_census_data(
        self,
        census_gdf: gpd.GeoDataFrame,
        poi_gdf: Optional[gpd.GeoDataFrame] = None,
        isochrone_gdf: Optional[gpd.GeoDataFrame] = None,
        demographic_columns: Optional[List[str]] = None,
        create_distance_map: bool = True,
        create_demographic_maps: bool = True,
        map_format: str = "png",
        dpi: int = 300
    ) -> Dict[str, Path]:
        """Create multiple maps from census data output.
        
        Args:
            census_gdf: GeoDataFrame with census and distance data
            poi_gdf: Optional POI locations
            isochrone_gdf: Optional isochrone boundaries
            demographic_columns: List of demographic columns to map. If None, auto-detect
            create_distance_map: Whether to create distance-based map
            create_demographic_maps: Whether to create demographic maps
            map_format: Output format (png, pdf, svg)
            dpi: DPI for raster formats
            
        Returns:
            Dictionary mapping map type to output file path
        """
        output_paths = {}
        
        # Create distance map if requested
        if create_distance_map and self._has_distance_data(census_gdf):
            distance_col = self._get_distance_column(census_gdf)
            if distance_col:
                map_path = self._create_distance_map(
                    census_gdf, distance_col, poi_gdf, map_format, dpi
                )
                output_paths["distance"] = map_path
        
        # Create demographic maps if requested
        if create_demographic_maps:
            if demographic_columns is None:
                demographic_columns = self._detect_demographic_columns(census_gdf)
            
            for col in demographic_columns:
                if col in census_gdf.columns:
                    map_path = self._create_demographic_map(
                        census_gdf, col, poi_gdf, isochrone_gdf, map_format, dpi
                    )
                    output_paths[f"demographic_{col}"] = map_path
        
        return output_paths
    
    def _has_distance_data(self, gdf: gpd.GeoDataFrame) -> bool:
        """Check if GeoDataFrame has distance data."""
        distance_columns = [
            "travel_distance_km", "travel_distance_miles",
            "distance_km", "distance_miles"
        ]
        return any(col in gdf.columns for col in distance_columns)
    
    def _get_distance_column(self, gdf: gpd.GeoDataFrame) -> Optional[str]:
        """Get the distance column name."""
        preferred_columns = [
            "travel_distance_km", "travel_distance_miles",
            "distance_km", "distance_miles"
        ]
        for col in preferred_columns:
            if col in gdf.columns:
                return col
        return None
    
    def _detect_demographic_columns(self, gdf: gpd.GeoDataFrame) -> List[str]:
        """Auto-detect demographic columns in the data."""
        demographic_columns = []
        
        # Common census variable patterns
        patterns = [
            ("B01003_001E", "Total Population"),  # Total population
            ("B19013_001E", "Median Household Income"),  # Median income
            ("B25001_001E", "Total Housing Units"),  # Housing units
            ("B15003_022E", "Bachelor's Degree"),  # Education
            ("B08301_010E", "Public Transportation"),  # Transportation
        ]
        
        for pattern, _ in patterns:
            if pattern in gdf.columns:
                demographic_columns.append(pattern)
        
        # Also look for columns with descriptive names
        descriptive_patterns = [
            "population", "income", "poverty", "education",
            "employment", "housing", "age", "race", "ethnicity"
        ]
        
        for col in gdf.columns:
            col_lower = col.lower()
            if any(pattern in col_lower for pattern in descriptive_patterns):
                if col not in demographic_columns:
                    demographic_columns.append(col)
        
        # Limit to top 5 to avoid too many maps
        return demographic_columns[:5]
    
    def _create_distance_map(
        self,
        gdf: gpd.GeoDataFrame,
        distance_column: str,
        poi_gdf: Optional[gpd.GeoDataFrame],
        format: str,
        dpi: int
    ) -> Path:
        """Create a distance-based choropleth map."""
        # Determine units from column name
        if "miles" in distance_column:
            units = "miles"
            fmt = "{:.1f}"
        else:
            units = "km"
            fmt = "{:.1f}"
        
        # Create configuration
        config = MapConfig(
            color_scheme=ColorScheme.YLORD,
            classification_scheme=ClassificationScheme.FISHER_JENKS,
            n_classes=5,
            title="Travel Distance to Nearest POI",
            legend_config={
                "title": f"Distance ({units})",
                "fmt": fmt
            }
        )
        
        # Create map
        mapper = ChoroplethMap(config)
        fig, ax = mapper.create_map(
            gdf,
            distance_column,
            map_type=MapType.DISTANCE,
            poi_gdf=poi_gdf
        )
        
        # Save map
        output_path = self.output_dir / f"distance_map.{format}"
        mapper.save(output_path, format=format, dpi=dpi)
        plt.close(fig)
        
        return output_path
    
    def _create_demographic_map(
        self,
        gdf: gpd.GeoDataFrame,
        column: str,
        poi_gdf: Optional[gpd.GeoDataFrame],
        isochrone_gdf: Optional[gpd.GeoDataFrame],
        format: str,
        dpi: int
    ) -> Path:
        """Create a demographic choropleth map."""
        # Get column title
        title = self._get_column_title(column)
        
        # Determine color scheme based on data type
        if "income" in column.lower():
            color_scheme = ColorScheme.GREENS
        elif "population" in column.lower():
            color_scheme = ColorScheme.BLUES
        elif "poverty" in column.lower():
            color_scheme = ColorScheme.REDS
        else:
            color_scheme = ColorScheme.VIRIDIS
        
        # Create configuration
        config = MapConfig(
            color_scheme=color_scheme,
            classification_scheme=ClassificationScheme.QUANTILES,
            n_classes=5,
            title=title,
            alpha=0.8 if isochrone_gdf is not None else 1.0
        )
        
        # Determine map type
        map_type = MapType.ACCESSIBILITY if isochrone_gdf is not None else MapType.DEMOGRAPHIC
        
        # Create map
        mapper = ChoroplethMap(config)
        fig, ax = mapper.create_map(
            gdf,
            column,
            map_type=map_type,
            poi_gdf=poi_gdf,
            isochrone_gdf=isochrone_gdf
        )
        
        # Save map
        safe_column_name = column.replace("/", "_").replace(" ", "_").lower()
        output_path = self.output_dir / f"{safe_column_name}_map.{format}"
        mapper.save(output_path, format=format, dpi=dpi)
        plt.close(fig)
        
        return output_path
    
    def _get_column_title(self, column: str) -> str:
        """Get a human-readable title for a column."""
        # Common census variable mappings
        variable_titles = {
            "B01003_001E": "Total Population",
            "B19013_001E": "Median Household Income",
            "B25001_001E": "Total Housing Units",
            "B15003_022E": "Population with Bachelor's Degree",
            "B08301_010E": "Public Transportation Usage",
            "B17001_002E": "Population Below Poverty Level",
            "B25077_001E": "Median Home Value",
            "B08303_001E": "Total Commuters",
            "B01002_001E": "Median Age",
        }
        
        if column in variable_titles:
            return variable_titles[column]
        
        # Format column name
        return column.replace("_", " ").title()


def add_visualization_to_pipeline(
    census_data_path: Union[str, Path],
    output_dir: Union[str, Path],
    poi_data_path: Optional[Union[str, Path]] = None,
    isochrone_data_path: Optional[Union[str, Path]] = None,
    **kwargs
) -> Dict[str, Path]:
    """Convenience function to add visualization to existing pipeline output.
    
    Args:
        census_data_path: Path to census data CSV or GeoParquet
        output_dir: Directory to save maps
        poi_data_path: Optional path to POI data
        isochrone_data_path: Optional path to isochrone data
        **kwargs: Additional arguments for create_maps_from_census_data
        
    Returns:
        Dictionary of output paths
    """
    # Load census data
    census_data_path = Path(census_data_path)
    if census_data_path.suffix == ".parquet":
        census_gdf = gpd.read_parquet(census_data_path)
    else:
        # CSV - need to recreate geometry from census block group IDs
        # This would require additional logic to fetch geometries
        raise NotImplementedError(
            "CSV input requires geometry reconstruction. Use GeoParquet output instead."
        )
    
    # Load POI data if provided
    poi_gdf = None
    if poi_data_path:
        poi_data_path = Path(poi_data_path)
        if poi_data_path.suffix == ".parquet":
            poi_gdf = gpd.read_parquet(poi_data_path)
    
    # Load isochrone data if provided
    isochrone_gdf = None
    if isochrone_data_path:
        isochrone_data_path = Path(isochrone_data_path)
        if isochrone_data_path.suffix == ".parquet":
            isochrone_gdf = gpd.read_parquet(isochrone_data_path)
    
    # Create visualization pipeline
    viz_pipeline = VisualizationPipeline(output_dir)
    
    # Create maps
    return viz_pipeline.create_maps_from_census_data(
        census_gdf,
        poi_gdf=poi_gdf,
        isochrone_gdf=isochrone_gdf,
        **kwargs
    )