#!/usr/bin/env python3
"""
Isolated neatnet benchmark to determine specific neatnet contribution.

This script tests different optimization components in isolation to understand
what performance gains come specifically from neatnet versus caching and
lightweight optimizations.
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
    
    # Use Manhattan as it showed the best performance in previous tests
    scenario = {
        "name": "Manhattan Libraries",
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
    }
    
    return scenario

def benchmark_method(method_name, poi_data, travel_time, **kwargs):
    """Benchmark a specific method configuration."""
    
    print(f"\nTesting {method_name}...")
    
    try:
        start_time = time.time()
        
        if method_name == "standard":
            # Pure standard method - no optimizations
            result = create_isochrones_from_poi_list(
                poi_data=poi_data,
                travel_time_limit=travel_time,
                output_dir=f"output/benchmark_isolation/standard",
                save_individual_files=False,
                combine_results=False
            )
        else:
            # Enhanced method with various configurations
            result = create_enhanced_isochrones_from_poi_list(
                poi_data=poi_data,
                travel_time_limit=travel_time,
                output_dir=f"output/benchmark_isolation/{method_name}",
                save_individual_files=False,
                combine_results=False,
                **kwargs
            )
        
        elapsed_time = time.time() - start_time
        
        print(f"{method_name}: {elapsed_time:.2f}s")
        return {
            'method': method_name,
            'time': elapsed_time,
            'success': True
        }
        
    except Exception as e:
        print(f"{method_name} failed: {e}")
        return {
            'method': method_name,
            'time': float('inf'),
            'success': False
        }

def clear_network_cache():
    """Clear the network cache between tests."""
    try:
        from socialmapper.isochrone.network_cache import get_network_cache
        cache = get_network_cache()
        cache.clear_cache()
        print("Network cache cleared")
    except Exception as e:
        print(f"Warning: Could not clear cache: {e}")

def run_isolated_benchmark():
    """Run benchmark with isolated components."""
    
    print("=" * 80)
    print("Isolated neatnet Component Benchmark")
    print("=" * 80)
    
    if not NEATNET_AVAILABLE:
        print("ERROR: neatnet is not available. Please install it first.")
        return
    
    # Create output directory
    output_dir = Path("output/benchmark_isolation")
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
    
    travel_time = 10
    results = []
    
    print(f"Testing scenario: {scenario['name']}")
    print(f"POIs: {len(scenario['pois'])}")
    print(f"Travel time: {travel_time} minutes")
    
    # Test configurations in order of increasing optimization
    test_configs = [
        {
            'name': 'standard',
            'description': 'Standard method (no optimizations)',
            'clear_cache': True
        },
        {
            'name': 'caching_only',
            'description': 'Enhanced method with caching only (no neatnet)',
            'kwargs': {'use_neatnet': False},
            'clear_cache': False  # Keep cache for this test
        },
        {
            'name': 'lightweight_only',
            'description': 'Enhanced method with lightweight optimizations (no neatnet, no cache benefit)',
            'kwargs': {'use_neatnet': False},
            'clear_cache': True  # Clear cache to isolate lightweight optimizations
        },
        {
            'name': 'neatnet_full',
            'description': 'Enhanced method with full neatnet processing',
            'kwargs': {'use_neatnet': True},
            'clear_cache': True  # Clear cache to isolate neatnet contribution
        },
        {
            'name': 'all_optimizations',
            'description': 'Enhanced method with all optimizations (caching + neatnet)',
            'kwargs': {'use_neatnet': True},
            'clear_cache': False  # Keep cache for maximum performance
        }
    ]
    
    for i, config in enumerate(test_configs, 1):
        print(f"\n[{i}/{len(test_configs)}] {config['description']}")
        
        # Clear cache if requested
        if config['clear_cache']:
            clear_network_cache()
        
        # Run benchmark
        if config['name'] == 'standard':
            result = benchmark_method(config['name'], poi_data, travel_time)
        else:
            result = benchmark_method(config['name'], poi_data, travel_time, **config.get('kwargs', {}))
        
        result['description'] = config['description']
        result['clear_cache'] = config['clear_cache']
        results.append(result)
    
    return results

def analyze_isolated_results(results):
    """Analyze the isolated benchmark results."""
    
    print(f"\n{'='*80}")
    print(f"ISOLATED COMPONENT ANALYSIS")
    print(f"{'='*80}")
    
    # Find baseline (standard method)
    baseline = next((r for r in results if r['method'] == 'standard'), None)
    if not baseline or not baseline['success']:
        print("ERROR: Could not establish baseline (standard method failed)")
        return
    
    baseline_time = baseline['time']
    
    print(f"\nBaseline (Standard Method): {baseline_time:.2f}s")
    print(f"\nComponent Analysis:")
    print(f"{'Method':<20} {'Time (s)':<10} {'Speedup':<10} {'vs Baseline':<12} {'Description'}")
    print("-" * 90)
    
    component_analysis = {}
    
    for result in results:
        if not result['success']:
            continue
            
        speedup = baseline_time / result['time']
        improvement = ((baseline_time - result['time']) / baseline_time) * 100
        
        print(f"{result['method']:<20} {result['time']:<10.2f} {speedup:<10.2f} {improvement:+8.1f}% {result['description']}")
        
        component_analysis[result['method']] = {
            'time': result['time'],
            'speedup': speedup,
            'improvement_percent': improvement
        }
    
    # Calculate specific component contributions
    print(f"\n{'='*60}")
    print(f"COMPONENT CONTRIBUTION ANALYSIS")
    print(f"{'='*60}")
    
    # Try to isolate individual component benefits
    standard_time = component_analysis.get('standard', {}).get('time')
    caching_time = component_analysis.get('caching_only', {}).get('time')
    lightweight_time = component_analysis.get('lightweight_only', {}).get('time')
    neatnet_time = component_analysis.get('neatnet_full', {}).get('time')
    full_time = component_analysis.get('all_optimizations', {}).get('time')
    
    if all(t is not None for t in [standard_time, caching_time, lightweight_time, neatnet_time]):
        
        # Caching benefit (caching_only vs standard)
        caching_benefit = standard_time - caching_time
        caching_speedup = standard_time / caching_time
        
        # Lightweight optimization benefit (lightweight_only vs standard, no cache)
        lightweight_benefit = standard_time - lightweight_time
        lightweight_speedup = standard_time / lightweight_time
        
        # neatnet benefit (neatnet_full vs standard, no cache)
        neatnet_benefit = standard_time - neatnet_time
        neatnet_speedup = standard_time / neatnet_time
        
        print(f"\nIndividual Component Benefits:")
        print(f"Network Caching:        {caching_speedup:.2f}x speedup ({caching_benefit:+.2f}s)")
        print(f"Lightweight Opts:       {lightweight_speedup:.2f}x speedup ({lightweight_benefit:+.2f}s)")
        print(f"neatnet Processing:     {neatnet_speedup:.2f}x speedup ({neatnet_benefit:+.2f}s)")
        
        # Compare neatnet vs lightweight optimizations
        if neatnet_time and lightweight_time:
            neatnet_vs_lightweight = lightweight_time / neatnet_time
            if neatnet_vs_lightweight > 1.05:
                print(f"\n✅ neatnet provides {neatnet_vs_lightweight:.2f}x speedup over lightweight optimizations")
            elif neatnet_vs_lightweight < 0.95:
                print(f"\n❌ neatnet is {1/neatnet_vs_lightweight:.2f}x slower than lightweight optimizations")
            else:
                print(f"\n➖ neatnet and lightweight optimizations have similar performance")
        
        # Overall assessment
        print(f"\n{'='*60}")
        print(f"NEATNET ASSESSMENT")
        print(f"{'='*60}")
        
        if neatnet_speedup > 1.1:
            print(f"✅ neatnet provides significant benefit: {neatnet_speedup:.2f}x speedup")
        elif neatnet_speedup > 1.05:
            print(f"✅ neatnet provides modest benefit: {neatnet_speedup:.2f}x speedup")
        elif neatnet_speedup > 0.95:
            print(f"➖ neatnet has neutral impact: {neatnet_speedup:.2f}x speedup")
        else:
            print(f"❌ neatnet causes performance regression: {neatnet_speedup:.2f}x speedup")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        if caching_speedup > 2.0:
            print(f"   • Network caching provides the largest benefit ({caching_speedup:.1f}x)")
            print(f"   • Focus on improving cache hit rates for maximum impact")
        
        if neatnet_speedup > lightweight_speedup:
            print(f"   • neatnet outperforms lightweight optimizations")
            print(f"   • Consider using neatnet for this network type")
        else:
            print(f"   • Lightweight optimizations are sufficient")
            print(f"   • neatnet overhead may not be justified")

def main():
    """Main benchmark execution."""
    
    results = run_isolated_benchmark()
    
    if results:
        # Save results
        output_dir = Path("output/benchmark_isolation")
        results_file = output_dir / "isolated_component_results.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Analyze results
        analyze_isolated_results(results)
        
        print(f"\nDetailed results saved to: {results_file}")
    
    print(f"\n{'='*80}")
    print(f"Isolated benchmark completed!")
    print(f"{'='*80}")

if __name__ == "__main__":
    main() 