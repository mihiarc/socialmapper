#!/usr/bin/env python3
"""
Test Script: Real Satellite Imagery Integration

This script demonstrates the new geoai integration for fetching
real NAIP and Sentinel-2 imagery for community boundary detection.

Run with: python examples/test_satellite_integration.py
"""

import sys
import os
from pathlib import Path

# Add socialmapper to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import geopandas as gpd
import numpy as np
from shapely.geometry import box, Point
import warnings
warnings.filterwarnings('ignore')

def create_test_buildings():
    """Create sample building footprints for testing."""
    print("🏠 Creating test building dataset...")
    
    # Focus on a small area in Cambridge, MA (good NAIP coverage)
    center_lat, center_lon = 42.3601, -71.0942  # Harvard Square area
    
    # Create a grid of building points
    buildings = []
    building_id = 0
    
    for i in range(-5, 6):  # 11x11 grid
        for j in range(-5, 6):
            # Add some randomness to positions
            lat = center_lat + (i * 0.001) + np.random.normal(0, 0.0002)
            lon = center_lon + (j * 0.001) + np.random.normal(0, 0.0002)
            
            # Create building footprint (small rectangles)
            size = np.random.uniform(0.00005, 0.0002)  # Varying building sizes
            building = box(lon - size/2, lat - size/2, lon + size/2, lat + size/2)
            
            buildings.append({
                'building_id': building_id,
                'geometry': building,
                'estimated_area': building.area * 111000 * 111000,  # Rough conversion to m²
                'building_type': np.random.choice(['residential', 'commercial', 'mixed'])
            })
            building_id += 1
    
    # Create GeoDataFrame
    buildings_gdf = gpd.GeoDataFrame(buildings, crs='EPSG:4326')
    print(f"   Created {len(buildings_gdf)} test buildings")
    return buildings_gdf


def test_satellite_fetcher_directly():
    """Test the satellite data fetcher directly."""
    print("\n🛰️ Testing SatelliteDataFetcher directly...")
    
    try:
        from socialmapper.community import SatelliteDataFetcher
        
        # Test area around Cambridge, MA
        bounds = (-71.1, 42.35, -71.08, 42.37)  # Small test area
        
        fetcher = SatelliteDataFetcher()
        
        print("   Testing NAIP imagery fetching...")
        naip_path = fetcher.get_best_imagery_for_bounds(
            bounds=bounds,
            imagery_type="naip"
        )
        
        if naip_path:
            print(f"   ✅ Successfully fetched NAIP imagery: {naip_path}")
        else:
            print("   ⚠️ No NAIP imagery available for test area")
        
        print("   Testing Sentinel-2 imagery fetching...")
        sentinel_path = fetcher.get_best_imagery_for_bounds(
            bounds=bounds,
            imagery_type="sentinel2"
        )
        
        if sentinel_path:
            print(f"   ✅ Successfully fetched Sentinel-2 imagery: {sentinel_path}")
        else:
            print("   ⚠️ No Sentinel-2 imagery available for test area")
        
        return naip_path or sentinel_path
        
    except ImportError as e:
        print(f"   ❌ geoai package not available: {e}")
        print("   💡 Install with: pip install geoai-py")
        return None
    except Exception as e:
        print(f"   ❌ Error testing satellite fetcher: {e}")
        return None


def test_computer_vision_integration(buildings_gdf):
    """Test the updated computer vision module with real data."""
    print("\n🔍 Testing computer vision integration...")
    
    try:
        from socialmapper.community import analyze_satellite_imagery
        
        # Get bounds from buildings
        bounds = buildings_gdf.total_bounds
        bounds_tuple = (bounds[0], bounds[1], bounds[2], bounds[3])
        
        print(f"   Analyzing area with bounds: {bounds_tuple}")
        
        # This should now automatically fetch real satellite imagery
        patches_gdf = analyze_satellite_imagery(
            bounds=bounds_tuple,
            imagery_type="naip",
            patch_size=256  # Smaller patches for faster processing
        )
        
        print(f"   ✅ Analysis completed!")
        print(f"   📊 Generated {len(patches_gdf)} analysis patches")
        print(f"   🏷️ Land use types found: {list(patches_gdf['land_use'].unique())}")
        print(f"   📈 Analysis methods: {list(patches_gdf['analysis_method'].unique())}")
        
        # Show distribution of land use types
        land_use_counts = patches_gdf['land_use'].value_counts()
        print("   📋 Land use distribution:")
        for land_use, count in land_use_counts.items():
            percentage = (count / len(patches_gdf)) * 100
            print(f"      - {land_use}: {count} patches ({percentage:.1f}%)")
        
        return patches_gdf
        
    except Exception as e:
        print(f"   ❌ Error in computer vision integration: {e}")
        return None


def test_community_boundary_detection(buildings_gdf):
    """Test the full community boundary detection with real imagery."""
    print("\n🏘️ Testing community boundary detection...")
    
    try:
        from socialmapper.community import discover_community_boundaries
        
        # Run community detection
        boundaries_gdf = discover_community_boundaries(
            buildings_gdf=buildings_gdf,
            satellite_image=None  # Let it fetch automatically
        )
        
        print(f"   ✅ Community detection completed!")
        print(f"   🗺️ Discovered {len(boundaries_gdf)} community boundaries")
        
        if len(boundaries_gdf) > 0:
            print("   📋 Community types found:")
            if 'community_type' in boundaries_gdf.columns:
                for comm_type in boundaries_gdf['community_type'].unique():
                    count = (boundaries_gdf['community_type'] == comm_type).sum()
                    print(f"      - {comm_type}: {count} communities")
        
        return boundaries_gdf
        
    except Exception as e:
        print(f"   ❌ Error in community boundary detection: {e}")
        return None


def main():
    """Run the complete test suite."""
    print("🚀 SocialMapper Satellite Imagery Integration Test")
    print("=" * 60)
    
    # Step 1: Create test data
    buildings_gdf = create_test_buildings()
    
    # Step 2: Test satellite fetcher directly
    satellite_path = test_satellite_fetcher_directly()
    
    # Step 3: Test computer vision integration
    patches_gdf = test_computer_vision_integration(buildings_gdf)
    
    # Step 4: Test full community boundary detection
    boundaries_gdf = test_community_boundary_detection(buildings_gdf)
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 TEST SUMMARY")
    print("=" * 60)
    
    if satellite_path:
        print("✅ Satellite data fetching: SUCCESS")
    else:
        print("⚠️ Satellite data fetching: FALLBACK (geoai not available or no data)")
    
    if patches_gdf is not None:
        real_imagery_used = 'real_satellite_imagery' in patches_gdf['analysis_method'].values
        if real_imagery_used:
            print("✅ Computer vision analysis: SUCCESS (real imagery)")
        else:
            print("⚠️ Computer vision analysis: SUCCESS (simulated data)")
    else:
        print("❌ Computer vision analysis: FAILED")
    
    if boundaries_gdf is not None:
        print("✅ Community boundary detection: SUCCESS")
    else:
        print("❌ Community boundary detection: FAILED")
    
    print("\n💡 Next Steps:")
    if not satellite_path:
        print("   • Install geoai package: pip install geoai-py")
        print("   • Try a different geographic area with better data coverage")
    print("   • Experiment with different imagery types (naip, sentinel2, landsat)")
    print("   • Adjust patch sizes and analysis parameters")
    print("   • Integrate with your own building footprint data")
    
    print("\n🎉 Test completed!")


if __name__ == "__main__":
    main() 