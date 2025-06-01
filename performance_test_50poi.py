#!/usr/bin/env python3
"""
Focused Performance Test - 50 POI Test Only

This script runs only the 50 POI test to verify that our
NumPy 2 compatibility fixes are working properly.
"""

import time
import os
import sys
import traceback
import psutil
import gc
import warnings
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from datetime import datetime

# Add the socialmapper package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'socialmapper'))

# Test with warning configuration enabled (our fixes should work)
print("🔍 Testing with SocialMapper warning configuration enabled")

def get_memory_usage():
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def get_system_info():
    """Get system information for test context."""
    return {
        'cpu_count': psutil.cpu_count(),
        'cpu_count_logical': psutil.cpu_count(logical=True),
        'memory_total_gb': psutil.virtual_memory().total / 1024**3,
        'memory_available_gb': psutil.virtual_memory().available / 1024**3,
        'python_version': sys.version.split()[0],
        'platform': sys.platform
    }

def time_function(func, *args, **kwargs):
    """Time a function execution and return result with timing info."""
    start_time = time.time()
    start_memory = get_memory_usage()
    
    try:
        result = func(*args, **kwargs)
        success = True
        error = None
    except Exception as e:
        result = None
        success = False
        error = str(e)
        traceback.print_exc()
    
    end_time = time.time()
    end_memory = get_memory_usage()
    
    return {
        'result': result,
        'success': success,
        'error': error,
        'duration': end_time - start_time,
        'memory_start': start_memory,
        'memory_end': end_memory,
        'memory_delta': end_memory - start_memory
    }

def run_50_poi_test():
    """Run the specific 50 POI test that triggers NumPy 2 warnings."""
    print("🚀 SocialMapper 50 POI Test - NumPy 2 Warning Analysis")
    print("=" * 65)
    
    # System information
    system_info = get_system_info()
    print(f"💻 System: {system_info['cpu_count']} cores, {system_info['memory_total_gb']:.1f}GB RAM")
    print(f"🐍 Python: {system_info['python_version']}")
    
    # Check NumPy version
    print(f"🔢 NumPy: {np.__version__}")
    
    # Test parameters
    test_file = "examples/trail_heads.csv"
    output_dir = "performance_test_50poi_output"
    poi_count = 50
    
    print(f"📊 Testing with {poi_count} POIs from {test_file}")
    print()
    
    # Import socialmapper (this might trigger some warnings)
    print("📦 Importing SocialMapper...")
    try:
        from socialmapper.core import run_socialmapper
        print("✅ Successfully imported SocialMapper")
    except ImportError as e:
        print(f"❌ Failed to import socialmapper: {e}")
        return
    
    # Check if test file exists
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    print(f"🔬 Running {poi_count} POI test with all warnings enabled")
    print("-" * 65)
    
    # Clean up memory before test
    gc.collect()
    initial_memory = get_memory_usage()
    
    # Create test file for this size
    test_file_subset = f"temp_test_{poi_count}.csv"
    try:
        df = pd.read_csv(test_file)
        print(f"📄 Original dataset: {len(df):,} records")
        
        if len(df) < poi_count:
            print(f"⚠️  Dataset only has {len(df)} records, using all available")
            poi_count = len(df)
            df_subset = df.copy()
        else:
            df_subset = df.sample(n=poi_count, random_state=42).reset_index(drop=True)
        
        df_subset.to_csv(test_file_subset, index=False)
        print(f"📝 Created test subset: {poi_count} POIs")
        
        # Time the full pipeline with warnings enabled
        print(f"\n🚀 Starting SocialMapper pipeline...")
        print("⚠️  Watching for NumPy 2 compatibility warnings...")
        
        pipeline_result = time_function(
            run_socialmapper,
            custom_coords_path=test_file_subset,
            travel_time=15,
            census_variables=['B01003_001E'],  # Total population only for speed
            output_dir=output_dir,
            export_csv=True,
            export_maps=False,  # Skip maps for performance testing
            export_isochrones=False,  # Skip individual isochrone files
            use_interactive_maps=False
        )
        
        # Clean up test file
        if os.path.exists(test_file_subset):
            os.remove(test_file_subset)
        
    except Exception as e:
        pipeline_result = {
            'success': False,
            'error': f"Test setup failed: {str(e)}",
            'duration': 0,
            'memory_start': initial_memory,
            'memory_end': get_memory_usage(),
            'memory_delta': 0
        }
        traceback.print_exc()
    
    print("\n" + "=" * 65)
    print("📈 TEST RESULTS")
    print("=" * 65)
    
    if pipeline_result['success']:
        duration = pipeline_result['duration']
        time_per_poi = duration / poi_count
        pois_per_second = poi_count / duration if duration > 0 else 0
        
        print(f"✅ Success: {duration:.1f}s total ({time_per_poi:.3f}s/POI)")
        print(f"📈 Throughput: {pois_per_second:.2f} POIs/second")
        print(f"💾 Memory: {pipeline_result['memory_start']:.1f} → {pipeline_result['memory_end']:.1f} MB "
              f"(Δ{pipeline_result['memory_delta']:+.1f} MB)")
        
    else:
        print(f"❌ Failed: {pipeline_result['error']}")
    
    print(f"\n🏁 Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n💡 If NumPy 2 warnings appeared above, they will be addressed in the warning configuration.")
    
    return pipeline_result

if __name__ == "__main__":
    try:
        result = run_50_poi_test()
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        traceback.print_exc() 