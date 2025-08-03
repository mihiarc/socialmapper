#!/usr/bin/env python3
"""Example of using polygon-based POI queries with SocialMapper.

This example demonstrates how to query POIs within polygon boundaries,
such as isochrone areas or custom geographic regions.
"""

import json

import geopandas as gpd
from shapely.geometry import Polygon

from socialmapper.console import get_logger
from socialmapper.query import (
    build_poi_discovery_query,
    query_pois_from_isochrone,
    query_pois_in_polygon,
)

logger = get_logger(__name__)


def example_simple_polygon_query():
    """Example: Query POIs in a simple polygon area."""
    print("\n=== Example 1: Simple Polygon Query ===")

    # Create a polygon for a small area in Manhattan
    # Roughly Times Square area
    manhattan_polygon = Polygon([
        (-73.9851, 40.7589),  # Northwest
        (-73.9851, 40.7549),  # Southwest
        (-73.9811, 40.7549),  # Southeast
        (-73.9811, 40.7589),  # Northeast
    ])

    # Query restaurants and cafes in the area
    result = query_pois_in_polygon(
        geometry=manhattan_polygon,
        categories=["food_and_drink"],
        timeout=60  # 60 second timeout
    )

    print(f"Found {result['poi_count']} food and drink POIs")

    # Show first 5 POIs
    for poi in result['pois'][:5]:
        name = poi['tags'].get('name', 'Unnamed')
        poi_type = poi['tags'].get('amenity', poi['tags'].get('shop', 'Unknown'))
        print(f"  - {name} ({poi_type}) at ({poi['lat']}, {poi['lon']})")

    return result


def example_multi_category_query():
    """Example: Query multiple categories of POIs."""
    print("\n=== Example 2: Multi-Category Query ===")

    # Create a polygon for Central Park area
    central_park_polygon = Polygon([
        (-73.9814, 40.7646),  # Southwest
        (-73.9814, 40.8003),  # Northwest
        (-73.9495, 40.8003),  # Northeast
        (-73.9495, 40.7646),  # Southeast
    ])

    # Query multiple categories
    result = query_pois_in_polygon(
        geometry=central_park_polygon,
        categories=["recreation", "food_and_drink", "utilities"],
        timeout=90,
        simplify_tolerance=0.0001  # Simplify polygon slightly
    )

    print(f"Found {result['poi_count']} POIs of various categories")

    # Organize by category
    from socialmapper.poi_categorization import organize_pois_by_category
    categorized = organize_pois_by_category(result['pois'])

    for category, pois in categorized.items():
        print(f"  {category}: {len(pois)} POIs")

    return result


def example_custom_tag_query():
    """Example: Query with custom OSM tags."""
    print("\n=== Example 3: Custom Tag Query ===")

    # Create a polygon for a neighborhood
    neighborhood_polygon = Polygon([
        (-73.9600, 40.7600),
        (-73.9600, 40.7700),
        (-73.9500, 40.7700),
        (-73.9500, 40.7600),
    ])

    # Query Italian restaurants specifically
    result = query_pois_in_polygon(
        geometry=neighborhood_polygon,
        categories=["food_and_drink"],
        additional_tags={"cuisine": "italian"},
        timeout=60
    )

    print(f"Found {result['poi_count']} Italian restaurants")

    for poi in result['pois']:
        name = poi['tags'].get('name', 'Unnamed')
        print(f"  - {name}")

    return result


def example_isochrone_query():
    """Example: Query POIs within an isochrone."""
    print("\n=== Example 4: Isochrone-based Query ===")

    # Create a mock isochrone GeoDataFrame
    # In real usage, this would come from isochrone generation
    isochrone_polygon = Polygon([
        (-73.9900, 40.7500),
        (-73.9900, 40.7600),
        (-73.9800, 40.7650),
        (-73.9700, 40.7600),
        (-73.9700, 40.7500),
        (-73.9800, 40.7450),
    ])

    isochrone_gdf = gpd.GeoDataFrame(
        {
            "travel_time": [15],  # 15-minute isochrone
            "mode": ["walk"]
        },
        geometry=[isochrone_polygon],
        crs="EPSG:4326"
    )

    # Query POIs within the isochrone
    result = query_pois_from_isochrone(
        isochrone_gdf=isochrone_gdf,
        categories=["shopping", "services"],
        simplify_tolerance=0.001
    )

    print(f"Found {result['poi_count']} POIs within 15-minute walk")

    return result


def example_building_custom_query():
    """Example: Build a custom Overpass query."""
    print("\n=== Example 5: Building Custom Query ===")

    polygon = Polygon([
        (-73.9700, 40.7600),
        (-73.9700, 40.7650),
        (-73.9650, 40.7650),
        (-73.9650, 40.7600),
    ])

    # Build query string without executing
    query = build_poi_discovery_query(
        geometry=polygon,
        categories=["healthcare"],
        timeout=120
    )

    print("Generated Overpass Query:")
    print(query[:500] + "..." if len(query) > 500 else query)

    return query


def save_results_to_file(results, filename):
    """Save query results to a JSON file."""
    with open(filename, 'w') as f:
        # Convert any non-serializable objects
        clean_results = {
            "poi_count": results["poi_count"],
            "pois": results["pois"],
            "query_info": {
                k: str(v) if not isinstance(v, (str, int, float, list, dict, type(None))) else v
                for k, v in results["query_info"].items()
            }
        }
        json.dump(clean_results, f, indent=2)
    print(f"\nResults saved to {filename}")


if __name__ == "__main__":
    print("SocialMapper Polygon Query Examples")
    print("===================================")

    # Note: These examples use real Overpass API queries
    # Make sure you have an internet connection

    try:
        # Run examples
        # Uncomment the examples you want to run

        # result1 = example_simple_polygon_query()
        # save_results_to_file(result1, "manhattan_food_pois.json")

        # result2 = example_multi_category_query()
        # save_results_to_file(result2, "central_park_pois.json")

        # result3 = example_custom_tag_query()
        # save_results_to_file(result3, "italian_restaurants.json")

        # result4 = example_isochrone_query()
        # save_results_to_file(result4, "isochrone_pois.json")

        query = example_building_custom_query()

    except Exception as e:
        logger.error(f"Error running examples: {e}")
        raise
