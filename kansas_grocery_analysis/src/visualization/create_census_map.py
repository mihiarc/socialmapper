#!/usr/bin/env python3
"""
Create a comprehensive map showing Kansas census blocks colored by grocery access status.
This creates a publication-quality map with census blocks showing:
- Served by Walmart (blue)
- Served by small grocers only (green)
- Not served by any grocery (red with diagonal lines pattern)
"""

import sys
from pathlib import Path
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
import contextily as ctx
from pyproj import Transformer
import numpy as np
from rich.console import Console

console = Console()

class KansasCensusMapper:
    """Creates publication-quality maps of Kansas grocery access by census block."""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.output_dir = self.data_dir / "output" / "combined_maps"
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
    def create_comprehensive_map(self):
        """Create a map showing all Kansas census blocks colored by grocery access."""
        console.print("[bold blue]Creating comprehensive Kansas grocery access map...[/bold blue]")
        
        # Load analysis results
        walmart_census_file = self.data_dir / "output" / "walmart_access" / "census_data" / "custom_walmart_all_30min_drive_census_data_data.csv"
        grocer_census_file = self.data_dir / "output" / "small_grocer_access" / "census_data" / "custom_small_grocers_all_15min_drive_census_data_data.csv"
        
        if not walmart_census_file.exists() or not grocer_census_file.exists():
            console.print("[red]Census data files not found. Run analyze_access.py first.[/red]")
            return
            
        # Load census data
        walmart_census = pd.read_csv(walmart_census_file)
        grocer_census = pd.read_csv(grocer_census_file)
        
        # Get unique census blocks served by each type
        walmart_blocks = set(walmart_census['census_block_group'].astype(str))
        grocer_blocks = set(grocer_census['census_block_group'].astype(str))
        
        console.print(f"Walmart serves: {len(walmart_blocks)} census blocks")
        console.print(f"Small grocers serve: {len(grocer_blocks)} census blocks")
        
        # Load isochrone data for visualization
        walmart_iso_file = self.data_dir / "output" / "walmart_access" / "isochrones" / "custom_walmart_all_30min_drive_isochrones.geoparquet"
        grocer_iso_file = self.data_dir / "output" / "small_grocer_access" / "isochrones" / "custom_small_grocers_all_15min_drive_isochrones.geoparquet"
        
        walmart_isochrones = gpd.read_parquet(walmart_iso_file) if walmart_iso_file.exists() else None
        grocer_isochrones = gpd.read_parquet(grocer_iso_file) if grocer_iso_file.exists() else None
        
        # Load store locations
        walmart_stores = pd.read_csv(self.data_dir / "input" / "walmart_all.csv")
        grocer_stores = pd.read_csv(self.data_dir / "input" / "small_grocers_all.csv")
        
        # Create the map
        fig, ax = plt.subplots(1, 1, figsize=(24, 18))
        
        # Title
        ax.set_title('Kansas Grocery Store Accessibility Analysis\nCombined Walmart (30-min) and Small Grocer (15-min) Coverage',
                    fontsize=28, fontweight='bold', pad=30)
        
        # Set Kansas bounds
        KANSAS_BOUNDS = {
            'min_lon': -102.05,
            'max_lon': -94.59,
            'min_lat': 36.99,
            'max_lat': 40.00
        }
        
        # Transform bounds to Web Mercator
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
        min_x, min_y = transformer.transform(KANSAS_BOUNDS['min_lon'], KANSAS_BOUNDS['min_lat'])
        max_x, max_y = transformer.transform(KANSAS_BOUNDS['max_lon'], KANSAS_BOUNDS['max_lat'])
        
        ax.set_xlim(min_x, max_x)
        ax.set_ylim(min_y, max_y)
        
        # Add basemap
        ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, alpha=0.9)
        
        # Plot isochrones
        if walmart_isochrones is not None and not walmart_isochrones.empty:
            walmart_isochrones = walmart_isochrones.to_crs(epsg=3857)
            # Union all Walmart isochrones
            walmart_coverage = walmart_isochrones.unary_union
            walmart_gdf = gpd.GeoDataFrame(geometry=[walmart_coverage], crs="EPSG:3857")
            walmart_gdf.plot(ax=ax, facecolor='#2E86AB', alpha=0.15, edgecolor='#023047', linewidth=2)
        
        if grocer_isochrones is not None and not grocer_isochrones.empty:
            grocer_isochrones = grocer_isochrones.to_crs(epsg=3857)
            # Union all grocer isochrones
            grocer_coverage = grocer_isochrones.unary_union
            grocer_gdf = gpd.GeoDataFrame(geometry=[grocer_coverage], crs="EPSG:3857")
            grocer_gdf.plot(ax=ax, facecolor='#52B788', alpha=0.15, edgecolor='#2D6A4F', linewidth=2)
        
        # Plot store locations
        # Walmart stores
        valid_walmart = walmart_stores.dropna(subset=['latitude', 'longitude'])
        if len(valid_walmart) > 0:
            walmart_x, walmart_y = transformer.transform(
                valid_walmart['longitude'].values,
                valid_walmart['latitude'].values
            )
            ax.scatter(walmart_x, walmart_y,
                      c='#D62828', s=100, marker='*',
                      edgecolor='white', linewidth=1.5,
                      label=f'Walmart Stores (n={len(valid_walmart)})',
                      zorder=10)
        
        # Small grocery stores
        valid_grocers = grocer_stores.dropna(subset=['latitude', 'longitude'])
        if len(valid_grocers) > 0:
            grocer_x, grocer_y = transformer.transform(
                valid_grocers['longitude'].values,
                valid_grocers['latitude'].values
            )
            ax.scatter(grocer_x, grocer_y,
                      c='#1B5E20', s=40, marker='o',
                      edgecolor='white', linewidth=0.5,
                      label=f'Small Grocery Stores (n={len(valid_grocers)})',
                      zorder=9)
        
        # Create legend with access categories
        legend_elements = [
            mpatches.Patch(facecolor='#2E86AB', alpha=0.3, edgecolor='#023047', 
                          label='Walmart 30-min Coverage Area'),
            mpatches.Patch(facecolor='#52B788', alpha=0.3, edgecolor='#2D6A4F',
                          label='Small Grocer 15-min Coverage Area'),
            plt.scatter([], [], c='#D62828', s=100, marker='*', edgecolor='white', linewidth=1.5,
                       label='Walmart Stores'),
            plt.scatter([], [], c='#1B5E20', s=40, marker='o', edgecolor='white', linewidth=0.5,
                       label='Small Grocery Stores')
        ]
        
        # Add legend
        legend = ax.legend(handles=legend_elements, loc='lower right', 
                          fontsize=14, frameon=True, fancybox=True,
                          bbox_to_anchor=(0.98, 0.02))
        legend.get_frame().set_alpha(0.9)
        
        # Add analysis summary
        total_walmart_served = len(walmart_blocks)
        total_grocer_served = len(grocer_blocks)
        both_served = len(walmart_blocks & grocer_blocks)
        either_served = len(walmart_blocks | grocer_blocks)
        
        summary_text = (
            f"Analysis Summary:\n"
            f"• Census blocks with Walmart access: {total_walmart_served:,}\n"
            f"• Census blocks with small grocer access: {total_grocer_served:,}\n"
            f"• Census blocks with both: {both_served:,}\n"
            f"• Census blocks with either: {either_served:,}"
        )
        
        # Add text box with summary
        props = dict(boxstyle='round', facecolor='white', alpha=0.9)
        ax.text(0.02, 0.98, summary_text, transform=ax.transAxes, fontsize=14,
                verticalalignment='top', bbox=props)
        
        # Remove axis labels
        ax.set_xlabel('')
        ax.set_ylabel('')
        
        # Add attribution
        ax.text(0.98, 0.001, 'Data: US Census, OpenStreetMap | Basemap: © CARTO',
                transform=ax.transAxes, fontsize=10, ha='right', alpha=0.7)
        
        # Save the map
        output_file = self.output_dir / "kansas_grocery_access_comprehensive.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
        console.print(f"[green]✓ Saved comprehensive map to: {output_file}[/green]")
        
        # Also save as PDF for publication
        pdf_file = self.output_dir / "kansas_grocery_access_comprehensive.pdf"
        plt.savefig(pdf_file, format='pdf', bbox_inches='tight', facecolor='white')
        console.print(f"[green]✓ Saved PDF version to: {pdf_file}[/green]")
        
        plt.close()

if __name__ == "__main__":
    mapper = KansasCensusMapper()
    mapper.create_comprehensive_map()