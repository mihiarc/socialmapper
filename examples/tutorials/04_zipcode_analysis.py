#!/usr/bin/env python3
"""
SocialMapper Tutorial 02: ZIP Code Tabulation Area (ZCTA) Analysis

This tutorial explores demographic analysis using ZIP Code Tabulation Areas (ZCTAs),
which are statistical geographic units that approximate ZIP code delivery areas.
You'll learn:
- What ZCTAs are and why they're useful
- How to fetch ZCTA boundaries and census data
- Comparing ZCTA vs block group analysis
- Batch processing for large-scale analysis
- Creating choropleth maps to visualize ZCTA demographics

Prerequisites:
- SocialMapper installed: uv add socialmapper
- Census API key (optional): Set CENSUS_API_KEY environment variable
"""

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available - continue without it
    pass

import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import geopandas as gpd

# Add parent directory to path if running from examples folder
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from socialmapper import get_census_system, CensusSystemBuilder, SocialMapperClient, SocialMapperBuilder
from socialmapper.api.builder import GeographicLevel
from socialmapper.census.services.zcta_service import ZctaService


def explain_zctas():
    """Explain what ZCTAs are and their use cases."""
    print("📮 Understanding ZIP Code Tabulation Areas (ZCTAs)")
    print("=" * 60)
    print()
    print("ZCTAs are statistical areas created by the Census Bureau that approximate")
    print("the geographic areas covered by US Postal Service ZIP codes.")
    print()
    print("🎯 Why use ZCTAs?")
    print("  • Familiar to most people (everyone knows ZIP codes)")
    print("  • Larger than block groups = faster processing")
    print("  • Good for regional/neighborhood-level analysis")
    print("  • Useful for business and marketing analysis")
    print()
    print("⚡ When to choose ZCTAs vs Block Groups:")
    print("  • ZCTAs: Regional analysis, marketing, service areas")
    print("  • Block Groups: Precise local analysis, walkability studies")
    print()


def demo_basic_zcta_operations():
    """Demonstrate basic ZCTA operations using the census system."""
    print("🔧 Basic ZCTA Operations")
    print("=" * 40)
    
    # Initialize the modern census system
    census_system = get_census_system()
    
    # Example: Get ZCTAs for North Carolina (state FIPS: 37)
    print("\n1. Fetching ZCTAs for North Carolina...")
    try:
        nc_zctas = census_system.get_zctas_for_state("37")
        print(f"   ✅ Found {len(nc_zctas)} ZCTAs in North Carolina")
        
        # Show some sample ZCTAs
        if not nc_zctas.empty:
            sample_zctas = nc_zctas.head(3)
            print(f"   📋 Sample ZCTAs: {', '.join(sample_zctas['GEOID'].astype(str))}")
            print(f"   🗺️  Columns available: {list(nc_zctas.columns)}")
    
    except Exception as e:
        print(f"   ❌ Error fetching ZCTAs: {e}")
        print("   💡 This might be due to API limits or network issues")
    
    # Example: Get ZCTA for a specific point
    print("\n2. Finding ZCTA for a specific location...")
    # Raleigh, NC coordinates
    lat, lon = 35.7796, -78.6382
    try:
        zcta_code = census_system.get_zcta_for_point(lat, lon)
        print(f"   📍 Point ({lat}, {lon}) is in ZCTA: {zcta_code}")
    except Exception as e:
        print(f"   ❌ Error geocoding point: {e}")
    
    print()


