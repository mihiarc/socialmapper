#!/usr/bin/env python3
"""
Performance testing script for Optimized SocialMapper pipeline.
Tests the trail_heads.csv file through the modernized system to validate optimizations.

This script provides a simpler alternative to the comprehensive benchmark,
focusing on quick performance validation and bottleneck identification.
"""

import time
import os
import sys
import traceback
import psutil
import gc
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from datetime import datetime

# Add the socialmapper package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'socialmapper'))

# Configure environment for performance testing
from socialmapper.util.warnings_config import setup_benchmark_environment
setup_benchmark_environment(verbose=False)  # Quiet setup for cleaner output

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

def analyze_dataset(file_path: str) -> Dict[str, Any]:
    """Analyze the test dataset and return key metrics."""
    if not os.path.exists(file_path):
        return {'error': f"File not found: {file_path}"}
    
    try:
        df = pd.read_csv(file_path)
        
        # Basic dataset info
        info = {
            'total_records': len(df),
            'columns': list(df.columns),
            'file_size_mb': os.path.getsize(file_path) / (1024 * 1024),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024)
        }
        
        # Geographic distribution
        if 'state' in df.columns:
            info['states'] = sorted(df['state'].unique().tolist())
            info['state_counts'] = df['state'].value_counts().to_dict()
        
        if 'latitude' in df.columns and 'longitude' in df.columns:
            info['lat_range'] = (df['latitude'].min(), df['latitude'].max())
            info['lon_range'] = (df['longitude'].min(), df['longitude'].max())
            
            # Calculate geographic spread
            lat_span = info['lat_range'][1] - info['lat_range'][0]
            lon_span = info['lon_range'][1] - info['lon_range'][0]
            info['geographic_spread'] = {
                'lat_degrees': lat_span,
                'lon_degrees': lon_span,
                'area_estimate_sq_deg': lat_span * lon_span
            }
        
        return info
        
    except Exception as e:
        return {'error': f"Failed to analyze dataset: {str(e)}"}

