#!/usr/bin/env python3
"""Test county neighbor initialization for the Southern region (13 states)."""

import time
import asyncio
import json
from pathlib import Path
from socialmapper.census import get_neighbor_manager

# Southern region states (US Census Bureau definition)
SOUTHERN_STATES = [
    '01',  # Alabama
    '05',  # Arkansas  
    '10',  # Delaware
    '11',  # District of Columbia
    '12',  # Florida
    '13',  # Georgia
    '21',  # Kentucky
    '22',  # Louisiana
    '24',  # Maryland
    '28',  # Mississippi
    '37',  # North Carolina
    '40',  # Oklahoma
    '45',  # South Carolina
    '47',  # Tennessee
    '48',  # Texas
    '51',  # Virginia
    '54'   # West Virginia
]

async def initialize_southern_counties():
    """Initialize county neighbors for all Southern states."""
    print("Initializing county neighbors for Southern region...")
    print(f"States to process: {len(SOUTHERN_STATES)}")
    print(f"State FIPS codes: {', '.join(SOUTHERN_STATES)}")
    
    manager = get_neighbor_manager()
    
    # Clear existing county data to get fresh timing
    print("\nClearing existing county neighbor data...")
    manager.db.conn.execute("DELETE FROM county_neighbors")
    
    # Initialize county neighbors for Southern states
    print(f"\nStarting county neighbor initialization...")
    start_time = time.time()
    
    try:
        count = await manager.initialize_county_neighbors(
            state_fips_list=SOUTHERN_STATES,
            force_refresh=True,
            include_cross_state=True
        )
        
        elapsed_time = time.time() - start_time
        
        print(f"\n✅ Initialization completed!")
        print(f"Time taken: {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")
        print(f"Relationships created: {count:,}")
        print(f"Average time per state: {elapsed_time/len(SOUTHERN_STATES):.1f} seconds")
        
        return count, elapsed_time
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"\n❌ Initialization failed after {elapsed_time:.1f} seconds")
        print(f"Error: {e}")
        return 0, elapsed_time

def analyze_data_size():
    """Analyze the size of the generated data."""
    print(f"\n" + "="*60)
    print("DATA SIZE ANALYSIS")
    print("="*60)
    
    manager = get_neighbor_manager()
    
    # Get statistics
    stats = manager.get_neighbor_statistics()
    print(f"Database statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value:,}")
    
    # Get detailed breakdown by state
    print(f"\nCounty relationships by state:")
    state_data = manager.db.conn.execute("""
        SELECT state_fips, COUNT(*) as relationship_count,
               COUNT(DISTINCT county_fips) as county_count
        FROM county_neighbors 
        GROUP BY state_fips
        ORDER BY state_fips
    """).fetchall()
    
    total_relationships = 0
    total_counties = 0
    
    for state_fips, rel_count, county_count in state_data:
        total_relationships += rel_count
        total_counties += county_count
        print(f"  State {state_fips}: {county_count:,} counties, {rel_count:,} relationships")
    
    # Cross-state relationships
    cross_state = manager.db.conn.execute("""
        SELECT COUNT(*) FROM county_neighbors 
        WHERE state_fips != neighbor_state_fips
    """).fetchone()[0]
    
    print(f"\nSummary:")
    print(f"  Total counties with data: {total_counties:,}")
    print(f"  Total relationships: {total_relationships:,}")
    print(f"  Cross-state relationships: {cross_state:,}")
    print(f"  Intra-state relationships: {total_relationships - cross_state:,}")
    
    # Estimate data sizes
    # Each relationship: ~50 bytes (state_fips + county_fips + neighbor_state + neighbor_county + boundary_length + metadata)
    estimated_raw_size = total_relationships * 50
    estimated_json_size = total_relationships * 120  # JSON overhead
    
    print(f"\nEstimated data sizes:")
    print(f"  Raw data: ~{estimated_raw_size:,} bytes ({estimated_raw_size/1024:.1f} KB)")
    print(f"  JSON format: ~{estimated_json_size:,} bytes ({estimated_json_size/1024:.1f} KB, {estimated_json_size/(1024*1024):.2f} MB)")
    
    return total_relationships, estimated_json_size