def demo_zcta_census_data():
    """Demonstrate fetching census data for ZCTAs."""
    print("📊 ZCTA Census Data Analysis")
    print("=" * 40)
    
    census_system = get_census_system()
    
    # Define some example ZCTAs (major cities)
    example_zctas = [
        "27601",  # Raleigh, NC downtown
        "27605",  # Raleigh, NC suburbs  
        "27609",  # Raleigh, NC north
        "28202",  # Charlotte, NC uptown
        "28204",  # Charlotte, NC south
    ]
    
    # Census variables for demographic analysis
    variables = [
        "B01003_001E",  # Total population
        "B19013_001E",  # Median household income
        "B25003_002E",  # Owner-occupied housing units
        "B25003_003E",  # Renter-occupied housing units
    ]
    
    print(f"\n🎯 Analyzing {len(example_zctas)} ZCTAs:")
    print(f"   ZCTAs: {', '.join(example_zctas)}")
    print(f"   Variables: Population, Income, Housing Tenure")
    
    try:
        # Fetch census data for these ZCTAs
        census_data = census_system.get_zcta_census_data(
            geoids=example_zctas,
            variables=variables
        )
        
        if not census_data.empty:
            print(f"\n✅ Retrieved {len(census_data)} data points")
            
            # Transform data for analysis
            analysis_data = []
            for zcta in example_zctas:
                zcta_data = census_data[census_data['GEOID'] == zcta]
                
                if not zcta_data.empty:
                    # Extract values for each variable
                    data_dict = {'ZCTA': zcta}
                    for _, row in zcta_data.iterrows():
                        var_code = row['variable_code']
                        value = row['value']
                        
                        if var_code == 'B01003_001E':
                            data_dict['Population'] = int(value) if value else 0
                        elif var_code == 'B19013_001E':
                            data_dict['Median_Income'] = int(value) if value else 0
                        elif var_code == 'B25003_002E':
                            data_dict['Owner_Occupied'] = int(value) if value else 0
                        elif var_code == 'B25003_003E':
                            data_dict['Renter_Occupied'] = int(value) if value else 0
                    
                    # Calculate derived metrics
                    total_occupied = data_dict.get('Owner_Occupied', 0) + data_dict.get('Renter_Occupied', 0)
                    if total_occupied > 0:
                        data_dict['Pct_Owner_Occupied'] = round(
                            (data_dict.get('Owner_Occupied', 0) / total_occupied) * 100, 1
                        )
                    
                    analysis_data.append(data_dict)
            
            # Display results in a formatted table
            if analysis_data:
                df = pd.DataFrame(analysis_data)
                print("\n📋 ZCTA Demographics Summary:")
                print("-" * 80)
                print(f"{'ZCTA':<8} {'Population':<12} {'Med Income':<12} {'% Owner Occ':<12}")
                print("-" * 80)
                
                for _, row in df.iterrows():
                    zcta = row.get('ZCTA', 'N/A')
                    pop = f"{row.get('Population', 0):,}" if row.get('Population') else 'N/A'
                    income = f"${row.get('Median_Income', 0):,}" if row.get('Median_Income') else 'N/A'
                    owner_pct = f"{row.get('Pct_Owner_Occupied', 0):.1f}%" if row.get('Pct_Owner_Occupied') else 'N/A'
                    
                    print(f"{zcta:<8} {pop:<12} {income:<12} {owner_pct:<12}")
                print("-" * 80)
        else:
            print("❌ No census data retrieved")
    
    except Exception as e:
        print(f"❌ Error fetching census data: {e}")
        print("💡 Try checking your internet connection or API limits")
    
    print()


def demo_batch_processing():
    """Demonstrate batch processing for multiple states."""
    print("⚡ Batch Processing Multiple States")
    print("=" * 40)
    
    census_system = get_census_system()
    
    # Small southeastern states for demo
    states = {
        "37": "North Carolina",
        "45": "South Carolina", 
        "13": "Georgia"
    }
    
    print(f"\n🗺️  Processing ZCTAs for {len(states)} states:")
    for fips, name in states.items():
        print(f"   • {name} (FIPS: {fips})")
    
    try:
        # Use batch processing
        state_fips_list = list(states.keys())
        all_zctas = census_system.batch_get_zctas(
            state_fips_list=state_fips_list,
            batch_size=2,  # Process 2 states at a time
            progress_callback=None  # Could add progress tracking
        )
        
        if not all_zctas.empty:
            print(f"\n✅ Successfully processed {len(all_zctas)} total ZCTAs")
            
            # Show state-by-state breakdown
            print("\n📊 ZCTAs by State:")
            for fips, name in states.items():
                state_zctas = all_zctas[all_zctas['STATEFP'] == fips]
                print(f"   • {name}: {len(state_zctas)} ZCTAs")
        else:
            print("❌ No ZCTAs retrieved in batch processing")
    
    except Exception as e:
        print(f"❌ Batch processing error: {e}")
        print("💡 This might be due to API rate limits or network issues")
    
    print()


