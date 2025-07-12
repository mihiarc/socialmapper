#!/usr/bin/env python3
"""
Visualize Montana Timber Mill Analysis Results

This script visualizes already-generated analysis data without re-running
the time-consuming analysis pipeline. It's optimized for performance,
especially for large areas like 2-hour drive radii.
"""

import sys
from pathlib import Path
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

console = Console()


def find_analysis_results(output_dir="output"):
    """Find all Montana mill analysis results in the output directory."""
    output_path = Path(output_dir)
    results = []
    
    # Look for census data files
    census_dir = output_path / "census_data"
    if census_dir.exists():
        for csv_file in census_dir.glob("*montana*.csv"):
            # Extract travel time from filename
            parts = csv_file.stem.split("_")
            for i, part in enumerate(parts):
                if part.endswith("min") and i > 0 and parts[i-1].isdigit():
                    travel_time = int(parts[i-1])
                    
                    # Check for corresponding isochrone file
                    iso_pattern = f"*montana*{travel_time}min*.geoparquet"
                    iso_files = list((output_path / "isochrones").glob(iso_pattern))
                    
                    results.append({
                        "travel_time": travel_time,
                        "census_file": csv_file,
                        "isochrone_file": iso_files[0] if iso_files else None,
                        "has_isochrone": len(iso_files) > 0
                    })
                    break
    
    # Also check subdirectories for timber mill analysis outputs
    for subdir in output_path.glob("timber_mill*"):
        census_subdir = subdir / "census_data"
        if census_subdir.exists():
            for csv_file in census_subdir.glob("*montana*.csv"):
                parts = csv_file.stem.split("_")
                for i, part in enumerate(parts):
                    if part.endswith("min") and i > 0 and parts[i-1].isdigit():
                        travel_time = int(parts[i-1])
                        
                        iso_pattern = f"*{travel_time}min*.geoparquet"
                        iso_files = list((subdir / "isochrones").glob(iso_pattern))
                        
                        results.append({
                            "travel_time": travel_time,
                            "census_file": csv_file,
                            "isochrone_file": iso_files[0] if iso_files else None,
                            "has_isochrone": len(iso_files) > 0,
                            "subdir": subdir.name
                        })
                        break
    
    return sorted(results, key=lambda x: x["travel_time"])


def load_census_data(csv_path):
    """Load census data from CSV file."""
    df = pd.read_csv(csv_path)
    console.print(f"Loaded {len(df)} census units from {csv_path.name}")
    return df


def load_isochrone_data(geoparquet_path):
    """Load isochrone data from GeoParquet file."""
    if geoparquet_path and geoparquet_path.exists():
        gdf = gpd.read_parquet(geoparquet_path)
        console.print(f"Loaded isochrone from {geoparquet_path.name}")
        return gdf
    return None


