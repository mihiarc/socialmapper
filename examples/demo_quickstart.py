#!/usr/bin/env python
"""
SocialMapper Demo Quick Start Example.

This example demonstrates how to use SocialMapper's demo module
for immediate exploration without requiring API keys.

Perfect for:
- First-time users exploring the library
- Workshops and tutorials
- Quick prototyping and testing
- Understanding SocialMapper's capabilities
"""

from socialmapper import demo


def main():
    """Run demo examples showcasing SocialMapper capabilities."""
    print("\n" + "=" * 70)
    print("SOCIALMAPPER DEMO - QUICK START")
    print("=" * 70)
    print("\nExploring accessibility analysis without API keys!")
    print()

    # Show available demos
    print("First, let's see what demo locations are available:\n")
    demo.list_available_demos()

    # Example 1: Quick start analysis
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Complete Accessibility Analysis")
    print("=" * 70)
    print("\nAnalyzing library accessibility in Portland, OR...")
    result = demo.quick_start("Portland, OR")

    # Access the data
    print(f"\nResults summary:")
    print(f"  - Found {result['poi_count']} libraries")
    print(f"  - Serving {result['total_population']:,} people")
    print(f"  - Coverage area: {result['area_sq_km']:.1f} km²")
    print(f"  - Median income: ${result['median_income']:,}")

    # Example 2: Library-focused analysis
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Library Accessibility Analysis")
    print("=" * 70)
    print("\nComparing library access across three cities...")

    for city in ["Portland, OR", "Chapel Hill, NC", "Durham, NC"]:
        result = demo.show_libraries(city)
        ratio = result["people_per_library"]
        print(f"\n{city}:")
        print(f"  - {result['library_count']} libraries")
        print(f"  - {result['population_served']:,} people served")
        print(f"  - {ratio:,} people per library")

    # Example 3: Food access analysis
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Food Access Analysis")
    print("=" * 70)
    print("\nAnalyzing food accessibility in Durham, NC...")
    result = demo.show_food_access("Durham, NC")

    print(f"\nFood access summary:")
    print(f"  - {result['grocery_count']} grocery stores")
    print(f"  - {result['restaurant_count']} restaurants")
    print(f"  - Serving {result['population_served']:,} people")

    # Show sample POIs
    print(f"\nSample restaurants:")
    restaurants = [
        poi for poi in result["food_pois"]
        if poi.get("category") == "restaurant"
    ]
    for restaurant in restaurants[:3]:
        print(f"  - {restaurant['name']} ({restaurant['distance_km']:.1f} km)")

    # Next steps
    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("\n1. Explore the demo data structure:")
    print("   result['pois'] - List of discovered POIs")
    print("   result['census_blocks'] - Census block group data")
    print("   result['isochrone'] - Travel-time polygon geometry")

    print("\n2. Ready for live data? Set up your Census API key:")
    print("   - Get free key: https://api.census.gov/data/key_signup.html")
    print("   - Set CENSUS_API_KEY environment variable")
    print("   - Use main API functions with any location")

    print("\n3. Example with live data:")
    print("   from socialmapper import create_isochrone, get_census_data")
    print('   iso = create_isochrone("Your City, State", travel_time=20)')
    print('   census = get_census_data(location=iso, variables=["population", "median_income"])')

    print("\n" + "=" * 70)
    print("Demo complete! Time to value: < 2 minutes ⚡")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
