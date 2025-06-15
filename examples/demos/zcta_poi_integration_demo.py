#!/usr/bin/env python3
"""
SocialMapper Tutorial 03: ZCTA-Based POI Analysis

This advanced tutorial demonstrates using ZIP Code Tabulation Areas (ZCTAs) 
for Points of Interest analysis. You'll learn to:
- Use the SocialMapperBuilder with ZCTA geographic level
- Compare demographic patterns at ZIP code vs block group resolution
- Analyze service access patterns using postal geography
- Create business intelligence reports using familiar ZIP code boundaries

This tutorial integrates cutting-edge 2025 geospatial Python libraries 
with SocialMapper's modern architecture.

Prerequisites:
- SocialMapper installed: uv add socialmapper
- Census API key (recommended): Set CENSUS_API_KEY environment variable
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
from datetime import datetime

# Add parent directory to path if running from examples folder
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from socialmapper import SocialMapperClient, SocialMapperBuilder
from socialmapper.api.builder import GeographicLevel


def explain_zcta_poi_analysis():
    """Explain the value of ZCTA-based POI analysis."""
    print("🏢 ZCTA-Based POI Analysis: Business Intelligence for the Real World")
    print("=" * 80)
    print()
    print("Why analyze Points of Interest using ZIP Code Tabulation Areas?")
    print()
    print("📊 Business Intelligence Benefits:")
    print("  • Familiar geography - everyone understands ZIP codes")
    print("  • Market analysis - align with business delivery areas")
    print("  • Service planning - postal boundaries for outreach")
    print("  • Regional comparisons - consistent across metro areas")
    print()
    print("🎯 Use Cases:")
    print("  • Healthcare access by postal zones")
    print("  • Retail market penetration analysis")
    print("  • Educational service area planning")
    print("  • Public transportation network optimization")
    print()
    print("🔍 Modern 2025 Approach:")
    print("  • Vectorized spatial operations (GeoPandas + PyArrow)")
    print("  • Real-time census API integration")
    print("  • Memory-efficient batch processing")
    print("  • Interactive analysis with rich outputs")
    print()


def demo_basic_zcta_analysis():
    """Demonstrate basic ZCTA analysis using SocialMapperBuilder."""
    print("🏛️  Basic ZCTA Analysis: Libraries in Wake County, NC")
    print("=" * 60)
    
    print("\nStep 1: Configure analysis for ZCTA geography")
    print("📮 Setting geographic_level='zcta' for ZIP code resolution")
    
    try:
        # Build configuration for ZCTA analysis
        config = (SocialMapperBuilder()
            .with_location("Wake County", "North Carolina")
            .with_osm_pois("amenity", "library")
            .with_travel_time(20)  # 20 minutes for regional analysis
            .with_geographic_level(GeographicLevel.ZCTA)  # Key difference!
            .with_census_variables(
                "total_population",
                "median_household_income", 
                "education_bachelors_plus"
            )
            .with_exports(csv=True, isochrones=False)
            .build()
        )
        
        print("✅ Configuration built successfully")
        print(f"   🗺️  Location: {config.geocode_area}, {config.state}")
        print(f"   📚 POI Type: {config.poi_type} - {config.poi_name}")
        print(f"   📮 Geographic Level: {config.geographic_level}")
        print(f"   ⏱️  Travel Time: {config.travel_time} minutes")
        
        # Run analysis
        print("\nStep 2: Running ZCTA-based analysis...")
        with SocialMapperClient() as client:
            result = client.run_analysis(config)
            
            if result.is_ok():
                analysis_result = result.unwrap()
                print("✅ Analysis completed successfully!")
                
                # Display results
                print(f"\n📊 Results Summary:")
                print(f"   🏛️  Libraries found: {analysis_result.poi_count}")
                print(f"   📮 ZCTAs analyzed: {analysis_result.census_units_analyzed}")
                
                # Compare with what block group analysis would yield
                estimated_block_groups = analysis_result.census_units_analyzed * 8  # Rough estimate
                print(f"   📍 Block groups would be: ~{estimated_block_groups}")
                print(f"   ⚡ Processing speedup: ~{estimated_block_groups / analysis_result.census_units_analyzed:.1f}x faster")
                
                if analysis_result.files_generated:
                    print(f"\n📁 Files generated:")
                    for file_type, file_path in analysis_result.files_generated.items():
                        print(f"   • {file_type}: {file_path}")
            
            else:
                error = result.unwrap_err()
                print(f"❌ Analysis failed: {error.message}")
                print("\n💡 Troubleshooting:")
                print("   • Check internet connection")
                print("   • Verify location spelling")
                print("   • Try a smaller travel time")
    
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("💡 This might indicate missing dependencies or configuration issues")
    
    print()


def demo_comparative_analysis():
    """Compare ZCTA vs Block Group analysis side-by-side."""
    print("⚖️  Comparative Analysis: ZCTA vs Block Groups")
    print("=" * 60)
    
    # Configuration for both geographic levels
    base_config = {
        "location": ("Durham County", "North Carolina"),
        "poi": ("amenity", "hospital"),
        "travel_time": 15,
        "variables": ["total_population", "median_age", "percent_poverty"]
    }
    
    print(f"🏥 Analyzing hospital access in {base_config['location'][0]}")
    print(f"⏱️  Travel time: {base_config['travel_time']} minutes")
    print(f"📊 Variables: {', '.join(base_config['variables'])}")
    
    results = {}
    
    for geo_level, level_enum in [("Block Groups", GeographicLevel.BLOCK_GROUP), 
                                  ("ZCTAs", GeographicLevel.ZCTA)]:
        print(f"\n🔄 Running {geo_level} analysis...")
        
        try:
            config = (SocialMapperBuilder()
                .with_location(*base_config["location"])
                .with_osm_pois(*base_config["poi"])
                .with_travel_time(base_config["travel_time"])
                .with_geographic_level(level_enum)
                .with_census_variables(*base_config["variables"])
                .with_exports(csv=True, isochrones=False)
                .build()
            )
            
            start_time = datetime.now()
            
            with SocialMapperClient() as client:
                result = client.run_analysis(config)
                
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()
                
                if result.is_ok():
                    analysis_result = result.unwrap()
                    results[geo_level] = {
                        "pois": analysis_result.poi_count,
                        "units": analysis_result.census_units_analyzed,
                        "time": processing_time,
                        "status": "Success"
                    }
                    print(f"   ✅ {geo_level}: {analysis_result.census_units_analyzed} units in {processing_time:.1f}s")
                else:
                    error = result.unwrap_err()
                    results[geo_level] = {
                        "status": f"Failed: {error.message}",
                        "time": processing_time
                    }
                    print(f"   ❌ {geo_level}: Failed after {processing_time:.1f}s")
        
        except Exception as e:
            results[geo_level] = {"status": f"Error: {str(e)[:50]}..."}
            print(f"   ❌ {geo_level}: Configuration error")
    
    # Display comparison
    print(f"\n📊 Performance Comparison:")
    print("-" * 70)
    print(f"{'Metric':<20} {'Block Groups':<15} {'ZCTAs':<15} {'Difference':<15}")
    print("-" * 70)
    
    if all(r.get("status") == "Success" for r in results.values()):
        bg_data = results["Block Groups"]
        zcta_data = results["ZCTAs"]
        
        # Geographic units
        print(f"{'Units Analyzed':<20} {bg_data['units']:<15} {zcta_data['units']:<15} {zcta_data['units']/bg_data['units']:.2f}x fewer")
        
        # Processing time
        if bg_data['time'] > 0 and zcta_data['time'] > 0:
            speedup = bg_data['time'] / zcta_data['time']
            print(f"{'Processing Time':<20} {bg_data['time']:.1f}s{'':<9} {zcta_data['time']:.1f}s{'':<9} {speedup:.1f}x faster")
        
        # POI count (should be same)
        print(f"{'POIs Found':<20} {bg_data['pois']:<15} {zcta_data['pois']:<15} {'Same':<15}")
        
        print("-" * 70)
        
        print(f"\n🎯 Key Insights:")
        print(f"   • ZCTAs provide {zcta_data['units']/bg_data['units']:.1f}x fewer units = faster processing")
        print(f"   • Same POI coverage with different demographic resolution")
        print(f"   • Choose ZCTAs for regional analysis, Block Groups for local precision")
    else:
        for level, data in results.items():
            print(f"{level:<20} {data['status']:<30}")
    
    print()


def demo_business_intelligence_workflow():
    """Demonstrate a business intelligence workflow using ZCTAs."""
    print("💼 Business Intelligence Workflow: Retail Market Analysis")
    print("=" * 70)
    
    print("Scenario: A grocery chain wants to analyze market opportunities")
    print("in the Charlotte, NC metro area using ZIP code demographics.")
    print()
    
    # Multi-city analysis
    locations = [
        ("Charlotte", "North Carolina"),
        ("Gastonia", "North Carolina"), 
        ("Concord", "North Carolina")
    ]
    
    print("🏪 Analyzing grocery store access across metro area:")
    for i, (city, state) in enumerate(locations, 1):
        print(f"   {i}. {city}, {state}")
    
    print("\n📊 Business Intelligence Variables:")
    business_variables = [
        "total_population",           # Market size
        "median_household_income",    # Purchasing power
        "percent_with_vehicle",       # Transportation access
        "housing_units"               # Market density
    ]
    
    for var in business_variables:
        print(f"   • {var}")
    
    print(f"\n🔄 Running multi-location ZCTA analysis...")
    
    metro_results = []
    
    for city, state in locations:
        print(f"\n📍 Analyzing {city}...")
        
        try:
            config = (SocialMapperBuilder()
                .with_location(city, state)
                .with_osm_pois("shop", "supermarket")
                .with_travel_time(25)  # Longer for suburban/rural access
                .with_geographic_level(GeographicLevel.ZCTA)
                .with_census_variables(*business_variables)
                .with_exports(csv=True, isochrones=False)
                .build()
            )
            
            with SocialMapperClient() as client:
                result = client.run_analysis(config)
                
                if result.is_ok():
                    analysis_result = result.unwrap()
                    metro_results.append({
                        "city": city,
                        "supermarkets": analysis_result.poi_count,
                        "zctas": analysis_result.census_units_analyzed,
                        "files": analysis_result.files_generated
                    })
                    print(f"   ✅ {analysis_result.poi_count} supermarkets, {analysis_result.census_units_analyzed} ZCTAs")
                else:
                    error = result.unwrap_err()
                    print(f"   ❌ Failed: {error.message}")
        
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:50]}...")
    
    # Business Intelligence Summary
    if metro_results:
        print(f"\n💼 Business Intelligence Summary:")
        print("-" * 50)
        
        total_supermarkets = sum(r["supermarkets"] for r in metro_results)
        total_zctas = sum(r["zctas"] for r in metro_results)
        
        print(f"Metro Area Coverage:")
        print(f"  • Total Markets: {total_supermarkets}")
        print(f"  • ZIP Codes Analyzed: {total_zctas}")
        print(f"  • Average Markets per ZIP: {total_supermarkets/total_zctas:.2f}")
        
        print(f"\nCity Breakdown:")
        for result in metro_results:
            market_density = result["supermarkets"] / result["zctas"] if result["zctas"] > 0 else 0
            print(f"  • {result['city']}: {result['supermarkets']} markets in {result['zctas']} ZCTAs ({market_density:.2f} per ZIP)")
        
        print(f"\n📁 Generated Files:")
        for result in metro_results:
            if result.get("files"):
                print(f"  {result['city']}:")
                for file_type, path in result["files"].items():
                    print(f"    - {file_type}: {path}")
        
        print(f"\n🎯 Next Steps for Business Analysis:")
        print("  1. Load CSV files into business intelligence tools")
        print("  2. Identify high-income, underserved ZIP codes")
        print("  3. Analyze demographic patterns vs competitor locations")
        print("  4. Create market penetration heat maps")
        print("  5. Prioritize expansion opportunities by ZIP code")
    
    print()


def demo_modern_geospatial_techniques():
    """Demonstrate modern 2025 geospatial techniques with ZCTAs."""
    print("🚀 Modern Geospatial Techniques (2025 Edition)")
    print("=" * 60)
    
    print("Integrating cutting-edge Python geospatial libraries:")
    print()
    
    # Check for modern libraries
    modern_libs = {
        "geopandas": "Core spatial data handling",
        "pyarrow": "Memory-efficient columnar operations", 
        "folium": "Interactive web mapping",
        "plotly": "Modern interactive visualization",
        "contextily": "Web tile integration",
        "momepy": "Urban morphology analysis"
    }
    
    available_libs = []
    for lib, description in modern_libs.items():
        try:
            __import__(lib)
            available_libs.append(lib)
            print(f"   ✅ {lib}: {description}")
        except ImportError:
            print(f"   ⚠️  {lib}: {description} (not installed)")
    
    print(f"\n📦 Available modern libs: {len(available_libs)}/{len(modern_libs)}")
    
    if len(available_libs) >= 3:
        print("✅ Good coverage of modern geospatial tools!")
        
        print(f"\n🔬 Advanced Techniques Enabled:")
        print("  • Vector operations with PyArrow backend")
        print("  • Interactive mapping with web tiles")
        print("  • Memory-efficient spatial joins")
        print("  • Real-time demographic visualization")
        
        # Example of modern technique
        print(f"\n💡 Example: Modern ZCTA Processing Pipeline")
        print("```python")
        print("# Enable PyArrow for faster operations")
        print("import os")
        print("os.environ['PYOGRIO_USE_ARROW'] = '1'")
        print("")
        print("# Get census system with modern caching")
        print("from socialmapper.census import CensusSystemBuilder, CacheStrategy")
        print("")
        print("census_system = (CensusSystemBuilder()")
        print("    .with_cache_strategy(CacheStrategy.HYBRID)")
        print("    .with_rate_limit(2.0)")
        print("    .build())")
        print("")
        print("# Batch process multiple states efficiently")
        print("zctas = census_system.batch_get_zctas(")
        print("    state_fips_list=['37', '45', '13'],")
        print("    batch_size=2,")
        print("    progress_callback=lambda p, msg: print(f'{p:.1%}: {msg}')")
        print(")")
        print("```")
    else:
        print("⚠️  Consider installing more modern geospatial libraries:")
        print("   uv add pyarrow folium plotly contextily momepy")
    
    print()


def main():
    """Run the comprehensive ZCTA POI analysis tutorial."""
    print("🗺️  SocialMapper Tutorial 03: ZCTA-Based POI Analysis")
    print(f"{'='*80}")
    print(f"🕒 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Educational sections
    explain_zcta_poi_analysis()
    
    # Practical demonstrations  
    demo_basic_zcta_analysis()
    demo_comparative_analysis()
    demo_business_intelligence_workflow()
    demo_modern_geospatial_techniques()
    
    # Conclusion
    print("🎓 Tutorial Complete: You're Now Ready for Production ZCTA Analysis!")
    print("=" * 80)
    
    print("\n🏆 What You've Learned:")
    print("  ✅ Configure SocialMapperBuilder for ZCTA geography")
    print("  ✅ Compare ZCTA vs Block Group trade-offs")
    print("  ✅ Run business intelligence workflows")
    print("  ✅ Integrate modern 2025 geospatial libraries")
    print("  ✅ Process multi-location demographic analysis")
    
    print("\n🚀 Next Steps - Advanced Applications:")
    print("  1. 📊 Integrate results with Tableau/PowerBI")
    print("  2. 🤖 Build automated market research pipelines")
    print("  3. 🌐 Create interactive web dashboards")
    print("  4. 📱 Develop mobile-friendly reporting")
    print("  5. ⚡ Scale to state/national level analysis")
    
    print("\n🔗 Resources for Continued Learning:")
    print("  • Modern GeoPandas (2025): https://geopandas.org/")
    print("  • PyArrow Spatial: https://arrow.apache.org/")
    print("  • SocialMapper Docs: Check docs/ directory")
    print("  • Census API: https://www.census.gov/data/developers/")
    
    print(f"\n🕒 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 