#!/usr/bin/env python3
"""
Urban vs Rural benchmark for neatnet integration.

This script tests the hypothesis that neatnet provides benefits in dense urban
areas but may cause performance regression in sparse rural areas.
"""

import os
import sys
import time
import json
from pathlib import Path

# Add the parent directory to the path so we can import socialmapper
sys.path.insert(0, str(Path(__file__).parent.parent))

from socialmapper.isochrone.neatnet_enhanced import (
    create_enhanced_isochrones_from_poi_list,
    NEATNET_AVAILABLE
)
from socialmapper.isochrone import create_isochrones_from_poi_list
from socialmapper.util import PerformanceBenchmark

def create_test_scenarios():
    """Create test scenarios for urban vs rural comparison."""
    
    scenarios = [
        {
            "name": "Dense Urban - Manhattan",
            "type": "urban_dense",
            "pois": [
                {
                    'id': 'manhattan_library_1',
                    'lat': 40.7589,  # New York Public Library
                    'lon': -73.9851,
                    'tags': {'name': 'New York Public Library'},
                    'type': 'amenity'
                },
                {
                    'id': 'manhattan_library_2', 
                    'lat': 40.7505,  # Nearby library
                    'lon': -73.9934,
                    'tags': {'name': 'Manhattan Library Branch'},
                    'type': 'amenity'
                }
            ]
        },
        {
            "name": "Suburban - Raleigh",
            "type": "suburban",
            "pois": [
                {
                    'id': 'raleigh_library_1',
                    'lat': 35.7796,  # Raleigh
                    'lon': -78.6382,
                    'tags': {'name': 'Raleigh Public Library'},
                    'type': 'amenity'
                },
                {
                    'id': 'raleigh_library_2',
                    'lat': 35.7896,  # Nearby
                    'lon': -78.6282,
                    'tags': {'name': 'North Raleigh Library'},
                    'type': 'amenity'
                }
            ]
        },
        {
            "name": "Rural - Small Town",
            "type": "rural",
            "pois": [
                {
                    'id': 'rural_library_1',
                    'lat': 35.5849,  # Fuquay-Varina (small town)
                    'lon': -78.8000,
                    'tags': {'name': 'Fuquay-Varina Library'},
                    'type': 'amenity'
                },
                {
                    'id': 'rural_library_2',
                    'lat': 35.5949,  # Nearby rural area
                    'lon': -78.7900,
                    'tags': {'name': 'Rural Branch Library'},
                    'type': 'amenity'
                }
            ]
        },
        {
            "name": "Very Dense Urban - San Francisco",
            "type": "urban_very_dense",
            "pois": [
                {
                    'id': 'sf_library_1',
                    'lat': 37.7749,  # San Francisco
                    'lon': -122.4194,
                    'tags': {'name': 'SF Main Library'},
                    'type': 'amenity'
                },
                {
                    'id': 'sf_library_2',
                    'lat': 37.7849,  # Nearby
                    'lon': -122.4094,
                    'tags': {'name': 'SF Branch Library'},
                    'type': 'amenity'
                }
            ]
        }
    ]
    
    return scenarios

def benchmark_scenario(scenario, travel_time=10):
    """Benchmark a single scenario comparing standard vs enhanced methods."""
    
    print(f"\n{'='*60}")
    print(f"Testing: {scenario['name']} ({scenario['type']})")
    print(f"{'='*60}")
    
    poi_data = {
        'pois': scenario['pois'],
        'metadata': {
            'source': 'test',
            'count': len(scenario['pois'])
        }
    }
    
    results = {
        'scenario': scenario['name'],
        'type': scenario['type'],
        'poi_count': len(scenario['pois']),
        'travel_time': travel_time
    }
    
    # Test standard method
    print("Testing standard method...")
    try:
        start_time = time.time()
        standard_result = create_isochrones_from_poi_list(
            poi_data=poi_data,
            travel_time_limit=travel_time,
            output_dir=f"output/benchmark_urban_rural/{scenario['type']}/standard",
            save_individual_files=False,
            combine_results=False
        )
        standard_time = time.time() - start_time
        results['standard_time'] = standard_time
        results['standard_success'] = True
        print(f"Standard method: {standard_time:.2f}s")
        
    except Exception as e:
        print(f"Standard method failed: {e}")
        results['standard_time'] = float('inf')
        results['standard_success'] = False
    
    # Test enhanced method
    print("Testing enhanced method...")
    try:
        start_time = time.time()
        enhanced_result = create_enhanced_isochrones_from_poi_list(
            poi_data=poi_data,
            travel_time_limit=travel_time,
            output_dir=f"output/benchmark_urban_rural/{scenario['type']}/enhanced",
            save_individual_files=False,
            combine_results=False,
            use_neatnet=True
        )
        enhanced_time = time.time() - start_time
        results['enhanced_time'] = enhanced_time
        results['enhanced_success'] = True
        print(f"Enhanced method: {enhanced_time:.2f}s")
        
    except Exception as e:
        print(f"Enhanced method failed: {e}")
        results['enhanced_time'] = float('inf')
        results['enhanced_success'] = False
    
    # Calculate performance metrics
    if results['standard_success'] and results['enhanced_success']:
        speedup = results['standard_time'] / results['enhanced_time']
        time_saved = results['standard_time'] - results['enhanced_time']
        improvement_pct = ((results['standard_time'] - results['enhanced_time']) / results['standard_time']) * 100
        
        results['speedup'] = speedup
        results['time_saved'] = time_saved
        results['improvement_percent'] = improvement_pct
        
        print(f"\nResults:")
        print(f"  Speedup: {speedup:.2f}x")
        print(f"  Time saved: {time_saved:.2f}s")
        print(f"  Improvement: {improvement_pct:.1f}%")
        
        if speedup > 1.0:
            print(f"  ✅ Enhanced method is FASTER")
        else:
            print(f"  ❌ Enhanced method is SLOWER")
    
    return results