def demo_comparison_analysis():
    """Compare ZCTA vs Block Group analysis."""
    print("🔍 ZCTA vs Block Group Comparison")
    print("=" * 40)
    
    print("\n📈 Key Differences:")
    print("┌─────────────────┬─────────────────┬─────────────────┐")
    print("│ Aspect          │ Block Groups    │ ZCTAs           │")
    print("├─────────────────┼─────────────────┼─────────────────┤")
    print("│ Size            │ ~600-3000 people│ ~5000-50000     │")
    print("│ Precision       │ Very High       │ Moderate        │")
    print("│ Processing      │ Slower          │ Faster          │")
    print("│ Familiarity     │ Technical       │ Everyone knows  │")
    print("│ Use Case        │ Local analysis  │ Regional trends │")
    print("└─────────────────┴─────────────────┴─────────────────┘")
    
    print("\n🎯 When to Use Each:")
    print("  📍 Block Groups:")
    print("     • Walking distance analysis")
    print("     • Neighborhood-level demographics")
    print("     • Urban planning studies")
    print("     • Environmental justice analysis")
    print()
    print("  📮 ZCTAs:")
    print("     • Business market analysis")
    print("     • Service area definition")
    print("     • Regional demographic trends")
    print("     • Mail-based service delivery")
    print()


def demo_advanced_features():
    """Demonstrate advanced ZCTA features."""
    print("🚀 Advanced ZCTA Features")
    print("=" * 40)
    
    print("\n1. 🗂️  ZCTA Data URLs")
    print("   Get direct download links for ZCTA shapefiles:")
    census_system = get_census_system()
    
    try:
        urls = census_system.get_zcta_urls(year=2020)
        for name, url in urls.items():
            print(f"   • {name}: {url}")
    except Exception as e:
        print(f"   ❌ Error getting URLs: {e}")
    
    print("\n2. 🎛️  Custom Configuration")
    print("   Build census system with custom settings:")
    print("   ```python")
    print("   from socialmapper.census import CensusSystemBuilder, CacheStrategy")
    print("   ")
    print("   census_system = (CensusSystemBuilder()")
    print("       .with_api_key('your_key')")
    print("       .with_cache_strategy(CacheStrategy.FILE)")
    print("       .with_rate_limit(2.0)  # 2 requests per second")
    print("       .build())")
    print("   ```")
    
    print("\n3. 📡 Streaming Interface")
    print("   For legacy compatibility:")
    print("   ```python")
    print("   streaming_manager = census_system.create_streaming_manager()")
    print("   zctas = streaming_manager.get_zctas(['37', '45'])")
    print("   ```")
    print()


