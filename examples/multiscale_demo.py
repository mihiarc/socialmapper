#!/usr/bin/env python3
"""
Multi-Scale Community Detection Demo (Modified)

This script has been modified to remove dependencies on the removed community module.
Note: Multi-scale community detection features have been removed.

This demo now shows a simple building analysis instead.
"""

import sys
import os
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def generate_complex_urban_area(n_buildings: int = 500) -> gpd.GeoDataFrame:
    """
    Generate a complex synthetic urban area with multiple scales of development.
    """
    print(f"🏗️ Generating complex urban area with {n_buildings} buildings...")
    
    buildings = []
    np.random.seed(42)
    
    # Dense downtown core (micro-scale: individual building clusters)
    for i in range(100):
        x = 5000 + np.random.normal(0, 200)
        y = 5000 + np.random.normal(0, 200)
        size = np.random.normal(80, 20)  # Small, dense buildings
        building = Point(x, y).buffer(size/2)
        buildings.append({
            'geometry': building,
            'building_type': 'dense_urban',
            'area': building.area
        })
    
    # Suburban neighborhoods (neighborhood-scale: planned communities)
    # Neighborhood 1
    for i in range(150):
        base_x, base_y = 3000, 3000
        x = base_x + (i % 15) * 120 + np.random.normal(0, 15)
        y = base_y + (i // 15) * 100 + np.random.normal(0, 10)
        size = np.random.normal(150, 25)
        building = Point(x, y).buffer(size/2)
        buildings.append({
            'geometry': building,
            'building_type': 'suburban_neighborhood_1',
            'area': building.area
        })
    
    # Neighborhood 2
    for i in range(120):
        base_x, base_y = 7000, 3000
        x = base_x + (i % 12) * 130 + np.random.normal(0, 20)
        y = base_y + (i // 12) * 110 + np.random.normal(0, 15)
        size = np.random.normal(160, 30)
        building = Point(x, y).buffer(size/2)
        buildings.append({
            'geometry': building,
            'building_type': 'suburban_neighborhood_2',
            'area': building.area
        })
    
    # Rural/scattered development (macro-scale: individual large lots)
    for i in range(80):
        x = np.random.uniform(1000, 9000)
        y = np.random.uniform(1000, 9000)
        # Avoid overlapping with dense areas
        if not (4500 <= x <= 5500 and 4500 <= y <= 5500):
            size = np.random.normal(200, 50)
            building = Point(x, y).buffer(size/2)
            buildings.append({
                'geometry': building,
                'building_type': 'rural_scattered',
                'area': building.area
            })
    
    # Industrial district (district-scale)
    for i in range(50):
        base_x, base_y = 8000, 7000
        x = base_x + np.random.uniform(-400, 400)
        y = base_y + np.random.uniform(-300, 300)
        size = np.random.normal(300, 80)  # Large industrial buildings
        building = Point(x, y).buffer(size/2)
        buildings.append({
            'geometry': building,
            'building_type': 'industrial',
            'area': building.area
        })
    
    buildings_gdf = gpd.GeoDataFrame(buildings, crs='EPSG:3857')
    print(f"✅ Generated {len(buildings_gdf)} buildings across multiple scales")
    
    return buildings_gdf


def visualize_building_types(buildings_gdf):
    """Create visualization of building types."""
    print("\n📊 Creating building type visualization...")
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    fig.suptitle('Urban Area Building Analysis', fontsize=16, fontweight='bold')
    
    # Define colors for each building type
    colors = {
        'dense_urban': '#FF6B6B',
        'suburban_neighborhood_1': '#4ECDC4',
        'suburban_neighborhood_2': '#45B7D1',
        'rural_scattered': '#96CEB4',
        'industrial': '#9C88FF'
    }
    
    # Plot each building type with its color
    for building_type, color in colors.items():
        buildings = buildings_gdf[buildings_gdf['building_type'] == building_type]
        if len(buildings) > 0:
            buildings.plot(ax=ax, color=color, alpha=0.8, label=building_type.replace('_', ' ').title())
    
    ax.set_title('Building Distribution by Type', fontweight='bold')
    ax.set_axis_off()
    ax.legend()
    
    plt.tight_layout()
    plt.savefig('building_type_analysis.png', dpi=300, bbox_inches='tight')
    print("💾 Saved building type visualization to building_type_analysis.png")
    
    return fig


def analyze_building_statistics(buildings_gdf):
    """Analyze and display building statistics."""
    print("\n📊 Building Statistics:")
    print("=" * 40)
    
    # Group by building type
    stats = buildings_gdf.groupby('building_type').agg({
        'area': ['count', 'mean', 'std', 'min', 'max']
    }).round(2)
    
    print(stats)
    
    # Overall statistics
    print(f"\n🏢 Total Buildings: {len(buildings_gdf)}")
    print(f"📐 Total Area: {buildings_gdf['area'].sum():,.0f} sq units")
    print(f"📏 Average Building Size: {buildings_gdf['area'].mean():.2f} sq units")
    
    # Building type distribution
    print("\n🏘️ Building Type Distribution:")
    type_counts = buildings_gdf['building_type'].value_counts()
    for building_type, count in type_counts.items():
        percentage = (count / len(buildings_gdf)) * 100
        print(f"   • {building_type.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")


def main():
    """
    Demonstrate building analysis without community detection.
    """
    print("🔬 Urban Building Analysis Demo")
    print("=" * 45)
    print("⚠️  Note: Multi-scale community detection features have been removed.")
    print("    This demo now shows building type analysis instead.\n")
    
    # Generate complex urban data
    buildings_gdf = generate_complex_urban_area()
    
    # Analyze building statistics
    analyze_building_statistics(buildings_gdf)
    
    # Create visualization
    visualize_building_types(buildings_gdf)
    
    # Export results
    print("\n💾 Exporting results...")
    buildings_gdf.to_file("output/buildings_by_type.geojson", driver="GeoJSON")
    print("   • Buildings saved to: output/buildings_by_type.geojson")
    
    print("\n🎉 Analysis Complete!")
    print("\n🔗 Key Insights:")
    print("   • Different building types show different spatial patterns")
    print("   • Dense urban areas have smaller, closely packed buildings")
    print("   • Suburban areas show regular grid patterns")
    print("   • Rural areas have larger, scattered buildings")
    print("   • Industrial areas cluster together")
    
    print("\n💡 Alternative Approaches for Community Detection:")
    print("   • Use external clustering libraries (scikit-learn, HDBSCAN)")
    print("   • Apply graph-based community detection algorithms")
    print("   • Use QGIS or ArcGIS for spatial analysis")
    print("   • Implement custom clustering based on your specific needs")


if __name__ == "__main__":
    main()