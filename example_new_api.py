"""Example demonstrating the new simplified SocialMapper API.

The API now consists of just 5 simple, direct functions:
1. create_isochrone - Generate travel-time polygons
2. get_census_blocks - Fetch census block groups
3. get_census_data - Get demographic data
4. create_map - Create choropleth visualizations
5. get_poi - Find points of interest
"""

from socialmapper import (
    create_isochrone,
    get_census_blocks, 
    get_census_data,
    create_map,
    get_poi
)


def example_isochrone():
    """Example: Create a 15-minute drive-time polygon."""
    print("\n=== Isochrone Example ===")
    
    # Create isochrone for downtown Seattle
    iso = create_isochrone("Seattle, WA", travel_time=15, travel_mode="drive")
    
    print(f"Created isochrone for: {iso['properties']['location']}")
    print(f"Travel time: {iso['properties']['travel_time']} minutes")
    print(f"Travel mode: {iso['properties']['travel_mode']}")
    print(f"Area covered: {iso['properties']['area_sq_km']:.1f} sq km")
    
    return iso


def example_poi_search():
    """Example: Find restaurants and cafes near a location."""
    print("\n=== POI Search Example ===")
    
    # Find food places in Portland
    pois = get_poi(
        location="Portland, OR",
        categories=["restaurant", "cafe", "bar"],
        limit=10
    )
    
    print(f"Found {len(pois)} POIs:")
    for poi in pois[:5]:  # Show first 5
        print(f"  • {poi['name']} ({poi['category']}) - {poi['distance_km']:.2f} km away")
    
    return pois


def example_poi_with_travel_time():
    """Example: Find POIs within a travel-time boundary."""
    print("\n=== POI within Travel Time Example ===")
    
    # Find all parks within 10-minute walk
    pois = get_poi(
        location=(37.7749, -122.4194),  # San Francisco coordinates
        categories=["park", "playground"],
        travel_time=10,  # Creates 10-minute drive boundary
        limit=20
    )
    
    print(f"Found {len(pois)} parks within 10-minute drive:")
    for poi in pois[:5]:
        print(f"  • {poi['name']} - {poi['distance_km']:.2f} km")
    
    return pois


def example_census_blocks():
    """Example: Get census blocks for an area."""
    print("\n=== Census Blocks Example ===")
    
    # Get blocks within 2km of a point
    blocks = get_census_blocks(
        location=(40.7128, -74.0060),  # New York City
        radius_km=2
    )
    
    print(f"Found {len(blocks)} census block groups")
    for block in blocks[:3]:  # Show first 3
        print(f"  • Block {block['geoid']} - {block['area_sq_km']:.2f} sq km")
    
    return blocks


def example_census_data():
    """Example: Get demographic data for locations."""
    print("\n=== Census Data Example ===")
    
    # Get data for a specific point
    data = get_census_data(
        location=(39.7392, -104.9903),  # Denver, CO
        variables=["population", "median_income", "median_age"]
    )
    
    print("Census data for location:")
    for var, value in data.items():
        if value is not None:
            print(f"  • {var}: {value:,.0f}" if isinstance(value, (int, float)) else f"  • {var}: {value}")
    
    return data


def example_census_with_isochrone():
    """Example: Get census data for an isochrone area."""
    print("\n=== Census Data for Isochrone Example ===")
    
    # Create isochrone
    iso = create_isochrone("Boston, MA", travel_time=10)
    
    # Get census data for the isochrone area
    data = get_census_data(
        location=iso,
        variables=["population", "median_income"]
    )
    
    # Calculate totals
    total_pop = sum(d.get("population", 0) for d in data.values() if d.get("population"))
    avg_income = sum(d.get("median_income", 0) for d in data.values() if d.get("median_income")) / len(data)
    
    print(f"Within 10-minute drive of Boston:")
    print(f"  • Total population: {total_pop:,.0f}")
    print(f"  • Average median income: ${avg_income:,.0f}")
    print(f"  • Number of block groups: {len(data)}")
    
    return data


def example_create_map():
    """Example: Create a choropleth map."""
    print("\n=== Map Creation Example ===")
    
    # Get census blocks
    blocks = get_census_blocks(
        location=(37.7749, -122.4194),  # San Francisco
        radius_km=3
    )
    
    # Get population data
    geoids = [b["geoid"] for b in blocks]
    census_data = get_census_data(geoids, ["population"])
    
    # Add population to blocks
    for block in blocks:
        block["population"] = census_data.get(block["geoid"], {}).get("population", 0)
    
    # Create map (saves to file)
    create_map(
        data=blocks,
        column="population",
        title="Population by Census Block Group",
        save_path="population_map.png"
    )
    
    print("Map saved to population_map.png")
    print(f"Visualized {len(blocks)} block groups")
    
    return blocks


def main():
    """Run all examples."""
    print("=" * 60)
    print("SocialMapper v2.0 - Simplified API Examples")
    print("=" * 60)
    
    # Run examples
    example_isochrone()
    example_poi_search()
    example_poi_with_travel_time()
    example_census_blocks()
    example_census_data()
    
    # Note: Commenting out examples that might fail without API keys
    # example_census_with_isochrone()
    # example_create_map()
    
    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()