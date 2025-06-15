#!/usr/bin/env python3
"""
SocialMapper Tutorial 05: TIGER REST API ZCTA Boundaries

This tutorial demonstrates the updated ZCTA boundary fetching using the correct
TIGER REST API endpoint. You'll learn:
- How to use the official TIGER REST API for ZCTA boundaries
- Understanding the API response format and field mapping
- Efficient state-level ZCTA boundary retrieval
- Combining boundary data with census demographics

Uses the official TIGER REST API endpoint:
https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/PUMA_TAD_TAZ_UGA_ZCTA/MapServer/7

Prerequisites:
- SocialMapper installed: uv add socialmapper
- GeoPandas: uv add geopandas
- Census API key (optional): Set CENSUS_API_KEY environment variable
"""

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import geopandas as gpd
from datetime import datetime

# Add parent directory to path if running from examples folder
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from socialmapper import get_census_system


def explain_tiger_api_integration():
    """Explain the TIGER REST API integration for ZCTA boundaries."""
    print("🐅 TIGER REST API ZCTA Boundary Integration")
    print("=" * 80)
    print()
    print("The updated ZCTA service now uses the official TIGER REST API endpoint")
    print("for reliable, accurate ZIP Code Tabulation Area boundary data.")
    print()
    print("📡 Official TIGER REST API Endpoint:")
    print("   https://tigerweb.geo.census.gov/arcgis/rest/services/")
    print("   TIGERweb/PUMA_TAD_TAZ_UGA_ZCTA/MapServer/7")
    print()
    print("📊 Layer Information:")
    print("   • Layer ID: 7")
    print("   • Name: 2020 Census ZIP Code Tabulation Areas")
    print("   • Geometry: Polygon (esriGeometryPolygon)")
    print("   • Vintage: January 1, 2020")
    print("   • Max Records: 100,000")
    print()
    print("🔧 Key Fields Available:")
    print("   • GEOID: ZIP Code Tabulation Area identifier")
    print("   • ZCTA5: 5-digit ZCTA code")
    print("   • BASENAME: Base name of the ZCTA")
    print("   • NAME: Full name of the ZCTA")
    print("   • AREALAND: Land area in square meters")
    print("   • AREAWATER: Water area in square meters")
    print("   • CENTLAT/CENTLON: Centroid coordinates")
    print("   • POP100: 2020 Census population")
    print("   • HU100: 2020 Census housing units")
    print()
    print("✨ Improvements:")
    print("   • Official Census Bureau API endpoint")
    print("   • GeoJSON response format for easy processing")
    print("   • Complete field set including demographics")
    print("   • Reliable geometry data")
    print("   • Proper error handling and caching")
    print()


