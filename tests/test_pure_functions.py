"""Tests for pure/internal functions that don't require external API calls.

These tests verify deterministic behavior of utility functions, caches,
validators, and data processing helpers.
"""

import threading

import pytest

from socialmapper._census import normalize_variable_names, validate_fips_code
from socialmapper._osm import (
    _expand_categories_to_osm_tags,
    _polygon_to_overpass_poly,
    build_overpass_query,
    determine_category,
    process_poi_results,
)
from socialmapper.exceptions import ValidationError
from socialmapper.helpers import is_conus
from socialmapper.performance.bounded_cache import BoundedCache


class TestValidateFipsCode:
    """Test validate_fips_code utility."""

    def test_valid_state_fips(self):
        assert validate_fips_code("41", 2) == "41"

    def test_valid_county_fips(self):
        assert validate_fips_code("051", 3) == "051"

    def test_empty_string(self):
        with pytest.raises(ValueError, match="empty value"):
            validate_fips_code("", 2)

    def test_non_digit(self):
        with pytest.raises(ValueError, match="non-digit"):
            validate_fips_code("AB", 2)

    def test_wrong_length(self):
        with pytest.raises(ValueError, match="expected 2 digits"):
            validate_fips_code("4", 2)
        with pytest.raises(ValueError, match="expected 2 digits"):
            validate_fips_code("410", 2)


class TestNormalizeVariableNames:
    """Test normalize_variable_names mapping."""

    def test_known_name_population(self):
        result = normalize_variable_names(["population"])
        assert "B01003_001E" in result

    def test_known_name_median_income(self):
        result = normalize_variable_names(["median_income"])
        assert "B19013_001E" in result

    def test_census_code_passthrough(self):
        result = normalize_variable_names(["B01003_001E"])
        assert result == ["B01003_001E"]

    def test_unknown_name_passthrough(self):
        result = normalize_variable_names(["some_unknown_var"])
        assert result == ["some_unknown_var"]

    def test_mixed_names_and_codes(self):
        result = normalize_variable_names(["population", "B19013_001E"])
        assert "B01003_001E" in result
        assert "B19013_001E" in result


