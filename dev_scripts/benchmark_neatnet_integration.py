#!/usr/bin/env python3
"""
Benchmark script for testing neatnet integration performance improvements.

This script compares the performance of standard isochrone generation
with neatnet-enhanced isochrone generation to measure improvements.
"""

import os
import sys
import time
import json
from pathlib import Path

# Add the parent directory to the path so we can import socialmapper
sys.path.insert(0, str(Path(__file__).parent.parent))

from socialmapper.isochrone.neatnet_enhanced import (
    compare_isochrone_methods,
    create_enhanced_isochrones_from_poi_list,
    NEATNET_AVAILABLE
)
from socialmapper.query import query_pois
from socialmapper.util import PerformanceBenchmark

def create_test_poi_data(location: str = "Fuquay-Varina", state: str = "North Carolina", 
                        poi_type: str = "amenity", poi_name: str = "library") -> dict:
    """
    Create test POI data for benchmarking.
    
    Args:
        location: Location to search for POIs
        state: State name
        poi_type: Type of POI to search for
        poi_name: Name of POI to search for
        
    Returns:
        Dictionary with POI data
    """
    print(f"Querying POIs: {poi_type}={poi_name} in {location}, {state}")
    
    try:
        poi_data = query_pois(
            geocode_area=location,
            state=state,
            poi_type=poi_type,
            poi_name=poi_name,
            additional_tags={}
        )
        
        pois = poi_data.get('pois', [])
        print(f"Found {len(pois)} POIs for testing")
        
        # Limit to first 3 POIs for faster testing
        if len(pois) > 3:
            poi_data['pois'] = pois[:3]
            print(f"Limited to first 3 POIs for benchmark testing")
        
        return poi_data
        
    except Exception as e:
        print(f"Error querying POIs: {e}")
        # Create a fallback test POI
        return {
            'pois': [{
                'id': 'test_poi_1',
                'lat': 35.5849,
                'lon': -78.8000,
                'tags': {'name': 'Test Library'},
                'type': 'amenity'
            }],
            'metadata': {
                'source': 'test',
                'count': 1
            }
        }

def run_performance_benchmark():
    """Run comprehensive performance benchmark."""
    
    print("=" * 80)
    print("SocialMapper neatnet Integration Benchmark")
    print("=" * 80)
    
    # Check neatnet availability
    if not NEATNET_AVAILABLE:
        print("WARNING: neatnet is not available. This benchmark will only test standard methods.")
        print("To install neatnet: pip install neatnet")
        return
    
    print(f"neatnet is available: {NEATNET_AVAILABLE}")
    
    # Create output directory
    output_dir = Path("output/benchmark")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test POI data
    print("\nStep 1: Creating test POI data...")
    poi_data = create_test_poi_data()
    
    if not poi_data.get('pois'):
        print("ERROR: No POIs available for testing")
        return
    
    # Run comparison benchmark
    print("\nStep 2: Running performance comparison...")
    
    travel_time = 15  # 15-minute isochrones
    benchmark_results_path = output_dir / "neatnet_comparison_results.json"
    
    try:
        comparison_results = compare_isochrone_methods(
            poi_data=poi_data,
            travel_time_limit=travel_time,
            output_dir=str(output_dir),
            benchmark_results_path=str(benchmark_results_path)
        )
        
        print("\nStep 3: Analyzing results...")
        
        # Print summary
        print(f"\nBenchmark Summary:")
        print(f"Standard method time: {comparison_results['standard_time']:.2f}s")
        print(f"Enhanced method time: {comparison_results['enhanced_time']:.2f}s")
        
        if comparison_results['enhanced_time'] < comparison_results['standard_time']:
            speedup = comparison_results['standard_time'] / comparison_results['enhanced_time']
            time_saved = comparison_results['standard_time'] - comparison_results['enhanced_time']
            print(f"Performance improvement: {speedup:.2f}x speedup")
            print(f"Time saved: {time_saved:.2f}s")
        else:
            print("No performance improvement detected")
        
        print(f"\nDetailed results saved to: {benchmark_results_path}")
        
    except Exception as e:
        print(f"Error running benchmark: {e}")
        import traceback
        traceback.print_exc()

def run_individual_tests():
    """Run individual tests for different scenarios."""
    
    print("\n" + "=" * 80)
    print("Individual Test Scenarios")
    print("=" * 80)
    
    output_dir = Path("output/individual_tests")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Test scenarios
    scenarios = [
        {
            "name": "Small Town Libraries",
            "location": "Fuquay-Varina",
            "state": "North Carolina",
            "poi_type": "amenity",
            "poi_name": "library",
            "travel_time": 10
        },
        {
            "name": "Urban Schools",
            "location": "Raleigh",
            "state": "North Carolina", 
            "poi_type": "amenity",
            "poi_name": "school",
            "travel_time": 15
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\nScenario {i}: {scenario['name']}")
        print("-" * 40)
        
        try:
            # Get POI data
            poi_data = create_test_poi_data(
                location=scenario['location'],
                state=scenario['state'],
                poi_type=scenario['poi_type'],
                poi_name=scenario['poi_name']
            )
            
            if not poi_data.get('pois'):
                print(f"No POIs found for scenario {i}")
                continue
            
            # Test enhanced method
            scenario_output = output_dir / f"scenario_{i}"
            scenario_output.mkdir(exist_ok=True)
            
            benchmark_path = scenario_output / "benchmark.json"
            
            print(f"Running enhanced isochrone generation...")
            start_time = time.time()
            
            results = create_enhanced_isochrones_from_poi_list(
                poi_data=poi_data,
                travel_time_limit=scenario['travel_time'],
                output_dir=str(scenario_output),
                save_individual_files=True,
                combine_results=False,
                use_neatnet=True,
                benchmark_results_path=str(benchmark_path)
            )
            
            elapsed_time = time.time() - start_time
            
            print(f"Completed in {elapsed_time:.2f}s")
            print(f"Generated {len(results) if isinstance(results, list) else 1} isochrone(s)")
            print(f"Results saved to: {scenario_output}")
            
        except Exception as e:
            print(f"Error in scenario {i}: {e}")

def main():
    """Main benchmark execution."""
    
    if len(sys.argv) > 1 and sys.argv[1] == "--individual":
        run_individual_tests()
    else:
        run_performance_benchmark()
    
    print("\n" + "=" * 80)
    print("Benchmark completed!")
    print("=" * 80)

if __name__ == "__main__":
    main() 