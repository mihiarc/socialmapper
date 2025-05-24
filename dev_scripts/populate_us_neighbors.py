#!/usr/bin/env python3
"""
Populate neighbor relationships for the entire United States.

This script initializes all neighbor relationships in the dedicated neighbor database:
- State neighbors (already done, but can refresh)
- County neighbors within each state
- Cross-state county neighbors
- Progress tracking and error handling
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional

from socialmapper.progress import get_progress_bar
from socialmapper.census import (
    get_neighbor_manager,
    initialize_all_neighbors
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_all_state_fips() -> List[str]:
    """Get all US state FIPS codes including DC."""
    return [
        '01', '02', '04', '05', '06', '08', '09', '10', '11', '12',
        '13', '15', '16', '17', '18', '19', '20', '21', '22', '23',
        '24', '25', '26', '27', '28', '29', '30', '31', '32', '33',
        '34', '35', '36', '37', '38', '39', '40', '41', '42', '44',
        '45', '46', '47', '48', '49', '50', '51', '53', '54', '55', '56'
    ]


async def populate_county_neighbors_by_state(
    manager,
    state_fips_list: Optional[List[str]] = None,
    force_refresh: bool = False,
    include_cross_state: bool = True
) -> Dict[str, int]:
    """
    Populate county neighbors state by state with detailed progress tracking.
    
    Args:
        manager: NeighborManager instance
        state_fips_list: List of state FIPS codes to process. If None, processes all states.
        force_refresh: Whether to refresh existing data
        include_cross_state: Whether to include cross-state county neighbors
        
    Returns:
        Dictionary with results per state
    """
    if state_fips_list is None:
        state_fips_list = get_all_state_fips()
    
    results = {}
    total_relationships = 0
    
    progress_bar = get_progress_bar()
    progress_bar.write(f"Starting county neighbor population for {len(state_fips_list)} states...")
    progress_bar.write(f"Include cross-state neighbors: {include_cross_state}")
    progress_bar.write(f"Force refresh: {force_refresh}")
    
    for i, state_fips in enumerate(state_fips_list, 1):
        progress_bar.write(f"\n[{i}/{len(state_fips_list)}] Processing state {state_fips}...")
        
        try:
            # Check if already processed
            if not force_refresh:
                count = manager.db.conn.execute(
                    "SELECT COUNT(*) FROM county_neighbors WHERE state_fips = ?", 
                    [state_fips]
                ).fetchone()[0]
                
                if count > 0:
                    progress_bar.write(f"  State {state_fips} already has {count} county relationships - skipping")
                    results[state_fips] = count
                    total_relationships += count
                    continue
            
            # Get counties with geometries for this state
            start_time = time.time()
            counties_gdf = await manager._get_counties_with_geometries(state_fips)
            load_time = time.time() - start_time
            
            if counties_gdf.empty:
                progress_bar.write(f"  No counties found for state {state_fips}")
                results[state_fips] = 0
                continue
            
            progress_bar.write(f"  Loaded {len(counties_gdf)} counties in {load_time:.2f}s")
            
            # Compute within-state neighbors
            start_time = time.time()
            within_state_neighbors = manager._compute_county_neighbors_spatial(counties_gdf, state_fips)
            compute_time = time.time() - start_time
            
            # Clear existing data for this state if refreshing
            if force_refresh:
                manager.db.conn.execute("DELETE FROM county_neighbors WHERE state_fips = ?", [state_fips])
            
            # Insert within-state relationships
            state_total = 0
            if within_state_neighbors:
                manager.db.conn.executemany("""
                    INSERT OR IGNORE INTO county_neighbors 
                    (state_fips, county_fips, neighbor_state_fips, neighbor_county_fips, relationship_type, shared_boundary_length)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, within_state_neighbors)
                
                state_total += len(within_state_neighbors)
                progress_bar.write(f"  Added {len(within_state_neighbors)} within-state neighbors in {compute_time:.2f}s")
            
            # Compute cross-state neighbors if requested
            if include_cross_state:
                # Get neighboring states
                neighboring_states = manager.get_neighboring_states(state_fips)
                progress_bar.write(f"  Processing cross-state neighbors with {len(neighboring_states)} neighboring states")
                
                for neighbor_state_fips in neighboring_states:
                    try:
                        # Get counties for neighboring state
                        neighbor_counties_gdf = await manager._get_counties_with_geometries(neighbor_state_fips)
                        if neighbor_counties_gdf.empty:
                            continue
                        
                        # Compute cross-state neighbors
                        start_time = time.time()
                        cross_state_neighbors = manager._compute_cross_state_county_neighbors(
                            counties_gdf, neighbor_counties_gdf, state_fips, neighbor_state_fips
                        )
                        cross_compute_time = time.time() - start_time
                        
                        if cross_state_neighbors:
                            manager.db.conn.executemany("""
                                INSERT OR IGNORE INTO county_neighbors 
                                (state_fips, county_fips, neighbor_state_fips, neighbor_county_fips, relationship_type, shared_boundary_length)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, cross_state_neighbors)
                            
                            state_total += len(cross_state_neighbors)
                            progress_bar.write(f"    Added {len(cross_state_neighbors)} cross-state neighbors with {neighbor_state_fips} in {cross_compute_time:.2f}s")
                        
                    except Exception as e:
                        progress_bar.write(f"    Error processing cross-state neighbors with {neighbor_state_fips}: {e}")
                        continue
            
            results[state_fips] = state_total
            total_relationships += state_total
            progress_bar.write(f"  State {state_fips} completed: {state_total} total relationships")
            
        except Exception as e:
            progress_bar.write(f"  Error processing state {state_fips}: {e}")
            results[state_fips] = 0
            continue
    
    # Update metadata
    manager.db.conn.execute(
        "INSERT OR REPLACE INTO neighbor_metadata (key, value) VALUES (?, ?)",
        ['county_neighbors_total', str(total_relationships)]
    )
    
    progress_bar.write(f"\nCompleted county neighbor population:")
    progress_bar.write(f"  Total relationships: {total_relationships}")
    progress_bar.write(f"  States processed: {len([s for s in results.values() if s > 0])}")
    
    return results


async def main():
    """Main function to populate all US neighbor relationships."""
    print("=" * 60)
    print("SocialMapper US Neighbor Population")
    print("=" * 60)
    
    # Initialize the neighbor manager
    print("Initializing neighbor manager...")
    manager = get_neighbor_manager()
    
    # Get initial statistics
    initial_stats = manager.get_neighbor_statistics()
    print(f"Initial statistics:")
    for key, value in initial_stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("Phase 1: State Neighbors")
    print("=" * 60)
    
    # Initialize state neighbors (should already be done, but ensure it's complete)
    state_count = manager.initialize_state_neighbors(force_refresh=False)
    print(f"State neighbors: {state_count} relationships")
    
    print("\n" + "=" * 60)
    print("Phase 2: County Neighbors")
    print("=" * 60)
    
    # Get all states
    all_states = get_all_state_fips()
    print(f"Processing county neighbors for {len(all_states)} states...")
    
    # Populate county neighbors
    start_time = time.time()
    county_results = await populate_county_neighbors_by_state(
        manager,
        state_fips_list=all_states,
        force_refresh=False,  # Don't refresh existing data
        include_cross_state=True  # Include cross-state relationships
    )
    total_time = time.time() - start_time
    
    print(f"\nCounty neighbor population completed in {total_time:.2f} seconds")
    
    # Get final statistics
    final_stats = manager.get_neighbor_statistics()
    print(f"\nFinal statistics:")
    for key, value in final_stats.items():
        print(f"  {key}: {value}")
    
    # Show improvement
    print(f"\nImprovement:")
    print(f"  County relationships: {initial_stats['county_relationships']} → {final_stats['county_relationships']} (+{final_stats['county_relationships'] - initial_stats['county_relationships']})")
    print(f"  Cross-state county relationships: {initial_stats['cross_state_county_relationships']} → {final_stats['cross_state_county_relationships']} (+{final_stats['cross_state_county_relationships'] - initial_stats['cross_state_county_relationships']})")
    print(f"  States with county data: {initial_stats['states_with_county_data']} → {final_stats['states_with_county_data']} (+{final_stats['states_with_county_data'] - initial_stats['states_with_county_data']})")
    
    # Show per-state results
    print(f"\nPer-state results:")
    successful_states = {k: v for k, v in county_results.items() if v > 0}
    failed_states = {k: v for k, v in county_results.items() if v == 0}
    
    print(f"  Successful states: {len(successful_states)}")
    print(f"  Failed states: {len(failed_states)}")
    
    if failed_states:
        print(f"  Failed state FIPS codes: {list(failed_states.keys())}")
    
    # Show top states by neighbor count
    top_states = sorted(successful_states.items(), key=lambda x: x[1], reverse=True)[:10]
    print(f"\nTop 10 states by neighbor relationships:")
    for state_fips, count in top_states:
        print(f"    {state_fips}: {count} relationships")
    
    print("\n" + "=" * 60)
    print("US Neighbor Population Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main()) 