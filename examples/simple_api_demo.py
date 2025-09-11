#!/usr/bin/env python3
"""
SocialMapper Simple API Demo

This example demonstrates the new, simplified SocialMapper API that eliminates
the over-engineering of the legacy complex API.

Compare:
- Old API: 8+ lines of ceremony, Result unwrapping, context managers
- New API: 2 lines, direct results, standard Python patterns
"""

from socialmapper import SocialMapper, quick_analysis, analyze_libraries

def main():
    """Demonstrate the simple API in action."""
    
    print("🗺️  SocialMapper Simple API Demo\n")
    
    # Example 1: Quick one-liner analysis
    print("1. Quick Analysis (one-liner):")
    print("-" * 40)
    
    result = quick_analysis(
        "Portland, OR",
        "library", 
        travel_time=15,
        census_variables=["total_population", "median_household_income"]
    )
    print(f"Found {result['poi_count']} libraries")
    print(f"Population served: {result.get('demographics', {}).get('total_population', 'N/A'):,}")
    print()
    
    # Example 2: Full client usage
    print("2. Full Client Usage:")
    print("-" * 40)
    
    mapper = SocialMapper()
    
    try:
        result = mapper.analyze_location(
            "San Francisco, CA",
            poi_types=["library", "school"],
            travel_time=20,
            travel_mode="walk",
            census_variables=["total_population", "median_age"]
        )
        
        print(f"Analysis completed successfully!")
        print(f"POIs found: {result.poi_count}")
        print(f"Census units analyzed: {result.census_units_analyzed}")
        print(f"Isochrone area: {result.isochrone_area_km2:.2f} km²")
        
        # Access demographics easily
        if result.demographics:
            print(f"Total population: {result.demographics.get('total_population', 'N/A'):,}")
            print(f"Median age: {result.demographics.get('median_age', 'N/A'):.1f}")
        
        print(f"Files created: {len(result.files_created)}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    print()
    
    # Example 3: Preset analysis functions
    print("3. Preset Analysis Functions:")
    print("-" * 40)
    
    try:
        result = analyze_libraries(
            "Boston, MA",
            travel_time=25,
            travel_mode="walk",
            include_demographics=True
        )
        
        result.print_summary()
        
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 4: POI discovery
    print("\n4. POI Discovery:")
    print("-" * 40)
    
    try:
        result = mapper.discover_nearby_pois(
            "Chapel Hill, NC",
            travel_time=15,
            travel_mode="walk",
            poi_categories=["food_and_drink", "healthcare"]
        )
        
        print(f"Total POIs discovered: {result.total_poi_count}")
        print(f"Categories found: {result.unique_categories}")
        print(f"Area covered: {result.isochrone_area_km2:.2f} km²")
        
        if result.category_counts:
            print("\nPOIs by category:")
            for category, count in sorted(result.category_counts.items()):
                print(f"  • {category}: {count}")
        
    except Exception as e:
        print(f"Error: {e}")


def compare_old_vs_new():
    """Show side-by-side comparison of old vs new API."""
    
    print("\n" + "="*60)
    print("API COMPARISON: Old vs New")
    print("="*60)
    
    print("\n📛 OLD COMPLEX API:")
    print("-" * 30)
    print("""
with SocialMapperClient() as client:
    result = client.analyze(
        location="San Francisco, CA",
        poi_type="amenity", 
        poi_name="library",
        travel_time=15
    )
    
    match result:
        case Ok(analysis):
            print(f"Found {analysis.poi_count} libraries")
            data = analysis.to_dict()
        case Err(error):
            print(f"Error: {error}")
    """)
    
    print("\n✅ NEW SIMPLE API:")
    print("-" * 30)
    print("""
mapper = SocialMapper()
result = mapper.analyze_location(
    "San Francisco, CA",
    poi_types=["library"],
    travel_time=15
)
print(f"Found {result.poi_count} libraries")
    """)
    
    print("\n📊 IMPROVEMENTS:")
    print("• 70% fewer lines of code")
    print("• No context managers required")
    print("• No Result type unwrapping")
    print("• Standard Python exceptions") 
    print("• Direct data access")
    print("• Cleaner, more readable code")


if __name__ == "__main__":
    main()
    compare_old_vs_new()