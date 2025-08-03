#!/usr/bin/env python3
"""Example demonstrating POI discovery using the SocialMapperBuilder.

This example shows how to use the new POI discovery methods in the
SocialMapperBuilder to configure nearby POI analysis around a location.
"""

from socialmapper.api.builder import SocialMapperBuilder
from socialmapper.isochrone import TravelMode


def main():
    """Demonstrate POI discovery builder functionality."""
    print("=== SocialMapper POI Discovery Builder Example ===\n")

    # 1. Basic POI discovery configuration
    print("1. Basic POI Discovery Configuration:")
    basic_builder = (
        SocialMapperBuilder()
        .with_nearby_poi_discovery("San Francisco, CA", 15, TravelMode.WALK)
    )

    print("   Location: San Francisco, CA")
    print("   Travel time: 15 minutes")
    print("   Travel mode: Walking")
    print(f"   Validation errors: {len(basic_builder.validate())}")
    print()

    # 2. POI discovery with specific categories
    print("2. POI Discovery with Category Filtering:")
    category_builder = (
        SocialMapperBuilder()
        .with_nearby_poi_discovery("Boston, MA", 20, "bike")
        .with_poi_categories("food_and_drink", "healthcare", "education")
        .limit_pois_per_category(25)
    )

    print("   Location: Boston, MA")
    print("   Travel time: 20 minutes")
    print("   Travel mode: Biking")
    print("   Categories: food_and_drink, healthcare, education")
    print("   Max POIs per category: 25")
    print(f"   Validation errors: {len(category_builder.validate())}")
    print()

    # 3. POI discovery with coordinate location and exclusions
    print("3. POI Discovery with Coordinates and Exclusions:")
    coords_builder = (
        SocialMapperBuilder()
        .with_nearby_poi_discovery((37.7749, -122.4194), 30, TravelMode.DRIVE)  # SF coords
        .exclude_poi_categories("utilities", "services")
        .with_exports(csv=True, maps=True)
        .with_output_directory("/tmp/poi_discovery_output")
    )

    print("   Location: (37.7749, -122.4194) - San Francisco coordinates")
    print("   Travel time: 30 minutes")
    print("   Travel mode: Driving")
    print("   Excluded categories: utilities, services")
    print("   Exports: CSV and maps enabled")
    print(f"   Validation errors: {len(coords_builder.validate())}")
    print()

    # 4. Combined analysis: OSM + POI discovery
    print("4. Combined OSM and POI Discovery Analysis:")
    combined_builder = (
        SocialMapperBuilder()
        .with_location("Seattle, WA")
        .with_osm_pois("amenity", "hospital")
        .with_nearby_poi_discovery("Seattle, WA", 15)
        .with_poi_categories("healthcare", "education")
        .with_census_variables("total_population", "median_income")
    )

    print("   OSM search: hospitals in Seattle, WA")
    print("   POI discovery: healthcare & education within 15 min")
    print("   Census variables: total_population, median_income")
    print(f"   Validation errors: {len(combined_builder.validate())}")
    print()

    # 5. Show available POI categories
    print("5. Available POI Categories:")
    categories_info = SocialMapperBuilder().list_available_poi_categories()
    print(f"   Total categories: {categories_info['total_categories']}")
    print(f"   Categories: {', '.join(categories_info['categories'])}")
    print()

    # 6. Build and inspect configuration
    print("6. Building Configuration Object:")
    try:
        config = category_builder.build()
        print("   Build successful!")
        print(f"   POI discovery enabled: {config.get('poi_discovery_enabled')}")

        if "poi_discovery_config" in config:
            poi_config = config["poi_discovery_config"]
            print(f"   POI config type: {type(poi_config).__name__}")
            print(f"   Location: {poi_config.location}")
            print(f"   Travel time: {poi_config.travel_time} minutes")
            print(f"   Travel mode: {poi_config.travel_mode}")
            print(f"   POI categories: {poi_config.poi_categories}")
            print(f"   Max POIs per category: {poi_config.max_pois_per_category}")

    except Exception as e:
        print(f"   Build failed: {e}")
    print()

    # 7. Error handling examples
    print("7. Error Handling Examples:")

    # Invalid travel time
    error_builder1 = (
        SocialMapperBuilder()
        .with_nearby_poi_discovery("Chicago, IL", 150)  # Too high
    )
    errors1 = error_builder1.validate()
    print(f"   Invalid travel time errors: {len(errors1)}")
    if errors1:
        print(f"   Error: {errors1[0]}")

    # Invalid coordinates
    error_builder2 = (
        SocialMapperBuilder()
        .with_nearby_poi_discovery((200.0, -300.0), 15)  # Invalid coords
    )
    errors2 = error_builder2.validate()
    print(f"   Invalid coordinates errors: {len(errors2)}")
    if errors2:
        print(f"   Error: {errors2[0]}")

    # Conflicting categories
    error_builder3 = (
        SocialMapperBuilder()
        .with_nearby_poi_discovery("Portland, OR", 15)
        .with_poi_categories("food_and_drink", "healthcare")
        .exclude_poi_categories("healthcare", "utilities")  # Conflict
    )
    errors3 = error_builder3.validate()
    print(f"   Conflicting categories errors: {len(errors3)}")
    if errors3:
        print(f"   Error: {errors3[0]}")

    print("\n=== Example Complete ===")


if __name__ == "__main__":
    main()