def create_simple_visualization(census_df, isochrone_gdf=None, travel_time=None, 
                              variable="B01003_001E", title_suffix=""):
    """Create a simple matplotlib visualization without basemaps."""
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    
    # Get mill location
    mill_lat = census_df['poi_lat'].iloc[0]
    mill_lon = census_df['poi_lon'].iloc[0]
    
    # Convert census data to GeoDataFrame using centroid WKT strings
    from shapely import wkt
    census_df['geometry'] = census_df['centroid'].apply(wkt.loads)
    census_gdf = gpd.GeoDataFrame(census_df, geometry='geometry', crs='EPSG:4326')
    
    # Project to a suitable CRS for Montana (EPSG:32612 - UTM Zone 12N)
    census_gdf = census_gdf.to_crs('EPSG:32612')
    
    if isochrone_gdf is not None:
        isochrone_gdf = isochrone_gdf.to_crs('EPSG:32612')
    
    # Create mill point
    mill_point = gpd.GeoDataFrame(
        [{'name': 'Mill Location', 'geometry': gpd.points_from_xy([mill_lon], [mill_lat])[0]}],
        crs='EPSG:4326'
    ).to_crs('EPSG:32612')
    
    # Plot census data
    if variable in census_df.columns:
        # Filter out invalid values
        valid_mask = pd.notna(census_df[variable]) & (census_df[variable] >= 0)
        plot_gdf = census_gdf[valid_mask]
        
        if len(plot_gdf) > 0:
            plot_gdf.plot(
                column=variable,
                ax=ax,
                legend=True,
                cmap='YlOrRd',
                edgecolor='black',
                linewidth=0.1,
                alpha=0.7,
                legend_kwds={
                    'label': get_variable_label(variable),
                    'orientation': 'vertical',
                    'shrink': 0.7
                }
            )
    
    # Plot isochrone boundary
    if isochrone_gdf is not None and not isochrone_gdf.empty:
        isochrone_gdf.boundary.plot(
            ax=ax,
            color='darkblue',
            linewidth=2,
            alpha=0.8,
            label=f'{travel_time}-minute drive'
        )
    
    # Plot mill location
    mill_point.plot(
        ax=ax,
        color='red',
        markersize=200,
        marker='*',
        edgecolor='black',
        linewidth=1,
        label='Mill Location',
        zorder=5
    )
    
    # Add labels for context
    ax.set_xlabel('Easting (m)', fontsize=10)
    ax.set_ylabel('Northing (m)', fontsize=10)
    
    # Title
    var_name = get_variable_label(variable)
    title = f"{var_name} within {travel_time}-minute Drive{title_suffix}"
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    # Add legend
    if isochrone_gdf is not None:
        handles = [
            plt.scatter([], [], color='red', marker='*', s=200, edgecolor='black', label='Mill Location'),
            plt.Line2D([0], [0], color='darkblue', linewidth=2, label=f'{travel_time}-min drive boundary')
        ]
        ax.legend(handles=handles, loc='upper right', frameon=True, fancybox=True, shadow=True)
    
    # Add statistics box
    stats_text = generate_stats_text(census_df, variable)
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
            verticalalignment='top', fontsize=9,
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Grid
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig, ax


def create_comparison_plot(results_list):
    """Create a comparison plot of multiple travel times."""
    
    fig, axes = plt.subplots(1, len(results_list), figsize=(6*len(results_list), 8))
    if len(results_list) == 1:
        axes = [axes]
    
    variable = "B01003_001E"  # Total population
    
    for idx, result in enumerate(results_list):
        ax = axes[idx]
        
        # Load data
        census_df = load_census_data(result['census_file'])
        isochrone_gdf = load_isochrone_data(result['isochrone_file'])
        
        # Convert to GeoDataFrame
        from shapely import wkt
        census_df['geometry'] = census_df['centroid'].apply(wkt.loads)
        census_gdf = gpd.GeoDataFrame(census_df, geometry='geometry', crs='EPSG:4326')
        census_gdf = census_gdf.to_crs('EPSG:32612')
        
        if isochrone_gdf is not None:
            isochrone_gdf = isochrone_gdf.to_crs('EPSG:32612')
        
        # Plot
        valid_mask = pd.notna(census_df[variable]) & (census_df[variable] >= 0)
        plot_gdf = census_gdf[valid_mask]
        
        if len(plot_gdf) > 0:
            plot_gdf.plot(
                column=variable,
                ax=ax,
                legend=False,
                cmap='YlOrRd',
                edgecolor='gray',
                linewidth=0.1,
                alpha=0.7
            )
        
        if isochrone_gdf is not None:
            isochrone_gdf.boundary.plot(ax=ax, color='darkblue', linewidth=2)
        
        # Mill location
        mill_lon = census_df['poi_lon'].iloc[0]
        mill_lat = census_df['poi_lat'].iloc[0]
        mill_point = gpd.GeoDataFrame(
            [{'geometry': gpd.points_from_xy([mill_lon], [mill_lat])[0]}],
            crs='EPSG:4326'
        ).to_crs('EPSG:32612')
        mill_point.plot(ax=ax, color='red', markersize=150, marker='*', edgecolor='black')
        
        # Title and stats
        total_pop = census_df[variable].sum()
        ax.set_title(f"{result['travel_time']} Minutes\nPop: {total_pop:,}", fontsize=12)
        ax.set_aspect('equal')
        ax.set_xticks([])
        ax.set_yticks([])
    
    fig.suptitle("Montana Timber Mill - Workforce Catchment Comparison", fontsize=16, y=1.02)
    plt.tight_layout()
    return fig