def export_southern_data():
    """Export the Southern region data to JSON."""
    print(f"\n" + "="*60)
    print("EXPORTING SOUTHERN REGION DATA")
    print("="*60)
    
    manager = get_neighbor_manager()
    
    # Get all county neighbor data
    result = manager.db.conn.execute("""
        SELECT state_fips, county_fips, neighbor_state_fips, neighbor_county_fips, 
               shared_boundary_length, relationship_type
        FROM county_neighbors 
        ORDER BY state_fips, county_fips, neighbor_state_fips, neighbor_county_fips
    """).fetchall()
    
    # Convert to structured format
    county_neighbors = {}
    
    for row in result:
        state_fips, county_fips, neighbor_state, neighbor_county, boundary_length, rel_type = row
        
        county_key = f"{state_fips}{county_fips}"
        
        if county_key not in county_neighbors:
            county_neighbors[county_key] = {
                "state_fips": state_fips,
                "county_fips": county_fips,
                "neighbors": []
            }
        
        county_neighbors[county_key]["neighbors"].append({
            "state_fips": neighbor_state,
            "county_fips": neighbor_county,
            "shared_boundary_length": round(boundary_length, 6),
            "relationship_type": rel_type
        })
    
    # Create export data
    export_data = {
        "metadata": {
            "description": "Pre-computed county neighbor relationships for Southern US region",
            "region": "Southern United States (US Census Bureau definition)",
            "states_included": SOUTHERN_STATES,
            "total_counties": len(county_neighbors),
            "total_relationships": len(result),
            "generated_by": "SocialMapper neighbor optimization system",
            "data_source": "US Census Bureau TIGER/Line Shapefiles",
            "computation_method": "Spatial analysis using DuckDB and GeoPandas"
        },
        "county_neighbors": county_neighbors
    }
    
    # Export to JSON
    output_file = Path("southern_county_neighbors.json")
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    # Get actual file size
    file_size = output_file.stat().st_size
    file_size_kb = file_size / 1024
    file_size_mb = file_size_kb / 1024
    
    print(f"Exported to: {output_file}")
    print(f"Actual file size: {file_size:,} bytes ({file_size_kb:.1f} KB, {file_size_mb:.2f} MB)")
    print(f"Counties included: {len(county_neighbors):,}")
    print(f"Relationships included: {len(result):,}")
    
    # GitHub feasibility
    print(f"\nGitHub storage feasibility:")
    if file_size_mb < 25:
        print(f"✅ FEASIBLE - File is under GitHub's 25MB limit")
        if file_size_mb < 1:
            print(f"   Excellent size for GitHub storage")
        elif file_size_mb < 5:
            print(f"   Good size for GitHub storage")
        else:
            print(f"   Acceptable size for GitHub storage")
    else:
        print(f"❌ TOO LARGE - File exceeds GitHub's 25MB limit")
    
    return output_file, file_size

async def main():
    print("="*60)
    print("SOUTHERN REGION COUNTY NEIGHBOR ANALYSIS")
    print("="*60)
    print(f"Testing county neighbor initialization for {len(SOUTHERN_STATES)} Southern states")
    
    # Initialize county neighbors
    count, elapsed_time = await initialize_southern_counties()
    
    if count > 0:
        # Analyze the data
        total_relationships, estimated_size = analyze_data_size()
        
        # Export the data
        output_file, actual_size = export_southern_data()
        
        # Final summary
        print(f"\n" + "="*60)
        print("FINAL SUMMARY")
        print("="*60)
        print(f"Initialization time: {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")
        print(f"States processed: {len(SOUTHERN_STATES)}")
        print(f"Relationships created: {count:,}")
        print(f"Exported file size: {actual_size:,} bytes ({actual_size/(1024*1024):.2f} MB)")
        print(f"GitHub storage: {'✅ Feasible' if actual_size < 25*1024*1024 else '❌ Too large'}")
        
        # Extrapolate to full US
        us_states = 50 + 1  # 50 states + DC
        estimated_us_size = (actual_size / len(SOUTHERN_STATES)) * us_states
        print(f"\nExtrapolated full US size: ~{estimated_us_size/(1024*1024):.1f} MB")
        print(f"Full US GitHub feasible: {'✅ Yes' if estimated_us_size < 25*1024*1024 else '❌ No'}")
    
    else:
        print(f"\n❌ Failed to initialize county neighbors")

if __name__ == "__main__":
    asyncio.run(main()) 