def demo_zcta_boundary_fetching():
    """Demonstrate ZCTA boundary fetching with the TIGER API."""
    print("🗺️ ZCTA Boundary Fetching Demo")
    print("=" * 50)
    
    # Get the modern census system
    census_system = get_census_system()
    
    # Test states - mix of different regions and sizes
    test_states = [
        ("37", "North Carolina"),
        ("06", "California"), 
        ("10", "Delaware"),  # Small state for quick testing
    ]
    
    print(f"\n📍 Testing ZCTA boundary fetching for {len(test_states)} states:")
    for fips, name in test_states:
        print(f"   • {fips}: {name}")
    
    results = {}
    
    for state_fips, state_name in test_states:
        print(f"\n🔄 Fetching ZCTAs for {state_name} (FIPS: {state_fips})...")
        start_time = time.time()
        
        try:
            # Fetch ZCTA boundaries using the TIGER API
            zctas = census_system._zcta_service.get_zctas_for_state(state_fips)
            processing_time = time.time() - start_time
            
            if not zctas.empty:
                results[state_fips] = {
                    'success': True,
                    'count': len(zctas),
                    'time': processing_time,
                    'columns': list(zctas.columns),
                    'sample_geoid': zctas['GEOID'].iloc[0] if 'GEOID' in zctas.columns else None,
                    'has_geometry': zctas.geometry.notna().all(),
                    'crs': str(zctas.crs) if zctas.crs else None
                }
                
                print(f"   ✅ Success: {len(zctas)} ZCTAs in {processing_time:.2f}s")
                print(f"   📊 Columns: {len(zctas.columns)} fields available")
                print(f"   🗺️ Geometry: {'Valid' if zctas.geometry.notna().all() else 'Issues detected'}")
                print(f"   🎯 CRS: {zctas.crs}")
                
                # Show sample ZCTA info
                if 'GEOID' in zctas.columns:
                    sample_zcta = zctas.iloc[0]
                    print(f"   📋 Sample ZCTA: {sample_zcta.get('GEOID', 'N/A')}")
                    if 'NAME' in zctas.columns:
                        print(f"       Name: {sample_zcta.get('NAME', 'N/A')}")
                    if 'POP100' in zctas.columns:
                        pop = sample_zcta.get('POP100', 'N/A')
                        print(f"       2020 Population: {pop:,.0f}" if isinstance(pop, (int, float)) else f"       2020 Population: {pop}")
                
            else:
                results[state_fips] = {
                    'success': False,
                    'error': 'No ZCTAs returned',
                    'time': processing_time
                }
                print(f"   ❌ No ZCTAs returned for {state_name}")
                
        except Exception as e:
            processing_time = time.time() - start_time
            results[state_fips] = {
                'success': False,
                'error': str(e),
                'time': processing_time
            }
            print(f"   ❌ Error: {e}")
    
    # Summary
    print(f"\n📊 TIGER API Performance Summary:")
    print("-" * 60)
    print(f"{'State':<15} {'Status':<10} {'Count':<8} {'Time (s)':<10} {'Rate':<12}")
    print("-" * 60)
    
    total_zctas = 0
    total_time = 0
    successful_states = 0
    
    for state_fips, state_name in test_states:
        result = results.get(state_fips, {})
        if result.get('success'):
            count = result['count']
            time_taken = result['time']
            rate = count / time_taken if time_taken > 0 else 0
            print(f"{state_name[:14]:<15} {'✅ Success':<10} {count:<8} {time_taken:.2f}{'s':<7} {rate:.1f}/s")
            total_zctas += count
            total_time += time_taken
            successful_states += 1
        else:
            error = result.get('error', 'Unknown')[:20]
            time_taken = result.get('time', 0)
            print(f"{state_name[:14]:<15} {'❌ Failed':<10} {'N/A':<8} {time_taken:.2f}{'s':<7} {error}")
    
    print("-" * 60)
    if successful_states > 0:
        avg_rate = total_zctas / total_time if total_time > 0 else 0
        print(f"{'TOTAL':<15} {f'{successful_states}/{len(test_states)}':<10} {total_zctas:<8} {total_time:.2f}{'s':<7} {avg_rate:.1f}/s")
    
    print()
    return results


