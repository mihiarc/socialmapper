#!/usr/bin/env python3
"""
Network size impact benchmark for neatnet integration.

This script tests how travel time (and thus network size) affects the
performance characteristics of different optimization strategies.
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

def create_test_scenario():
    """Create a single test scenario for detailed analysis."""
    
    # Use Manhattan as it's dense and will show network size effects clearly
    scenario = {
        "name": "Manhattan Library",
        "type": "urban_dense",
        "pois": [
            {
                'id': 'manhattan_library_1',
                'lat': 40.7589,  # New York Public Library
                'lon': -73.9851,
                'tags': {'name': 'New York Public Library'},
                'type': 'amenity'
            }
        ]
    }
    
    return scenario

def benchmark_travel_time(travel_time, poi_data):
    """Benchmark different methods for a specific travel time."""
    
    print(f"\n{'='*60}")
    print(f"Testing Travel Time: {travel_time} minutes")
    print(f"{'='*60}")
    
    results = {
        'travel_time': travel_time,
        'methods': {}
    }
    
    # Clear cache before each travel time test
    clear_network_cache()
    
    # Test configurations
    test_configs = [
        {
            'name': 'standard',
            'description': 'Standard method',
            'use_enhanced': False
        },
        {
            'name': 'cache_only',
            'description': 'Enhanced with caching only',
            'use_enhanced': True,
            'kwargs': {'use_neatnet': False}
        },
        {
            'name': 'neatnet_full',
            'description': 'Enhanced with neatnet',
            'use_enhanced': True,
            'kwargs': {'use_neatnet': True}
        }
    ]
    
    for config in test_configs:
        print(f"\nTesting {config['description']}...")
        
        try:
            start_time = time.time()
            
            if config['use_enhanced']:
                result = create_enhanced_isochrones_from_poi_list(
                    poi_data=poi_data,
                    travel_time_limit=travel_time,
                    output_dir=f"output/network_size_test/{travel_time}min/{config['name']}",
                    save_individual_files=False,
                    combine_results=False,
                    **config.get('kwargs', {})
                )
            else:
                result = create_isochrones_from_poi_list(
                    poi_data=poi_data,
                    travel_time_limit=travel_time,
                    output_dir=f"output/network_size_test/{travel_time}min/{config['name']}",
                    save_individual_files=False,
                    combine_results=False
                )
            
            elapsed_time = time.time() - start_time
            
            results['methods'][config['name']] = {
                'time': elapsed_time,
                'success': True,
                'description': config['description']
            }
            
            print(f"{config['name']}: {elapsed_time:.2f}s")
            
        except Exception as e:
            print(f"{config['name']} failed: {e}")
            results['methods'][config['name']] = {
                'time': float('inf'),
                'success': False,
                'description': config['description'],
                'error': str(e)
            }
    
    return results

def clear_network_cache():
    """Clear the network cache between tests."""
    try:
        from socialmapper.isochrone.network_cache import get_network_cache
        cache = get_network_cache()
        cache.clear_cache()
        print("Network cache cleared")
    except Exception as e:
        print(f"Warning: Could not clear cache: {e}")

def run_network_size_benchmark():
    """Run benchmark across different travel times (network sizes)."""
    
    print("=" * 80)
    print("Network Size Impact Benchmark")
    print("=" * 80)
    
    if not NEATNET_AVAILABLE:
        print("ERROR: neatnet is not available. Please install it first.")
        return
    
    # Create output directory
    output_dir = Path("output/network_size_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get test scenario
    scenario = create_test_scenario()
    poi_data = {
        'pois': scenario['pois'],
        'metadata': {
            'source': 'test',
            'count': len(scenario['pois'])
        }
    }
    
    # Test different travel times (network sizes)
    travel_times = [5, 10, 15, 20, 30, 45]  # minutes
    
    print(f"Testing scenario: {scenario['name']}")
    print(f"Travel times to test: {travel_times} minutes")
    print(f"Expected network sizes will increase significantly with travel time")
    
    all_results = []
    
    for i, travel_time in enumerate(travel_times, 1):
        print(f"\n[{i}/{len(travel_times)}] Testing {travel_time}-minute isochrones")
        
        try:
            result = benchmark_travel_time(travel_time, poi_data)
            all_results.append(result)
        except Exception as e:
            print(f"Error testing {travel_time} minutes: {e}")
            continue
    
    return all_results

def analyze_network_size_results(all_results):
    """Analyze how network size affects performance."""
    
    print(f"\n{'='*80}")
    print(f"NETWORK SIZE IMPACT ANALYSIS")
    print(f"{'='*80}")
    
    # Create summary table
    print(f"\nPerformance by Travel Time (Network Size):")
    print(f"{'Time (min)':<10} {'Standard':<12} {'Cache Only':<12} {'neatnet':<12} {'Cache Speedup':<15} {'neatnet Speedup':<15}")
    print("-" * 85)
    
    analysis_data = []
    
    for result in all_results:
        travel_time = result['travel_time']
        methods = result['methods']
        
        standard_time = methods.get('standard', {}).get('time')
        cache_time = methods.get('cache_only', {}).get('time')
        neatnet_time = methods.get('neatnet_full', {}).get('time')
        
        if all(t is not None and t != float('inf') for t in [standard_time, cache_time, neatnet_time]):
            cache_speedup = standard_time / cache_time
            neatnet_speedup = standard_time / neatnet_time
            
            print(f"{travel_time:<10} {standard_time:<12.2f} {cache_time:<12.2f} {neatnet_time:<12.2f} "
                  f"{cache_speedup:<15.2f} {neatnet_speedup:<15.2f}")
            
            analysis_data.append({
                'travel_time': travel_time,
                'standard_time': standard_time,
                'cache_time': cache_time,
                'neatnet_time': neatnet_time,
                'cache_speedup': cache_speedup,
                'neatnet_speedup': neatnet_speedup
            })
        else:
            print(f"{travel_time:<10} {'FAILED':<12} {'FAILED':<12} {'FAILED':<12} {'N/A':<15} {'N/A':<15}")
    
    if not analysis_data:
        print("No successful results to analyze")
        return
    
    # Analyze trends
    print(f"\n{'='*60}")
    print(f"TREND ANALYSIS")
    print(f"{'='*60}")
    
    # Find crossover points where neatnet becomes beneficial
    neatnet_beneficial = [d for d in analysis_data if d['neatnet_speedup'] > 1.05]  # 5% threshold
    cache_beneficial = [d for d in analysis_data if d['cache_speedup'] > 1.05]
    
    print(f"\nCache Performance:")
    if cache_beneficial:
        avg_cache_speedup = sum(d['cache_speedup'] for d in cache_beneficial) / len(cache_beneficial)
        print(f"  • Beneficial for {len(cache_beneficial)}/{len(analysis_data)} travel times")
        print(f"  • Average speedup when beneficial: {avg_cache_speedup:.2f}x")
    else:
        print(f"  • No significant benefit observed")
    
    print(f"\nneatnet Performance:")
    if neatnet_beneficial:
        avg_neatnet_speedup = sum(d['neatnet_speedup'] for d in neatnet_beneficial) / len(neatnet_beneficial)
        min_beneficial_time = min(d['travel_time'] for d in neatnet_beneficial)
        print(f"  • Beneficial for {len(neatnet_beneficial)}/{len(analysis_data)} travel times")
        print(f"  • Average speedup when beneficial: {avg_neatnet_speedup:.2f}x")
        print(f"  • Becomes beneficial at: {min_beneficial_time} minutes")
    else:
        print(f"  • No significant benefit observed at any travel time")
    
    # Network size correlation
    print(f"\nNetwork Size Correlation:")
    
    # Estimate relative network sizes (proportional to travel time squared for urban areas)
    for data in analysis_data:
        relative_network_size = data['travel_time'] ** 2  # Rough approximation
        data['relative_network_size'] = relative_network_size
    
    # Check if neatnet benefits increase with network size
    if len(analysis_data) >= 3:
        small_networks = [d for d in analysis_data if d['travel_time'] <= 10]
        large_networks = [d for d in analysis_data if d['travel_time'] >= 20]
        
        if small_networks and large_networks:
            small_avg_neatnet = sum(d['neatnet_speedup'] for d in small_networks) / len(small_networks)
            large_avg_neatnet = sum(d['neatnet_speedup'] for d in large_networks) / len(large_networks)
            
            print(f"  • Small networks (≤10 min): {small_avg_neatnet:.2f}x average speedup")
            print(f"  • Large networks (≥20 min): {large_avg_neatnet:.2f}x average speedup")
            
            if large_avg_neatnet > small_avg_neatnet + 0.1:
                print(f"  ✅ neatnet benefits increase with network size")
            elif small_avg_neatnet > large_avg_neatnet + 0.1:
                print(f"  ❌ neatnet benefits decrease with network size")
            else:
                print(f"  ➖ neatnet benefits are consistent across network sizes")
    
    # Recommendations
    print(f"\n{'='*60}")
    print(f"RECOMMENDATIONS")
    print(f"{'='*60}")
    
    if neatnet_beneficial:
        min_time = min(d['travel_time'] for d in neatnet_beneficial)
        print(f"✅ Enable neatnet for travel times ≥ {min_time} minutes")
        print(f"   (Larger networks where optimization overhead is justified)")
    else:
        print(f"❌ neatnet not beneficial for any tested travel time")
        print(f"   (Optimization overhead outweighs benefits)")
    
    if cache_beneficial:
        print(f"✅ Network caching beneficial for all scenarios")
        print(f"   (Primary source of performance improvement)")
    
    # Optimal strategy
    print(f"\n💡 OPTIMAL STRATEGY:")
    if neatnet_beneficial:
        min_beneficial = min(d['travel_time'] for d in neatnet_beneficial)
        print(f"   • Use caching + neatnet for travel times ≥ {min_beneficial} minutes")
        print(f"   • Use caching only for travel times < {min_beneficial} minutes")
    else:
        print(f"   • Use caching only for all travel times")
        print(f"   • Disable neatnet processing entirely")

def main():
    """Main benchmark execution."""
    
    results = run_network_size_benchmark()
    
    if results:
        # Save results
        output_dir = Path("output/network_size_test")
        results_file = output_dir / "network_size_impact_results.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Analyze results
        analyze_network_size_results(results)
        
        print(f"\nDetailed results saved to: {results_file}")
    
    print(f"\n{'='*80}")
    print(f"Network size benchmark completed!")
    print(f"{'='*80}")

if __name__ == "__main__":
    main() 