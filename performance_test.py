#!/usr/bin/env python3
"""
Performance testing script for SocialMapper pipeline.
Tests the trail_heads.csv file through the system to identify bottlenecks.
"""

import time
import os
import sys
import traceback
import psutil
import gc
from typing import Dict, Any
import pandas as pd

# Add the socialmapper package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'socialmapper'))

def get_memory_usage():
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

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

def run_performance_test():
    """Run performance test on trail_heads.csv."""
    print("🚀 Starting SocialMapper Performance Test")
    print("=" * 60)
    
    # Test parameters
    test_file = "examples/trail_heads.csv"
    output_dir = "performance_test_output"
    
    # Check if test file exists
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    # Load and inspect the test data
    print(f"📊 Loading test data: {test_file}")
    df = pd.read_csv(test_file)
    print(f"   - Total records: {len(df)}")
    print(f"   - Columns: {list(df.columns)}")
    print(f"   - States: {df['state'].unique()}")
    print(f"   - Sample records:")
    print(df.head(3).to_string(index=False))
    print()
    
    # Test different POI counts to identify scaling bottlenecks
    test_sizes = [10, 50, 100, 500]  # Start with smaller sizes
    
    # Import socialmapper
    try:
        from socialmapper.core import run_socialmapper
        print("✅ Successfully imported socialmapper")
    except ImportError as e:
        print(f"❌ Failed to import socialmapper: {e}")
        return
    
    results = {}
    
    for poi_count in test_sizes:
        if poi_count > len(df):
            print(f"⏭️  Skipping {poi_count} POIs (exceeds dataset size of {len(df)})")
            continue
            
        print(f"\n🧪 Testing with {poi_count} POIs")
        print("-" * 40)
        
        # Clean up memory before each test
        gc.collect()
        
        # Time the full pipeline
        pipeline_result = time_function(
            run_socialmapper,
            custom_coords_path=test_file,
            travel_time=15,
            census_variables=["total_population", "median_household_income"],
            output_dir=f"{output_dir}_{poi_count}",
            export_csv=True,
            export_maps=False,  # Skip maps for performance testing
            export_isochrones=False,  # Skip individual isochrone files
            max_poi_count=poi_count
        )
        
        results[poi_count] = pipeline_result
        
        if pipeline_result['success']:
            print(f"✅ Pipeline completed successfully")
            print(f"   - Duration: {pipeline_result['duration']:.2f} seconds")
            print(f"   - Memory usage: {pipeline_result['memory_start']:.1f} → {pipeline_result['memory_end']:.1f} MB")
            print(f"   - Memory delta: {pipeline_result['memory_delta']:.1f} MB")
            
            # Extract detailed results
            result_data = pipeline_result['result']
            if result_data:
                poi_data = result_data.get('poi_data', {})
                isochrones = result_data.get('isochrones')
                census_data = result_data.get('census_data')
                
                print(f"   - POIs processed: {len(poi_data.get('pois', []))}")
                if isochrones is not None:
                    print(f"   - Isochrones generated: {len(isochrones)}")
                if census_data is not None:
                    print(f"   - Census block groups: {len(census_data)}")
        else:
            print(f"❌ Pipeline failed: {pipeline_result['error']}")
            break  # Stop testing larger sizes if we hit an error
    
    # Performance analysis
    print("\n📈 Performance Analysis")
    print("=" * 60)
    
    successful_results = {k: v for k, v in results.items() if v['success']}
    
    if len(successful_results) >= 2:
        # Calculate scaling metrics
        sizes = sorted(successful_results.keys())
        times = [successful_results[size]['duration'] for size in sizes]
        memories = [successful_results[size]['memory_delta'] for size in sizes]
        
        print("POI Count | Duration (s) | Memory (MB) | Time/POI (s) | Scaling")
        print("-" * 65)
        
        for i, size in enumerate(sizes):
            duration = times[i]
            memory = memories[i]
            time_per_poi = duration / size
            
            if i > 0:
                prev_size = sizes[i-1]
                prev_time = times[i-1]
                scaling_factor = (duration / prev_time) / (size / prev_size)
                scaling_str = f"{scaling_factor:.2f}x"
            else:
                scaling_str = "baseline"
            
            print(f"{size:8d} | {duration:11.2f} | {memory:10.1f} | {time_per_poi:11.4f} | {scaling_str}")
        
        # Identify potential bottlenecks
        print(f"\n🔍 Bottleneck Analysis:")
        
        # Check if scaling is worse than linear
        if len(sizes) >= 2:
            last_scaling = (times[-1] / times[0]) / (sizes[-1] / sizes[0])
            if last_scaling > 1.5:
                print(f"⚠️  Non-linear scaling detected: {last_scaling:.2f}x")
                print("   This suggests O(n²) or worse complexity in some operations")
            elif last_scaling > 1.2:
                print(f"⚠️  Slightly super-linear scaling: {last_scaling:.2f}x")
                print("   Some operations may have higher than O(n) complexity")
            else:
                print(f"✅ Good linear scaling: {last_scaling:.2f}x")
        
        # Memory analysis
        max_memory = max(memories)
        if max_memory > 1000:  # > 1GB
            print(f"⚠️  High memory usage detected: {max_memory:.1f} MB")
        
        # Time per POI analysis
        time_per_poi_values = [times[i] / sizes[i] for i in range(len(sizes))]
        if len(time_per_poi_values) >= 2:
            time_increase = time_per_poi_values[-1] / time_per_poi_values[0]
            if time_increase > 1.5:
                print(f"⚠️  Time per POI increasing significantly: {time_increase:.2f}x")
                print("   This indicates algorithmic inefficiency with larger datasets")
    
    # Recommendations
    print(f"\n💡 Optimization Recommendations:")
    print("-" * 40)
    
    if successful_results:
        max_tested = max(successful_results.keys())
        avg_time_per_poi = sum(successful_results[size]['duration'] / size for size in successful_results.keys()) / len(successful_results)
        
        print(f"1. Current performance: ~{avg_time_per_poi:.3f} seconds per POI")
        
        # Estimate time for full dataset
        full_dataset_estimate = len(df) * avg_time_per_poi
        if full_dataset_estimate > 3600:  # > 1 hour
            print(f"2. ⚠️  Full dataset ({len(df)} POIs) estimated time: {full_dataset_estimate/3600:.1f} hours")
            print("   Consider implementing batch processing or parallelization")
        elif full_dataset_estimate > 300:  # > 5 minutes
            print(f"2. ⚠️  Full dataset ({len(df)} POIs) estimated time: {full_dataset_estimate/60:.1f} minutes")
            print("   Consider optimizing the most time-consuming operations")
        else:
            print(f"2. ✅ Full dataset ({len(df)} POIs) estimated time: {full_dataset_estimate:.1f} seconds")
        
        print("3. Key areas to investigate for optimization:")
        print("   - Isochrone generation (road network downloads)")
        print("   - Census block group intersection calculations")
        print("   - Travel distance calculations")
        print("   - Memory usage patterns")
    
    print(f"\n🏁 Performance test completed!")
    return results

if __name__ == "__main__":
    results = run_performance_test() 