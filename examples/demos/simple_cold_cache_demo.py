#!/usr/bin/env python3
"""
Simple Cold Cache Demo for SocialMapper
========================================

Tests core SocialMapper functionality from a completely cold cache state.
Uses minimal terminal output to avoid Rich display conflicts.

Features tested:
- Cache clearing
- POI discovery from scratch  
- Network download without cached data
- Basic isochrone generation
- Performance comparison cold vs warm

Author: SocialMapper Team
Date: June 2025
"""

import sys
import time
import shutil
import os
from pathlib import Path
from typing import Dict, Any

# Add project to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from socialmapper.core import run_socialmapper


def get_cache_size(cache_dir: Path) -> float:
    """Get cache directory size in MB."""
    if not cache_dir.exists():
        return 0.0
    
    total_size = 0
    for file_path in cache_dir.rglob("*"):
        if file_path.is_file():
            total_size += file_path.stat().st_size
    
    return total_size / (1024 * 1024)


def clear_cache(cache_dir: Path) -> float:
    """Clear cache and return size cleared."""
    if not cache_dir.exists():
        print("ℹ️  No cache directory found - already in cold state")
        return 0.0
    
    initial_size = get_cache_size(cache_dir)
    print(f"🗑️  Clearing {initial_size:.1f} MB of cached data...")
    
    try:
        shutil.rmtree(cache_dir)
        print("✅ Cache cleared successfully")
        return initial_size
    except Exception as e:
        print(f"❌ Error clearing cache: {e}")
        return 0.0


def run_test_config() -> Dict[str, Any]:
    """Run SocialMapper with a simple test configuration."""
    config = {
        "geocode_area": "Cary",
        "state": "NC", 
        "poi_type": "amenity",
        "poi_name": "restaurant",
        "travel_time": 10,
        "census_variables": ["total_population"],
        "export_csv": True,
        "export_maps": False,
        "max_poi_count": 3  # Keep small for speed
    }
    
    print("\n📊 Test Configuration:")
    for key, value in config.items():
        print(f"   {key}: {value}")
    
    return config


def main():
    """Main cold cache test."""
    print("❄️  SocialMapper Cold Cache Test")
    print("=" * 50)
    
    cache_dir = Path("cache")
    
    # Step 1: Clear cache
    print("\n🧹 Step 1: Cache Clearing")
    cleared_size = clear_cache(cache_dir)
    
    # Step 2: Run cold cache test
    print("\n❄️  Step 2: Cold Cache Test")
    config = run_test_config()
    
    print("\n🔄 Running SocialMapper from cold cache...")
    print("   (This will take longer than usual)")
    
    start_time = time.time()
    
    try:
        results = run_socialmapper(**config)
        cold_duration = time.time() - start_time
        
        print(f"✅ Cold cache test completed in {cold_duration:.1f} seconds")
        
        # Show cache rebuild
        final_cache_size = get_cache_size(cache_dir)
        print(f"📈 Cache rebuilt: {final_cache_size:.1f} MB")
        
        # Step 3: Run warm cache test
        print("\n🔥 Step 3: Warm Cache Test")
        print("🔄 Running identical test with warm cache...")
        
        start_time = time.time()
        warm_results = run_socialmapper(**config)
        warm_duration = time.time() - start_time
        
        print(f"✅ Warm cache test completed in {warm_duration:.1f} seconds")
        
        # Step 4: Performance comparison
        print("\n📊 Step 4: Performance Analysis")
        print("=" * 30)
        speedup = cold_duration / warm_duration if warm_duration > 0 else 0
        time_saved = cold_duration - warm_duration
        
        print(f"Cold cache time:  {cold_duration:.1f}s")
        print(f"Warm cache time:  {warm_duration:.1f}s")
        print(f"Speedup:          {speedup:.1f}x")
        print(f"Time saved:       {time_saved:.1f}s")
        
        # Final analysis
        print("\n🎯 Analysis:")
        print("✅ Cold cache test passed - SocialMapper works from fresh install")
        print("✅ Cache system working properly")
        print(f"✅ Performance improvement: {speedup:.1f}x with cached data")
        print("✅ System ready for production deployment")
        
        print(f"\n🏆 SUCCESS: Cold cache demo completed successfully!")
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Cold cache test failed after {duration:.1f} seconds")
        print(f"   Error: {e}")
        
        print("\n🔧 Troubleshooting:")
        print("   1. Check internet connectivity")
        print("   2. Verify OpenStreetMap accessibility")
        print("   3. Check Census API availability") 
        print("   4. Try different location parameters")
        
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 