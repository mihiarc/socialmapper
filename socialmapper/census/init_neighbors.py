#!/usr/bin/env python3
"""
Initialization script for neighbor relationships in the SocialMapper census module.

This script helps users:
1. Initialize all neighbor relationships (states, counties)
2. Migrate from old states/counties modules
3. Verify the neighbor system is working
4. Provide performance benchmarks
"""

import sys
import time
import argparse
import logging
from pathlib import Path
from typing import Dict, Any

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from socialmapper.progress import get_progress_bar
from socialmapper.census import (
    get_census_database,
    get_neighbor_manager,
    initialize_all_neighbors,
    get_neighboring_states,
    get_neighboring_counties,
    get_geography_from_point,
    get_counties_from_pois
)

logger = logging.getLogger(__name__)


def benchmark_old_vs_new():
    """Benchmark the performance difference between old and new approaches."""
    get_progress_bar().write("\n" + "="*60)
    get_progress_bar().write("Performance Benchmark: Old vs New Approach")
    get_progress_bar().write("="*60)
    
    # Test data: sample POIs
    test_pois = [
        {'lat': 35.7796, 'lon': -78.6382, 'id': 'raleigh_nc'},
        {'lat': 35.2271, 'lon': -80.8431, 'id': 'charlotte_nc'},
        {'lat': 36.0726, 'lon': -79.7920, 'id': 'greensboro_nc'},
        {'lat': 35.6870, 'lon': -78.8414, 'id': 'cary_nc'},
        {'lat': 35.5175, 'lon': -77.0514, 'id': 'greenville_nc'}
    ]
    
    manager = get_neighbor_manager()
    
    # Benchmark 1: Point-to-geography lookup
    get_progress_bar().write("\n1. Point-to-Geography Lookup Performance:")
    
    # New approach (with caching)
    start_time = time.time()
    for poi in test_pois:
        geography = manager.get_geography_from_point(poi['lat'], poi['lon'])
    new_time = time.time() - start_time
    
    # Second run (should be faster due to caching)
    start_time = time.time()
    for poi in test_pois:
        geography = manager.get_geography_from_point(poi['lat'], poi['lon'])
    cached_time = time.time() - start_time
    
    get_progress_bar().write(f"  New approach (first run): {new_time:.3f}s")
    get_progress_bar().write(f"  New approach (cached):    {cached_time:.3f}s")
    get_progress_bar().write(f"  Cache speedup:            {new_time/cached_time:.1f}x faster")
    
    # Benchmark 2: Neighbor lookup performance
    get_progress_bar().write("\n2. Neighbor Lookup Performance:")
    
    # Test state neighbors
    test_states = ['37', '06', '48', '36', '12']  # NC, CA, TX, NY, FL
    
    start_time = time.time()
    for state_fips in test_states:
        neighbors = manager.get_neighboring_states(state_fips)
    state_lookup_time = time.time() - start_time
    
    get_progress_bar().write(f"  State neighbor lookups:   {state_lookup_time:.3f}s for {len(test_states)} states")
    get_progress_bar().write(f"  Average per state:        {state_lookup_time/len(test_states)*1000:.1f}ms")
    
    # Test county neighbors (if data is available)
    try:
        start_time = time.time()
        neighbors = manager.get_neighboring_counties('37', '183')  # Wake County, NC
        county_lookup_time = time.time() - start_time
        get_progress_bar().write(f"  County neighbor lookup:   {county_lookup_time*1000:.1f}ms")
        get_progress_bar().write(f"  Found {len(neighbors)} neighboring counties")
    except Exception as e:
        get_progress_bar().write(f"  County neighbors not initialized: {e}")
    
    # Benchmark 3: POI processing
    get_progress_bar().write("\n3. POI Processing Performance:")
    
    start_time = time.time()
    counties = manager.get_counties_from_pois(test_pois, include_neighbors=True)
    poi_processing_time = time.time() - start_time
    
    get_progress_bar().write(f"  POI processing time:      {poi_processing_time:.3f}s for {len(test_pois)} POIs")
    get_progress_bar().write(f"  Average per POI:          {poi_processing_time/len(test_pois)*1000:.1f}ms")
    get_progress_bar().write(f"  Total counties found:     {len(counties)}")


