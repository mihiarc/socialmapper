#!/usr/bin/env python3
"""
Quick benchmark to test isochrone generation with clustering.
"""

import os
import sys
import time
import pandas as pd
import logging
import shutil

# Add the socialmapper package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from socialmapper.isochrone import (
    create_isochrones_from_poi_list,
    benchmark_clustering_performance
)
import osmnx as ox

# Setup logging
logging.basicConfig(level=logging.INFO)
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

def quick_test():
    """Quick test with 15 POIs from Florida."""
    
    # Load a subset of trail heads data
    df = pd.read_csv("examples/trail_heads.csv")
    
    # Filter to Florida and take first 15 POIs
    df_fl = df[df['state'] == 'FL'].head(15)
    
    # Convert to POI format
    pois = []
    for _, row in df_fl.iterrows():
        poi = {
            'id': str(row['id']),
            'lat': float(row['lat']),
            'lon': float(row['lon']),
            'tags': {'name': str(row['name'])}
        }
        pois.append(poi)
    
    poi_data = {'pois': pois}
    
    logger.info(f"Quick test with {len(pois)} POIs from Florida")
    
    # Analyze clustering potential
    benchmark = benchmark_clustering_performance(poi_data, travel_time_limit=15)
    logger.info(f"Clustering analysis: {benchmark['reduction_percentage']:.1f}% reduction potential")
    
    # Clear cache before testing original method
    logger.info("Clearing cache before original method test...")
    clear_osmnx_cache()
    
    # Test original method
    logger.info("Testing original method...")
    start_time = time.time()
    try:
        original_result = create_isochrones_from_poi_list(
            poi_data=poi_data,
            travel_time_limit=15,
            save_individual_files=False,
            combine_results=True,
            use_clustering=False
        )
        original_time = time.time() - start_time
        logger.info(f"Original method: {original_time:.1f} seconds, {len(original_result)} isochrones")
    except Exception as e:
        logger.error(f"Original method failed: {e}")
        return False
    
    # Clear cache before testing clustering method
    logger.info("Clearing cache before clustering method test...")
    clear_osmnx_cache()
    
    # Test clustering method
    logger.info("Testing clustering method...")
    start_time = time.time()
    try:
        clustered_result = create_isochrones_from_poi_list(
            poi_data=poi_data,
            travel_time_limit=15,
            save_individual_files=False,
            combine_results=True,
            use_clustering=True
        )
        clustered_time = time.time() - start_time
        logger.info(f"Clustering method: {clustered_time:.1f} seconds, {len(clustered_result)} isochrones")
    except Exception as e:
        logger.error(f"Clustering method failed: {e}")
        return False
    
    # Compare results
    if original_time > 0 and clustered_time > 0:
        improvement = ((original_time - clustered_time) / original_time) * 100
        speedup = original_time / clustered_time
        logger.info(f"Performance: {improvement:.1f}% improvement ({speedup:.2f}x speedup)")
        
        if improvement > 0:
            logger.info("✅ Clustering optimization is faster!")
        else:
            logger.info("⚠️  Clustering optimization is slower (expected for small datasets)")
    
    return True

if __name__ == "__main__":
    try:
        if quick_test():
            logger.info("✅ Quick benchmark completed successfully!")
        else:
            logger.error("❌ Quick benchmark failed!")
            sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Quick benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 