def generate_stats_text(census_df, variable):
    """Generate statistics text for the plot."""
    valid_data = census_df[census_df[variable].notna()][variable]
    
    if len(valid_data) == 0:
        return "No valid data"
    
    stats = f"Statistics:\n"
    stats += f"Census Units: {len(census_df)}\n"
    stats += f"Total {get_variable_label(variable)}: {valid_data.sum():,.0f}\n"
    stats += f"Average: {valid_data.mean():,.0f}\n"
    stats += f"Median: {valid_data.median():,.0f}"
    
    return stats


def get_variable_label(variable_code):
    """Get human-readable label for census variable."""
    labels = {
        "B01003_001E": "Population",
        "B19013_001E": "Median Income",
        "B01002_001E": "Median Age",
        "B11001_001E": "Households",
        "B25001_001E": "Housing Units",
        "B15003_022E": "Bachelor's Degree+",
        "B17001_002E": "Below Poverty"
    }
    return labels.get(variable_code, variable_code)


def create_folium_map(census_df, isochrone_gdf=None, travel_time=None):
    """Create an interactive Folium map."""
    try:
        import folium
        from folium import plugins
    except ImportError:
        console.print("[red]Folium not installed. Run: pip install folium[/red]")
        return None
    
    # Get mill location
    mill_lat = census_df['poi_lat'].iloc[0]
    mill_lon = census_df['poi_lon'].iloc[0]
    
    # Create map centered on mill
    m = folium.Map(location=[mill_lat, mill_lon], zoom_start=9)
    
    # Add mill marker
    folium.Marker(
        [mill_lat, mill_lon],
        popup="Montana Timber Mill Site",
        tooltip="Proposed Mill Location",
        icon=folium.Icon(color='red', icon='industry', prefix='fa')
    ).add_to(m)
    
    # Add isochrone if available
    if isochrone_gdf is not None and not isochrone_gdf.empty:
        # Ensure it's in WGS84
        iso_wgs84 = isochrone_gdf.to_crs('EPSG:4326')
        
        folium.GeoJson(
            iso_wgs84.to_json(),
            name=f'{travel_time}-minute drive area',
            style_function=lambda x: {
                'fillColor': '#3388ff',
                'color': '#0066cc',
                'weight': 2,
                'fillOpacity': 0.2
            }
        ).add_to(m)
    
    # Add census data as circle markers
    from shapely import wkt
    census_df['geometry'] = census_df['centroid'].apply(wkt.loads)
    
    # Create population circles
    for idx, row in census_df.iterrows():
        if pd.notna(row['B01003_001E']) and row['B01003_001E'] > 0:
            # Scale circle size by population
            radius = np.sqrt(row['B01003_001E']) * 50  # Adjust multiplier as needed
            
            folium.CircleMarker(
                location=[row.geometry.y, row.geometry.x],
                radius=radius,
                popup=f"Population: {row['B01003_001E']:,.0f}<br>"
                      f"Median Income: ${row.get('B19013_001E', 'N/A'):,.0f}<br>"
                      f"Distance: {row['travel_distance_km']:.1f} km",
                color='orange',
                fill=True,
                fillColor='orange',
                fillOpacity=0.6,
                weight=1
            ).add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Add fullscreen button
    plugins.Fullscreen().add_to(m)
    
    return m


