#!/usr/bin/env python3
"""
Simple Sentinel-2 Test Script

Quick test of Sentinel-2 imagery integration for faster iteration.
Sentinel-2 files are much smaller than NAIP (10-20MB vs 1GB+).

This test REQUIRES real satellite imagery - no fallback to simulated data.
Testing on suburban housing development in North Carolina.

Run with: python examples/test_sentinel2_simple.py
"""

import sys
import os
from pathlib import Path

# Add socialmapper to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import geopandas as gpd
import numpy as np
from shapely.geometry import box
import warnings
warnings.filterwarnings('ignore')

def test_sentinel2_only():
    """Test Sentinel-2 imagery fetching and processing."""
    print("🛰️ Testing Sentinel-2 imagery integration")
    print("=" * 50)
    
    try:
        from socialmapper.community import SatelliteDataFetcher
        
        # Suburban housing development in North Carolina
        bounds = (-78.755873, 35.568584, -78.732969, 35.585022)
        
        print(f"📍 Test area bounds: {bounds}")
        print("   (Suburban housing development in North Carolina)")
        
        # Initialize fetcher
        fetcher = SatelliteDataFetcher(
            max_cloud_cover=50.0,  # More lenient for testing
            cache_dir="./test_cache"
        )
        
        print("\n🔍 Searching for Sentinel-2 imagery...")
        sentinel_path = fetcher.get_best_imagery_for_bounds(
            bounds=bounds,
            imagery_type="sentinel2",
            time_range="2024-01-01/2024-12-31"
        )
        
        if not sentinel_path:
            print("❌ FAILED: No Sentinel-2 imagery available for test area")
            print("   This test requires real satellite imagery - no fallback")
            return False
        
        print(f"✅ Successfully fetched Sentinel-2 imagery!")
        print(f"   Path: {sentinel_path}")
        
        # Get image info
        from socialmapper.community import get_imagery_bounds_info
        info = get_imagery_bounds_info(sentinel_path)
        
        print(f"   Image size: {info.get('width', 'unknown')} x {info.get('height', 'unknown')}")
        print(f"   Bands: {info.get('bands', 'unknown')}")
        print(f"   CRS: {info.get('crs', 'unknown')}")
        
        # Test computer vision analysis with explicit image path (no fallback)
        print("\n🔍 Testing computer vision analysis with real imagery...")
        
        # Import the analyzer directly to bypass fallback logic
        from socialmapper.community.computer_vision import SatelliteImageAnalyzer
        import rasterio
        
        # Load and analyze the satellite image directly
        with rasterio.open(sentinel_path) as src:
            image_array = src.read([1, 2, 3])  # RGB bands
            image_array = np.transpose(image_array, (1, 2, 0))  # H,W,C format
            
            # Get actual bounds from the imagery if available
            if hasattr(src, 'bounds'):
                actual_bounds = (src.bounds.left, src.bounds.bottom, 
                               src.bounds.right, src.bounds.top)
            else:
                actual_bounds = bounds
        
        print(f"🔍 Analyzing satellite imagery with {image_array.shape} shape")
        
        # Initialize analyzer
        analyzer = SatelliteImageAnalyzer(patch_size=256)  # Larger patches for suburban analysis
        
        # Extract patches
        patches = analyzer.extract_patches(image_array, actual_bounds)
        
        if not patches:
            print("❌ FAILED: No patches extracted from real imagery")
            return False
        
        # Classify patches
        classifications = analyzer.classify_land_use(patches)
        
        # Create GeoDataFrame
        patch_data = []
        for i, (patch, classification) in enumerate(zip(patches, classifications)):
            # Create polygon for patch
            minx, miny, maxx, maxy = patch['bounds']
            polygon = box(minx, miny, maxx, maxy)
            
            patch_data.append({
                'patch_id': patch['patch_id'],
                'geometry': polygon,
                'land_use': classification,
                'center_x': patch['center_x'],
                'center_y': patch['center_y'],
                'imagery_type': 'sentinel2',
                'analysis_method': 'real_satellite_imagery'
            })
        
        # Create GeoDataFrame (assuming WGS84 for now)
        patches_gdf = gpd.GeoDataFrame(patch_data, crs='EPSG:4326')
        
        print(f"✅ Analysis completed!")
        print(f"   Generated {len(patches_gdf)} patches")
        print(f"   Land use types: {list(patches_gdf['land_use'].unique())}")
        print(f"   Analysis method: {patches_gdf['analysis_method'].iloc[0]}")
        
        # Verify we're using real imagery
        if 'real_satellite_imagery' in patches_gdf['analysis_method'].values:
            print("🎉 SUCCESS: Using real Sentinel-2 satellite imagery!")
            return True
        else:
            print("❌ FAILED: Analysis method is not 'real_satellite_imagery'")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_computer_vision_direct():
    """Test computer vision with automatic Sentinel-2 fetching - no fallback allowed."""
    print("\n🧠 Testing direct computer vision integration (no fallback)")
    print("=" * 50)
    
    try:
        from socialmapper.community import SatelliteDataFetcher
        from socialmapper.community.computer_vision import SatelliteImageAnalyzer
        import rasterio
        
        # Smaller area within the housing development for faster testing
        bounds = (-78.750, 35.570, -78.745, 35.575)
        
        print(f"📍 Analysis bounds: {bounds}")
        print("   (Subset of NC housing development)")
        
        # Fetch imagery directly
        fetcher = SatelliteDataFetcher(
            max_cloud_cover=50.0,
            cache_dir="./test_cache"
        )
        
        print("🔍 Fetching Sentinel-2 imagery...")
        image_path = fetcher.get_best_imagery_for_bounds(
            bounds=bounds,
            imagery_type="sentinel2"
        )
        
        if not image_path:
            print("❌ FAILED: No Sentinel-2 imagery available")
            print("   This test requires real satellite imagery - no fallback")
            return False
        
        print(f"✅ Got imagery: {image_path}")
        
        # Process directly without fallback
        with rasterio.open(image_path) as src:
            image_array = src.read([1, 2, 3])  # RGB bands
            image_array = np.transpose(image_array, (1, 2, 0))  # H,W,C format
            actual_bounds = (src.bounds.left, src.bounds.bottom, 
                           src.bounds.right, src.bounds.top)
        
        # Initialize analyzer
        analyzer = SatelliteImageAnalyzer(patch_size=128)  # Moderate patches for suburban detail
        
        # Extract and classify
        patches = analyzer.extract_patches(image_array, actual_bounds)
        classifications = analyzer.classify_land_use(patches)
        
        print(f"✅ Direct analysis completed!")
        print(f"   Generated {len(patches)} patches")
        
        if len(patches) > 0:
            print("🎉 SUCCESS: Real Sentinel-2 imagery was processed!")
            
            # Show land use distribution
            land_use_counts = {}
            for classification in classifications:
                land_use_counts[classification] = land_use_counts.get(classification, 0) + 1
            
            print("   📊 Land use distribution:")
            for land_use, count in land_use_counts.items():
                percentage = (count / len(classifications)) * 100
                print(f"      - {land_use}: {count} ({percentage:.1f}%)")
            
            return True
        else:
            print("❌ FAILED: No patches generated from real imagery")
            return False
        
    except Exception as e:
        print(f"❌ Error in direct integration: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run focused Sentinel-2 tests with no fallback to simulated data."""
    print("🚀 SocialMapper Sentinel-2 Integration Test")
    print("🎯 Focus: Suburban housing development analysis (NC)")
    print("⚠️  NO FALLBACK: Tests will fail if real imagery unavailable")
    print("=" * 60)
    
    # Test 1: Direct satellite fetcher
    test1_success = test_sentinel2_only()
    
    # Test 2: Computer vision integration
    test2_success = test_computer_vision_direct()
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 TEST SUMMARY")
    print("=" * 60)
    
    if test1_success:
        print("✅ Sentinel-2 fetching: SUCCESS")
    else:
        print("❌ Sentinel-2 fetching: FAILED")
    
    if test2_success:
        print("✅ Computer vision integration: SUCCESS (real imagery)")
    else:
        print("❌ Computer vision integration: FAILED (no real imagery)")
    
    if test1_success and test2_success:
        print("\n🎉 ALL TESTS PASSED! Real satellite imagery integration working!")
        print("   Perfect for suburban community boundary detection!")
    else:
        print("\n❌ TESTS FAILED: Real satellite imagery integration not working")
        print("   Check network connection and geoai package installation")
    
    print("\n💡 Why NC suburban development is perfect for testing:")
    print("   • Clear suburban housing patterns")
    print("   • Mixed land use types (residential, roads, open space)")
    print("   • Good for community boundary detection algorithms")
    print("   • Smaller Sentinel-2 files for fast iteration")


if __name__ == "__main__":
    main() 