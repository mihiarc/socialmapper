#!/usr/bin/env python3
"""Unit tests for POI categorization module."""


from socialmapper.poi_categorization import (
    POI_CATEGORY_MAPPING,
    add_category_value,
    categorize_poi,
    create_custom_category,
    get_category_values,
    get_poi_category_info,
    is_valid_category,
    organize_pois_by_category,
)


class TestPOICategorization:
    """Test POI categorization functionality."""

    def test_categorize_poi_basic_amenity(self):
        """Test basic amenity categorization."""
        # Food and drink
        assert categorize_poi({"amenity": "restaurant"}) == "food_and_drink"
        assert categorize_poi({"amenity": "cafe"}) == "food_and_drink"
        assert categorize_poi({"amenity": "bar"}) == "food_and_drink"
        assert categorize_poi({"amenity": "fast_food"}) == "food_and_drink"

        # Education
        assert categorize_poi({"amenity": "school"}) == "education"
        assert categorize_poi({"amenity": "university"}) == "education"
        assert categorize_poi({"amenity": "library"}) == "education"

        # Healthcare
        assert categorize_poi({"amenity": "hospital"}) == "healthcare"
        assert categorize_poi({"amenity": "clinic"}) == "healthcare"
        assert categorize_poi({"amenity": "pharmacy"}) == "healthcare"

        # Services
        assert categorize_poi({"amenity": "bank"}) == "services"
        assert categorize_poi({"amenity": "post_office"}) == "services"
        assert categorize_poi({"amenity": "police"}) == "services"

    def test_categorize_poi_shop_tags(self):
        """Test shop tag categorization."""
        # Shopping
        assert categorize_poi({"shop": "supermarket"}) == "shopping"
        assert categorize_poi({"shop": "convenience"}) == "shopping"
        assert categorize_poi({"shop": "clothes"}) == "shopping"
        assert categorize_poi({"shop": "electronics"}) == "shopping"

        # Food shops should be in food_and_drink
        assert categorize_poi({"shop": "bakery"}) == "food_and_drink"
        assert categorize_poi({"shop": "butcher"}) == "food_and_drink"
        assert categorize_poi({"shop": "alcohol"}) == "food_and_drink"

    def test_categorize_poi_leisure_tags(self):
        """Test leisure tag categorization."""
        assert categorize_poi({"leisure": "park"}) == "recreation"
        assert categorize_poi({"leisure": "playground"}) == "recreation"
        assert categorize_poi({"leisure": "sports_centre"}) == "recreation"
        assert categorize_poi({"leisure": "swimming_pool"}) == "recreation"

    def test_categorize_poi_tourism_tags(self):
        """Test tourism tag categorization."""
        assert categorize_poi({"tourism": "hotel"}) == "accommodation"
        assert categorize_poi({"tourism": "hostel"}) == "accommodation"
        assert categorize_poi({"tourism": "museum"}) == "recreation"
        assert categorize_poi({"tourism": "attraction"}) == "recreation"

    def test_categorize_poi_multiple_tags(self):
        """Test POIs with multiple tags (first matching tag wins)."""
        # Amenity takes precedence over shop in our priority order
        poi = {
            "amenity": "restaurant",
            "shop": "supermarket"
        }
        assert categorize_poi(poi) == "food_and_drink"

        # Shop comes before leisure
        poi = {
            "shop": "clothes",
            "leisure": "park"
        }
        assert categorize_poi(poi) == "shopping"

    def test_categorize_poi_case_insensitive(self):
        """Test that categorization is case-insensitive."""
        assert categorize_poi({"amenity": "Restaurant"}) == "food_and_drink"
        assert categorize_poi({"amenity": "RESTAURANT"}) == "food_and_drink"
        assert categorize_poi({"shop": "Supermarket"}) == "shopping"

    def test_categorize_poi_special_cases(self):
        """Test special case categorizations."""
        # Building=church should be religious
        assert categorize_poi({"building": "church"}) == "religious"

        # Place of worship
        assert categorize_poi({"amenity": "place_of_worship"}) == "religious"

    def test_categorize_poi_by_name_fallback(self):
        """Test categorization by name when no matching tags."""
        # Should match "restaurant" in name
        assert categorize_poi({"name": "Joe's Restaurant"}) == "food_and_drink"
        assert categorize_poi({"name": "City Hospital"}) == "healthcare"
        assert categorize_poi({"name": "Central Park"}) == "recreation"

    def test_categorize_poi_edge_cases(self):
        """Test edge cases for categorization."""
        # Empty tags
        assert categorize_poi({}) == "other"

        # None input
        assert categorize_poi(None) == "other"

        # Non-dict input
        assert categorize_poi("not a dict") == "other"

        # Unknown tags
        assert categorize_poi({"unknown_key": "unknown_value"}) == "other"
        assert categorize_poi({"building": "yes"}) == "other"

        # Numeric values
        assert categorize_poi({"amenity": 123}) == "other"

    def test_organize_pois_by_category(self):
        """Test organizing POIs into categories."""
        pois = [
            {"id": 1, "tags": {"amenity": "restaurant"}, "name": "Pizza Place"},
            {"id": 2, "tags": {"shop": "supermarket"}, "name": "Food Mart"},
            {"id": 3, "tags": {"amenity": "hospital"}, "name": "City Hospital"},
            {"id": 4, "tags": {"amenity": "cafe"}, "name": "Coffee Shop"},
            {"id": 5, "tags": {"unknown": "value"}, "name": "Unknown Place"},
        ]

        result = organize_pois_by_category(pois)

        # Check categories are created
        assert "food_and_drink" in result
        assert "shopping" in result
        assert "healthcare" in result
        assert "other" in result

        # Check POI counts
        assert len(result["food_and_drink"]) == 2
        assert len(result["shopping"]) == 1
        assert len(result["healthcare"]) == 1
        assert len(result["other"]) == 1

        # Check specific POIs
        food_ids = [poi["id"] for poi in result["food_and_drink"]]
        assert 1 in food_ids
        assert 4 in food_ids

    def test_organize_pois_empty_list(self):
        """Test organizing empty POI list."""
        result = organize_pois_by_category([])
        assert result == {}

    def test_organize_pois_missing_tags(self):
        """Test organizing POIs with missing tags field."""
        pois = [
            {"id": 1, "name": "No Tags"},
            {"id": 2, "tags": None},
            {"id": 3, "tags": {"amenity": "restaurant"}},
        ]

        result = organize_pois_by_category(pois)

        assert "other" in result
        assert "food_and_drink" in result
        assert len(result["other"]) == 2
        assert len(result["food_and_drink"]) == 1

    def test_get_poi_category_info(self):
        """Test getting category information."""
        info = get_poi_category_info()

        assert "categories" in info
        assert "total_categories" in info
        assert "category_details" in info

        # Check all categories are included
        assert set(info["categories"]) == set(POI_CATEGORY_MAPPING.keys())
        assert info["total_categories"] == len(POI_CATEGORY_MAPPING)

        # Check category details
        for category in POI_CATEGORY_MAPPING:
            assert category in info["category_details"]
            details = info["category_details"][category]
            assert "value_count" in details
            assert "sample_values" in details
            assert details["value_count"] == len(POI_CATEGORY_MAPPING[category])

    def test_is_valid_category(self):
        """Test category validation."""
        # Valid categories
        assert is_valid_category("food_and_drink")
        assert is_valid_category("shopping")
        assert is_valid_category("education")
        assert is_valid_category("healthcare")

        # Invalid categories
        assert not is_valid_category("invalid_category")
        assert not is_valid_category("")
        assert not is_valid_category("other")  # "other" is not in the mapping

    def test_get_category_values(self):
        """Test getting values for a category."""
        # Valid category
        values = get_category_values("food_and_drink")
        assert isinstance(values, list)
        assert "restaurant" in values
        assert "cafe" in values
        assert len(values) > 0

        # Invalid category
        assert get_category_values("invalid_category") is None
        assert get_category_values("") is None

    def test_add_category_value(self):
        """Test adding values to existing categories."""
        # Store original values
        original_values = POI_CATEGORY_MAPPING["food_and_drink"].copy()

        try:
            # Add new value
            assert add_category_value("food_and_drink", "test_restaurant")
            assert "test_restaurant" in POI_CATEGORY_MAPPING["food_and_drink"]

            # Try adding duplicate (should not duplicate)
            original_len = len(POI_CATEGORY_MAPPING["food_and_drink"])
            assert add_category_value("food_and_drink", "test_restaurant")
            assert len(POI_CATEGORY_MAPPING["food_and_drink"]) == original_len

            # Invalid category
            assert not add_category_value("invalid_category", "value")
        finally:
            # Restore original values
            POI_CATEGORY_MAPPING["food_and_drink"] = original_values

    def test_create_custom_category(self):
        """Test creating custom categories."""
        try:
            # Create new category
            assert create_custom_category("test_category", ["test1", "test2"])
            assert "test_category" in POI_CATEGORY_MAPPING
            assert POI_CATEGORY_MAPPING["test_category"] == ["test1", "test2"]

            # Try creating duplicate category
            assert not create_custom_category("test_category", ["test3"])

            # Verify the new category works with categorization
            assert categorize_poi({"amenity": "test1"}) == "test_category"
        finally:
            # Clean up
            if "test_category" in POI_CATEGORY_MAPPING:
                del POI_CATEGORY_MAPPING["test_category"]

    def test_comprehensive_category_coverage(self):
        """Test that all defined categories have proper coverage."""
        # Test sample values from each category
        test_cases = {
            "food_and_drink": [
                ("amenity", "restaurant"),
                ("amenity", "bar"),
                ("shop", "bakery"),
            ],
            "shopping": [
                ("shop", "supermarket"),
                ("shop", "clothes"),
                ("amenity", "marketplace"),
            ],
            "education": [
                ("amenity", "school"),
                ("amenity", "university"),
                ("amenity", "library"),
            ],
            "healthcare": [
                ("amenity", "hospital"),
                ("amenity", "pharmacy"),
                ("healthcare", "clinic"),
            ],
            "transportation": [
                ("amenity", "bus_station"),
                ("amenity", "parking"),
                ("amenity", "fuel"),
            ],
            "recreation": [
                ("leisure", "park"),
                ("leisure", "playground"),
                ("amenity", "cinema"),
            ],
            "services": [
                ("amenity", "bank"),
                ("amenity", "post_office"),
                ("office", "government"),
            ],
            "accommodation": [
                ("tourism", "hotel"),
                ("tourism", "hostel"),
                ("tourism", "guest_house"),
            ],
            "religious": [
                ("amenity", "place_of_worship"),
                ("amenity", "church"),
                ("amenity", "mosque"),
            ],
            "utilities": [
                ("amenity", "toilets"),
                ("amenity", "drinking_water"),
                ("amenity", "waste_basket"),
            ],
        }

        for expected_category, test_tags in test_cases.items():
            for key, value in test_tags:
                result = categorize_poi({key: value})
                assert result == expected_category, \
                    f"Expected {key}={value} to be categorized as {expected_category}, got {result}"

    def test_real_world_poi_examples(self):
        """Test with real-world POI examples."""
        # McDonald's (fast food restaurant)
        poi = {
            "amenity": "fast_food",
            "brand": "McDonald's",
            "cuisine": "burger",
            "name": "McDonald's"
        }
        assert categorize_poi(poi["tags"] if "tags" in poi else poi) == "food_and_drink"

        # Walmart (supermarket)
        poi = {
            "shop": "supermarket",
            "brand": "Walmart",
            "name": "Walmart Supercenter"
        }
        assert categorize_poi(poi["tags"] if "tags" in poi else poi) == "shopping"

        # Central Park (recreation)
        poi = {
            "leisure": "park",
            "name": "Central Park",
            "tourism": "attraction"
        }
        assert categorize_poi(poi["tags"] if "tags" in poi else poi) == "recreation"

        # City Hospital (healthcare)
        poi = {
            "amenity": "hospital",
            "emergency": "yes",
            "name": "City General Hospital"
        }
        assert categorize_poi(poi["tags"] if "tags" in poi else poi) == "healthcare"
