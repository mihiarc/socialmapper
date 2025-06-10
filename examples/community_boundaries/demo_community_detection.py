#!/usr/bin/env python3
"""
AI-Powered Community Boundary Detection Demo

This script demonstrates how to use machine learning and computer vision
to automatically detect organic community boundaries based on spatial patterns.

Example workflow:
1. Load building footprints from OpenStreetMap
2. Apply spatial clustering to detect housing patterns
3. (Optional) Analyze satellite imagery for land use classification
4. Generate community boundaries
5. Visualize and export results
"""

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import warnings
from pathlib import Path
import osmnx as ox
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

# Import our community detection modules
from socialmapper.community import discover_community_boundaries
from socialmapper.community.spatial_clustering import detect_housing_developments

warnings.filterwarnings('ignore')


def download_sample_data(place_name: str, buffer_distance: int = 1000) -> tuple:
    """
    Download sample data for a given place using OpenStreetMap.
    
    Args:
        place_name: Name of place to analyze (e.g., "Cambridge, MA, USA")
        buffer_distance: Buffer around place in meters
        
    Returns:
        Tuple of (buildings_gdf, roads_gdf, study_area)
    """
    print(f"🌍 Downloading data for {place_name}...")
    
    # Get the place boundary
    gdf_place = ox.geocode_to_gdf(place_name)
    study_area = gdf_place.iloc[0].geometry
    
    # Buffer the area slightly for context
    study_area_buffered = study_area.buffer(buffer_distance)
    
    # Download buildings
    print("🏠 Downloading building footprints...")
    buildings = ox.features_from_polygon(
        study_area_buffered, 
        tags={'building': True}
    )
    
    # Clean buildings data
    buildings_gdf = gpd.GeoDataFrame(buildings).reset_index()
    buildings_gdf = buildings_gdf[buildings_gdf.geometry.type.isin(['Polygon', 'MultiPolygon'])]
    buildings_gdf = buildings_gdf.to_crs('EPSG:3857')  # Project to meters
    
    # Download road network for context
    print("🛣️ Downloading road network...")
    try:
        roads = ox.features_from_polygon(
            study_area_buffered,
            tags={'highway': ['motorway', 'trunk', 'primary', 'secondary', 'tertiary']}
        )
        roads_gdf = gpd.GeoDataFrame(roads).reset_index()
        roads_gdf = roads_gdf.to_crs('EPSG:3857')
    except:
        print("⚠️ Could not download roads, continuing without them")
        roads_gdf = None
    
    print(f"✅ Downloaded {len(buildings_gdf)} buildings")
    
    return buildings_gdf, roads_gdf, study_area