def analyze_results(all_results):
    """Analyze results across all scenarios."""
    
    print(f"\n{'='*80}")
    print(f"COMPREHENSIVE ANALYSIS")
    print(f"{'='*80}")
    
    # Group by scenario type
    by_type = {}
    for result in all_results:
        scenario_type = result['type']
        if scenario_type not in by_type:
            by_type[scenario_type] = []
        by_type[scenario_type].append(result)
    
    print(f"\nPerformance by Area Type:")
    print(f"{'Type':<20} {'Scenarios':<10} {'Avg Speedup':<12} {'Avg Improvement':<15} {'Status':<10}")
    print("-" * 80)
    
    for area_type, results in by_type.items():
        successful_results = [r for r in results if r.get('speedup') is not None]
        
        if successful_results:
            avg_speedup = sum(r['speedup'] for r in successful_results) / len(successful_results)
            avg_improvement = sum(r['improvement_percent'] for r in successful_results) / len(successful_results)
            
            if avg_speedup > 1.05:  # 5% improvement threshold
                status = "✅ BETTER"
            elif avg_speedup > 0.95:  # Within 5%
                status = "➖ NEUTRAL"
            else:
                status = "❌ WORSE"
            
            print(f"{area_type:<20} {len(results):<10} {avg_speedup:<12.2f} {avg_improvement:<15.1f}% {status:<10}")
        else:
            print(f"{area_type:<20} {len(results):<10} {'N/A':<12} {'N/A':<15} {'FAILED':<10}")
    
    # Detailed results
    print(f"\nDetailed Results:")
    for result in all_results:
        print(f"\n{result['scenario']} ({result['type']}):")
        if result.get('speedup'):
            print(f"  Standard: {result['standard_time']:.2f}s")
            print(f"  Enhanced: {result['enhanced_time']:.2f}s") 
            print(f"  Speedup: {result['speedup']:.2f}x ({result['improvement_percent']:+.1f}%)")
        else:
            print(f"  Failed to complete benchmark")
    
    # Recommendations
    print(f"\n{'='*60}")
    print(f"RECOMMENDATIONS")
    print(f"{'='*60}")
    
    urban_results = [r for r in all_results if 'urban' in r['type'] and r.get('speedup')]
    rural_results = [r for r in all_results if 'rural' in r['type'] and r.get('speedup')]
    
    if urban_results:
        urban_avg = sum(r['speedup'] for r in urban_results) / len(urban_results)
        print(f"Urban areas average speedup: {urban_avg:.2f}x")
        if urban_avg > 1.0:
            print("✅ Recommend enabling neatnet for urban areas")
        else:
            print("❌ neatnet not beneficial for urban areas")
    
    if rural_results:
        rural_avg = sum(r['speedup'] for r in rural_results) / len(rural_results)
        print(f"Rural areas average speedup: {rural_avg:.2f}x")
        if rural_avg > 1.0:
            print("✅ Recommend enabling neatnet for rural areas")
        else:
            print("❌ neatnet not beneficial for rural areas")
    
    # Suggest adaptive strategy
    print(f"\n💡 ADAPTIVE STRATEGY SUGGESTION:")
    print(f"   Implement network density detection to automatically enable/disable neatnet")
    print(f"   based on the characteristics of the downloaded network.")

def main():
    """Main benchmark execution."""
    
    print("=" * 80)
    print("Urban vs Rural neatnet Performance Benchmark")
    print("=" * 80)
    
    if not NEATNET_AVAILABLE:
        print("ERROR: neatnet is not available. Please install it first.")
        return
    
    # Create output directory
    output_dir = Path("output/benchmark_urban_rural")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get test scenarios
    scenarios = create_test_scenarios()
    
    print(f"Testing {len(scenarios)} scenarios...")
    
    all_results = []
    
    # Run benchmarks for each scenario
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n[{i}/{len(scenarios)}] Running scenario: {scenario['name']}")
        
        try:
            result = benchmark_scenario(scenario, travel_time=10)
            all_results.append(result)
        except Exception as e:
            print(f"Error in scenario {scenario['name']}: {e}")
            continue
    
    # Save results
    results_file = output_dir / "urban_vs_rural_results.json"
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    # Analyze and display results
    analyze_results(all_results)
    
    print(f"\nDetailed results saved to: {results_file}")
    print(f"\n{'='*80}")
    print(f"Benchmark completed!")
    print(f"{'='*80}")

if __name__ == "__main__":
    main() 