def demo_zcta_map_visualization():
    """Demonstrate full SocialMapper pipeline with ZCTA-level choropleth maps."""
    print("🗺️  ZCTA Choropleth Map Visualization")
    print("=" * 40)
    
    print("\nThis demonstrates the full SocialMapper pipeline at the ZCTA level,")
    print("including automated choropleth map generation.")
    
    # Define search parameters
    print("\n📍 Setting up analysis parameters...")
    geocode_area = "Wake County"
    state = "North Carolina"
    poi_type = "amenity"
    poi_name = "library"
    travel_time = 15
    
    print(f"  • Location: {geocode_area}, {state}")
    print(f"  • POI Type: {poi_type} - {poi_name}")
    print(f"  • Travel Time: {travel_time} minutes")
    print("  • Geographic Level: ZCTA (ZIP Code areas)")
    
    # Census variables to analyze
    census_variables = [
        "total_population",
        "median_household_income",
        "median_age"
    ]
    print(f"  • Census Variables: {', '.join(census_variables)}")
    
    print("\n🚀 Running ZCTA-level analysis...")
    
    try:
        # Use the SocialMapper client with ZCTA geographic level
        with SocialMapperClient() as client:
            # Build configuration using fluent interface
            config = (SocialMapperBuilder()
                .with_location(geocode_area, state)
                .with_osm_pois(poi_type, poi_name)
                .with_travel_time(travel_time)
                .with_census_variables(*census_variables)
                .with_geographic_level(GeographicLevel.ZCTA)  # Use ZCTA instead of block group
                .with_exports(csv=True, isochrones=False, maps=True)  # Enable map generation
                .build()
            )
            
            # Run analysis
            result = client.run_analysis(config)
            
            # Handle result
            if result.is_err():
                error = result.unwrap_err()
                print(f"\n❌ Error: {error.message}")
                return
            
            # Get successful result
            analysis_result = result.unwrap()
            
            print("\n✅ ZCTA analysis complete!")
            
            # Show results summary
            print(f"\n📊 Results Summary:")
            print(f"  • Found {analysis_result.poi_count} libraries")
            print(f"  • Analyzed {analysis_result.census_units_analyzed} ZCTAs")
            
            # Show generated files
            if analysis_result.files_generated:
                print("\n📁 Files generated:")
                for file_type, file_path in analysis_result.files_generated.items():
                    print(f"  • {file_type}: {file_path}")
            
            # Check for generated maps
            map_dir = Path("output/maps")
            if map_dir.exists():
                map_files = list(map_dir.glob("*zcta*.png"))
                if map_files:
                    print("\n🗺️  ZCTA Choropleth maps generated:")
                    for map_file in sorted(map_files):
                        print(f"  • {map_file.name}")
                    
                    print("\n💡 Map descriptions:")
                    print("  • Population maps: Show population density by ZCTA")
                    print("  • Income maps: Display median household income patterns")
                    print("  • Age maps: Visualize median age demographics")
                    print("  • Distance maps: Show travel distance to nearest library")
                    print("  • Accessibility maps: Highlight ZCTAs within 15-minute reach")
                else:
                    print("\n📍 Note: Maps were requested but may not have been generated.")
                    print("   This could happen if no POIs were found in the area.")
            
            print("\n🔍 ZCTA vs Block Group Comparison:")
            print("  • ZCTAs provide broader regional patterns")
            print("  • Processing is faster with fewer geographic units")
            print("  • Results are more suitable for business/marketing analysis")
            print("  • Trade-off: Less precision than block group analysis")
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        print("💡 Try checking your internet connection or Census API key")
    
    print()


def main():
    """Run the ZCTA analysis tutorial."""
    print("🗺️  SocialMapper Tutorial 02: ZCTA Analysis\n")
    
    # Educational content
    explain_zctas()
    
    # Basic operations
    demo_basic_zcta_operations()
    
    # Census data analysis
    demo_zcta_census_data()
    
    # Batch processing
    demo_batch_processing()
    
    # Comparison analysis
    demo_comparison_analysis()
    
    # Advanced features
    demo_advanced_features()
    
    # NEW: Full pipeline with choropleth map visualization
    demo_zcta_map_visualization()
    
    # Next steps
    print("🎉 Tutorial Complete! Next Steps:")
    print("=" * 40)
    print("1. 🔍 Try the SocialMapperBuilder with geographic_level='zcta'")
    print("2. 📊 Explore different census variables in ZCTA analysis")
    print("3. 🗺️  Compare ZCTA vs block group results for your area")
    print("4. ⚡ Use batch processing for multi-state analysis")
    print("5. 🎯 Check out the generated choropleth maps in output/maps/")
    
    print("\n💡 Pro Tips:")
    print("  • ZCTAs are great for business/marketing analysis")
    print("  • Choropleth maps at ZCTA level show regional patterns clearly")
    print("  • Use caching to speed up repeated analyses")
    print("  • Consider rate limiting for large batch jobs")
    print("  • Remember: ZCTAs ≈ ZIP codes, but not exactly the same!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 