def main():
    """Main function to run the visualization."""
    
    console.print("[bold blue]Montana Timber Mill Results Visualizer[/bold blue]\n")
    console.print("This tool visualizes already-generated analysis results")
    console.print("without re-running the time-consuming analysis pipeline.\n")
    
    # Find available results
    results = find_analysis_results()
    
    if not results:
        console.print("[red]No Montana mill analysis results found in output directory![/red]")
        console.print("\nPlease run one of the analysis scripts first:")
        console.print("- ./montana_mill_quick_demo.py")
        console.print("- ./montana_timber_mill_analysis.py")
        return
    
    # Display available results
    table = Table(title="Available Analysis Results")
    table.add_column("Index", style="cyan")
    table.add_column("Travel Time", style="green")
    table.add_column("Census Data", style="yellow")
    table.add_column("Isochrone", style="magenta")
    table.add_column("Location", style="white")
    
    for idx, result in enumerate(results):
        location = result.get('subdir', 'main output')
        table.add_row(
            str(idx + 1),
            f"{result['travel_time']} minutes",
            "✓",
            "✓" if result['has_isochrone'] else "✗",
            location
        )
    
    console.print(table)
    
    # Get user choice
    console.print("\n[bold]Visualization Options:[/bold]")
    console.print("1. Visualize single analysis")
    console.print("2. Compare multiple travel times")
    console.print("3. Create interactive map (requires folium)")
    console.print("4. Export all as images")
    console.print("5. Exit")
    
    choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5"], default="1")
    
    if choice == "5":
        console.print("Exiting...")
        return
    
    elif choice == "1":
        # Single visualization
        idx = int(Prompt.ask("Select analysis index", default="1")) - 1
        if 0 <= idx < len(results):
            result = results[idx]
            
            # Load data
            census_df = load_census_data(result['census_file'])
            isochrone_gdf = load_isochrone_data(result['isochrone_file'])
            
            # Choose variable
            available_vars = [col for col in census_df.columns if col.startswith('B') and col.endswith('E')]
            console.print(f"\nAvailable variables: {', '.join(available_vars)}")
            variable = Prompt.ask("Select variable to visualize", default="B01003_001E")
            
            # Create visualization
            fig, ax = create_simple_visualization(
                census_df, isochrone_gdf, result['travel_time'], variable
            )
            
            plt.show()
            
            if Confirm.ask("Save figure?"):
                filename = f"montana_mill_{result['travel_time']}min_{variable}.png"
                fig.savefig(filename, dpi=150, bbox_inches='tight')
                console.print(f"[green]Saved to {filename}[/green]")
    
    elif choice == "2":
        # Comparison
        selected = []
        console.print("\nSelect travel times to compare (enter indices separated by commas):")
        indices = Prompt.ask("Indices", default="1,2,3")
        
        for idx_str in indices.split(','):
            idx = int(idx_str.strip()) - 1
            if 0 <= idx < len(results):
                selected.append(results[idx])
        
        if selected:
            fig = create_comparison_plot(selected)
            plt.show()
            
            if Confirm.ask("Save comparison figure?"):
                filename = "montana_mill_comparison.png"
                fig.savefig(filename, dpi=150, bbox_inches='tight')
                console.print(f"[green]Saved to {filename}[/green]")
    
    elif choice == "3":
        # Interactive map
        idx = int(Prompt.ask("Select analysis index for interactive map", default="1")) - 1
        if 0 <= idx < len(results):
            result = results[idx]
            
            census_df = load_census_data(result['census_file'])
            isochrone_gdf = load_isochrone_data(result['isochrone_file'])
            
            m = create_folium_map(census_df, isochrone_gdf, result['travel_time'])
            
            if m:
                filename = f"montana_mill_{result['travel_time']}min_interactive.html"
                m.save(filename)
                console.print(f"[green]Interactive map saved to {filename}[/green]")
                console.print("Open this file in a web browser to view.")
    
    elif choice == "4":
        # Export all
        output_dir = Path("montana_mill_visualizations")
        output_dir.mkdir(exist_ok=True)
        
        for result in results:
            console.print(f"\nProcessing {result['travel_time']}-minute analysis...")
            
            census_df = load_census_data(result['census_file'])
            isochrone_gdf = load_isochrone_data(result['isochrone_file'])
            
            # Create population map
            fig, ax = create_simple_visualization(
                census_df, isochrone_gdf, result['travel_time'], "B01003_001E"
            )
            
            filename = output_dir / f"montana_mill_{result['travel_time']}min_population.png"
            fig.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            console.print(f"[green]Saved {filename}[/green]")
        
        console.print(f"\n[green]All visualizations saved to {output_dir}/[/green]")


if __name__ == "__main__":
    main()