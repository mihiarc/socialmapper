#!/usr/bin/env python3
"""Analyze storage requirements for neighbor data across the entire United States."""

import json
import gzip
import tempfile
import os
from pathlib import Path

# US states and territories with their county counts (from US Census Bureau)
US_COUNTY_COUNTS = {
    # States with highest county counts
    'TX': 254,  # Texas - highest
    'GA': 159,  # Georgia
    'VA': 133,  # Virginia (includes independent cities)
    'KY': 120,  # Kentucky
    'MO': 115,  # Missouri
    'KS': 105,  # Kansas
    'IL': 102,  # Illinois
    'NC': 100,  # North Carolina (our test case)
    'IA': 99,   # Iowa
    'TN': 95,   # Tennessee
    'NE': 93,   # Nebraska
    'IN': 92,   # Indiana
    'OH': 88,   # Ohio
    'OK': 77,   # Oklahoma
    'AR': 75,   # Arkansas
    'MI': 83,   # Michigan
    'MN': 87,   # Minnesota
    'MS': 82,   # Mississippi
    'AL': 67,   # Alabama
    'WI': 72,   # Wisconsin
    'FL': 67,   # Florida
    'PA': 67,   # Pennsylvania
    'SC': 46,   # South Carolina
    'LA': 64,   # Louisiana (parishes)
    'ND': 53,   # North Dakota
    'SD': 66,   # South Dakota
    'WV': 55,   # West Virginia
    'NY': 62,   # New York
    'ME': 16,   # Maine
    'VT': 14,   # Vermont
    'NH': 10,   # New Hampshire
    'MA': 14,   # Massachusetts
    'RI': 5,    # Rhode Island
    'CT': 8,    # Connecticut
    'NJ': 21,   # New Jersey
    'MD': 23,   # Maryland
    'DE': 3,    # Delaware
    'WA': 39,   # Washington
    'OR': 36,   # Oregon
    'CA': 58,   # California
    'NV': 17,   # Nevada
    'ID': 44,   # Idaho
    'UT': 29,   # Utah
    'AZ': 15,   # Arizona
    'CO': 64,   # Colorado
    'NM': 33,   # New Mexico
    'WY': 23,   # Wyoming
    'MT': 56,   # Montana
    'AK': 30,   # Alaska (boroughs and census areas)
    'HI': 5,    # Hawaii
    # DC is not included as it has no counties
}

def analyze_nc_baseline():
    """Analyze what we know from the NC test case."""
    print("="*60)
    print("NORTH CAROLINA BASELINE ANALYSIS")
    print("="*60)
    
    # From our previous analysis
    nc_counties = 100
    nc_relationships_estimated = 672  # From the Southern region test
    nc_json_size_estimated = 126000   # 126 KB from previous analysis
    
    print(f"North Carolina baseline:")
    print(f"  Counties: {nc_counties}")
    print(f"  Estimated relationships: {nc_relationships_estimated}")
    print(f"  Estimated JSON size: {nc_json_size_estimated:,} bytes ({nc_json_size_estimated/1024:.1f} KB)")
    print(f"  Relationships per county: {nc_relationships_estimated/nc_counties:.1f}")
    print(f"  Bytes per relationship: {nc_json_size_estimated/nc_relationships_estimated:.1f}")
    
    return nc_counties, nc_relationships_estimated, nc_json_size_estimated

def calculate_us_totals():
    """Calculate total US counties and estimated relationships."""
    print(f"\n" + "="*60)
    print("US TOTALS CALCULATION")
    print("="*60)
    
    total_counties = sum(US_COUNTY_COUNTS.values())
    total_states = len(US_COUNTY_COUNTS)
    
    print(f"Total US counties: {total_counties:,}")
    print(f"Total states/territories: {total_states}")
    print(f"Average counties per state: {total_counties/total_states:.1f}")
    
    # Analyze distribution
    county_counts = list(US_COUNTY_COUNTS.values())
    county_counts.sort(reverse=True)
    
    print(f"\nCounty distribution:")
    print(f"  Largest states: {county_counts[:5]} counties")
    print(f"  Smallest states: {county_counts[-5:]} counties")
    print(f"  Median: {county_counts[len(county_counts)//2]} counties")
    
    # Estimate relationships
    # Each county typically has 4-8 neighbors (including cross-state)
    # Larger states have more internal neighbors, smaller states more cross-state
    avg_neighbors_per_county = 6.0  # Conservative estimate
    
    # Total relationships (each relationship counted once)
    total_relationships = int(total_counties * avg_neighbors_per_county / 2)
    
    print(f"\nRelationship estimates:")
    print(f"  Average neighbors per county: {avg_neighbors_per_county}")
    print(f"  Total county relationships: {total_relationships:,}")
    
    return total_counties, total_relationships