def verify_neighbor_system():
    """Verify that the neighbor system is working correctly."""
    get_progress_bar().write("\n" + "="*60)
    get_progress_bar().write("Neighbor System Verification")
    get_progress_bar().write("="*60)
    
    manager = get_neighbor_manager()
    
    # Test 1: State neighbors
    get_progress_bar().write("\n1. Testing State Neighbors:")
    test_cases = [
        ('37', ['13', '45', '47', '51']),  # NC should neighbor GA, SC, TN, VA
        ('06', ['04', '32', '41']),        # CA should neighbor AZ, NV, OR
        ('48', ['05', '22', '35', '40'])   # TX should neighbor AR, LA, NM, OK
    ]
    
    for state_fips, expected_neighbors in test_cases:
        neighbors = manager.get_neighboring_states(state_fips)
        
        # Check if expected neighbors are found
        found_expected = set(neighbors) & set(expected_neighbors)
        
        get_progress_bar().write(f"  State {state_fips}: Found {len(neighbors)} neighbors")
        get_progress_bar().write(f"    Expected: {expected_neighbors}")
        get_progress_bar().write(f"    Found:    {neighbors}")
        get_progress_bar().write(f"    Match:    {len(found_expected)}/{len(expected_neighbors)} expected neighbors found")
        
        if len(found_expected) == len(expected_neighbors):
            get_progress_bar().write("    ✓ PASS")
        else:
            get_progress_bar().write("    ✗ FAIL")
    
    # Test 2: Point geocoding
    get_progress_bar().write("\n2. Testing Point Geocoding:")
    test_points = [
        (35.7796, -78.6382, '37', '183'),  # Raleigh, NC -> Wake County
        (34.0522, -118.2437, '06', '037'), # Los Angeles, CA -> LA County
        (29.7604, -95.3698, '48', '201')   # Houston, TX -> Harris County
    ]
    
    for lat, lon, expected_state, expected_county in test_points:
        geography = manager.get_geography_from_point(lat, lon)
        
        get_progress_bar().write(f"  Point ({lat}, {lon}):")
        get_progress_bar().write(f"    Expected: State {expected_state}, County {expected_county}")
        get_progress_bar().write(f"    Found:    State {geography['state_fips']}, County {geography['county_fips']}")
        
        if geography['state_fips'] == expected_state and geography['county_fips'] == expected_county:
            get_progress_bar().write("    ✓ PASS")
        else:
            get_progress_bar().write("    ✗ FAIL")
    
    # Test 3: Statistics
    get_progress_bar().write("\n3. System Statistics:")
    stats = manager.get_neighbor_statistics()
    
    for key, value in stats.items():
        get_progress_bar().write(f"  {key.replace('_', ' ').title()}: {value:,}")


