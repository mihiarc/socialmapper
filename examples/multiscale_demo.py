#!/usr/bin/env python3
"""
Multi-Scale Community Detection Demo

This demonstrates the advanced multi-scale analysis capabilities of the
AI-powered community detection system.
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

from socialmapper.community.multiscale_analysis import analyze_communities_multiscale


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


def main():
    """
    Demonstrate multi-scale community detection.
    """
    print("🔬 Multi-Scale AI Community Detection Demo")
    print("=" * 45)
    
    # Generate complex urban data
    buildings_gdf = generate_complex_urban_area()
    
    # Perform multi-scale analysis
    print("\n🤖 Performing multi-scale analysis...")
    multiscale_results = analyze_communities_multiscale(
        buildings_gdf,
        method='hierarchical',
        include_gnn=False  # Disable GNN for this demo
    )
    
    # Display results for each scale
    print("\n📊 Multi-Scale Analysis Results:")
    print("=" * 40)
    
    for scale_name, communities in multiscale_results.items():
        unique_communities = len(communities['cluster_id'].unique()) - 1  # Exclude noise
        outliers = len(communities[communities['cluster_id'] == -1])
        avg_size = communities.groupby('cluster_id').size().mean() if unique_communities > 0 else 0
        
        print(f"\n🔍 {scale_name.upper()} Scale:")
        print(f"   • Communities detected: {unique_communities}")
        print(f"   • Average community size: {avg_size:.1f} buildings")
        print(f"   • Outlier buildings: {outliers}")
        
        if 'scale_compactness' in communities.columns:
            avg_compactness = communities['scale_compactness'].mean()
            print(f"   • Average compactness: {avg_compactness:.2f}")
    
    # Create visualization
    print("\n📊 Creating multi-scale visualization...")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Multi-Scale Community Detection Results', fontsize=16, fontweight='bold')
    
    scale_names = list(multiscale_results.keys())
    
    for i, (scale_name, communities) in enumerate(multiscale_results.items()):
        if i >= 4:  # Only show first 4 scales
            break
            
        ax = axes[i // 2, i % 2]
        
        # Get unique clusters (excluding noise)
        unique_clusters = communities['cluster_id'].unique()
        unique_clusters = unique_clusters[unique_clusters != -1]
        
        if len(unique_clusters) > 0:
            # Create colormap
            colors = plt.cm.Set3(np.linspace(0, 1, len(unique_clusters)))
            color_map = dict(zip(unique_clusters, colors))
            color_map[-1] = 'lightgray'  # Noise points
            
            for cluster_id in unique_clusters:
                cluster_buildings = communities[communities['cluster_id'] == cluster_id]
                cluster_buildings.plot(ax=ax, color=color_map[cluster_id], alpha=0.8)
            
            # Plot noise points
            noise_buildings = communities[communities['cluster_id'] == -1]
            if len(noise_buildings) > 0:
                noise_buildings.plot(ax=ax, color='lightgray', alpha=0.5)
        else:
            # No clusters found
            communities.plot(ax=ax, color='lightgray', alpha=0.5)
        
        ax.set_title(f'{scale_name.title()} Scale\n({len(unique_clusters)} communities)', 
                    fontweight='bold')
        ax.set_axis_off()
    
    plt.tight_layout()
    plt.savefig('multiscale_analysis_results.png', dpi=300, bbox_inches='tight')
    print("💾 Saved multi-scale visualization to multiscale_analysis_results.png")
    
    # Export scale-specific results
    print("\n💾 Exporting scale-specific results...")
    for scale_name, communities in multiscale_results.items():
        filename = f"output/communities_{scale_name}_scale.geojson"
        communities.to_file(filename, driver="GeoJSON")
        print(f"   • {scale_name} scale: {filename}")
    
    print("\n🎉 Multi-Scale Analysis Complete!")
    print("\n🔗 Key Insights:")
    print("   • Different scales reveal different community patterns")
    print("   • Hierarchical analysis shows nested community structures")
    print("   • Each scale is useful for different planning applications:")
    print("     - Micro: Building-level interventions")
    print("     - Neighborhood: Local service planning") 
    print("     - District: Infrastructure development")
    print("     - Macro: Regional policy decisions")


if __name__ == "__main__":
    main() 