def estimate_state_neighbors():
    """Estimate state neighbor relationships."""
    print(f"\n" + "="*60)
    print("STATE NEIGHBOR ANALYSIS")
    print("="*60)
    
    # US has 50 states + DC = 51 entities
    # Each state has on average 4-5 neighbors
    # Some states like Missouri have 8 neighbors, others like Hawaii have 0
    
    total_states = 51  # 50 states + DC
    avg_neighbors_per_state = 4.3  # Based on geographic analysis
    
    # Total state relationships (each counted once)
    state_relationships = int(total_states * avg_neighbors_per_state / 2)
    
    print(f"State neighbor estimates:")
    print(f"  Total states/territories: {total_states}")
    print(f"  Average neighbors per state: {avg_neighbors_per_state}")
    print(f"  Total state relationships: {state_relationships}")
    
    return state_relationships

def estimate_storage_sizes(total_counties, county_relationships, state_relationships):
    """Estimate storage sizes for different formats."""
    print(f"\n" + "="*60)
    print("STORAGE SIZE ESTIMATES")
    print("="*60)
    
    # Base our estimates on NC data
    nc_counties, nc_relationships, nc_json_size = analyze_nc_baseline()
    
    # Scale factors
    county_scale = total_counties / nc_counties
    relationship_scale = county_relationships / nc_relationships
    
    print(f"\nScaling factors:")
    print(f"  County scale: {county_scale:.1f}x")
    print(f"  Relationship scale: {relationship_scale:.1f}x")
    
    # Estimate JSON sizes
    # State data is relatively small, county data dominates
    state_json_overhead = 5000  # ~5KB for all state relationships
    county_json_base = nc_json_size - state_json_overhead
    
    # Scale county data
    us_county_json = int(county_json_base * relationship_scale)
    us_total_json = us_county_json + state_json_overhead
    
    # Different JSON formats
    json_formatted = us_total_json
    json_compact = int(json_formatted * 0.6)  # ~40% reduction without formatting
    json_gz_formatted = int(json_formatted * 0.02)  # ~98% compression (very repetitive data)
    json_gz_compact = int(json_compact * 0.02)  # Best compression
    
    # Database sizes (DuckDB is very efficient for structured data)
    # Each relationship: ~50-80 bytes in DuckDB with indexes
    bytes_per_county_rel = 70
    bytes_per_state_rel = 50
    db_overhead = 100000  # 100KB base overhead
    
    duckdb_size = (county_relationships * bytes_per_county_rel + 
                   state_relationships * bytes_per_state_rel + 
                   db_overhead)
    
    sqlite_size = int(duckdb_size * 1.25)  # SQLite typically 25% larger
    
    print(f"\nEstimated storage sizes:")
    print(f"  JSON (formatted):        {json_formatted:,} bytes ({json_formatted/(1024*1024):.2f} MB)")
    print(f"  JSON (compact):          {json_compact:,} bytes ({json_compact/(1024*1024):.2f} MB)")
    print(f"  JSON.gz (formatted):     {json_gz_formatted:,} bytes ({json_gz_formatted/1024:.1f} KB)")
    print(f"  JSON.gz (compact):       {json_gz_compact:,} bytes ({json_gz_compact/1024:.1f} KB)")
    print(f"  DuckDB database:         {duckdb_size:,} bytes ({duckdb_size/(1024*1024):.2f} MB)")
    print(f"  SQLite database:         {sqlite_size:,} bytes ({sqlite_size/(1024*1024):.2f} MB)")
    
    return {
        'json_formatted': json_formatted,
        'json_compact': json_compact,
        'json_gz_formatted': json_gz_formatted,
        'json_gz_compact': json_gz_compact,
        'duckdb': duckdb_size,
        'sqlite': sqlite_size
    }

def analyze_github_feasibility(sizes):
    """Analyze GitHub storage feasibility for full US data."""
    print(f"\n" + "="*60)
    print("GITHUB STORAGE FEASIBILITY")
    print("="*60)
    
    github_limit = 25 * 1024 * 1024  # 25 MB
    
    print(f"GitHub file size limit: {github_limit/(1024*1024):.0f} MB")
    print(f"\nFeasibility analysis:")
    
    formats = [
        ("JSON (formatted)", sizes['json_formatted']),
        ("JSON (compact)", sizes['json_compact']),
        ("JSON.gz (formatted)", sizes['json_gz_formatted']),
        ("JSON.gz (compact)", sizes['json_gz_compact']),
        ("DuckDB database", sizes['duckdb']),
        ("SQLite database", sizes['sqlite'])
    ]
    
    feasible_formats = []
    
    for name, size in formats:
        feasible = size < github_limit
        status = "✅ FEASIBLE" if feasible else "❌ TOO LARGE"
        percentage = (size / github_limit) * 100
        
        print(f"  {name}: {status}")
        print(f"    Size: {size:,} bytes ({size/(1024*1024):.2f} MB)")
        print(f"    GitHub usage: {percentage:.1f}% of limit")
        
        if feasible:
            feasible_formats.append((name, size))
        print()
    
    return feasible_formats