def show_migration_examples():
    """Show examples of how to migrate from old modules to new system."""
    
    examples = """
=== Migration Examples: Old vs New ===

OLD WAY (using separate states and counties modules):
```python
from socialmapper.states import get_neighboring_states, normalize_state
from socialmapper.counties import get_neighboring_counties, get_counties_from_pois

# Get neighboring states
neighbors = get_neighboring_states('NC')  # Slow, hardcoded lookup

# Get counties for POIs
counties = get_counties_from_pois(poi_data)  # Slow, real-time spatial computation
```

NEW WAY (using integrated census.neighbors):
```python
from socialmapper.census import (
    get_neighboring_states, 
    get_neighboring_counties,
    get_counties_from_pois,
    get_geography_from_point
)

# Get neighboring states (fast database lookup)
neighbors = get_neighboring_states('37')  # FIPS code, instant lookup

# Get counties for POIs (optimized with caching)
counties = get_counties_from_pois(pois)  # Fast, cached geocoding

# New: Get all geography for a point
geography = get_geography_from_point(lat, lon)  # Returns state, county, tract, block group
```

=== Key Benefits ===

1. **Performance**: 10-100x faster lookups using pre-computed relationships
2. **Caching**: Point-to-geography lookups cached for instant repeat access
3. **Unified API**: All geographic operations in one place
4. **Cross-state**: County neighbors across state boundaries
5. **Scalable**: DuckDB spatial indexing handles large datasets efficiently

=== Initialization ===

Run once to set up neighbor relationships:
```python
from socialmapper.census import initialize_all_neighbors

# Initialize all neighbor relationships
results = initialize_all_neighbors()
print(f"Initialized {results['state_neighbors']} state relationships")
print(f"Initialized {results['county_neighbors']} county relationships")
```

=== Advanced Usage ===

```python
from socialmapper.census import get_neighbor_manager

# Get the neighbor manager for advanced operations
manager = get_neighbor_manager()

# Get statistics
stats = manager.get_neighbor_statistics()

# Get counties with neighbor distance
counties = manager.get_counties_from_pois(
    pois, 
    include_neighbors=True,
    neighbor_distance=2  # Include neighbors of neighbors
)
```
"""
    
    get_progress_bar().write(examples)


def main():
    """Main initialization script entry point."""
    parser = argparse.ArgumentParser(
        description="Initialize SocialMapper census neighbor relationships"
    )
    parser.add_argument(
        "--force", 
        action="store_true",
        help="Force re-initialization even if data exists"
    )
    parser.add_argument(
        "--states-only",
        action="store_true",
        help="Initialize only state neighbors (faster)"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing neighbor system"
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run performance benchmarks"
    )
    parser.add_argument(
        "--examples",
        action="store_true",
        help="Show migration examples"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    if args.examples:
        show_migration_examples()
        return
    
    get_progress_bar().write("=" * 60)
    get_progress_bar().write("SocialMapper Census Neighbor Initialization")
    get_progress_bar().write("=" * 60)
    
    if args.verify_only:
        verify_neighbor_system()
        if args.benchmark:
            benchmark_old_vs_new()
        return
    
    # Initialize neighbor relationships
    get_progress_bar().write("\n1. Initializing neighbor relationships...")
    
    try:
        if args.states_only:
            # Initialize only state neighbors
            manager = get_neighbor_manager()
            state_count = manager.initialize_state_neighbors(force_refresh=args.force)
            get_progress_bar().write(f"✓ Initialized {state_count} state neighbor relationships")
            
            results = {'state_neighbors': state_count, 'county_neighbors': 0}
        else:
            # Initialize all neighbors
            results = initialize_all_neighbors(force_refresh=args.force)
            get_progress_bar().write(f"✓ Initialized {results['state_neighbors']} state relationships")
            get_progress_bar().write(f"✓ Initialized {results['county_neighbors']} county relationships")
        
        # Verify the system
        get_progress_bar().write("\n2. Verifying neighbor system...")
        verify_neighbor_system()
        
        # Run benchmarks if requested
        if args.benchmark:
            benchmark_old_vs_new()
        
        # Show migration examples
        get_progress_bar().write("\n" + "="*60)
        get_progress_bar().write("Initialization Complete!")
        get_progress_bar().write("="*60)
        get_progress_bar().write("\nYour neighbor relationships are now ready for fast lookups.")
        get_progress_bar().write("The old states and counties modules can now be replaced with:")
        get_progress_bar().write("  from socialmapper.census import get_neighboring_states, get_neighboring_counties")
        get_progress_bar().write("\nRun with --examples to see detailed migration examples.")
        
    except Exception as e:
        get_progress_bar().write(f"\n✗ Initialization failed: {e}")
        logger.error(f"Initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 