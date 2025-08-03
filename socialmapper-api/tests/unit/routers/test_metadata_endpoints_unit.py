"""Unit tests for metadata endpoints (census variables, POI types, location search).
"""

from api_server.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_census_variables_endpoint():
    """Test the census variables endpoint."""
    response = client.get("/api/v1/census/variables")
    assert response.status_code == 200

    data = response.json()
    assert "variables" in data
    assert "total_count" in data
    assert "categories" in data

    # Check that we have variables
    assert len(data["variables"]) > 0
    assert data["total_count"] > 0

    # Validate first variable structure
    first_var = data["variables"][0]
    assert "code" in first_var
    assert "name" in first_var
    assert "concept" in first_var

    print(f"✓ Census variables endpoint works - {data['total_count']} variables available")


def test_census_variables_filtering():
    """Test census variables filtering by group."""
    response = client.get("/api/v1/census/variables?group=Demographics")
    assert response.status_code == 200

    data = response.json()
    assert len(data["variables"]) > 0

    # Check all returned variables are in Demographics group
    for var in data["variables"]:
        assert var["group"] == "Demographics"

    print(f"✓ Census variables filtering works - {data['total_count']} Demographics variables")


def test_census_variables_search():
    """Test census variables search functionality."""
    response = client.get("/api/v1/census/variables?search=income")
    assert response.status_code == 200

    data = response.json()
    assert len(data["variables"]) > 0

    # Check that at least one result contains "income"
    found_income = False
    for var in data["variables"]:
        if "income" in var["name"].lower() or "income" in var["concept"].lower():
            found_income = True
            break
    assert found_income

    print(f"✓ Census variables search works - {data['total_count']} results for 'income'")


def test_poi_types_endpoint():
    """Test the POI types endpoint."""
    response = client.get("/api/v1/poi/types")
    assert response.status_code == 200

    data = response.json()
    assert "poi_types" in data
    assert "total_count" in data
    assert "categories" in data

    # Check that we have POI types
    assert len(data["poi_types"]) > 0
    assert data["total_count"] > 0

    # Validate first POI type structure
    first_poi = data["poi_types"][0]
    assert "type" in first_poi
    assert "name" in first_poi
    assert "category" in first_poi

    print(f"✓ POI types endpoint works - {data['total_count']} POI types available")


def test_poi_types_filtering():
    """Test POI types filtering by category."""
    response = client.get("/api/v1/poi/types?category=Healthcare")
    assert response.status_code == 200

    data = response.json()
    assert len(data["poi_types"]) > 0

    # Check all returned POIs are in Healthcare category
    for poi in data["poi_types"]:
        assert poi["category"] == "Healthcare"

    print(f"✓ POI types filtering works - {data['total_count']} Healthcare POIs")


def test_poi_types_search():
    """Test POI types search functionality."""
    response = client.get("/api/v1/poi/types?search=library")
    assert response.status_code == 200

    data = response.json()
    assert len(data["poi_types"]) > 0

    # Check that library is in the results
    found_library = False
    for poi in data["poi_types"]:
        if poi["name"] == "library":
            found_library = True
            break
    assert found_library

    print("✓ POI types search works - found library in results")


def test_location_search_endpoint():
    """Test the location search endpoint."""
    response = client.get("/api/v1/geography/search?q=Portland")
    assert response.status_code == 200

    data = response.json()
    assert "query" in data
    assert "results" in data
    assert "total_count" in data

    assert data["query"] == "Portland"
    assert len(data["results"]) > 0

    # Check first result structure
    first_result = data["results"][0]
    assert "display_name" in first_result
    assert "latitude" in first_result
    assert "longitude" in first_result
    assert "city" in first_result
    assert "state" in first_result
    assert "country" in first_result

    print(f"✓ Location search works - {data['total_count']} results for 'Portland'")


def test_location_search_multiple_queries():
    """Test location search with different queries."""
    test_queries = ["Chicago", "Durham", "Random City"]

    for query in test_queries:
        response = client.get(f"/api/v1/geography/search?q={query}")
        assert response.status_code == 200

        data = response.json()
        assert data["query"] == query
        assert len(data["results"]) > 0

        print(f"✓ Location search for '{query}' - {data['total_count']} results")


def test_pagination():
    """Test pagination on census variables endpoint."""
    # Get first page
    response1 = client.get("/api/v1/census/variables?limit=3&offset=0")
    assert response1.status_code == 200
    data1 = response1.json()

    # Get second page
    response2 = client.get("/api/v1/census/variables?limit=3&offset=3")
    assert response2.status_code == 200
    data2 = response2.json()

    # Check that results are different
    assert len(data1["variables"]) == 3
    assert len(data2["variables"]) <= 3
    assert data1["variables"][0]["code"] != data2["variables"][0]["code"]

    print("✓ Pagination works correctly")


def test_validation_errors():
    """Test validation errors on endpoints."""
    # Test location search without query
    response = client.get("/api/v1/geography/search")
    assert response.status_code == 422

    # Test with invalid limit
    response = client.get("/api/v1/census/variables?limit=0")
    assert response.status_code == 422

    # Test with negative offset
    response = client.get("/api/v1/census/variables?offset=-1")
    assert response.status_code == 422

    print("✓ Validation errors work correctly")


if __name__ == "__main__":
    print("Testing Metadata Endpoints (Unit Tests)")
    print("=" * 50)

    test_census_variables_endpoint()
    test_census_variables_filtering()
    test_census_variables_search()
    print()

    test_poi_types_endpoint()
    test_poi_types_filtering()
    test_poi_types_search()
    print()

    test_location_search_endpoint()
    test_location_search_multiple_queries()
    print()

    test_pagination()
    test_validation_errors()

    print("\nAll metadata endpoint tests passed!")
