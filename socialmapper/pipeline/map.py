"""
Mapping module for the SocialMapper pipeline.

This module handles map creation from pipeline outputs using the visualization system.
It creates choropleth maps showing demographic data, travel distances, and accessibility analysis.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import geopandas as gpd
import matplotlib.pyplot as plt

from ..progress import get_progress_bar
from ..visualization import ChoroplethMap, ColorScheme, MapConfig, MapType
from ..visualization.config import ClassificationScheme, LegendConfig


def create_pipeline_maps(
    census_data_gdf: gpd.GeoDataFrame,
    poi_data: Dict[str, Any],
    isochrone_gdf: Optional[gpd.GeoDataFrame] = None,
    output_dir: str = "output/maps",
    base_filename: str = "socialmapper",
    travel_time: int = 15,
    census_variables: Optional[List[str]] = None,
    geographic_level: str = "block-group",
    create_demographic_maps: bool = True,
    create_distance_map: bool = True,
    create_accessibility_map: bool = True,
    map_format: str = "png",
    dpi: int = 300
) -> Dict[str, Path]:
    """
    Create comprehensive maps from pipeline outputs.
    
    Args:
        census_data_gdf: GeoDataFrame with census data and geometries
        poi_data: POI data dictionary from pipeline
        isochrone_gdf: Optional isochrone boundaries
        output_dir: Directory to save maps
        base_filename: Base filename for output maps
        travel_time: Travel time in minutes (for titles)
        census_variables: List of census variables to map
        geographic_level: Geographic unit type ('block-group' or 'zcta')
        create_demographic_maps: Whether to create demographic maps
        create_distance_map: Whether to create distance map
        create_accessibility_map: Whether to create accessibility map
        map_format: Output format (png, pdf, svg)
        dpi: DPI for raster formats
        
    Returns:
        Dictionary mapping map type to output file path
    """
    print("\n=== Creating Maps from Pipeline Outputs ===")
    
    # Setup output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Prepare geographic data with proper simplification and projection
    census_data_gdf, poi_gdf = _prepare_geographic_data(census_data_gdf, poi_data)
    
    # Also project isochrones if available
    if isochrone_gdf is not None:
        isochrone_gdf = isochrone_gdf.to_crs("EPSG:3857")
    
    # Detect available variables if not specified
    if census_variables is None:
        census_variables = _detect_census_variables(census_data_gdf)
    
    output_paths = {}
    map_count = 0
    
    # Calculate total maps to create for progress tracking
    total_maps = 0
    if create_demographic_maps:
        total_maps += len(census_variables)
    if create_distance_map and _has_distance_data(census_data_gdf):
        total_maps += 1
    if create_accessibility_map and isochrone_gdf is not None:
        total_maps += 1
    
    if total_maps == 0:
        print("⚠️ No maps to create based on available data and settings")
        return output_paths
    
    with get_progress_bar(total=total_maps, desc="🗺️ Creating Maps", unit="map") as pbar:
        
        # Create demographic maps
        if create_demographic_maps and census_variables:
            for variable in census_variables:
                if variable in census_data_gdf.columns:
                    try:
                        map_path = _create_demographic_map(
                            census_data_gdf, 
                            variable, 
                            poi_gdf, 
                            isochrone_gdf,
                            output_path, 
                            base_filename, 
                            travel_time,
                            geographic_level,
                            map_format, 
                            dpi
                        )
                        output_paths[f"demographic_{variable}"] = map_path
                        map_count += 1
                        print(f"✅ Created demographic map: {variable}")
                    except Exception as e:
                        print(f"⚠️ Failed to create demographic map for {variable}: {e}")
                    pbar.update(1)
        
        # Create distance map
        if create_distance_map and _has_distance_data(census_data_gdf):
            try:
                distance_column = _get_distance_column(census_data_gdf)
                if distance_column:
                    map_path = _create_distance_map(
                        census_data_gdf, 
                        distance_column, 
                        poi_gdf,
                        output_path, 
                        base_filename, 
                        travel_time,
                        geographic_level,
                        map_format, 
                        dpi
                    )
                    output_paths["distance"] = map_path
                    map_count += 1
                    print("✅ Created distance map")
                pbar.update(1)
            except Exception as e:
                print(f"⚠️ Failed to create distance map: {e}")
                pbar.update(1)
        
        # Create accessibility map
        if create_accessibility_map and isochrone_gdf is not None:
            try:
                # Use the first demographic variable for accessibility analysis
                if census_variables and census_variables[0] in census_data_gdf.columns:
                    map_path = _create_accessibility_map(
                        census_data_gdf,
                        census_variables[0],
                        poi_gdf,
                        isochrone_gdf,
                        output_path,
                        base_filename,
                        travel_time,
                        geographic_level,
                        map_format,
                        dpi
                    )
                    output_paths["accessibility"] = map_path
                    map_count += 1
                    print("✅ Created accessibility map")
                pbar.update(1)
            except Exception as e:
                print(f"⚠️ Failed to create accessibility map: {e}")
                pbar.update(1)
    
    print(f"📊 Successfully created {map_count} maps in {output_dir}")
    return output_paths


def _convert_poi_to_geodataframe(poi_data: Dict[str, Any]) -> Optional[gpd.GeoDataFrame]:
    """Convert POI data to GeoDataFrame."""
    from .helpers import convert_poi_to_geodataframe
    
    if "pois" in poi_data and poi_data["pois"]:
        return convert_poi_to_geodataframe(poi_data["pois"])
    return None


def _prepare_geographic_data(
    census_data_gdf: gpd.GeoDataFrame,
    poi_data: Dict[str, Any]
) -> Tuple[gpd.GeoDataFrame, Optional[gpd.GeoDataFrame]]:
    """Prepare geographic data for mapping with proper simplification and projection."""
    
    print("🗺️ Preparing geographic data for mapping...")
    
    # Convert POI data to GeoDataFrame if available
    poi_gdf = _convert_poi_to_geodataframe(poi_data)
    
    # Project to Web Mercator for better visualization
    target_crs = "EPSG:3857"  # Web Mercator
    
    print(f"  - Projecting from {census_data_gdf.crs} to {target_crs}")
    census_data_gdf = census_data_gdf.to_crs(target_crs)
    if poi_gdf is not None:
        poi_gdf = poi_gdf.to_crs(target_crs)
    
    # Simplify geometries for better visualization performance
    # Calculate appropriate tolerance based on the spatial extent
    bbox = census_data_gdf.total_bounds
    map_width = bbox[2] - bbox[0]  # width in projected units (meters for Web Mercator)
    
    # Set tolerance to ~0.05% of map width for reasonable simplification
    # This removes unnecessary detail while preserving shape
    tolerance = max(map_width * 0.0005, 100)  # minimum 100m tolerance
    
    print(f"  - Simplifying geometries with tolerance: {tolerance:.0f} meters")
    original_count = len(census_data_gdf)
    
    # Simplify geometries
    census_data_gdf = census_data_gdf.copy()
    census_data_gdf['geometry'] = census_data_gdf.geometry.simplify(tolerance=tolerance, preserve_topology=True)
    
    # Remove any invalid geometries that might result from simplification
    valid_geom = census_data_gdf.geometry.is_valid & census_data_gdf.geometry.notna()
    if not valid_geom.all():
        invalid_count = (~valid_geom).sum()
        print(f"  - Removing {invalid_count} invalid geometries after simplification")
        census_data_gdf = census_data_gdf[valid_geom].copy()
    
    # Also remove tiny geometries that might clutter the map
    if target_crs == "EPSG:3857":  # Web Mercator uses meters
        min_area = 10000  # 10,000 sq meters (1 hectare)
        large_enough = census_data_gdf.geometry.area > min_area
        if not large_enough.all():
            tiny_count = (~large_enough).sum()
            print(f"  - Removing {tiny_count} very small geometries (< {min_area} sq meters)")
            census_data_gdf = census_data_gdf[large_enough].copy()
    
    remaining_count = len(census_data_gdf)
    print(f"  - Processed {original_count} → {remaining_count} geographic units")
    
    return census_data_gdf, poi_gdf


def _detect_census_variables(gdf: gpd.GeoDataFrame) -> List[str]:
    """Auto-detect census variables in the GeoDataFrame."""
    census_variables = []
    
    # Common census variable patterns
    patterns = [
        ("B01003_001E", "Total Population"),
        ("B19013_001E", "Median Household Income"), 
        ("B25001_001E", "Total Housing Units"),
        ("B15003_022E", "Bachelor's Degree"),
        ("B08301_010E", "Public Transportation"),
        ("B17001_002E", "Population Below Poverty"),
    ]
    
    for pattern, _ in patterns:
        if pattern in gdf.columns:
            census_variables.append(pattern)
    
    # Look for any other B-series variables
    for col in gdf.columns:
        if (col.startswith("B") and "_" in col and "E" in col and 
            col not in census_variables):
            census_variables.append(col)
    
    # Limit to avoid too many maps
    return census_variables[:5]


def _has_distance_data(gdf: gpd.GeoDataFrame) -> bool:
    """Check if GeoDataFrame has distance data."""
    distance_columns = [
        "travel_distance_km", "travel_distance_miles",
        "distance_km", "distance_miles"
    ]
    return any(col in gdf.columns for col in distance_columns)


def _get_distance_column(gdf: gpd.GeoDataFrame) -> Optional[str]:
    """Get the distance column name."""
    preferred_columns = [
        "travel_distance_km", "travel_distance_miles",
        "distance_km", "distance_miles"
    ]
    for col in preferred_columns:
        if col in gdf.columns:
            return col
    return None


def _create_demographic_map(
    gdf: gpd.GeoDataFrame,
    variable: str,
    poi_gdf: Optional[gpd.GeoDataFrame],
    isochrone_gdf: Optional[gpd.GeoDataFrame],
    output_path: Path,
    base_filename: str,
    travel_time: int,
    geographic_level: str,
    map_format: str,
    dpi: int
) -> Path:
    """Create a demographic choropleth map."""
    
    # Get human-readable title
    title = _get_variable_title(variable, geographic_level, travel_time)
    
    # Determine color scheme based on variable type
    color_scheme = _get_color_scheme_for_variable(variable)
    
    # Calculate appropriate zoom level based on map extent
    bbox = gdf.total_bounds
    # Rough calculation: smaller areas need higher zoom
    bbox_width = bbox[2] - bbox[0]
    bbox_height = bbox[3] - bbox[1]
    bbox_size = max(bbox_width, bbox_height)
    
    # Estimate zoom level (very rough approximation)
    if bbox_size < 0.01:  # Very small area (neighborhood)
        zoom_level = 15
    elif bbox_size < 0.05:  # Small area (district)
        zoom_level = 13
    elif bbox_size < 0.1:   # Medium area (city)
        zoom_level = 11
    else:  # Large area
        zoom_level = "auto"
    
    # Create configuration
    config = MapConfig(
        figsize=(12, 10),
        color_scheme=color_scheme,
        classification_scheme=ClassificationScheme.QUANTILES,
        n_classes=5,
        title=title,
        alpha=0.8 if isochrone_gdf is not None else 0.7,  # More transparent with basemap
        add_basemap=True,
        basemap_source="OpenStreetMap.Mapnik",
        basemap_alpha=0.6,
        basemap_zoom=zoom_level,
        edge_color="white",
        edge_width=0.3,
        legend_config=LegendConfig(
            title=_get_legend_title(variable),
            fmt=_get_format_string(variable),
            loc="lower left"
        )
    )
    
    # Create map
    mapper = ChoroplethMap(config)
    fig, ax = mapper.create_map(
        gdf,
        variable,
        map_type=MapType.DEMOGRAPHIC,
        poi_gdf=poi_gdf,
        isochrone_gdf=isochrone_gdf
    )
    
    # Save map
    safe_variable_name = variable.replace("/", "_").replace(" ", "_").lower()
    filename = f"{base_filename}_{travel_time}min_{safe_variable_name}_map.{map_format}"
    output_file = output_path / filename
    
    mapper.save(output_file, format=map_format, dpi=dpi)
    plt.close(fig)
    
    return output_file


def _create_distance_map(
    gdf: gpd.GeoDataFrame,
    distance_column: str,
    poi_gdf: Optional[gpd.GeoDataFrame],
    output_path: Path,
    base_filename: str,
    travel_time: int,
    geographic_level: str,
    map_format: str,
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
    
    unit_label = "ZIP Code Areas" if geographic_level == "zcta" else "Block Groups"
    title = f"Travel Distance to Nearest POI by {unit_label}"
    
    # Calculate appropriate zoom level
    bbox = gdf.total_bounds
    bbox_size = max(bbox[2] - bbox[0], bbox[3] - bbox[1])
    if bbox_size < 0.01:
        zoom_level = 15
    elif bbox_size < 0.05:
        zoom_level = 13
    elif bbox_size < 0.1:
        zoom_level = 11
    else:
        zoom_level = "auto"
    
    # Create configuration
    config = MapConfig(
        figsize=(12, 10),
        color_scheme=ColorScheme.YLORD,
        classification_scheme=ClassificationScheme.FISHER_JENKS,
        n_classes=5,
        title=title,
        alpha=0.7,  # More transparent with basemap
        add_basemap=True,
        basemap_source="OpenStreetMap.Mapnik",
        basemap_alpha=0.6,
        basemap_zoom=zoom_level,
        edge_color="white",
        edge_width=0.3,
        legend_config=LegendConfig(
            title=f"Distance ({units})",
            fmt=fmt,
            loc="lower left"
        )
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
    filename = f"{base_filename}_{travel_time}min_distance_map.{map_format}"
    output_file = output_path / filename
    
    mapper.save(output_file, format=map_format, dpi=dpi)
    plt.close(fig)
    
    return output_file


def _create_accessibility_map(
    gdf: gpd.GeoDataFrame,
    variable: str,
    poi_gdf: Optional[gpd.GeoDataFrame],
    isochrone_gdf: gpd.GeoDataFrame,
    output_path: Path,
    base_filename: str,
    travel_time: int,
    geographic_level: str,
    map_format: str,
    dpi: int
) -> Path:
    """Create an accessibility-focused map with isochrones."""
    
    unit_label = "ZIP Code Areas" if geographic_level == "zcta" else "Block Groups"
    variable_name = _get_legend_title(variable)
    title = f"{variable_name} within {travel_time}-Minute Travel Time"
    
    # Calculate appropriate zoom level
    bbox = gdf.total_bounds
    bbox_size = max(bbox[2] - bbox[0], bbox[3] - bbox[1])
    if bbox_size < 0.01:
        zoom_level = 15
    elif bbox_size < 0.05:
        zoom_level = 13
    elif bbox_size < 0.1:
        zoom_level = 11
    else:
        zoom_level = "auto"
    
    # Create configuration
    config = MapConfig(
        figsize=(12, 10),
        color_scheme=ColorScheme.VIRIDIS,
        classification_scheme=ClassificationScheme.QUANTILES,
        n_classes=5,
        title=title,
        alpha=0.7,  # More transparent for overlay
        add_basemap=True,
        basemap_source="OpenStreetMap.Mapnik",
        basemap_alpha=0.6,
        basemap_zoom=zoom_level,
        edge_color="white",
        edge_width=0.3,
        legend_config=LegendConfig(
            title=_get_legend_title(variable),
            fmt=_get_format_string(variable),
            loc="lower left"
        )
    )
    
    # Create map
    mapper = ChoroplethMap(config)
    fig, ax = mapper.create_map(
        gdf,
        variable,
        map_type=MapType.ACCESSIBILITY,
        poi_gdf=poi_gdf,
        isochrone_gdf=isochrone_gdf
    )
    
    # Save map
    filename = f"{base_filename}_{travel_time}min_accessibility_map.{map_format}"
    output_file = output_path / filename
    
    mapper.save(output_file, format=map_format, dpi=dpi)
    plt.close(fig)
    
    return output_file


def _get_variable_title(variable: str, geographic_level: str, travel_time: int) -> str:
    """Get a human-readable title for a census variable."""
    
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
    
    if variable in variable_titles:
        var_title = variable_titles[variable]
    else:
        var_title = variable.replace("_", " ").title()
    
    unit_label = "ZIP Code Areas" if geographic_level == "zcta" else "Block Groups"
    return f"{var_title} by {unit_label}"


def _get_legend_title(variable: str) -> str:
    """Get legend title for a variable."""
    
    legend_titles = {
        "B01003_001E": "Population",
        "B19013_001E": "Income ($)",
        "B25001_001E": "Housing Units",
        "B15003_022E": "With Bachelor's",
        "B08301_010E": "Use Transit",
        "B17001_002E": "Below Poverty",
        "B25077_001E": "Home Value ($)",
        "B08303_001E": "Commuters",
        "B01002_001E": "Median Age",
    }
    
    return legend_titles.get(variable, variable.replace("_", " ").title())


def _get_format_string(variable: str) -> str:
    """Get appropriate format string for a variable."""
    
    # Variables that should show as currency
    currency_vars = ["B19013_001E", "B25077_001E"]
    if variable in currency_vars:
        return "${:,.0f}"
    
    # Variables that should show decimals
    decimal_vars = ["B01002_001E"]  # Age
    if variable in decimal_vars:
        return "{:.1f}"
    
    # Default to whole numbers
    return "{:,.0f}"


def _get_color_scheme_for_variable(variable: str) -> ColorScheme:
    """Get appropriate color scheme based on variable type."""
    
    # Income-related variables
    if "income" in variable.lower() or variable in ["B19013_001E", "B25077_001E"]:
        return ColorScheme.GREENS
    
    # Population-related variables  
    if "population" in variable.lower() or variable == "B01003_001E":
        return ColorScheme.BLUES
    
    # Poverty-related variables
    if "poverty" in variable.lower() or variable == "B17001_002E":
        return ColorScheme.REDS
    
    # Education variables
    if "education" in variable.lower() or variable == "B15003_022E":
        return ColorScheme.PURPLES
    
    # Transportation variables
    if "transport" in variable.lower() or variable == "B08301_010E":
        return ColorScheme.ORANGES
    
    # Default
    return ColorScheme.VIRIDIS


# Integration function for pipeline orchestrator
def generate_pipeline_maps(
    census_data_gdf: gpd.GeoDataFrame,
    poi_data: Dict[str, Any],
    isochrone_gdf: Optional[gpd.GeoDataFrame],
    directories: Dict[str, str],
    base_filename: str,
    travel_time: int,
    census_codes: List[str],
    geographic_level: str = "block-group"
) -> Dict[str, Any]:
    """
    Generate maps for pipeline integration.
    
    This function is designed to be called from the pipeline orchestrator.
    
    Args:
        census_data_gdf: Census data GeoDataFrame
        poi_data: POI data dictionary
        isochrone_gdf: Optional isochrone GeoDataFrame
        directories: Directory paths from pipeline setup
        base_filename: Base filename for outputs
        travel_time: Travel time in minutes
        census_codes: List of census variable codes
        geographic_level: Geographic unit type
        
    Returns:
        Dictionary of result information
    """
    print("\n=== Generating Pipeline Maps ===")
    
    # Determine output directory
    if "maps" in directories:
        output_dir = directories["maps"]
    else:
        # Create maps subdirectory in base output
        base_dir = Path(directories.get("base", "output"))
        output_dir = base_dir / "maps"
        output_dir.mkdir(exist_ok=True)
    
    try:
        # Create maps using the main function
        output_paths = create_pipeline_maps(
            census_data_gdf=census_data_gdf,
            poi_data=poi_data,
            isochrone_gdf=isochrone_gdf,
            output_dir=str(output_dir),
            base_filename=base_filename,
            travel_time=travel_time,
            census_variables=census_codes,
            geographic_level=geographic_level,
            create_demographic_maps=True,
            create_distance_map=True,
            create_accessibility_map=isochrone_gdf is not None,
            map_format="png",
            dpi=300
        )
        
        return {
            "maps_created": len(output_paths),
            "output_paths": output_paths,
            "output_directory": str(output_dir)
        }
        
    except Exception as e:
        print(f"⚠️ Map generation failed: {e}")
        return {
            "maps_created": 0,
            "output_paths": {},
            "error": str(e)
        } 