def demo_multi_state_batch_processing():
    """Demonstrate efficient multi-state ZCTA boundary fetching."""
    print("⚡ Multi-State Batch Processing")
    print("=" * 50)
    
    census_system = get_census_system()
    
    # Test with a few smaller states for demonstration
    batch_states = ["10", "50", "02"]  # Delaware, Vermont, Alaska
    state_names = {"10": "Delaware", "50": "Vermont", "02": "Alaska"}
    
    print(f"\n🔄 Batch processing {len(batch_states)} states:")
    for fips in batch_states:
        print(f"   • {fips}: {state_names.get(fips, 'Unknown')}")
    
    start_time = time.time()
    
    try:
        # Use the batch method
        all_zctas = census_system._zcta_service.get_zctas_for_states(batch_states)
        processing_time = time.time() - start_time
        
        if not all_zctas.empty:
            print(f"\n✅ Batch Success!")
            print(f"   📊 Total ZCTAs: {len(all_zctas)}")
            print(f"   ⏱️  Total time: {processing_time:.2f} seconds")
            print(f"   🏃 Processing rate: {len(all_zctas)/processing_time:.1f} ZCTAs/second")
            
            # Analyze by state
            if 'STATEFP' in all_zctas.columns:
                state_counts = all_zctas['STATEFP'].value_counts()
                print(f"\n📋 ZCTAs by State:")
                for state_fips in batch_states:
                    count = state_counts.get(state_fips, 0)
                    state_name = state_names.get(state_fips, f"State {state_fips}")
                    print(f"   • {state_name}: {count} ZCTAs")
            
            # Show data quality
            print(f"\n🔍 Data Quality Check:")
            print(f"   • Valid geometries: {all_zctas.geometry.is_valid.sum()}/{len(all_zctas)}")
            print(f"   • Non-null GEOIDs: {all_zctas['GEOID'].notna().sum()}/{len(all_zctas)}")
            print(f"   • Available fields: {len(all_zctas.columns)}")
            
            return all_zctas
        else:
            print(f"❌ No ZCTAs returned from batch processing")
            return None
            
    except Exception as e:
        processing_time = time.time() - start_time
        print(f"❌ Batch processing failed: {e}")
        print(f"   Time elapsed: {processing_time:.2f} seconds")
        return None


def demo_zcta_data_integration():
    """Demonstrate combining ZCTA boundaries with census data."""
    print("🔗 ZCTA Boundary + Census Data Integration")
    print("=" * 50)
    
    census_system = get_census_system()
    
    # Use a small state for demonstration
    test_state = "10"  # Delaware
    test_variables = ["B01003_001E", "B19013_001E"]  # Population, Median Income
    
    print(f"\n🎯 Integration Demo: Delaware ZCTAs with Demographics")
    print(f"   State FIPS: {test_state}")
    print(f"   Variables: {', '.join(test_variables)}")
    
    try:
        # Step 1: Get ZCTA boundaries
        print(f"\n📍 Step 1: Fetching ZCTA boundaries...")
        start_time = time.time()
        zctas = census_system._zcta_service.get_zctas_for_state(test_state)
        boundary_time = time.time() - start_time
        
        if zctas.empty:
            print(f"❌ No ZCTA boundaries retrieved")
            return
        
        print(f"   ✅ Retrieved {len(zctas)} ZCTA boundaries in {boundary_time:.2f}s")
        
        # Step 2: Get census data for the ZCTAs
        print(f"\n📊 Step 2: Fetching census data...")
        if 'GEOID' in zctas.columns:
            geoids = zctas['GEOID'].tolist()[:10]  # Limit to first 10 for demo
            print(f"   Fetching data for {len(geoids)} ZCTAs...")
            
            start_time = time.time()
            census_data = census_system._zcta_service.get_census_data(
                geoids=geoids,
                variables=test_variables
            )
            data_time = time.time() - start_time
            
            if not census_data.empty:
                print(f"   ✅ Retrieved {len(census_data)} data points in {data_time:.2f}s")
                
                # Step 3: Combine the data
                print(f"\n🔗 Step 3: Combining boundary and census data...")
                
                # Pivot census data for easier joining
                census_pivot = census_data.pivot(
                    index='GEOID', 
                    columns='variable_code', 
                    values='value'
                ).reset_index()
                
                # Join with boundaries
                combined = zctas.merge(census_pivot, on='GEOID', how='left')
                
                print(f"   ✅ Combined dataset: {len(combined)} ZCTAs with demographics")
                print(f"   📊 Final columns: {len(combined.columns)} fields")
                
                # Show sample results
                print(f"\n📋 Sample Combined Data:")
                print("-" * 70)
                print(f"{'ZCTA':<8} {'Population':<12} {'Med Income':<12} {'Has Geometry':<12}")
                print("-" * 70)
                
                for _, row in combined.head(5).iterrows():
                    zcta = row.get('GEOID', 'N/A')
                    pop = row.get('B01003_001E', 'N/A')
                    income = row.get('B19013_001E', 'N/A')
                    has_geom = 'Yes' if row.geometry is not None else 'No'
                    
                    pop_str = f"{pop:,.0f}" if isinstance(pop, (int, float)) and not pd.isna(pop) else "N/A"
                    income_str = f"${income:,.0f}" if isinstance(income, (int, float)) and not pd.isna(income) else "N/A"
                    
                    print(f"{zcta:<8} {pop_str:<12} {income_str:<12} {has_geom:<12}")
                
                print("-" * 70)
                
                return combined
            else:
                print(f"   ❌ No census data retrieved")
        else:
            print(f"   ❌ No GEOID column found in boundaries")
            
    except Exception as e:
        print(f"❌ Integration failed: {e}")
        return None


