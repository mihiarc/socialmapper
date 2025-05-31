#!/usr/bin/env python3
"""
Simple test script to verify clustering functionality.
"""

import os
import sys
import pandas as pd
import logging

# Add the socialmapper package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from socialmapper.isochrone.clustering import (
    cluster_pois_by_proximity,
    benchmark_clustering_performance
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_clustering():
    """Test clustering functionality with trail heads data."""
    
    # Load a small subset of trail heads data
    df = pd.read_csv("examples/trail_heads.csv")
    
    # Filter to Florida and take first 20 POIs
    df_fl = df[df['state'] == 'FL'].head(20)
    
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
    
    logger.info(f"Testing with {len(pois)} POIs from Florida")
    
    # Test clustering
    logger.info("Testing clustering algorithm...")
    clusters = cluster_pois_by_proximity(pois, max_cluster_radius_km=10.0, min_cluster_size=2)
    
    logger.info(f"Created {len(clusters)} clusters:")
    for i, cluster in enumerate(clusters):
        logger.info(f"  Cluster {cluster.cluster_id}: {len(cluster)} POIs, radius: {cluster.radius_km:.2f} km")
        for poi in cluster.pois:
            logger.info(f"    - {poi['tags']['name']} ({poi['lat']:.4f}, {poi['lon']:.4f})")
    
    # Test benchmark analysis
    logger.info("\nTesting benchmark analysis...")
    benchmark = benchmark_clustering_performance(poi_data, travel_time_limit=15)
    
    logger.info(f"Benchmark results:")
    logger.info(f"  Total POIs: {benchmark['total_pois']}")
    logger.info(f"  Total clusters: {benchmark['total_clusters']}")
    logger.info(f"  Network download reduction: {benchmark['reduction_percentage']:.1f}%")
    logger.info(f"  Estimated time savings: {benchmark['estimated_time_savings_min_seconds']:.0f}-{benchmark['estimated_time_savings_max_seconds']:.0f} seconds")
    
    return True

if __name__ == "__main__":
    try:
        test_clustering()
        logger.info("✅ Clustering test completed successfully!")
    except Exception as e:
        logger.error(f"❌ Clustering test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 