def create_recommendations(sizes, feasible_formats):
    """Create recommendations for full US storage."""
    print(f"" + "="*60)
    print("RECOMMENDATIONS FOR FULL US DATA")
    print("="*60)
    
    if not feasible_formats:
        print("❌ NO FORMATS ARE FEASIBLE for GitHub storage")
        print("\nAlternatives:")
        print("• Use Git LFS for larger files")
        print("• Host on cloud storage (S3, etc.)")
        print("• Split data by regions")
        return
    
    # Find best options
    smallest_feasible = min(feasible_formats, key=lambda x: x[1])
    
    print(f"✅ {len(feasible_formats)} formats are feasible for GitHub storage")
    print(f"\n🏆 BEST OPTION: {smallest_feasible[0]}")
    print(f"   Size: {smallest_feasible[1]:,} bytes ({smallest_feasible[1]/1024:.1f} KB)")
    
    # Specific recommendations
    if sizes['json_gz_compact'] < 25*1024*1024:
        print(f"\n📋 RECOMMENDED APPROACH:")
        print(f"• Primary: Compressed compact JSON ({sizes['json_gz_compact']/1024:.1f} KB)")
        print(f"  - Smallest size, universal compatibility")
        print(f"  - Human readable when decompressed")
        print(f"  - Easy version control")
        
        if sizes['duckdb'] < 25*1024*1024:
            print(f"• Secondary: DuckDB database ({sizes['duckdb']/(1024*1024):.1f} MB)")
            print(f"  - Maximum query performance")
            print(f"  - Ready-to-use format")
            print(f"  - Same technology as main system")
    
    print(f"\n💡 IMPLEMENTATION STRATEGY:")
    print(f"• Generate data once during build/release process")
    print(f"• Include both formats in repository")
    print(f"• Load DuckDB directly if available, fall back to JSON")
    print(f"• Eliminates 60+ second initialization for all users")
    
    # Performance implications
    print(f"\n⚡ PERFORMANCE IMPACT:")
    print(f"• Current: 60+ seconds initialization per user")
    print(f"• With pre-computed data: <1 second loading")
    print(f"• 60x+ improvement in user experience")
    print(f"• No spatial computation dependencies")

def analyze_regional_alternatives(total_counties, county_relationships):
    """Analyze regional splitting as an alternative."""
    print(f"\n" + "="*60)
    print("REGIONAL SPLITTING ANALYSIS")
    print("="*60)
    
    # US Census regions
    regions = {
        'Northeast': ['CT', 'ME', 'MA', 'NH', 'NJ', 'NY', 'PA', 'RI', 'VT'],
        'Midwest': ['IL', 'IN', 'IA', 'KS', 'MI', 'MN', 'MO', 'NE', 'ND', 'OH', 'SD', 'WI'],
        'South': ['AL', 'AR', 'DE', 'FL', 'GA', 'KY', 'LA', 'MD', 'MS', 'NC', 'OK', 'SC', 'TN', 'TX', 'VA', 'WV'],
        'West': ['AK', 'AZ', 'CA', 'CO', 'HI', 'ID', 'MT', 'NV', 'NM', 'OR', 'UT', 'WA', 'WY']
    }
    
    print("Regional breakdown:")
    for region, states in regions.items():
        region_counties = sum(US_COUNTY_COUNTS.get(state, 0) for state in states)
        region_percentage = (region_counties / total_counties) * 100
        estimated_relationships = int((county_relationships * region_counties) / total_counties)
        
        # Estimate size (using our scaling from NC)
        nc_size_per_relationship = 126000 / 672  # bytes per relationship
        estimated_size = int(estimated_relationships * nc_size_per_relationship)
        compressed_size = int(estimated_size * 0.02)  # 98% compression
        
        print(f"  {region}:")
        print(f"    States: {len(states)}")
        print(f"    Counties: {region_counties:,} ({region_percentage:.1f}%)")
        print(f"    Est. relationships: {estimated_relationships:,}")
        print(f"    Est. compressed size: {compressed_size/1024:.1f} KB")
        print()

def main():
    print("FULL US NEIGHBOR DATA STORAGE ANALYSIS")
    print("="*60)
    
    # Get baseline from NC
    analyze_nc_baseline()
    
    # Calculate US totals
    total_counties, county_relationships = calculate_us_totals()
    state_relationships = estimate_state_neighbors()
    
    # Estimate storage sizes
    sizes = estimate_storage_sizes(total_counties, county_relationships, state_relationships)
    
    # Analyze GitHub feasibility
    feasible_formats = analyze_github_feasibility(sizes)
    
    # Create recommendations
    create_recommendations(sizes, feasible_formats)
    
    # Analyze regional alternatives
    analyze_regional_alternatives(total_counties, county_relationships)
    
    print(f"\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"• Total US counties: {total_counties:,}")
    print(f"• Estimated relationships: {county_relationships + state_relationships:,}")
    print(f"• Smallest format: {min(sizes.values())/1024:.1f} KB (compressed JSON)")
    print(f"• GitHub feasible: {'Yes' if feasible_formats else 'No'}")
    print(f"• Recommended: Dual format distribution (JSON + DuckDB)")

if __name__ == "__main__":
    main() 