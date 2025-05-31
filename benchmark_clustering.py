#!/usr/bin/env python3
"""
Benchmark script for testing clustering optimization with trail_heads.csv data.

This script compares the performance of the original isochrone generation
method with the new clustering optimization.
"""

import os
import sys
import time
import json
import pandas as pd
import logging
import shutil
from typing import Dict, Any, List

# Add the socialmapper package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from socialmapper.isochrone import (
    create_isochrones_from_poi_list,
    benchmark_clustering_performance
)
import osmnx as ox

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clear_osmnx_cache():
    """Clear OSMnx cache to ensure fair benchmarking."""
    try:
        cache_folder = ox.settings.cache_folder
        if os.path.exists(cache_folder):
            shutil.rmtree(cache_folder)
            logger.info(f"Cleared OSMnx cache: {cache_folder}")
        else:
            logger.info("OSMnx cache folder not found")
    except Exception as e:
        logger.warning(f"Could not clear OSMnx cache: {e}")

def load_trail_heads_data(csv_path: str, limit: int = None, state_filter: str = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Load trail heads data from CSV and convert to POI format.
    
    Args:
        csv_path: Path to the trail_heads.csv file
        limit: Maximum number of POIs to load (for testing)
        state_filter: Filter to specific state (e.g., 'FL', 'KY')
        
    Returns:
        Dictionary with 'pois' key containing list of POI dictionaries
    """
    df = pd.read_csv(csv_path)
    
    # Filter by state if specified
    if state_filter:
        df = df[df['state'] == state_filter]
        logger.info(f"Filtered to {len(df)} POIs in state {state_filter}")
    
    # Limit number of POIs if specified
    if limit:
        df = df.head(limit)
        logger.info(f"Limited to {len(df)} POIs for testing")
    
    # Convert to POI format
    pois = []
    for _, row in df.iterrows():
        poi = {
            'id': str(row['id']),
            'lat': float(row['lat']),
            'lon': float(row['lon']),
            'tags': {
                'name': str(row['name'])
            }
        }
        pois.append(poi)
    
    return {'pois': pois}

def run_benchmark(poi_data: Dict[str, List[Dict[str, Any]]], 
                 travel_time_limit: int = 15,
                 output_dir: str = "benchmark_output") -> Dict[str, Any]:
    """
    Run benchmark comparing original vs clustering optimization.
    
    Args:
        poi_data: POI data dictionary
        travel_time_limit: Travel time limit in minutes
        output_dir: Output directory for results
        
    Returns:
        Dictionary with benchmark results
    """
    pois = poi_data['pois']
    logger.info(f"Benchmarking with {len(pois)} POIs")
    
    # Create output directories
    original_dir = os.path.join(output_dir, "original")
    clustered_dir = os.path.join(output_dir, "clustered")
    os.makedirs(original_dir, exist_ok=True)
    os.makedirs(clustered_dir, exist_ok=True)
    
    # Analyze clustering potential first
    logger.info("Analyzing clustering potential...")
    cluster_analysis = benchmark_clustering_performance(
        poi_data, travel_time_limit, max_cluster_radius_km=10.0
    )
    
    logger.info(f"Clustering analysis:")
    logger.info(f"  Total POIs: {cluster_analysis['total_pois']}")
    logger.info(f"  Total clusters: {cluster_analysis['total_clusters']}")
    logger.info(f"  Network download reduction: {cluster_analysis['reduction_percentage']:.1f}%")
    logger.info(f"  Estimated time savings: {cluster_analysis['estimated_time_savings_min_seconds']:.0f}-{cluster_analysis['estimated_time_savings_max_seconds']:.0f} seconds")
    
    results = {
        'poi_count': len(pois),
        'travel_time_limit': travel_time_limit,
        'cluster_analysis': cluster_analysis
    }
    
    # Test original method
    logger.info("Testing original method...")
    clear_osmnx_cache()  # Clear cache before test
    start_time = time.time()
    try:
        original_result = create_isochrones_from_poi_list(
            poi_data=poi_data,
            travel_time_limit=travel_time_limit,
            output_dir=original_dir,
            save_individual_files=False,
            combine_results=True,
            use_clustering=False  # Force original method
        )
        original_time = time.time() - start_time
        original_success = True
        original_isochrone_count = len(original_result) if hasattr(original_result, '__len__') else 1
    except Exception as e:
        logger.error(f"Original method failed: {e}")
        original_time = time.time() - start_time
        original_success = False
        original_isochrone_count = 0
    
    results['original'] = {
        'success': original_success,
        'time_seconds': original_time,
        'isochrone_count': original_isochrone_count
    }
    
    # Test clustering optimization
    logger.info("Testing clustering optimization...")
    clear_osmnx_cache()  # Clear cache before test
    start_time = time.time()
    try:
        clustered_result = create_isochrones_from_poi_list(
            poi_data=poi_data,
            travel_time_limit=travel_time_limit,
            output_dir=clustered_dir,
            save_individual_files=False,
            combine_results=True,
            use_clustering=True  # Force clustering method
        )
        clustered_time = time.time() - start_time
        clustered_success = True
        clustered_isochrone_count = len(clustered_result) if hasattr(clustered_result, '__len__') else 1
    except Exception as e:
        logger.error(f"Clustering method failed: {e}")
        clustered_time = time.time() - start_time
        clustered_success = False
        clustered_isochrone_count = 0
    
    results['clustered'] = {
        'success': clustered_success,
        'time_seconds': clustered_time,
        'isochrone_count': clustered_isochrone_count
    }
    
    # Calculate performance improvement
    if original_success and clustered_success:
        time_improvement = ((original_time - clustered_time) / original_time) * 100
        results['performance'] = {
            'time_improvement_percent': time_improvement,
            'speedup_factor': original_time / clustered_time if clustered_time > 0 else float('inf')
        }
        
        logger.info(f"Performance Results:")
        logger.info(f"  Original time: {original_time:.1f} seconds")
        logger.info(f"  Clustered time: {clustered_time:.1f} seconds")
        logger.info(f"  Time improvement: {time_improvement:.1f}%")
        logger.info(f"  Speedup factor: {results['performance']['speedup_factor']:.2f}x")
    
    return results

def main():
    """Main benchmarking function."""
    # Configuration
    csv_path = "examples/trail_heads.csv"
    travel_time_limit = 15  # minutes
    output_dir = "benchmark_output"
    
    # Test scenarios
    test_scenarios = [
        {"name": "Small test (10 POIs FL)", "limit": 10, "state_filter": "FL"},
        {"name": "Medium test (20 POIs FL)", "limit": 20, "state_filter": "FL"},
        {"name": "Large test (30 POIs FL)", "limit": 30, "state_filter": "FL"},
        {"name": "Mixed states (25 POIs)", "limit": 25, "state_filter": None},
    ]
    
    all_results = {}
    
    for scenario in test_scenarios:
        logger.info(f"\n{'='*60}")
        logger.info(f"Running scenario: {scenario['name']}")
        logger.info(f"{'='*60}")
        
        try:
            # Load data for this scenario
            poi_data = load_trail_heads_data(
                csv_path, 
                limit=scenario['limit'],
                state_filter=scenario.get('state_filter')
            )
            
            # Run benchmark
            scenario_output_dir = os.path.join(output_dir, scenario['name'].replace(' ', '_').replace('(', '').replace(')', ''))
            results = run_benchmark(poi_data, travel_time_limit, scenario_output_dir)
            
            all_results[scenario['name']] = results
            
        except Exception as e:
            logger.error(f"Scenario {scenario['name']} failed: {e}")
            all_results[scenario['name']] = {"error": str(e)}
    
    # Save results to JSON
    results_file = os.path.join(output_dir, "benchmark_results.json")
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    logger.info(f"\nBenchmark complete! Results saved to {results_file}")
    
    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info("BENCHMARK SUMMARY")
    logger.info(f"{'='*60}")
    
    for scenario_name, results in all_results.items():
        if 'error' in results:
            logger.info(f"{scenario_name}: FAILED - {results['error']}")
        elif 'performance' in results:
            perf = results['performance']
            logger.info(f"{scenario_name}: {perf['time_improvement_percent']:.1f}% faster ({perf['speedup_factor']:.2f}x speedup)")
        else:
            logger.info(f"{scenario_name}: Completed but no performance comparison available")

if __name__ == "__main__":
    main() 