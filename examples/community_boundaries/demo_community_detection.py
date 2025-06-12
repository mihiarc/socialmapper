#!/usr/bin/env python3
"""
Community Boundary Detection Demo (Modified)

This script has been modified to remove dependencies on the removed community module.
Note: AI-powered community boundary detection features have been removed.

This demo now shows basic building pattern analysis using standard GIS techniques.
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
from sklearn.cluster import DBSCAN

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


def simple_clustering_analysis(buildings_gdf: gpd.GeoDataFrame, 
                              eps: float = 200, min_samples: int = 5) -> tuple:
    """
    Simple clustering analysis using DBSCAN.
    
    Args:
        buildings_gdf: GeoDataFrame with building footprints
        eps: Maximum distance between samples
        min_samples: Minimum samples in a neighborhood
        
    Returns:
        Tuple of (clustered_buildings, cluster_boundaries)
    """
    print(f"🤖 Analyzing building patterns using simple DBSCAN clustering...")
    
    # Get building centroids
    centroids = buildings_gdf.geometry.centroid
    coords = np.array([(p.x, p.y) for p in centroids])
    
    # Apply DBSCAN clustering
    clustering = DBSCAN(eps=eps, min_samples=min_samples)
    cluster_labels = clustering.fit_predict(coords)
    
    # Add cluster labels to the buildings
    buildings_with_clusters = buildings_gdf.copy()
    buildings_with_clusters['cluster_id'] = cluster_labels
    
    # Create cluster boundaries using convex hulls
    boundaries = []
    unique_clusters = np.unique(cluster_labels)
    unique_clusters = unique_clusters[unique_clusters != -1]  # Exclude noise
    
    for cluster_id in unique_clusters:
        cluster_buildings = buildings_with_clusters[
            buildings_with_clusters['cluster_id'] == cluster_id
        ]
        
        if len(cluster_buildings) >= 3:  # Need at least 3 points for convex hull
            # Create convex hull around cluster buildings
            cluster_geoms = cluster_buildings.geometry.tolist()
            cluster_union = unary_union(cluster_geoms)
            
            if hasattr(cluster_union, 'convex_hull'):
                boundary = cluster_union.convex_hull
            else:
                boundary = cluster_union
            
            boundaries.append({
                'cluster_id': cluster_id,
                'geometry': boundary,
                'building_count': len(cluster_buildings),
                'avg_building_size': cluster_buildings['area'].mean(),
                'density': len(cluster_buildings) / boundary.area * 1000000  # per sq km
            })
    
    boundaries_gdf = gpd.GeoDataFrame(boundaries, crs=buildings_gdf.crs)
    
    # Calculate statistics
    n_communities = len(boundaries_gdf)
    avg_buildings_per_community = len(buildings_with_clusters) / max(n_communities, 1)
    
    print(f"📊 Analysis Results:")
    print(f"   • {n_communities} clusters detected")
    print(f"   • {avg_buildings_per_community:.1f} buildings per cluster (avg)")
    print(f"   • {len(buildings_with_clusters[buildings_with_clusters['cluster_id'] == -1])} outlier buildings")
    
    return buildings_with_clusters, boundaries_gdf


def create_visualizations(buildings_gdf: gpd.GeoDataFrame,
                         clustered_buildings: gpd.GeoDataFrame,
                         boundaries: gpd.GeoDataFrame,
                         roads_gdf: gpd.GeoDataFrame = None,
                         save_path: str = None):
    """
    Create comprehensive visualizations of the clustering results.
    """
    print("📊 Creating visualizations...")
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Simple Building Pattern Analysis Results', fontsize=16, fontweight='bold')
    
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
                             label=f'Cluster {cluster_id}')
    
    # Plot noise points
    noise_buildings = clustered_buildings[clustered_buildings['cluster_id'] == -1]
    if len(noise_buildings) > 0:
        noise_buildings.plot(ax=ax2, color='gray', alpha=0.5, label='Outliers')
    
    if roads_gdf is not None:
        roads_gdf.plot(ax=ax2, color='black', alpha=0.3, linewidth=0.5)
    
    ax2.set_title('Detected Building Clusters', fontweight='bold')
    ax2.set_axis_off()
    if len(unique_clusters) <= 10:  # Only show legend if not too many clusters
        ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # 3. Cluster boundaries
    ax3 = axes[1, 0]
    buildings_gdf.plot(ax=ax3, color='lightgray', alpha=0.5, edgecolor='none')
    
    if len(boundaries) > 0:
        boundaries.plot(ax=ax3, facecolor='none', edgecolor='red', linewidth=2, alpha=0.8)
        
        # Add labels for clusters
        for idx, boundary in boundaries.iterrows():
            centroid = boundary.geometry.centroid
            ax3.annotate(f"C{boundary['cluster_id']}", 
                        xy=(centroid.x, centroid.y), 
                        ha='center', va='center',
                        fontsize=10, fontweight='bold',
                        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    
    ax3.set_title('Cluster Boundaries', fontweight='bold')
    ax3.set_axis_off()
    
    # 4. Building type classification (if available)
    ax4 = axes[1, 1]
    
    if 'building_type' in clustered_buildings.columns:
        building_types = clustered_buildings['building_type'].unique()
        type_colors = plt.cm.viridis(np.linspace(0, 1, len(building_types)))
        type_color_map = dict(zip(building_types, type_colors))
        
        for building_type in building_types:
            type_buildings = clustered_buildings[clustered_buildings['building_type'] == building_type]
            if len(type_buildings) > 0:
                type_buildings.plot(ax=ax4, color=type_color_map[building_type], 
                                  alpha=0.8, label=building_type.replace('_', ' ').title())
        
        ax4.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax4.set_title('Building Type Classification', fontweight='bold')
    else:
        # If no building type, show density analysis
        clustered_buildings.plot(ax=ax4, column='cluster_id', cmap='viridis', 
                               alpha=0.8, legend=True)
        ax4.set_title('Cluster Density Analysis', fontweight='bold')
    
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
    boundaries.to_file(output_path / "cluster_boundaries.shp")
    
    # Export to GeoJSON
    clustered_buildings.to_file(output_path / "clustered_buildings.geojson", driver="GeoJSON")
    boundaries.to_file(output_path / "cluster_boundaries.geojson", driver="GeoJSON")
    
    # Create summary report
    summary = {
        'total_buildings': len(clustered_buildings),
        'clusters_detected': len(boundaries),
        'outlier_buildings': len(clustered_buildings[clustered_buildings['cluster_id'] == -1]),
        'avg_buildings_per_cluster': len(clustered_buildings) / max(len(boundaries), 1)
    }
    
    # Cluster statistics
    cluster_stats = []
    for _, boundary in boundaries.iterrows():
        cluster_buildings = clustered_buildings[
            clustered_buildings['cluster_id'] == boundary['cluster_id']
        ]
        
        stats = {
            'cluster_id': boundary['cluster_id'],
            'building_count': boundary['building_count'],
            'total_area': cluster_buildings.geometry.area.sum(),
            'avg_building_size': boundary['avg_building_size'],
            'density': boundary['density']
        }
        cluster_stats.append(stats)
    
    summary['cluster_details'] = cluster_stats
    
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
    print("🚀 Building Pattern Analysis Demo (Modified)")
    print("=" * 50)
    print("⚠️  Note: AI-powered community detection features have been removed.")
    print("    This demo now uses simple DBSCAN clustering instead.\n")
    
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
    
    # Analyze building patterns using simple clustering
    clustered_buildings, boundaries = simple_clustering_analysis(buildings_gdf)
    
    # Create visualizations
    fig = create_visualizations(
        buildings_gdf, 
        clustered_buildings, 
        boundaries, 
        roads_gdf,
        save_path="building_pattern_analysis_results.png"
    )
    
    # Export results
    output_path = export_results(clustered_buildings, boundaries)
    
    print("\n🎉 Analysis Complete!")
    print(f"📁 Results saved to: {output_path}")
    print("\n📋 Summary:")
    print(f"   • Buildings analyzed: {len(buildings_gdf)}")
    print(f"   • Clusters detected: {len(boundaries)}")
    print(f"   • Method used: Simple DBSCAN clustering")
    
    if len(boundaries) > 0:
        print(f"   • Largest cluster: {boundaries['building_count'].max()} buildings")
        print(f"   • Smallest cluster: {boundaries['building_count'].min()} buildings")
    
    # Information about limitations
    print("\n🔗 About This Modified Version:")
    print("   The original AI-powered community detection features have been removed.")
    print("   This version uses simple DBSCAN clustering for building pattern analysis.")
    print("   \n💡 For advanced community detection, consider:")
    print("   • External clustering libraries (scikit-learn, HDBSCAN)")
    print("   • Graph-based community detection algorithms") 
    print("   • Commercial GIS software (ArcGIS, QGIS)")
    print("   • Custom spatial analysis solutions")


if __name__ == "__main__":
    main()