class TestBoundedCache:
    """Test BoundedCache LRU behavior."""

    def test_get_set(self):
        cache = BoundedCache(maxsize=10)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_missing(self):
        cache = BoundedCache(maxsize=10)
        assert cache.get("missing") is None

    def test_lru_eviction(self):
        cache = BoundedCache(maxsize=3)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        # Cache is full: [a, b, c]
        cache.set("d", 4)
        # 'a' should have been evicted
        assert cache.get("a") is None
        assert cache.get("b") == 2
        assert cache.get("d") == 4

    def test_lru_promotion(self):
        cache = BoundedCache(maxsize=3)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        # Access 'a' to promote it
        cache.get("a")
        # Now add 'd' - 'b' should be evicted (oldest unused)
        cache.set("d", 4)
        assert cache.get("a") == 1  # Still present (was promoted)
        assert cache.get("b") is None  # Evicted
        assert cache.get("d") == 4

    def test_thread_safety(self):
        cache = BoundedCache(maxsize=100)
        errors = []

        def worker(start):
            try:
                for i in range(start, start + 50):
                    cache.set(f"key_{i}", i)
                    val = cache.get(f"key_{i}")
                    if val is not None and val != i:
                        errors.append(f"Expected {i}, got {val}")
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=worker, args=(i * 50,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Thread safety errors: {errors}"


class TestIsConus:
    """Test is_conus coordinate checker."""

    def test_portland_is_conus(self):
        assert is_conus(45.5152, -122.6784) is True

    def test_honolulu_not_conus(self):
        assert is_conus(21.3069, -157.8583) is False

    def test_london_not_conus(self):
        assert is_conus(51.5074, -0.1278) is False

    def test_anchorage_not_conus(self):
        assert is_conus(61.2181, -149.9003) is False


class TestDetermineCategory:
    """Test OSM tag -> category mapping."""

    def test_restaurant(self):
        assert determine_category({"amenity": "restaurant"}) == "food_and_drink"

    def test_supermarket(self):
        assert determine_category({"shop": "supermarket"}) == "shopping"

    def test_hospital(self):
        assert determine_category({"amenity": "hospital"}) == "healthcare"

    def test_unknown_tags(self):
        result = determine_category({"building": "yes"})
        assert result == "other"

    def test_raw_tag_returned_for_unmatched_key(self):
        result = determine_category({"amenity": "some_rare_amenity"})
        assert result == "some_rare_amenity"


class TestProcessPoiResults:
    """Test process_poi_results element parsing."""

    def test_node_element(self):
        elements = [{
            "type": "node",
            "id": 1,
            "lat": 45.5,
            "lon": -122.6,
            "tags": {"name": "Test", "amenity": "cafe"},
        }]
        pois = process_poi_results(elements)
        assert len(pois) == 1
        assert pois[0]["name"] == "Test"
        assert pois[0]["lat"] == 45.5
        assert pois[0]["lon"] == -122.6

    def test_way_with_center(self):
        elements = [{
            "type": "way",
            "id": 2,
            "center": {"lat": 45.5, "lon": -122.6},
            "tags": {"name": "Shop", "shop": "supermarket"},
        }]
        pois = process_poi_results(elements)
        assert len(pois) == 1
        assert pois[0]["lat"] == 45.5

    def test_way_without_center(self):
        elements = [{
            "type": "way",
            "id": 3,
            "tags": {"name": "Unknown", "amenity": "bank"},
        }]
        pois = process_poi_results(elements)
        # Should skip ways without center
        assert len(pois) == 0

    def test_relation_with_center(self):
        elements = [{
            "type": "relation",
            "id": 4,
            "center": {"lat": 45.5, "lon": -122.6},
            "tags": {"name": "Mall", "shop": "mall"},
        }]
        pois = process_poi_results(elements)
        assert len(pois) == 1
        assert pois[0]["name"] == "Mall"


class TestExpandCategoriesToOsmTags:
    """Test _expand_categories_to_osm_tags helper."""

    def test_specific_category(self):
        tags = _expand_categories_to_osm_tags(["food_and_drink"])
        assert isinstance(tags, list)
        assert len(tags) > 0
        # Should contain restaurant, cafe, etc.
        assert any("restaurant" in t for t in tags)

    def test_none_returns_all(self):
        tags = _expand_categories_to_osm_tags(None)
        assert isinstance(tags, list)
        assert len(tags) > 0


class TestPolygonToOverpassPoly:
    """Test _polygon_to_overpass_poly helper."""

    def test_basic_polygon(self):
        from shapely.geometry import Polygon

        poly = Polygon([(-122.68, 45.51), (-122.68, 45.52),
                        (-122.67, 45.52), (-122.67, 45.51)])
        result = _polygon_to_overpass_poly(poly)
        assert isinstance(result, str)
        assert "45.51" in result
        assert "-122.68" in result


class TestBuildOverpassQuery:
    """Test build_overpass_query generates valid Overpass QL."""

    def test_contains_output_format(self):
        from shapely.geometry import Polygon

        poly = Polygon([(-122.68, 45.51), (-122.68, 45.52),
                        (-122.67, 45.52), (-122.67, 45.51)])
        tags = ["amenity=restaurant"]
        query = build_overpass_query(poly, tags)
        assert "[out:json]" in query

    def test_contains_tag_filter(self):
        from shapely.geometry import Polygon

        poly = Polygon([(-122.68, 45.51), (-122.68, 45.52),
                        (-122.67, 45.52), (-122.67, 45.51)])
        tags = ["amenity=restaurant"]
        query = build_overpass_query(poly, tags)
        assert "amenity" in query
        assert "restaurant" in query


class TestValidationErrorIsValueError:
    """Test that ValidationError can be caught as ValueError."""

    def test_isinstance(self):
        err = ValidationError("test")
        assert isinstance(err, ValueError)

    def test_except_catches(self):
        with pytest.raises(ValueError):
            raise ValidationError("test")
