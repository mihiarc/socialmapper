#!/usr/bin/env python3
"""Integration tests for POI categorization with query module."""


from socialmapper.poi_categorization import categorize_poi, organize_pois_by_category


class TestPOICategorationIntegration:
    """Test POI categorization integration with actual OSM query data format."""

    def test_categorize_actual_osm_poi_format(self):
        """Test categorization with actual POI format from query module."""
        # Sample POI data matching the format from format_results() in query module
        poi = {
            "id": 123456789,
            "type": "node",
            "lat": 35.9132,
            "lon": -79.0558,
            "tags": {
                "amenity": "restaurant",
                "cuisine": "italian",
                "name": "Bella Italia",
                "opening_hours": "Mo-Su 11:00-22:00",
                "phone": "+1-919-555-0123"
            },
            "state": "NC"
        }

        # Extract tags and categorize
        category = categorize_poi(poi["tags"])
        assert category == "food_and_drink"

    def test_organize_query_results(self):
        """Test organizing POIs from a simulated query result."""
        # Simulate output from query_pois() function
        query_result = {
            "poi_count": 6,
            "pois": [
                {
                    "id": 1001,
                    "type": "node",
                    "lat": 35.9110,
                    "lon": -79.0560,
                    "tags": {"amenity": "restaurant", "name": "The Corner Bistro"},
                    "state": "NC"
                },
                {
                    "id": 1002,
                    "type": "way",
                    "lat": 35.9120,
                    "lon": -79.0570,
                    "tags": {"shop": "supermarket", "name": "Harris Teeter"},
                    "state": "NC"
                },
                {
                    "id": 1003,
                    "type": "node",
                    "lat": 35.9130,
                    "lon": -79.0580,
                    "tags": {"leisure": "park", "name": "Battle Park"},
                    "state": "NC"
                },
                {
                    "id": 1004,
                    "type": "relation",
                    "lat": 35.9140,
                    "lon": -79.0590,
                    "tags": {"amenity": "university", "name": "UNC Chapel Hill"},
                    "state": "NC"
                },
                {
                    "id": 1005,
                    "type": "node",
                    "lat": 35.9150,
                    "lon": -79.0600,
                    "tags": {"healthcare": "hospital", "name": "UNC Hospital"},
                    "state": "NC"
                },
                {
                    "id": 1006,
                    "type": "node",
                    "lat": 35.9160,
                    "lon": -79.0610,
                    "tags": {"building": "yes", "name": "Random Building"},
                    "state": "NC"
                }
            ]
        }

        # Organize POIs by category
        categorized = organize_pois_by_category(query_result["pois"])

        # Verify categories
        assert "food_and_drink" in categorized
        assert "shopping" in categorized
        assert "recreation" in categorized
        assert "education" in categorized
        assert "healthcare" in categorized
        assert "other" in categorized

        # Verify counts
        assert len(categorized["food_and_drink"]) == 1
        assert len(categorized["shopping"]) == 1
        assert len(categorized["recreation"]) == 1
        assert len(categorized["education"]) == 1
        assert len(categorized["healthcare"]) == 1
        assert len(categorized["other"]) == 1

        # Verify specific POIs retained their data
        restaurant = categorized["food_and_drink"][0]
        assert restaurant["id"] == 1001
        assert restaurant["state"] == "NC"
        assert restaurant["tags"]["name"] == "The Corner Bistro"

    def test_categorize_complex_osm_tags(self):
        """Test categorization with complex OSM tag combinations."""
        # Test cases with multiple potential categorization tags
        test_cases = [
            # Restaurant with building tag
            {
                "tags": {
                    "amenity": "restaurant",
                    "building": "commercial",
                    "cuisine": "chinese",
                    "takeaway": "yes"
                },
                "expected": "food_and_drink"
            },
            # Pharmacy inside a shop
            {
                "tags": {
                    "shop": "chemist",
                    "amenity": "pharmacy",
                    "dispensing": "yes"
                },
                "expected": "healthcare"  # amenity comes before shop in priority
            },
            # Hotel with restaurant
            {
                "tags": {
                    "tourism": "hotel",
                    "amenity": "restaurant",
                    "stars": "3"
                },
                "expected": "food_and_drink"  # amenity has higher priority
            },
            # Sports complex
            {
                "tags": {
                    "leisure": "sports_centre",
                    "sport": "multi",
                    "building": "yes"
                },
                "expected": "recreation"
            },
            # Government office
            {
                "tags": {
                    "office": "government",
                    "government": "ministry",
                    "name": "Ministry of Transportation"
                },
                "expected": "services"
            }
        ]

        for test_case in test_cases:
            category = categorize_poi(test_case["tags"])
            assert category == test_case["expected"], \
                f"Expected {test_case['expected']} for tags {test_case['tags']}, got {category}"

    def test_handle_different_osm_element_types(self):
        """Test that categorization works for all OSM element types."""
        # Node
        node_poi = {
            "id": 1,
            "type": "node",
            "lat": 35.9,
            "lon": -79.0,
            "tags": {"amenity": "cafe"}
        }
        assert categorize_poi(node_poi["tags"]) == "food_and_drink"

        # Way
        way_poi = {
            "id": 2,
            "type": "way",
            "lat": 35.9,
            "lon": -79.0,
            "tags": {"leisure": "park"}
        }
        assert categorize_poi(way_poi["tags"]) == "recreation"

        # Relation
        relation_poi = {
            "id": 3,
            "type": "relation",
            "lat": 35.9,
            "lon": -79.0,
            "tags": {"amenity": "university"}
        }
        assert categorize_poi(relation_poi["tags"]) == "education"

    def test_categorize_with_missing_fields(self):
        """Test categorization robustness with missing or malformed data."""
        # POI without tags field
        poi_no_tags = {"id": 1, "type": "node", "lat": 35.9, "lon": -79.0}
        organized = organize_pois_by_category([poi_no_tags])
        assert "other" in organized
        assert len(organized["other"]) == 1

        # POI with empty tags
        poi_empty_tags = {
            "id": 2,
            "type": "node",
            "lat": 35.9,
            "lon": -79.0,
            "tags": {}
        }
        assert categorize_poi(poi_empty_tags["tags"]) == "other"

        # POI with None tags
        poi_none_tags = {
            "id": 3,
            "type": "node",
            "lat": 35.9,
            "lon": -79.0,
            "tags": None
        }
        organized = organize_pois_by_category([poi_none_tags])
        assert "other" in organized
