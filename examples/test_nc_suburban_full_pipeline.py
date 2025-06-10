#!/usr/bin/env python3
"""
Full SocialMapper Pipeline Test: NC Suburban Housing Development

This script demonstrates the complete community boundary detection pipeline:
1. Real satellite imagery fetching (Sentinel-2)
2. Computer vision analysis of land use patterns
3. Spatial clustering of building patterns
4. Community boundary detection
5. Comprehensive visualizations and export

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


def test_satellite_imagery_integration():
    """Test satellite imagery fetching and processing."""
    print("\n🛰️ Testing satellite imagery integration...")
    
    try:
        from socialmapper.community import SatelliteDataFetcher, analyze_satellite_imagery
        
        # Initialize fetcher with caching
        fetcher = SatelliteDataFetcher(
            max_cloud_cover=50.0,
            cache_dir="./test_cache"
        )
        
        print(f"   📍 Study area bounds: {STUDY_BOUNDS}")
        
        # Fetch Sentinel-2 imagery
        print("   🔍 Fetching Sentinel-2 imagery...")
        sentinel_path = fetcher.get_best_imagery_for_bounds(
            bounds=STUDY_BOUNDS,
            imagery_type="sentinel2",
            time_range="2024-01-01/2024-12-31"
        )
        
        if not sentinel_path:
            print("   ❌ No satellite imagery available")
            return None, None
        
        print(f"   ✅ Successfully fetched imagery: {sentinel_path}")
        
        # Analyze satellite imagery for land use
        print("   🔍 Analyzing land use patterns...")
        land_use_patches = analyze_satellite_imagery(
            bounds=STUDY_BOUNDS,
            imagery_type="sentinel2",
            patch_size=256,  # Good for suburban analysis
            image_path=sentinel_path
        )
        
        print(f"   ✅ Generated {len(land_use_patches)} land use patches")
        print(f"   📊 Land use types: {list(land_use_patches['land_use'].unique())}")
        
        return sentinel_path, land_use_patches
        
    except Exception as e:
        print(f"   ❌ Error in satellite imagery integration: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def run_community_boundary_detection(buildings_gdf, satellite_image_path=None):
    """Run the full community boundary detection pipeline."""
    print("\n🏘️ Running community boundary detection...")
    
    try:
        from socialmapper.community import discover_community_boundaries
        from socialmapper.community.spatial_clustering import detect_housing_developments
        
        # Method 1: Spatial clustering only
        print("   📍 Running spatial clustering analysis...")
        clustered_buildings, spatial_boundaries = detect_housing_developments(
            buildings_gdf=buildings_gdf,
            method='hdbscan',
            min_cluster_size=20,
            min_samples=5
        )
        
        print(f"   ✅ Spatial analysis: {len(spatial_boundaries)} communities detected")
        
        # Method 2: Integrated analysis (if satellite data available)
        integrated_boundaries = None
        if satellite_image_path:
            print("   🔗 Running integrated analysis with satellite imagery...")
            try:
                integrated_boundaries = discover_community_boundaries(
                    buildings_gdf=buildings_gdf,
                    satellite_image=satellite_image_path
                )
                print(f"   ✅ Integrated analysis: {len(integrated_boundaries)} communities detected")
            except Exception as e:
                print(f"   ⚠️ Integrated analysis failed: {e}")
        
        return clustered_buildings, spatial_boundaries, integrated_boundaries
        
    except Exception as e:
        print(f"   ❌ Error in community detection: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None


def create_comprehensive_visualizations(buildings_gdf, clustered_buildings, boundaries, 
                                       land_use_patches=None, roads_gdf=None, output_dir=None):
    """Create comprehensive visualizations of all results."""
    print("\n📊 Creating comprehensive visualizations...")
    
    try:
        # Create figure with multiple subplots
        fig, axes = plt.subplots(2, 3, figsize=(20, 12))
        fig.suptitle(f'Community Boundary Detection: {STUDY_AREA_NAME}', fontsize=16, fontweight='bold')
        
        # 1. Original building footprints
        ax1 = axes[0, 0]
        buildings_gdf.plot(ax=ax1, color='lightblue', alpha=0.7, edgecolor='darkblue', linewidth=0.5)
        if roads_gdf is not None:
            roads_gdf.plot(ax=ax1, color='gray', alpha=0.5, linewidth=1)
        ax1.set_title(f'Building Footprints\n({len(buildings_gdf)} buildings)', fontweight='bold')
        ax1.set_axis_off()
        
        # 2. Clustered buildings
        ax2 = axes[0, 1]
        if clustered_buildings is not None:
            unique_clusters = clustered_buildings['cluster_id'].unique()
            unique_clusters = unique_clusters[unique_clusters != -1]
            
            # Create colormap for clusters
            colors = plt.cm.Set3(np.linspace(0, 1, len(unique_clusters)))
            color_map = dict(zip(unique_clusters, colors))
            color_map[-1] = 'lightgray'  # Noise points
            
            for cluster_id in unique_clusters:
                cluster_buildings = clustered_buildings[clustered_buildings['cluster_id'] == cluster_id]
                cluster_buildings.plot(ax=ax2, color=color_map[cluster_id], alpha=0.8, 
                                     label=f'Cluster {cluster_id}')
            
            # Plot noise points
            noise_buildings = clustered_buildings[clustered_buildings['cluster_id'] == -1]
            if len(noise_buildings) > 0:
                noise_buildings.plot(ax=ax2, color='lightgray', alpha=0.5, label='Outliers')
            
            ax2.set_title(f'Spatial Clusters\n({len(unique_clusters)} clusters)', fontweight='bold')
        else:
            ax2.text(0.5, 0.5, 'No clustering data', ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title('Spatial Clusters\n(No data)', fontweight='bold')
        
        ax2.set_axis_off()
        
        # 3. Community boundaries
        ax3 = axes[0, 2]
        buildings_gdf.plot(ax=ax3, color='lightgray', alpha=0.3, edgecolor='none')
        
        if boundaries is not None and len(boundaries) > 0:
            boundaries.plot(ax=ax3, facecolor='none', edgecolor='red', linewidth=2, alpha=0.8)
            
            # Add community labels
            for idx, boundary in boundaries.iterrows():
                if hasattr(boundary.geometry, 'centroid'):
                    centroid = boundary.geometry.centroid
                    community_id = boundary.get('cluster_id', boundary.get('community_id', idx))
                    ax3.annotate(f"C{community_id}", 
                                xy=(centroid.x, centroid.y), 
                                ha='center', va='center',
                                fontsize=10, fontweight='bold',
                                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
            
            ax3.set_title(f'Community Boundaries\n({len(boundaries)} communities)', fontweight='bold')
        else:
            ax3.set_title('Community Boundaries\n(No data)', fontweight='bold')
        
        ax3.set_axis_off()
        
        # 4. Land use analysis
        ax4 = axes[1, 0]
        if land_use_patches is not None:
            land_use_patches.plot(ax=ax4, column='land_use', cmap='viridis', alpha=0.7, legend=True)
            ax4.set_title(f'Land Use Analysis\n({len(land_use_patches)} patches)', fontweight='bold')
        else:
            ax4.text(0.5, 0.5, 'No satellite data', ha='center', va='center', transform=ax4.transAxes)
            ax4.set_title('Land Use Analysis\n(No data)', fontweight='bold')
        ax4.set_axis_off()
        
        # 5. Development density
        ax5 = axes[1, 1]
        if clustered_buildings is not None:
            # Calculate building density per cluster
            cluster_stats = []
            for cluster_id in clustered_buildings['cluster_id'].unique():
                if cluster_id != -1:
                    cluster_data = clustered_buildings[clustered_buildings['cluster_id'] == cluster_id]
                    if len(cluster_data) > 0:
                        total_area = cluster_data.geometry.area.sum()
                        building_count = len(cluster_data)
                        density = building_count / (total_area / 10000)  # buildings per hectare
                        
                        cluster_stats.append({
                            'cluster_id': cluster_id,
                            'density': density,
                            'building_count': building_count
                        })
            
            if cluster_stats:
                cluster_df = pd.DataFrame(cluster_stats)
                bars = ax5.bar(cluster_df['cluster_id'], cluster_df['density'], alpha=0.7)
                ax5.set_xlabel('Community ID')
                ax5.set_ylabel('Building Density (per hectare)')
                ax5.set_title('Community Density Analysis', fontweight='bold')
                
                # Add value labels on bars
                for bar, density in zip(bars, cluster_df['density']):
                    ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                            f'{density:.1f}', ha='center', va='bottom', fontsize=8)
            else:
                ax5.text(0.5, 0.5, 'No density data', ha='center', va='center', transform=ax5.transAxes)
        else:
            ax5.text(0.5, 0.5, 'No clustering data', ha='center', va='center', transform=ax5.transAxes)
        
        # 6. Summary statistics
        ax6 = axes[1, 2]
        ax6.axis('off')
        
        # Compile summary statistics
        stats_text = f"📊 ANALYSIS SUMMARY\n\n"
        stats_text += f"Study Area: {STUDY_AREA_NAME}\n"
        stats_text += f"Bounds: {STUDY_BOUNDS}\n\n"
        
        stats_text += f"Buildings Analyzed: {len(buildings_gdf)}\n"
        
        if clustered_buildings is not None:
            n_clusters = len(clustered_buildings['cluster_id'].unique()) - (1 if -1 in clustered_buildings['cluster_id'].unique() else 0)
            stats_text += f"Communities Detected: {n_clusters}\n"
            
            if n_clusters > 0:
                avg_buildings = clustered_buildings[clustered_buildings['cluster_id'] != -1].groupby('cluster_id').size().mean()
                stats_text += f"Avg Buildings/Community: {avg_buildings:.1f}\n"
        
        if boundaries is not None:
            stats_text += f"Boundary Polygons: {len(boundaries)}\n"
        
        if land_use_patches is not None:
            stats_text += f"\nLand Use Patches: {len(land_use_patches)}\n"
            land_use_types = land_use_patches['land_use'].unique()
            stats_text += f"Land Use Types: {len(land_use_types)}\n"
            for lu_type in land_use_types:
                count = (land_use_patches['land_use'] == lu_type).sum()
                pct = (count / len(land_use_patches)) * 100
                stats_text += f"  • {lu_type}: {pct:.1f}%\n"
        
        ax6.text(0.1, 0.9, stats_text, transform=ax6.transAxes, fontsize=10, 
                verticalalignment='top', fontfamily='monospace')
        
        plt.tight_layout()
        
        # Save the comprehensive visualization
        if output_dir:
            viz_path = output_dir / "maps" / "comprehensive_analysis.png"
            plt.savefig(viz_path, dpi=300, bbox_inches='tight')
            print(f"   💾 Saved comprehensive visualization: {viz_path}")
        
        plt.show()
        
        return fig
        
    except Exception as e:
        print(f"   ❌ Error creating visualizations: {e}")
        import traceback
        traceback.print_exc()
        return None


def export_results(buildings_gdf, clustered_buildings, boundaries, land_use_patches, output_dir):
    """Export all results to various formats."""
    print("\n💾 Exporting results...")
    
    try:
        data_dir = output_dir / "data"
        
        # Export buildings data
        if buildings_gdf is not None:
            buildings_gdf.to_file(data_dir / "buildings.shp")
            buildings_gdf.to_file(data_dir / "buildings.geojson", driver="GeoJSON")
            print(f"   ✅ Exported building footprints")
        
        # Export clustered buildings
        if clustered_buildings is not None:
            clustered_buildings.to_file(data_dir / "clustered_buildings.shp")
            clustered_buildings.to_file(data_dir / "clustered_buildings.geojson", driver="GeoJSON")
            print(f"   ✅ Exported clustered buildings")
        
        # Export community boundaries
        if boundaries is not None:
            boundaries.to_file(data_dir / "community_boundaries.shp")
            boundaries.to_file(data_dir / "community_boundaries.geojson", driver="GeoJSON")
            print(f"   ✅ Exported community boundaries")
        
        # Export land use patches
        if land_use_patches is not None:
            land_use_patches.to_file(data_dir / "land_use_patches.shp")
            land_use_patches.to_file(data_dir / "land_use_patches.geojson", driver="GeoJSON")
            print(f"   ✅ Exported land use analysis")
        
        # Create analysis report
        report_path = output_dir / "reports" / "analysis_report.md"
        with open(report_path, 'w') as f:
            f.write(f"# Community Boundary Detection Analysis Report\n\n")
            f.write(f"**Study Area:** {STUDY_AREA_NAME}\n")
            f.write(f"**Bounds:** {STUDY_BOUNDS}\n")
            f.write(f"**Analysis Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"## Summary Statistics\n\n")
            f.write(f"- **Total Buildings:** {len(buildings_gdf) if buildings_gdf is not None else 0}\n")
            
            if clustered_buildings is not None:
                n_clusters = len(clustered_buildings['cluster_id'].unique()) - (1 if -1 in clustered_buildings['cluster_id'].unique() else 0)
                f.write(f"- **Communities Detected:** {n_clusters}\n")
            
            if boundaries is not None:
                f.write(f"- **Boundary Polygons:** {len(boundaries)}\n")
            
            if land_use_patches is not None:
                f.write(f"- **Land Use Patches:** {len(land_use_patches)}\n")
                land_use_types = land_use_patches['land_use'].value_counts()
                f.write(f"\n### Land Use Distribution\n\n")
                for lu_type, count in land_use_types.items():
                    pct = (count / len(land_use_patches)) * 100
                    f.write(f"- **{lu_type}:** {count} patches ({pct:.1f}%)\n")
        
        print(f"   ✅ Created analysis report: {report_path}")
        
        print(f"\n📁 All results exported to: {output_dir}")
        
    except Exception as e:
        print(f"   ❌ Error exporting results: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run the complete SocialMapper pipeline."""
    print("🚀 SocialMapper Full Pipeline Test")
    print(f"🎯 Study Area: {STUDY_AREA_NAME}")
    print("=" * 60)
    
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
    
    # Test satellite imagery
    print("\n🛰️ Fetching satellite imagery...")
    try:
        from socialmapper.community import SatelliteDataFetcher, analyze_satellite_imagery
        import time
        
        print(f"   📡 Initializing satellite data fetcher...")
        fetcher = SatelliteDataFetcher(cache_dir="./test_cache")
        
        print(f"   🔍 Searching for Sentinel-2 imagery...")
        print(f"   📍 Search area: {STUDY_BOUNDS}")
        
        start_time = time.time()
        sentinel_path = fetcher.get_best_imagery_for_bounds(
            bounds=STUDY_BOUNDS,
            imagery_type="sentinel2"
        )
        search_time = time.time() - start_time
        
        if sentinel_path:
            print(f"   ⏱️ Imagery search completed in {search_time:.1f} seconds")
            print(f"✅ Got satellite imagery: {sentinel_path}")
            
            print(f"   🔍 Analyzing land use patterns...")
            start_analysis = time.time()
            
            land_use_patches = analyze_satellite_imagery(
                bounds=STUDY_BOUNDS,
                imagery_type="sentinel2",
                patch_size=256,
                image_path=sentinel_path
            )
            
            analysis_time = time.time() - start_analysis
            print(f"   ⏱️ Analysis completed in {analysis_time:.1f} seconds")
            print(f"✅ Generated {len(land_use_patches)} land use patches")
            
            # Show land use breakdown
            land_use_counts = land_use_patches['land_use'].value_counts()
            print(f"   📊 Land use distribution:")
            for land_use, count in land_use_counts.items():
                percentage = (count / len(land_use_patches)) * 100
                print(f"      - {land_use}: {count} ({percentage:.1f}%)")
        else:
            print(f"   ⏱️ Search completed in {search_time:.1f} seconds")
            print("⚠️ No satellite imagery available for this area")
            land_use_patches = None
            
    except Exception as e:
        print(f"❌ Satellite imagery error: {e}")
        land_use_patches = None
    
    # Run community detection
    print("\n🏘️ Running community detection...")
    try:
        from socialmapper.community.spatial_clustering import detect_housing_developments
        import time
        
        print(f"   🔧 Initializing spatial clustering algorithm...")
        print(f"   📊 Input: {len(buildings_gdf)} building footprints")
        print(f"   ⚙️ Method: HDBSCAN clustering")
        print(f"   ⚙️ Min cluster size: 20 buildings")
        
        start_time = time.time()
        clustered_buildings, boundaries = detect_housing_developments(
            buildings_gdf=buildings_gdf,
            method='hdbscan',
            min_cluster_size=20
        )
        detection_time = time.time() - start_time
        
        n_communities = len(boundaries)
        n_clustered = len(clustered_buildings[clustered_buildings['cluster_id'] != -1])
        n_outliers = len(clustered_buildings[clustered_buildings['cluster_id'] == -1])
        
        print(f"   ⏱️ Community detection completed in {detection_time:.1f} seconds")
        print(f"✅ Detected {n_communities} distinct communities")
        print(f"   📊 Buildings in communities: {n_clustered}")
        print(f"   📊 Outlier buildings: {n_outliers}")
        
        if n_communities > 0:
            # Show community size distribution
            community_sizes = clustered_buildings[clustered_buildings['cluster_id'] != -1]['cluster_id'].value_counts()
            print(f"   📊 Community size distribution:")
            print(f"      - Largest: {community_sizes.max()} buildings")
            print(f"      - Smallest: {community_sizes.min()} buildings")
            print(f"      - Average: {community_sizes.mean():.1f} buildings")
        
    except Exception as e:
        print(f"❌ Community detection error: {e}")
        clustered_buildings, boundaries = None, None
    
    # Create visualization
    print("\n📊 Creating visualization...")
    try:
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'Community Analysis: {STUDY_AREA_NAME}', fontsize=16)
        
        # 1. Original buildings
        ax1 = axes[0, 0]
        buildings_gdf.plot(ax=ax1, color='lightblue', alpha=0.7)
        ax1.set_title(f'Buildings ({len(buildings_gdf)})')
        ax1.set_axis_off()
        
        # 2. Clustered buildings
        ax2 = axes[0, 1]
        if clustered_buildings is not None:
            unique_clusters = clustered_buildings['cluster_id'].unique()
            unique_clusters = unique_clusters[unique_clusters != -1]
            
            colors = plt.cm.Set3(np.linspace(0, 1, len(unique_clusters)))
            for i, cluster_id in enumerate(unique_clusters):
                cluster_data = clustered_buildings[clustered_buildings['cluster_id'] == cluster_id]
                cluster_data.plot(ax=ax2, color=colors[i], alpha=0.8)
            
            ax2.set_title(f'Communities ({len(unique_clusters)})')
        else:
            ax2.set_title('Communities (No data)')
        ax2.set_axis_off()
        
        # 3. Boundaries
        ax3 = axes[1, 0]
        buildings_gdf.plot(ax=ax3, color='lightgray', alpha=0.3)
        if boundaries is not None and len(boundaries) > 0:
            boundaries.plot(ax=ax3, facecolor='none', edgecolor='red', linewidth=2)
            ax3.set_title(f'Boundaries ({len(boundaries)})')
        else:
            ax3.set_title('Boundaries (No data)')
        ax3.set_axis_off()
        
        # 4. Land use
        ax4 = axes[1, 1]
        if land_use_patches is not None:
            land_use_patches.plot(ax=ax4, column='land_use', cmap='viridis', alpha=0.7)
            ax4.set_title(f'Land Use ({len(land_use_patches)} patches)')
        else:
            ax4.set_title('Land Use (No data)')
        ax4.set_axis_off()
        
        plt.tight_layout()
        
        # Save visualization
        output_dir = Path("./output")
        output_dir.mkdir(exist_ok=True)
        viz_path = output_dir / "nc_suburban_analysis.png"
        plt.savefig(viz_path, dpi=300, bbox_inches='tight')
        print(f"💾 Saved visualization: {viz_path}")
        
        plt.show()
        
    except Exception as e:
        print(f"❌ Visualization error: {e}")
    
    # Export results
    print("\n💾 Exporting results...")
    try:
        output_dir = Path("./output")
        
        if clustered_buildings is not None:
            clustered_buildings.to_file(output_dir / "clustered_buildings.geojson", driver="GeoJSON")
            print("✅ Exported clustered buildings")
        
        if boundaries is not None:
            boundaries.to_file(output_dir / "community_boundaries.geojson", driver="GeoJSON")
            print("✅ Exported boundaries")
        
        if land_use_patches is not None:
            land_use_patches.to_file(output_dir / "land_use_patches.geojson", driver="GeoJSON")
            print("✅ Exported land use data")
            
    except Exception as e:
        print(f"❌ Export error: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 PIPELINE COMPLETE!")
    print("=" * 60)
    
    print(f"✅ Buildings analyzed: {len(buildings_gdf)}")
    
    if clustered_buildings is not None:
        n_clusters = len(clustered_buildings['cluster_id'].unique()) - (1 if -1 in clustered_buildings['cluster_id'].unique() else 0)
        print(f"✅ Communities detected: {n_clusters}")
    
    if land_use_patches is not None:
        print(f"✅ Land use patches: {len(land_use_patches)}")
        print(f"   Types: {list(land_use_patches['land_use'].unique())}")
    
    print(f"\n📁 Results saved to: ./output/")


if __name__ == "__main__":
    main() 