def run_performance_test():
    """Run comprehensive performance test on trail_heads.csv."""
    print("🚀 SocialMapper Performance Test - Optimized System")
    print("=" * 65)
    
    # System information
    system_info = get_system_info()
    print(f"💻 System: {system_info['cpu_count']} cores, {system_info['memory_total_gb']:.1f}GB RAM")
    print(f"🐍 Python: {system_info['python_version']}")
    print()
    
    # Test parameters
    test_file = "examples/trail_heads.csv"
    output_dir = "performance_test_output"
    
    # Analyze dataset
    print(f"📊 Analyzing test dataset: {test_file}")
    dataset_info = analyze_dataset(test_file)
    
    if 'error' in dataset_info:
        print(f"❌ {dataset_info['error']}")
        return
    
    print(f"   📄 Records: {dataset_info['total_records']:,}")
    print(f"   💾 File size: {dataset_info['file_size_mb']:.1f} MB")
    print(f"   🗂️  Memory usage: {dataset_info['memory_usage_mb']:.1f} MB")
    
    if 'states' in dataset_info:
        print(f"   🗺️  States: {', '.join(dataset_info['states'])}")
        
    if 'geographic_spread' in dataset_info:
        spread = dataset_info['geographic_spread']
        print(f"   📍 Geographic spread: {spread['lat_degrees']:.1f}° × {spread['lon_degrees']:.1f}°")
    
    print()
    
    # Import socialmapper
    try:
        from socialmapper.core import run_socialmapper
        print("✅ Successfully imported optimized SocialMapper")
    except ImportError as e:
        print(f"❌ Failed to import socialmapper: {e}")
        return
    
    # Test different POI counts to analyze scaling
    total_records = dataset_info['total_records']
    test_sizes = [10, 50, 100, 500, 1000]
    
    # Add full dataset if reasonable size
    if total_records <= 3000:
        test_sizes.append(total_records)
    
    # Filter test sizes to available data
    test_sizes = [size for size in test_sizes if size <= total_records]
    
    print(f"🧪 Testing with POI counts: {test_sizes}")
    print()
    
    results = {}
    
    for poi_count in test_sizes:
        print(f"🔬 Testing {poi_count:,} POIs")
        print("-" * 45)
        
        # Clean up memory before each test
        gc.collect()
        initial_memory = get_memory_usage()
        
        # Create test file for this size
        test_file_subset = f"temp_test_{poi_count}.csv"
        try:
            df = pd.read_csv(test_file)
            df_subset = df.sample(n=poi_count, random_state=42).reset_index(drop=True)
            df_subset.to_csv(test_file_subset, index=False)
            
            # Time the full pipeline
            pipeline_result = time_function(
                run_socialmapper,
                custom_coords_path=test_file_subset,
                travel_time=15,
                census_variables=['B01003_001E'],  # Total population only for speed
                output_dir=f"{output_dir}_{poi_count}",
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
        
        results[poi_count] = pipeline_result
        
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
            # Continue with other tests even if one fails
        
        print()
        
        # Brief pause between tests
        time.sleep(1)
    
    # Performance analysis
    print("📈 PERFORMANCE ANALYSIS")
    print("=" * 65)
    
    successful_results = {k: v for k, v in results.items() if v['success']}
    
    if not successful_results:
        print("❌ No successful test runs to analyze")
        return results
    
    # Performance table
    print(f"{'POI Count':<10} {'Time(s)':<10} {'Time/POI':<12} {'POIs/sec':<10} {'Memory(MB)':<12}")
    print("-" * 65)
    
    scaling_data = []
    for poi_count in sorted(successful_results.keys()):
        result = successful_results[poi_count]
        duration = result['duration']
        time_per_poi = duration / poi_count
        pois_per_second = poi_count / duration
        memory_peak = result['memory_end']
        
        scaling_data.append({
            'poi_count': poi_count,
            'duration': duration,
            'time_per_poi': time_per_poi,
            'pois_per_second': pois_per_second,
            'memory_peak': memory_peak
        })
        
        print(f"{poi_count:<10,} {duration:<10.1f} {time_per_poi:<12.4f} {pois_per_second:<10.2f} {memory_peak:<12.1f}")
    
    # Scaling analysis
    if len(scaling_data) >= 2:
        print(f"\n🔍 SCALING ANALYSIS:")
        
        # Calculate scaling efficiency
        first = scaling_data[0]
        last = scaling_data[-1]
        
        size_ratio = last['poi_count'] / first['poi_count']
        time_ratio = last['duration'] / first['duration']
        scaling_efficiency = size_ratio / time_ratio
        
        print(f"   Size scaling: {size_ratio:.1f}x ({first['poi_count']:,} → {last['poi_count']:,} POIs)")
        print(f"   Time scaling: {time_ratio:.1f}x ({first['duration']:.1f}s → {last['duration']:.1f}s)")
        print(f"   Efficiency: {scaling_efficiency:.2f} (1.0 = perfect linear scaling)")
        
        if scaling_efficiency > 0.8:
            print("   ✅ Excellent scaling performance!")
        elif scaling_efficiency > 0.6:
            print("   ✅ Good scaling performance")
        elif scaling_efficiency > 0.4:
            print("   ⚠️  Moderate scaling - some optimization opportunities")
        else:
            print("   ⚠️  Poor scaling - significant optimization needed")
        
        # Performance trend
        time_per_poi_trend = last['time_per_poi'] / first['time_per_poi']
        if time_per_poi_trend < 0.8:
            print(f"   🚀 Super-linear performance: Time/POI improved by {(1-time_per_poi_trend)*100:.1f}%")
        elif time_per_poi_trend < 1.2:
            print(f"   ✅ Linear performance: Time/POI stable")
        else:
            print(f"   ⚠️  Sub-linear performance: Time/POI increased by {(time_per_poi_trend-1)*100:.1f}%")
    
    # Full dataset projection
    if total_records not in successful_results and successful_results:
        avg_time_per_poi = np.mean([data['time_per_poi'] for data in scaling_data])
        full_dataset_time = total_records * avg_time_per_poi
        
        print(f"\n🎯 FULL DATASET PROJECTION:")
        print(f"   Dataset size: {total_records:,} POIs")
        print(f"   Estimated time: {full_dataset_time:.1f}s ({full_dataset_time/60:.1f} minutes)")
        
        if full_dataset_time > 3600:
            print(f"   ⚠️  Long processing time - consider batch processing")
        elif full_dataset_time > 600:
            print(f"   ⚠️  Moderate processing time - acceptable for batch jobs")
        else:
            print(f"   ✅ Fast processing time - suitable for interactive use")
    
    # Memory analysis
    if scaling_data:
        max_memory = max(data['memory_peak'] for data in scaling_data)
        avg_memory_per_poi = np.mean([data['memory_peak'] / data['poi_count'] for data in scaling_data])
        
        print(f"\n💾 MEMORY ANALYSIS:")
        print(f"   Peak memory: {max_memory:.1f} MB")
        print(f"   Average memory/POI: {avg_memory_per_poi:.2f} MB")
        
        if max_memory > 2000:
            print("   ⚠️  High memory usage - monitor for large datasets")
        elif max_memory > 1000:
            print("   ⚠️  Moderate memory usage - acceptable for most systems")
        else:
            print("   ✅ Low memory usage - very efficient")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if successful_results:
        best_result = max(scaling_data, key=lambda x: x['pois_per_second'])
        print(f"   🏆 Best performance: {best_result['pois_per_second']:.2f} POIs/sec at {best_result['poi_count']:,} POIs")
        
        if len(scaling_data) >= 2:
            if scaling_efficiency > 0.8:
                print("   ✅ System is well-optimized for scaling")
            else:
                print("   🔧 Consider optimizing for better scaling:")
                print("      - Vectorize remaining operations")
                print("      - Implement parallel processing")
                print("      - Optimize memory usage patterns")
    
    print(f"\n🏁 Performance test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return results

if __name__ == "__main__":
    try:
        results = run_performance_test()
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        traceback.print_exc() 