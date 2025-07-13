#!/usr/bin/env python3
"""
Visualize the actual isochrones from the full analysis to identify truly small ones.
"""

import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path
from rich.console import Console
import pandas as pd
import contextily as ctx
from pyproj import Transformer

console = Console()

def visualize_all_isochrones():
    """Load and visualize all Walmart isochrones to identify the small ones."""
    
    data_dir = Path(__file__).parent.parent / "data"
    
    # Load the full isochrone file from the main analysis
    iso_file = data_dir / "output" / "walmart_access" / "isochrones" / "custom_walmart_cleaned_30min_drive_isochrones.geoparquet"
    
    if not iso_file.exists():
        # Try the original file name
        iso_file = data_dir / "output" / "walmart_access" / "isochrones" / "custom_walmart_all_30min_drive_isochrones.geoparquet"
    
    if not iso_file.exists():
        console.print("[red]No isochrone file found. Run analyze_access.py first.[/red]")
        return
    
    console.print(f"[cyan]Loading isochrones from: {iso_file}[/cyan]")
    
    # Load isochrones
    isochrones_gdf = gpd.read_parquet(iso_file)
    isochrones_gdf = isochrones_gdf.to_crs(epsg=3857)  # Web Mercator
    
    # Calculate area for each isochrone
    isochrones_gdf['area_km2'] = isochrones_gdf.geometry.area / 1_000_000
    
    # Get statistics
    console.print(f"\n[bold]Isochrone Statistics:[/bold]")
    console.print(f"Total isochrones: {len(isochrones_gdf)}")
    console.print(f"Mean area: {isochrones_gdf['area_km2'].mean():.1f} km²")
    console.print(f"Median area: {isochrones_gdf['area_km2'].median():.1f} km²")
    console.print(f"Min area: {isochrones_gdf['area_km2'].min():.1f} km²")
    console.print(f"Max area: {isochrones_gdf['area_km2'].max():.1f} km²")
    
    # Identify small isochrones (less than 100 km²)
    small_threshold = 100
    small_isochrones = isochrones_gdf[isochrones_gdf['area_km2'] < small_threshold]
    
    console.print(f"\n[yellow]Found {len(small_isochrones)} isochrones smaller than {small_threshold} km²[/yellow]")
    
    if len(small_isochrones) > 0:
        console.print("\n[bold]Small isochrones:[/bold]")
        for idx, row in small_isochrones.iterrows():
            console.print(f"  • Index {idx}: {row['area_km2']:.2f} km²")
            if 'poi_name' in row:
                console.print(f"    POI: {row['poi_name']}")
    
    # Create visualization
    fig, ax = plt.subplots(1, 1, figsize=(20, 16))
    
    # Plot all isochrones with color gradient based on size
    isochrones_gdf.plot(
        column='area_km2',
        cmap='RdYlGn',  # Red for small, green for large
        ax=ax,
        alpha=0.6,
        edgecolor='black',
        linewidth=0.5,
        legend=True,
        legend_kwds={'label': 'Area (km²)', 'orientation': 'horizontal', 'shrink': 0.8}
    )
    
    # Highlight very small isochrones
    if len(small_isochrones) > 0:
        small_isochrones.plot(
            ax=ax,
            facecolor='none',
            edgecolor='red',
            linewidth=3,
            alpha=1.0
        )
        
        # Add labels for small isochrones
        for idx, row in small_isochrones.iterrows():
            centroid = row.geometry.centroid
            ax.annotate(
                f"{idx}: {row['area_km2']:.0f} km²",
                xy=(centroid.x, centroid.y),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=10,
                color='red',
                weight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8)
            )
    
    # Set title
    ax.set_title('Kansas Walmart Isochrone Analysis\nColor indicates area size (red=small, green=large)',
                fontsize=20, fontweight='bold', pad=20)
    
    # Add basemap
    ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, alpha=0.8)
    
    # Remove axes
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Save figure
    output_file = data_dir / "output" / "walmart_isochrone_size_analysis.png"
    plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
    console.print(f"\n[green]✓ Saved visualization to: {output_file}[/green]")
    plt.close()
    
    # Also create a focused view of just the problematic areas
    if len(small_isochrones) > 0:
        fig2, ax2 = plt.subplots(1, 1, figsize=(12, 10))
        
        # Get bounds of small isochrones
        bounds = small_isochrones.total_bounds
        x_pad = (bounds[2] - bounds[0]) * 0.2
        y_pad = (bounds[3] - bounds[1]) * 0.2
        
        ax2.set_xlim(bounds[0] - x_pad, bounds[2] + x_pad)
        ax2.set_ylim(bounds[1] - y_pad, bounds[3] + y_pad)
        
        # Plot small isochrones
        small_isochrones.plot(
            ax=ax2,
            facecolor='red',
            alpha=0.5,
            edgecolor='darkred',
            linewidth=2
        )
        
        # Add basemap
        ctx.add_basemap(ax2, source=ctx.providers.CartoDB.Positron)
        
        ax2.set_title(f'Close-up of {len(small_isochrones)} Problematic Small Isochrones',
                     fontsize=16, fontweight='bold')
        
        # Save focused view
        output_file2 = data_dir / "output" / "walmart_small_isochrones_closeup.png"
        plt.savefig(output_file2, dpi=150, bbox_inches='tight')
        console.print(f"[green]✓ Saved closeup to: {output_file2}[/green]")
        plt.close()

if __name__ == "__main__":
    visualize_all_isochrones()