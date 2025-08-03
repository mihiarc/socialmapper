"""Test script for the metadata endpoints (census variables, POI types, location search).
"""

import asyncio

import httpx

BASE_URL = "http://localhost:8000/api/v1"


async def test_metadata_endpoints():
    """Test the metadata endpoints."""
    async with httpx.AsyncClient() as client:
        print("Testing Metadata Endpoints")
        print("=" * 50)

        # Test census variables endpoint
        print("\n1. Testing GET /census/variables...")
        census_response = await client.get(f"{BASE_URL}/census/variables")

        if census_response.status_code == 200:
            census_data = census_response.json()
            print("✓ Successfully retrieved census variables")
            print(f"   - Total variables: {census_data.get('total_count', 0)}")
            print(f"   - Categories: {', '.join(census_data.get('categories', []))}")
            print(f"   - First variable: {census_data['variables'][0]['code']} - {census_data['variables'][0]['name']}")
        else:
            print(f"✗ Failed to get census variables: {census_response.status_code}")
            print(census_response.text)

        # Test census variables with filtering
        print("\n2. Testing census variables with group filter...")
        filtered_response = await client.get(
            f"{BASE_URL}/census/variables",
            params={"group": "Demographics"}
        )

        if filtered_response.status_code == 200:
            filtered_data = filtered_response.json()
            print("✓ Successfully filtered census variables")
            print(f"   - Demographics variables: {filtered_data.get('total_count', 0)}")
        else:
            print(f"✗ Failed to filter census variables: {filtered_response.status_code}")

        # Test census variables with search
        print("\n3. Testing census variables with search...")
        search_response = await client.get(
            f"{BASE_URL}/census/variables",
            params={"search": "income"}
        )

        if search_response.status_code == 200:
            search_data = search_response.json()
            print("✓ Successfully searched census variables")
            print(f"   - Results for 'income': {search_data.get('total_count', 0)}")
        else:
            print(f"✗ Failed to search census variables: {search_response.status_code}")

        # Test POI types endpoint
        print("\n4. Testing GET /poi/types...")
        poi_response = await client.get(f"{BASE_URL}/poi/types")

        if poi_response.status_code == 200:
            poi_data = poi_response.json()
            print("✓ Successfully retrieved POI types")
            print(f"   - Total POI types: {poi_data.get('total_count', 0)}")
            print(f"   - Categories: {', '.join(poi_data.get('categories', []))}")
            if poi_data['poi_types']:
                first_poi = poi_data['poi_types'][0]
                print(f"   - First POI: {first_poi['type']}:{first_poi['name']} - {first_poi.get('description', 'N/A')}")
        else:
            print(f"✗ Failed to get POI types: {poi_response.status_code}")
            print(poi_response.text)

        # Test POI types with category filter
        print("\n5. Testing POI types with category filter...")
        category_response = await client.get(
            f"{BASE_URL}/poi/types",
            params={"category": "Healthcare"}
        )

        if category_response.status_code == 200:
            category_data = category_response.json()
            print("✓ Successfully filtered POI types")
            print(f"   - Healthcare POIs: {category_data.get('total_count', 0)}")
            if category_data['poi_types']:
                for poi in category_data['poi_types']:
                    print(f"     • {poi['type']}:{poi['name']}")
        else:
            print(f"✗ Failed to filter POI types: {category_response.status_code}")

        # Test POI types with search
        print("\n6. Testing POI types with search...")
        poi_search_response = await client.get(
            f"{BASE_URL}/poi/types",
            params={"search": "library"}
        )

        if poi_search_response.status_code == 200:
            poi_search_data = poi_search_response.json()
            print("✓ Successfully searched POI types")
            print(f"   - Results for 'library': {poi_search_data.get('total_count', 0)}")
        else:
            print(f"✗ Failed to search POI types: {poi_search_response.status_code}")

        # Test location search endpoint
        print("\n7. Testing GET /geography/search...")
        location_response = await client.get(
            f"{BASE_URL}/geography/search",
            params={"q": "Portland"}
        )

        if location_response.status_code == 200:
            location_data = location_response.json()
            print("✓ Successfully searched locations")
            print(f"   - Query: {location_data.get('query')}")
            print(f"   - Results: {location_data.get('total_count', 0)}")
            if location_data['results']:
                for result in location_data['results']:
                    print(f"     • {result['display_name']} ({result['latitude']}, {result['longitude']})")
        else:
            print(f"✗ Failed to search locations: {location_response.status_code}")
            print(location_response.text)

        # Test location search with different queries
        print("\n8. Testing location search with different queries...")
        test_queries = ["Chicago", "Durham", "New York"]

        for query in test_queries:
            query_response = await client.get(
                f"{BASE_URL}/geography/search",
                params={"q": query, "limit": 5}
            )

            if query_response.status_code == 200:
                query_data = query_response.json()
                print(f"✓ Search for '{query}': {query_data.get('total_count', 0)} results")
            else:
                print(f"✗ Failed to search for '{query}': {query_response.status_code}")

        # Test pagination
        print("\n9. Testing pagination...")
        page_response = await client.get(
            f"{BASE_URL}/census/variables",
            params={"limit": 3, "offset": 2}
        )

        if page_response.status_code == 200:
            page_data = page_response.json()
            print("✓ Successfully tested pagination")
            print(f"   - Retrieved {len(page_data['variables'])} variables (limit: 3, offset: 2)")
        else:
            print(f"✗ Failed pagination test: {page_response.status_code}")

        print("\n" + "=" * 50)
        print("Metadata endpoints test completed!")


if __name__ == "__main__":
    asyncio.run(test_metadata_endpoints())
