#!/usr/bin/env python3
"""
NC Suburban Housing Development Test (Modified)

This script demonstrates building analysis using OpenStreetMap data.
Note: Community detection features have been removed from this version.

Test Area: Suburban housing development in North Carolina
Bounds: (-78.755873, 35.568584, -78.732969, 35.585022)

Run with: python examples/test_nc_suburban_full_pipeline.py
"""

import sys
import os
from pathlib import Path
import warnings

# Add socialmapper to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import box
import osmnx as ox

warnings.filterwarnings('ignore')

# NC Suburban Study Area
STUDY_BOUNDS = (-78.755873, 35.568584, -78.732969, 35.585022)  # minx, miny, maxx, maxy
STUDY_AREA_NAME = "NC Suburban Housing Development"

def setup_output_directory():
    """Create output directory for results."""
    output_dir = Path("./output/nc_suburban_analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    (output_dir / "maps").mkdir(exist_ok=True)
    (output_dir / "data").mkdir(exist_ok=True)
    (output_dir / "reports").mkdir(exist_ok=True)
    
    print(f"📁 Output directory: {output_dir}")
    return output_dir


def download_osm_data():
    """Download building and road data from OpenStreetMap."""
    print("🌍 Downloading OpenStreetMap data...")
    
    try:
        # Create bounding box
        north, south, east, west = STUDY_BOUNDS[3], STUDY_BOUNDS[1], STUDY_BOUNDS[2], STUDY_BOUNDS[0]
        
        # Download buildings
        print("   📦 Downloading building footprints...")
        buildings_gdf = ox.features_from_bbox(
            north=north, south=south, east=east, west=west,
            tags={'building': True}
        )
        
        # Clean and prepare buildings data
        if 'geometry' in buildings_gdf.columns:
            buildings_gdf = buildings_gdf[['geometry']].reset_index(drop=True)
            buildings_gdf = buildings_gdf[buildings_gdf.geometry.notna()]
            buildings_gdf = buildings_gdf[buildings_gdf.geometry.is_valid]
            
        print(f"   ✅ Downloaded {len(buildings_gdf)} building footprints")
        
        # Download roads
        print("   🛣️ Downloading road network...")
        try:
            roads_gdf = ox.features_from_bbox(
                north=north, south=south, east=east, west=west,
                tags={'highway': True}
            )
            roads_gdf = roads_gdf[['geometry']].reset_index(drop=True)
            roads_gdf = roads_gdf[roads_gdf.geometry.notna()]
            print(f"   ✅ Downloaded {len(roads_gdf)} road segments")
        except Exception as e:
            print(f"   ⚠️ Could not download roads: {e}")
            roads_gdf = None
        
        return buildings_gdf, roads_gdf
        
    except Exception as e:
        print(f"   ❌ Error downloading OSM data: {e}")
        return None, None


def create_simple_visualization(buildings_gdf, roads_gdf=None, output_dir=None):
    """Create a simple visualization of the downloaded data."""
    print("\n📊 Creating visualization...")
    
    try:
        # Create figure
        fig, ax = plt.subplots(1, 1, figsize=(12, 10))
        fig.suptitle(f'Building Analysis: {STUDY_AREA_NAME}', fontsize=16, fontweight='bold')
        
        # Plot buildings
        buildings_gdf.plot(ax=ax, color='lightblue', alpha=0.7, edgecolor='darkblue', linewidth=0.5)
        
        # Plot roads if available
        if roads_gdf is not None:
            roads_gdf.plot(ax=ax, color='gray', alpha=0.5, linewidth=1)
        
        ax.set_title(f'Building Footprints ({len(buildings_gdf)} buildings)', fontweight='bold')
        ax.set_axis_off()
        
        plt.tight_layout()
        
        # Save the visualization
        if output_dir:
            viz_path = output_dir / "maps" / "building_analysis.png"
            plt.savefig(viz_path, dpi=300, bbox_inches='tight')
            print(f"   💾 Saved visualization: {viz_path}")
        
        plt.show()
        
        return fig
        
    except Exception as e:
        print(f"   ❌ Error creating visualization: {e}")
        import traceback
        traceback.print_exc()
        return None


def export_results(buildings_gdf, roads_gdf, output_dir):
    """Export results to various formats."""
    print("\n💾 Exporting results...")
    
    try:
        data_dir = output_dir / "data"
        
        # Export buildings data
        if buildings_gdf is not None:
            buildings_gdf.to_file(data_dir / "buildings.shp")
            buildings_gdf.to_file(data_dir / "buildings.geojson", driver="GeoJSON")
            print(f"   ✅ Exported building footprints")
        
        # Export roads data
        if roads_gdf is not None:
            roads_gdf.to_file(data_dir / "roads.shp")
            roads_gdf.to_file(data_dir / "roads.geojson", driver="GeoJSON")
            print(f"   ✅ Exported road network")
        
        # Create analysis report
        report_path = output_dir / "reports" / "analysis_report.md"
        with open(report_path, 'w') as f:
            f.write(f"# Building Analysis Report\n\n")
            f.write(f"**Study Area:** {STUDY_AREA_NAME}\n")
            f.write(f"**Bounds:** {STUDY_BOUNDS}\n")
            f.write(f"**Analysis Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"## Summary Statistics\n\n")
            f.write(f"- **Total Buildings:** {len(buildings_gdf) if buildings_gdf is not None else 0}\n")
            
            if roads_gdf is not None:
                f.write(f"- **Road Segments:** {len(roads_gdf)}\n")
        
        print(f"   ✅ Created analysis report: {report_path}")
        
        print(f"\n📁 All results exported to: {output_dir}")
        
    except Exception as e:
        print(f"   ❌ Error exporting results: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run the OpenStreetMap building analysis."""
    print("🚀 OpenStreetMap Building Analysis")
    print(f"🎯 Study Area: {STUDY_AREA_NAME}")
    print("=" * 60)
    
    # Setup output directory
    output_dir = setup_output_directory()
    
    # Download buildings from OSM
    print("🌍 Downloading building data from OpenStreetMap...")
    north, south, east, west = STUDY_BOUNDS[3], STUDY_BOUNDS[1], STUDY_BOUNDS[2], STUDY_BOUNDS[0]
    
    print(f"   📍 Bounding box: ({west:.6f}, {south:.6f}, {east:.6f}, {north:.6f})")
    area_km2 = (east - west) * (north - south) * 111 * 111  # Rough area calculation
    print(f"   📐 Approximate area: {area_km2:.2f} km²")
    print(f"   🏗️ Querying building features...")
    
    try:
        import time
        start_time = time.time()
        
        buildings_gdf = ox.features_from_bbox(
            bbox=(north, south, east, west),
            tags={'building': True}
        )
        
        download_time = time.time() - start_time
        print(f"   ⏱️ Download completed in {download_time:.1f} seconds")
        
        # Process the data
        print(f"   🔧 Processing building data...")
        original_count = len(buildings_gdf)
        
        buildings_gdf = buildings_gdf[['geometry']].reset_index(drop=True)
        buildings_gdf = buildings_gdf[buildings_gdf.geometry.notna()]
        buildings_gdf = buildings_gdf[buildings_gdf.geometry.is_valid]
        
        final_count = len(buildings_gdf)
        print(f"   📊 Raw features: {original_count}")
        print(f"   📊 Valid buildings: {final_count}")
        print(f"✅ Successfully downloaded {final_count} building footprints")
        
        if final_count == 0:
            print("⚠️ Warning: No valid buildings found in this area")
            return
            
    except Exception as e:
        print(f"❌ Error downloading buildings: {e}")
        print(f"   🔍 This could be due to:")
        print(f"      - Network connectivity issues")
        print(f"      - No building data available in OSM for this area")
        print(f"      - Invalid bounding box coordinates")
        print(f"      - OSM API temporary issues")
        return
    
    # Download roads for context
    roads_gdf = None
    try:
        print("\n🛣️ Downloading road network...")
        roads_gdf = ox.features_from_bbox(
            bbox=(north, south, east, west),
            tags={'highway': True}
        )
        roads_gdf = roads_gdf[['geometry']].reset_index(drop=True)
        roads_gdf = roads_gdf[roads_gdf.geometry.notna()]
        print(f"✅ Downloaded {len(roads_gdf)} road segments")
    except Exception as e:
        print(f"⚠️ Could not download roads: {e}")
    
    # Create visualization
    create_simple_visualization(buildings_gdf, roads_gdf, output_dir)
    
    # Export results
    export_results(buildings_gdf, roads_gdf, output_dir)
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 ANALYSIS COMPLETE!")
    print("=" * 60)
    
    print(f"✅ Buildings analyzed: {len(buildings_gdf)}")
    if roads_gdf is not None:
        print(f"✅ Roads downloaded: {len(roads_gdf)}")
    
    print(f"\n📁 Results saved to: {output_dir}")
    print("\n📝 Note: Community detection features have been removed from this version.")
    print("   This script now focuses on OpenStreetMap data visualization only.")


if __name__ == "__main__":
    main()