def generate_synthetic_housing_development(n_buildings: int = 200) -> gpd.GeoDataFrame:
    """
    Generate synthetic housing development data for testing.
    Creates a realistic pattern with planned developments and scattered buildings.
    """
    print(f"🏗️ Generating synthetic housing development with {n_buildings} buildings...")
    
    buildings = []
    
    # Planned development 1: Grid pattern (suburban development)
    np.random.seed(42)
    for i in range(80):
        x = 1000 + (i % 10) * 100 + np.random.normal(0, 10)
        y = 1000 + (i // 10) * 80 + np.random.normal(0, 8)
        size = np.random.normal(150, 30)  # Uniform house sizes
        building = Point(x, y).buffer(size/2)
        buildings.append({
            'geometry': building,
            'building_type': 'planned_development',
            'area': building.area
        })
    
    # Planned development 2: Cluster pattern (dense residential)
    for i in range(60):
        angle = i * 2 * np.pi / 60
        radius = 200 + np.random.normal(0, 30)
        x = 2500 + radius * np.cos(angle)
        y = 1500 + radius * np.sin(angle)
        size = np.random.normal(100, 20)  # Smaller, denser houses
        building = Point(x, y).buffer(size/2)
        buildings.append({
            'geometry': building,
            'building_type': 'dense_residential',
            'area': building.area
        })
    
    # Scattered rural buildings
    for i in range(40):
        x = np.random.uniform(500, 3500)
        y = np.random.uniform(500, 2500)
        size = np.random.normal(200, 50)  # Larger, varied sizes
        building = Point(x, y).buffer(size/2)
        buildings.append({
            'geometry': building,
            'building_type': 'rural_residential',
            'area': building.area
        })
    
    # Mixed urban development
    for i in range(20):
        x = np.random.uniform(2000, 3000)
        y = np.random.uniform(2000, 2500)
        size = np.random.normal(120, 40)
        building = Point(x, y).buffer(size/2)
        buildings.append({
            'geometry': building,
            'building_type': 'mixed_urban',
            'area': building.area
        })
    
    buildings_gdf = gpd.GeoDataFrame(buildings, crs='EPSG:3857')
    print(f"✅ Generated {len(buildings_gdf)} synthetic buildings")
    
    return buildings_gdf


def analyze_community_patterns(buildings_gdf: gpd.GeoDataFrame, 
                             method: str = 'hdbscan') -> tuple:
    """
    Analyze building patterns to detect community boundaries.
    
    Args:
        buildings_gdf: GeoDataFrame with building footprints
        method: Clustering method ('hdbscan', 'dbscan', or 'spectral')
        
    Returns:
        Tuple of (clustered_buildings, community_boundaries)
    """
    print(f"🤖 Analyzing community patterns using {method}...")
    
    # Detect housing developments using spatial clustering
    clustered_buildings, boundaries = detect_housing_developments(
        buildings_gdf, 
        method=method,
        min_cluster_size=20,
        min_samples=5
    )
    
    # Calculate some statistics
    n_communities = len(boundaries)
    avg_buildings_per_community = len(clustered_buildings) / max(n_communities, 1)
    
    print(f"📊 Analysis Results:")
    print(f"   • {n_communities} communities detected")
    print(f"   • {avg_buildings_per_community:.1f} buildings per community (avg)")
    print(f"   • {len(clustered_buildings[clustered_buildings['cluster_id'] == -1])} outlier buildings")
    
    return clustered_buildings, boundaries


def create_visualizations(buildings_gdf: gpd.GeoDataFrame,
                         clustered_buildings: gpd.GeoDataFrame,
                         boundaries: gpd.GeoDataFrame,
                         roads_gdf: gpd.GeoDataFrame = None,
                         save_path: str = None):
    """
    Create comprehensive visualizations of the community detection results.
    """
    print("📊 Creating visualizations...")
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('AI-Powered Community Boundary Detection Results', fontsize=16, fontweight='bold')
    
    # 1. Original building footprints
    ax1 = axes[0, 0]
    buildings_gdf.plot(ax=ax1, color='lightblue', alpha=0.7, edgecolor='darkblue', linewidth=0.5)
    if roads_gdf is not None:
        roads_gdf.plot(ax=ax1, color='gray', alpha=0.5, linewidth=1)
    ax1.set_title('Original Building Footprints', fontweight='bold')
    ax1.set_axis_off()
    
    # 2. Clustered buildings with colors
    ax2 = axes[0, 1]
    
    # Get unique clusters (excluding noise)
    unique_clusters = clustered_buildings['cluster_id'].unique()
    unique_clusters = unique_clusters[unique_clusters != -1]
    
    # Create colormap
    colors = plt.cm.Set3(np.linspace(0, 1, len(unique_clusters)))
    color_map = dict(zip(unique_clusters, colors))
    color_map[-1] = 'gray'  # Noise points
    
    for cluster_id in unique_clusters:
        cluster_buildings = clustered_buildings[clustered_buildings['cluster_id'] == cluster_id]
        cluster_buildings.plot(ax=ax2, color=color_map[cluster_id], alpha=0.8, 
                             label=f'Community {cluster_id}')
    
    # Plot noise points
    noise_buildings = clustered_buildings[clustered_buildings['cluster_id'] == -1]
    if len(noise_buildings) > 0:
        noise_buildings.plot(ax=ax2, color='gray', alpha=0.5, label='Outliers')
    
    if roads_gdf is not None:
        roads_gdf.plot(ax=ax2, color='black', alpha=0.3, linewidth=0.5)
    
    ax2.set_title('Detected Housing Patterns', fontweight='bold')
    ax2.set_axis_off()
    if len(unique_clusters) <= 10:  # Only show legend if not too many clusters
        ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # 3. Community boundaries
    ax3 = axes[1, 0]
    buildings_gdf.plot(ax=ax3, color='lightgray', alpha=0.5, edgecolor='none')
    
    if len(boundaries) > 0:
        boundaries.plot(ax=ax3, facecolor='none', edgecolor='red', linewidth=2, alpha=0.8)
        
        # Add labels for communities
        for idx, boundary in boundaries.iterrows():
            centroid = boundary.geometry.centroid
            ax3.annotate(f"C{boundary['cluster_id']}", 
                        xy=(centroid.x, centroid.y), 
                        ha='center', va='center',
                        fontsize=10, fontweight='bold',
                        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    
    ax3.set_title('Community Boundaries', fontweight='bold')
    ax3.set_axis_off()
    
    # 4. Development type classification
    ax4 = axes[1, 1]
    
    if 'development_type' in clustered_buildings.columns:
        dev_types = clustered_buildings['development_type'].unique()
        dev_colors = plt.cm.viridis(np.linspace(0, 1, len(dev_types)))
        dev_color_map = dict(zip(dev_types, dev_colors))
        
        for dev_type in dev_types:
            dev_buildings = clustered_buildings[clustered_buildings['development_type'] == dev_type]
            if len(dev_buildings) > 0:
                dev_buildings.plot(ax=ax4, color=dev_color_map[dev_type], 
                                 alpha=0.8, label=dev_type.replace('_', ' ').title())
        
        ax4.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax4.set_title('Development Type Classification', fontweight='bold')
    else:
        # If no development type, show density analysis
        clustered_buildings.plot(ax=ax4, column='cluster_id', cmap='viridis', 
                               alpha=0.8, legend=True)
        ax4.set_title('Community Density Analysis', fontweight='bold')
    
    ax4.set_axis_off()
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"💾 Saved visualization to {save_path}")
    
    plt.show()
    
    return fig


def export_results(clustered_buildings: gpd.GeoDataFrame,
                  boundaries: gpd.GeoDataFrame,
                  output_dir: str = "output"):
    """
    Export results to various formats.
    """
    print("💾 Exporting results...")
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Export to shapefiles
    clustered_buildings.to_file(output_path / "clustered_buildings.shp")
    boundaries.to_file(output_path / "community_boundaries.shp")
    
    # Export to GeoJSON
    clustered_buildings.to_file(output_path / "clustered_buildings.geojson", driver="GeoJSON")
    boundaries.to_file(output_path / "community_boundaries.geojson", driver="GeoJSON")
    
    # Create summary report
    summary = {
        'total_buildings': len(clustered_buildings),
        'communities_detected': len(boundaries),
        'outlier_buildings': len(clustered_buildings[clustered_buildings['cluster_id'] == -1]),
        'avg_buildings_per_community': len(clustered_buildings) / max(len(boundaries), 1)
    }
    
    # Community statistics
    community_stats = []
    for _, boundary in boundaries.iterrows():
        cluster_buildings = clustered_buildings[
            clustered_buildings['cluster_id'] == boundary['cluster_id']
        ]
        
        stats = {
            'community_id': boundary['cluster_id'],
            'building_count': boundary['building_count'],
            'total_area': cluster_buildings.geometry.area.sum(),
            'avg_building_size': boundary['avg_building_size'],
            'density': boundary['density'],
            'development_type': boundary.get('development_type', 'unknown')
        }
        community_stats.append(stats)
    
    summary['community_details'] = community_stats
    
    # Save summary as JSON
    import json
    with open(output_path / "analysis_summary.json", 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"✅ Results exported to {output_path}/")
    return output_path


def main():
    """
    Main demonstration function.
    """
    print("🚀 AI-Powered Community Boundary Detection Demo")
    print("=" * 50)
    
    # Option 1: Use real data from OpenStreetMap
    use_real_data = input("Use real data from OpenStreetMap? (y/n): ").lower().strip() == 'y'
    
    if use_real_data:
        place_name = input("Enter place name (e.g., 'Cambridge, MA, USA'): ").strip()
        if not place_name:
            place_name = "Cambridge, MA, USA"
        
        try:
            buildings_gdf, roads_gdf, study_area = download_sample_data(place_name)
        except Exception as e:
            print(f"❌ Error downloading data: {e}")
            print("🔄 Falling back to synthetic data...")
            buildings_gdf = generate_synthetic_housing_development()
            roads_gdf = None
    else:
        buildings_gdf = generate_synthetic_housing_development()
        roads_gdf = None
    
    # Analyze community patterns
    method = 'hdbscan'  # Options: 'hdbscan', 'dbscan', 'spectral'
    clustered_buildings, boundaries = analyze_community_patterns(buildings_gdf, method=method)
    
    # Create visualizations
    fig = create_visualizations(
        buildings_gdf, 
        clustered_buildings, 
        boundaries, 
        roads_gdf,
        save_path="community_analysis_results.png"
    )
    
    # Export results
    output_path = export_results(clustered_buildings, boundaries)
    
    print("\n🎉 Analysis Complete!")
    print(f"📁 Results saved to: {output_path}")
    print("\n📋 Summary:")
    print(f"   • Buildings analyzed: {len(buildings_gdf)}")
    print(f"   • Communities detected: {len(boundaries)}")
    print(f"   • Method used: {method}")
    
    if len(boundaries) > 0:
        print(f"   • Largest community: {boundaries['building_count'].max()} buildings")
        print(f"   • Smallest community: {boundaries['building_count'].min()} buildings")
    
    # Demonstrate integration with SocialMapper
    print("\n🔗 Integration with SocialMapper:")
    print("   The detected communities can be used as:")
    print("   • Custom geographic boundaries for demographic analysis")
    print("   • Service area definitions for accessibility studies") 
    print("   • Zones for targeted policy interventions")
    print("   • Input for transportation network analysis")


if __name__ == "__main__":
    main() 