def demo_api_field_mapping():
    """Demonstrate understanding of TIGER API field mapping."""
    print("🗂️ TIGER API Field Mapping Analysis")
    print("=" * 50)
    
    print("The TIGER REST API provides rich field data for ZCTAs.")
    print("Understanding the field mapping helps optimize data usage.")
    print()
    
    print("📋 Key TIGER API Fields:")
    field_info = {
        "GEOID": "ZIP Code Tabulation Area identifier (5 digits)",
        "ZCTA5": "5-digit ZCTA code (same as GEOID)",
        "BASENAME": "Base name of the ZCTA",
        "NAME": "Full descriptive name",
        "AREALAND": "Land area in square meters",
        "AREAWATER": "Water area in square meters", 
        "CENTLAT": "Centroid latitude",
        "CENTLON": "Centroid longitude",
        "INTPTLAT": "Interior point latitude",
        "INTPTLON": "Interior point longitude",
        "POP100": "2020 Census population count",
        "HU100": "2020 Census housing unit count"
    }
    
    for field, description in field_info.items():
        print(f"   • {field:<12}: {description}")
    
    print()
    print("🔧 SocialMapper Field Standardization:")
    print("   • ZCTA5 → ZCTA5CE (standard column name)")
    print("   • GEOID → GEOID (kept as primary identifier)")
    print("   • Added STATEFP for state filtering")
    print("   • Geometry validation and CRS standardization")
    print()
    
    print("✨ Benefits of Rich Field Set:")
    print("   • Built-in population and housing data")
    print("   • Precise centroid coordinates")
    print("   • Area calculations for density analysis")
    print("   • Consistent naming across all ZCTAs")
    print()


def main():
    """Run the TIGER API ZCTA boundary demonstration."""
    print("🐅 SocialMapper Tutorial 05: TIGER REST API ZCTA Boundaries")
    print(f"{'='*80}")
    print(f"🕒 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Educational sections
    explain_tiger_api_integration()
    
    # Practical demonstrations
    demo_zcta_boundary_fetching()
    demo_multi_state_batch_processing()
    demo_zcta_data_integration()
    demo_api_field_mapping()
    
    # Conclusion
    print("🎓 Tutorial Complete: TIGER API ZCTA Mastery!")
    print("=" * 60)
    
    print("\n🏆 What You've Learned:")
    print("  ✅ Official TIGER REST API endpoint usage")
    print("  ✅ ZCTA boundary fetching with proper field mapping")
    print("  ✅ Multi-state batch processing techniques")
    print("  ✅ Boundary + census data integration")
    print("  ✅ API response format and error handling")
    
    print("\n🚀 Next Steps:")
    print("  1. 🗺️ Use ZCTA boundaries for spatial analysis")
    print("  2. 📊 Combine with demographic data for insights")
    print("  3. 🔧 Implement caching for production workflows")
    print("  4. 📈 Scale to national-level ZCTA analysis")
    print("  5. 🎨 Create visualizations with boundary data")
    
    print("\n💡 Pro Tips:")
    print("  • TIGER API returns national data - filter by state")
    print("  • Use GeoJSON format for easier processing")
    print("  • Cache boundary data - it changes infrequently")
    print("  • Validate geometries before spatial operations")
    print("  • ZCTAs can cross state boundaries - handle appropriately")
    
    print(f"\n🕒 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 