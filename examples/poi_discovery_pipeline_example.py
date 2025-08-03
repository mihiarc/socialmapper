#!/usr/bin/env python3
"""Example demonstrating the nearby POI discovery pipeline.

This example shows how to use the complete POI discovery pipeline to find
Points of Interest near a location within a specified travel time.
"""

from pathlib import Path

from socialmapper.api.result_types import NearbyPOIDiscoveryConfig
from socialmapper.isochrone.travel_modes import TravelMode
from socialmapper.pipeline import (
    discover_pois_near_address,
    discover_pois_near_coordinates,
    execute_poi_discovery_pipeline,
)


def basic_poi_discovery_example():
    """Basic example using the main pipeline function."""
    print("=== Basic POI Discovery Example ===\n")

    # Create configuration
    config = NearbyPOIDiscoveryConfig(
        location="Chapel Hill, NC",
        travel_time=15,  # 15 minutes
        travel_mode=TravelMode.DRIVE,
        poi_categories=["food_and_drink", "shopping", "entertainment"],
        export_csv=True,
        export_geojson=True,
        create_map=True,
        output_dir=Path("output/poi_discovery_chapel_hill"),
        max_pois_per_category=20,
        include_poi_details=True,
    )

    # Execute pipeline
    result = execute_poi_discovery_pipeline(config)

    match result:
        case result if result.is_ok():
            poi_result = result.unwrap()
            print(f"✅ Success! Found {poi_result.total_poi_count} POIs")
            print(f"📍 Origin: {poi_result.origin_location}")
            print(f"🕒 Travel time: {poi_result.travel_time} minutes ({poi_result.travel_mode.value})")
            print(f"📐 Isochrone area: {poi_result.isochrone_area_km2:.2f} km²")
            print("\n📊 POIs by category:")
            for category, count in poi_result.category_counts.items():
                print(f"  {category}: {count}")

            # Show closest POIs
            print("\n🏆 Top 5 closest POIs:")
            closest_pois = poi_result.get_pois_by_distance()[:5]
            for i, poi in enumerate(closest_pois, 1):
                distance_km = poi.straight_line_distance_m / 1000
                print(f"  {i}. {poi.name} ({poi.category}) - {distance_km:.1f} km")

            # Show summary statistics
            stats = poi_result.get_summary_stats()
            print("\n📈 Summary:")
            print(f"  Average distance: {stats['avg_distance_m']:.0f} m")
            print(f"  Distance range: {stats['min_distance_m']:.0f} - {stats['max_distance_m']:.0f} m")

            # Show generated files
            if poi_result.files_generated:
                print("\n📄 Generated files:")
                for file_type, path in poi_result.files_generated.items():
                    print(f"  {file_type}: {path}")

        case result if result.is_err():
            error = result.unwrap_err()
            print(f"❌ Error: {error.message}")
            if error.context:
                print(f"   Context: {error.context}")


def convenience_functions_example():
    """Example using convenience functions."""
    print("\n=== Convenience Functions Example ===\n")

    # Example 1: POI discovery near an address
    print("Example 1: Finding restaurants near Duke University")
    result = discover_pois_near_address(
        address="Duke University, Durham, NC",
        travel_time=10,
        travel_mode=TravelMode.WALK,
        categories=["food_and_drink"],
        output_dir=Path("output/duke_restaurants"),
    )

    if result.is_ok():
        poi_result = result.unwrap()
        print(f"✅ Found {poi_result.total_poi_count} restaurants within 10-minute walk")
        for poi in poi_result.get_pois_by_distance()[:3]:
            distance_km = poi.straight_line_distance_m / 1000
            print(f"  • {poi.name} - {distance_km:.1f} km")
    else:
        print(f"❌ Error: {result.unwrap_err().message}")

    # Example 2: POI discovery near coordinates
    print("\nExample 2: Finding shops near specific coordinates")
    result = discover_pois_near_coordinates(
        latitude=35.9940,  # Durham, NC
        longitude=-78.8986,
        travel_time=20,
        travel_mode=TravelMode.BIKE,
        categories=["shopping"],
        output_dir=Path("output/durham_shops"),
    )

    if result.is_ok():
        poi_result = result.unwrap()
        print(f"✅ Found {poi_result.total_poi_count} shops within 20-minute bike ride")
        for poi in poi_result.get_pois_by_distance()[:3]:
            distance_km = poi.straight_line_distance_m / 1000
            print(f"  • {poi.name} - {distance_km:.1f} km")
    else:
        print(f"❌ Error: {result.unwrap_err().message}")


def advanced_filtering_example():
    """Example with advanced filtering options."""
    print("\n=== Advanced Filtering Example ===\n")

    config = NearbyPOIDiscoveryConfig(
        location="Carrboro, NC",
        travel_time=30,
        travel_mode=TravelMode.DRIVE,
        poi_categories=["food_and_drink", "shopping", "health"],
        exclude_categories=["transportation"],  # Exclude gas stations, etc.
        max_pois_per_category=5,  # Limit to top 5 closest in each category
        include_poi_details=True,  # Include contact info, hours, etc.
        export_csv=True,
        create_map=False,  # Skip map creation for this example
        output_dir=Path("output/carrboro_filtered"),
    )

    result = execute_poi_discovery_pipeline(config)

    if result.is_ok():
        poi_result = result.unwrap()
        print(f"✅ Found {poi_result.total_poi_count} POIs with filtering")

        # Show POIs with details
        print("\n📋 POIs with details:")
        for category, pois in poi_result.pois_by_category.items():
            print(f"\n  {category.upper()}:")
            for poi in pois[:2]:  # Show first 2 in each category
                print(f"    • {poi.name}")
                if poi.address:
                    print(f"      Address: {poi.address}")
                if poi.phone:
                    print(f"      Phone: {poi.phone}")
                if poi.website:
                    print(f"      Website: {poi.website}")
                if poi.opening_hours:
                    print(f"      Hours: {poi.opening_hours}")
                distance_km = poi.straight_line_distance_m / 1000
                print(f"      Distance: {distance_km:.1f} km")
    else:
        print(f"❌ Error: {result.unwrap_err().message}")


def error_handling_example():
    """Example demonstrating error handling."""
    print("\n=== Error Handling Example ===\n")

    # Example with invalid location
    config = NearbyPOIDiscoveryConfig(
        location="Nonexistent Place, XX",
        travel_time=15,
        travel_mode=TravelMode.WALK,
        output_dir=Path("output/error_test"),
    )

    result = execute_poi_discovery_pipeline(config)

    if result.is_err():
        error = result.unwrap_err()
        print("Expected error for invalid location:")
        print(f"  Type: {error.type}")
        print(f"  Message: {error.message}")
        if error.context:
            print(f"  Context: {error.context}")
    else:
        print("Unexpected success with invalid location")


if __name__ == "__main__":
    print("POI Discovery Pipeline Examples")
    print("=" * 50)

    try:
        basic_poi_discovery_example()
        convenience_functions_example()
        advanced_filtering_example()
        error_handling_example()

        print("\n✅ All examples completed!")
        print("Check the 'output/' directory for generated files.")

    except Exception as e:
        print(f"\n❌ Example failed with error: {e}")
        print("This might be due to missing dependencies or network issues.")
        print("Make sure you have an internet connection for geocoding and POI queries.")
