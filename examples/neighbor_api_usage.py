#!/usr/bin/env python3
"""
SocialMapper Neighbors API Usage Examples

This script demonstrates the different ways to access neighbor functionality
directly without using the full SocialMapper workflow.
"""

def demo_package_level_access():
    """Demonstrate accessing neighbors at the package level."""
    print("=" * 60)
    print("1. Package-Level Access")
    print("=" * 60)
    
    # Import directly from the main package
    import socialmapper
    
    print("✅ Available functions at package level:")
    neighbor_functions = [attr for attr in dir(socialmapper) if 'neighbor' in attr.lower() or attr.startswith('get_')]
    for func in neighbor_functions:
        print(f"   • socialmapper.{func}")
    
    # Use the functions
    print("\n📍 Example usage:")
    nc_neighbors = socialmapper.get_neighboring_states('37')
    print(f"   NC neighboring states: {nc_neighbors}")
    
    wake_neighbors = socialmapper.get_neighboring_counties('37', '183')
    print(f"   Wake County neighbors: {len(wake_neighbors)} counties")

def demo_dedicated_module_access():
    """Demonstrate using the dedicated neighbors module."""
    print("\n" + "=" * 60)
    print("2. Dedicated Neighbors Module")
    print("=" * 60)
    
    # Import the dedicated neighbors module
    import socialmapper.neighbors as neighbors
    
    print("✅ Using dedicated neighbors module:")
    
    # State neighbors with abbreviations
    print("\n🏛️  State neighbors (with abbreviations):")
    nc_neighbors = neighbors.get_neighboring_states_by_abbr('NC')
    print(f"   NC neighbors: {nc_neighbors}")
    
    ca_neighbors = neighbors.get_neighboring_states_by_abbr('CA')
    print(f"   CA neighbors: {ca_neighbors}")
    
    # County neighbors
    print("\n🏘️  County neighbors:")
    wake_neighbors = neighbors.get_neighboring_counties('37', '183')
    print(f"   Wake County, NC: {len(wake_neighbors)} neighbors")
    
    la_neighbors = neighbors.get_neighboring_counties('06', '037')
    print(f"   Los Angeles County, CA: {len(la_neighbors)} neighbors")
    
    # Point geocoding
    print("\n📍 Point geocoding:")
    raleigh = neighbors.get_geography_from_point(35.7796, -78.6382)
    print(f"   Raleigh, NC: State {raleigh['state_fips']}, County {raleigh['county_fips']}")
    
    la_point = neighbors.get_geography_from_point(34.0522, -118.2437)
    print(f"   Los Angeles, CA: State {la_point['state_fips']}, County {la_point['county_fips']}")
    
    # Database statistics
    print("\n📊 Database statistics:")
    stats = neighbors.get_statistics()
    print(f"   • State relationships: {stats['state_relationships']:,}")
    print(f"   • County relationships: {stats['county_relationships']:,}")
    print(f"   • Cross-state relationships: {stats['cross_state_county_relationships']:,}")
    print(f"   • States with data: {stats['states_with_county_data']}")

def demo_census_module_access():
    """Demonstrate accessing through the census module."""
    print("\n" + "=" * 60)
    print("3. Census Module Access")
    print("=" * 60)
    
    # Import from census module (original location)
    from socialmapper.census import (
        get_neighboring_states,
        get_neighboring_counties,
        get_geography_from_point
    )
    
    print("✅ Using census module (original location):")
    
    # This is the original way to access the functions
    print("\n🔧 Original API access:")
    neighbors = get_neighboring_states('48')  # Texas
    print(f"   Texas neighbors: {neighbors}")
    
    harris_neighbors = get_neighboring_counties('48', '201')  # Harris County, TX
    print(f"   Harris County, TX: {len(harris_neighbors)} neighbors")

