#!/usr/bin/env python3
"""
Demonstration of the graph caching optimization for isochrone generation.
This script generates isochrones for multiple POIs in a given area and compares
the performance with and without graph caching.
"""
import os
import time
import json
import logging
import argparse
from typing import List, Dict, Any

# Import the required modules
from socialmapper.isochrone import create_isochrones_from_poi_list, graph_cache
from socialmapper.query import get_pois_from_location

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_performance_test(location: str, poi_type: str, limit: int, travel_time: int, output_dir: str) -> None:
    """
    Run a performance test comparing isochrone generation with and without caching.
    
    Args:
        location: Location name (e.g., "San Francisco, CA")
        poi_type: Type of POI to query (e.g., "amenity=restaurant")
        limit: Maximum number of POIs to process
        travel_time: Travel time limit in minutes
        output_dir: Directory to save output files
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Querying {limit} POIs of type '{poi_type}' in {location}")
    
    # Query POIs
    poi_data = get_pois_from_location(
        location=location,
        query=poi_type,
        limit=limit
    )
    
    # Save POIs to file for reference
    poi_file = os.path.join(output_dir, "queried_pois.json")
    with open(poi_file, "w") as f:
        json.dump(poi_data, f, indent=2)
    
    logger.info(f"Retrieved {len(poi_data.get('pois', []))} POIs and saved to {poi_file}")
    
    # First run: without cache (clear cache to ensure fair test)
    graph_cache.clear()
    logger.info(f"Running WITHOUT cache optimization...")
    
    cache_off_start = time.time()
    result = create_isochrones_from_poi_list(
        poi_data=poi_data,
        travel_time_limit=travel_time,
        output_dir=os.path.join(output_dir, "no_cache"),
        combine_results=True
    )
    cache_off_time = time.time() - cache_off_start
    
    # Calculate per-POI time
    poi_count = len(poi_data.get('pois', []))
    cache_off_per_poi = cache_off_time / poi_count if poi_count > 0 else 0
    
    logger.info(f"WITHOUT cache: {cache_off_time:.2f} seconds total, {cache_off_per_poi:.2f} seconds per POI")
    
    # Second run: with cache (should already have data from first run)
    logger.info(f"Running WITH cache optimization...")
    
    cache_on_start = time.time()
    result = create_isochrones_from_poi_list(
        poi_data=poi_data,
        travel_time_limit=travel_time,
        output_dir=os.path.join(output_dir, "with_cache"),
        combine_results=True
    )
    cache_on_time = time.time() - cache_on_start
    
    # Calculate per-POI time
    cache_on_per_poi = cache_on_time / poi_count if poi_count > 0 else 0
    
    logger.info(f"WITH cache: {cache_on_time:.2f} seconds total, {cache_on_per_poi:.2f} seconds per POI")
    
    # Calculate improvement
    if cache_off_time > 0:
        improvement = (cache_off_time - cache_on_time) / cache_off_time * 100
        logger.info(f"Performance improvement: {improvement:.2f}%")
        
        # Save results to summary file
        summary = {
            "location": location,
            "poi_type": poi_type,
            "poi_count": poi_count,
            "travel_time_minutes": travel_time,
            "without_cache_time": cache_off_time,
            "without_cache_per_poi": cache_off_per_poi,
            "with_cache_time": cache_on_time,
            "with_cache_per_poi": cache_on_per_poi,
            "improvement_percent": improvement,
            "cache_size": len(graph_cache.cache)
        }
        
        summary_file = os.path.join(output_dir, "performance_summary.json")
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Performance summary saved to {summary_file}")

def main():
    parser = argparse.ArgumentParser(description="Demonstrate graph caching optimization for isochrone generation")
    parser.add_argument("--location", default="San Francisco, CA", help="Location name")
    parser.add_argument("--poi-type", default="amenity=restaurant", help="Type of POI to query")
    parser.add_argument("--limit", type=int, default=20, help="Maximum number of POIs to process")
    parser.add_argument("--travel-time", type=int, default=10, help="Travel time limit in minutes")
    parser.add_argument("--output-dir", default="examples/example_output/cache_demo", help="Output directory")
    
    args = parser.parse_args()
    
    # Run the performance test
    run_performance_test(
        location=args.location,
        poi_type=args.poi_type,
        limit=args.limit,
        travel_time=args.travel_time,
        output_dir=args.output_dir
    )
    
    logger.info("Demo completed!")

if __name__ == "__main__":
    main() 