def demo_poi_batch_processing():
    """Demonstrate POI batch processing capabilities."""
    print("\n" + "=" * 60)
    print("4. POI Batch Processing")
    print("=" * 60)
    
    import socialmapper.neighbors as neighbors
    
    # Create sample POIs across different states
    pois = [
        {'lat': 35.7796, 'lon': -78.6382, 'name': 'Raleigh, NC'},
        {'lat': 35.2271, 'lon': -80.8431, 'name': 'Charlotte, NC'},
        {'lat': 34.0522, 'lon': -118.2437, 'name': 'Los Angeles, CA'},
        {'lat': 37.7749, 'lon': -122.4194, 'name': 'San Francisco, CA'},
        {'lat': 29.7604, 'lon': -95.3698, 'name': 'Houston, TX'},
        {'lat': 32.7767, 'lon': -96.7970, 'name': 'Dallas, TX'},
    ]
    
    print(f"✅ Processing {len(pois)} POIs:")
    for poi in pois:
        print(f"   • {poi['name']}")
    
    # Get counties without neighbors
    print("\n📍 Counties (POI locations only):")
    counties_only = neighbors.get_counties_from_pois(pois, include_neighbors=False)
    print(f"   Found {len(counties_only)} unique counties")
    for state_fips, county_fips in counties_only:
        state_abbr = neighbors.get_state_abbr(state_fips)
        print(f"     • {state_abbr}-{county_fips}")
    
    # Get counties with neighbors
    print("\n🌐 Counties (including neighbors):")
    counties_with_neighbors = neighbors.get_counties_from_pois(pois, include_neighbors=True)
    print(f"   Found {len(counties_with_neighbors)} counties (including neighbors)")
    print(f"   Expansion factor: {len(counties_with_neighbors) / len(counties_only):.1f}x")

def demo_convenience_functions():
    """Demonstrate convenience functions."""
    print("\n" + "=" * 60)
    print("5. Convenience Functions")
    print("=" * 60)
    
    import socialmapper.neighbors as neighbors
    
    print("✅ State code conversions:")
    
    # FIPS to abbreviation
    print("\n🔄 FIPS to abbreviation:")
    test_fips = ['37', '06', '48', '12', '36']
    for fips in test_fips:
        abbr = neighbors.get_state_abbr(fips)
        print(f"   {fips} → {abbr}")
    
    # Abbreviation to FIPS
    print("\n🔄 Abbreviation to FIPS:")
    test_abbrs = ['NC', 'CA', 'TX', 'FL', 'NY']
    for abbr in test_abbrs:
        fips = neighbors.get_state_fips(abbr)
        print(f"   {abbr} → {fips}")
    
    # Reference dictionaries
    print("\n📚 Reference data available:")
    print(f"   • STATE_FIPS_CODES: {len(neighbors.STATE_FIPS_CODES)} states")
    print(f"   • FIPS_TO_STATE: {len(neighbors.FIPS_TO_STATE)} mappings")

def main():
    """Run all demonstrations."""
    print("🗺️  SocialMapper Neighbors API Usage Examples")
    print("=" * 60)
    print("This script demonstrates multiple ways to access neighbor functionality")
    print("independently of the main SocialMapper workflow.\n")
    
    try:
        # Demo 1: Package-level access
        demo_package_level_access()
        
        # Demo 2: Dedicated module
        demo_dedicated_module_access()
        
        # Demo 3: Census module (original)
        demo_census_module_access()
        
        # Demo 4: POI batch processing
        demo_poi_batch_processing()
        
        # Demo 5: Convenience functions
        demo_convenience_functions()
        
        print("\n" + "=" * 60)
        print("🎉 All demonstrations completed successfully!")
        print("=" * 60)
        
        print("\n📋 Summary of access methods:")
        print("1. Package level:     import socialmapper")
        print("2. Dedicated module:  import socialmapper.neighbors")
        print("3. Census module:     from socialmapper.census import ...")
        print("4. All methods provide the same functionality with different APIs")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 