#!/usr/bin/env python3
"""Unit tests for polygon-based POI queries."""

from unittest.mock import Mock, patch

import geopandas as gpd
import overpy
import pytest
from shapely.geometry import MultiPolygon, Point, Polygon

from socialmapper.query.polygon_queries import (
    DEFAULT_OVERPASS_TIMEOUT,
    MAX_POLYGON_COORDINATES,
    _build_category_tag_filters,
    _format_coordinate,
    _infer_osm_key,
    _multipolygon_to_overpass_queries,
    _polygon_to_overpass_format,
    build_poi_discovery_query,
    query_pois_from_isochrone,
    query_pois_in_polygon,
)


class TestCoordinateFormatting:
    """Test coordinate formatting functions."""

    def test_format_coordinate_default_precision(self):
        """Test coordinate formatting with default precision."""
        assert _format_coordinate(12.3456789) == "12.3456789"
        assert _format_coordinate(-45.123) == "-45.1230000"
        assert _format_coordinate(0.0) == "0.0000000"

    def test_format_coordinate_custom_precision(self):
        """Test coordinate formatting with custom precision."""
        assert _format_coordinate(12.3456789, precision=3) == "12.346"
        assert _format_coordinate(-45.123456, precision=5) == "-45.12346"
        assert _format_coordinate(180.0, precision=1) == "180.0"


class TestPolygonConversion:
    """Test polygon to Overpass format conversion."""

    def test_polygon_to_overpass_format_simple(self):
        """Test converting a simple polygon."""
        # Create a square polygon
        polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        result = _polygon_to_overpass_format(polygon)

        # Expected format: "lat1 lon1 lat2 lon2 ..."
        # Shapely stores as (lon, lat), so (0,0) becomes "0.0000000 0.0000000"
        expected = "0.0000000 0.0000000 0.0000000 1.0000000 1.0000000 1.0000000 1.0000000 0.0000000"
        assert result == expected

    def test_polygon_to_overpass_format_complex(self):
        """Test converting a polygon with decimal coordinates."""
        polygon = Polygon([
            (-73.9851, 40.7589),  # NYC coordinates
            (-73.9851, 40.7489),
            (-73.9751, 40.7489),
            (-73.9751, 40.7589)
        ])
        result = _polygon_to_overpass_format(polygon)

        # Check format and coordinate order
        coords = result.split()
        assert len(coords) == 8  # 4 points * 2 coords each
        assert coords[0] == "40.7589000"  # First latitude
        assert coords[1] == "-73.9851000"  # First longitude

    def test_polygon_to_overpass_format_too_many_coords(self):
        """Test error handling for polygons with too many coordinates."""
        # Create a polygon with more than MAX_POLYGON_COORDINATES points
        coords = [(float(i), float(i)) for i in range(MAX_POLYGON_COORDINATES + 1)]
        polygon = Polygon(coords)

        with pytest.raises(ValueError) as exc_info:
            _polygon_to_overpass_format(polygon)

        assert "exceeding Overpass API limit" in str(exc_info.value)

    def test_multipolygon_to_overpass_queries(self):
        """Test converting a MultiPolygon."""
        # Create two simple polygons
        poly1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        poly2 = Polygon([(2, 2), (3, 2), (3, 3), (2, 3)])
        multipolygon = MultiPolygon([poly1, poly2])

        result = _multipolygon_to_overpass_queries(multipolygon)

        assert len(result) == 2
        assert isinstance(result[0], str)
        assert isinstance(result[1], str)
        # Each should have 8 coordinate values (4 points * 2 coords)
        assert len(result[0].split()) == 8
        assert len(result[1].split()) == 8


class TestOSMKeyInference:
    """Test OSM key inference logic."""

    def test_infer_osm_key_food_and_drink(self):
        """Test OSM key inference for food and drink category."""
        assert _infer_osm_key("restaurant", "food_and_drink") == "amenity"
        assert _infer_osm_key("cafe", "food_and_drink") == "amenity"
        assert _infer_osm_key("bakery", "food_and_drink") == "shop"
        assert _infer_osm_key("wine", "food_and_drink") == "shop"

    def test_infer_osm_key_shopping(self):
        """Test OSM key inference for shopping category."""
        assert _infer_osm_key("marketplace", "shopping") == "amenity"
        assert _infer_osm_key("clothes", "shopping") == "shop"
        assert _infer_osm_key("electronics", "shopping") == "shop"

    def test_infer_osm_key_transportation(self):
        """Test OSM key inference for transportation category."""
        assert _infer_osm_key("fuel", "transportation") == "amenity"
        assert _infer_osm_key("bus_station", "transportation") == "railway"
        assert _infer_osm_key("tram_stop", "transportation") == "public_transport"

    def test_infer_osm_key_recreation(self):
        """Test OSM key inference for recreation category."""
        assert _infer_osm_key("cinema", "recreation") == "amenity"
        assert _infer_osm_key("park", "recreation") == "leisure"
        assert _infer_osm_key("swimming_pool", "recreation") == "leisure"

    def test_infer_osm_key_default_fallback(self):
        """Test default fallback for unknown combinations."""
        assert _infer_osm_key("unknown_value", "unknown_category") == "amenity"


class TestCategoryTagFilters:
    """Test category-based tag filter building."""

    def test_build_category_tag_filters_single_category(self):
        """Test building filters for a single category."""
        filters = _build_category_tag_filters(["food_and_drink"])

        assert len(filters) > 0
        # Should contain amenity and shop tags
        amenity_tags = [f for f in filters if "amenity" in f]
        shop_tags = [f for f in filters if "shop" in f]
        assert len(amenity_tags) > 0
        assert len(shop_tags) > 0

    def test_build_category_tag_filters_multiple_categories(self):
        """Test building filters for multiple categories."""
        filters = _build_category_tag_filters(["food_and_drink", "shopping"])

        assert len(filters) > 0
        # Should have more filters than single category
        single_cat_filters = _build_category_tag_filters(["food_and_drink"])
        assert len(filters) > len(single_cat_filters)

    def test_build_category_tag_filters_invalid_category(self):
        """Test handling of invalid categories."""
        filters = _build_category_tag_filters(["invalid_category", "food_and_drink"])

        # Should still return filters for valid category
        assert len(filters) > 0
        # Should be same as just food_and_drink
        valid_filters = _build_category_tag_filters(["food_and_drink"])
        assert len(filters) == len(valid_filters)

    def test_build_category_tag_filters_none(self):
        """Test building filters with no categories (all categories)."""
        filters = _build_category_tag_filters(None)

        # Should include filters for all categories
        assert len(filters) > 100  # Should have many filters


class TestQueryBuilding:
    """Test Overpass query building."""

    def test_build_query_simple_polygon(self):
        """Test building a query for a simple polygon."""
        polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        query = build_poi_discovery_query(polygon)

        # Check query structure
        assert "[out:json]" in query
        assert f"[timeout:{DEFAULT_OVERPASS_TIMEOUT}]" in query
        assert "(poly:" in query
        assert "out center;" in query
        assert "node" in query
        assert "way" in query
        assert "relation" in query

    def test_build_query_with_categories(self):
        """Test building a query with category filters."""
        polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        query = build_poi_discovery_query(polygon, categories=["food_and_drink"])

        # Should contain amenity tags for restaurants, cafes, etc
        assert '["amenity"="restaurant"]' in query or '"amenity"' in query
        assert "(poly:" in query

    def test_build_query_with_timeout(self):
        """Test building a query with custom timeout."""
        polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        query = build_poi_discovery_query(polygon, timeout=300)

        assert "[timeout:300]" in query

    def test_build_query_with_additional_tags(self):
        """Test building a query with additional tags."""
        polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        query = build_poi_discovery_query(
            polygon,
            additional_tags={"cuisine": "italian"}
        )

        assert '["cuisine"="italian"]' in query

    def test_build_query_multipolygon(self):
        """Test building a query for a MultiPolygon."""
        poly1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        poly2 = Polygon([(2, 2), (3, 2), (3, 3), (2, 3)])
        multipolygon = MultiPolygon([poly1, poly2])

        query = build_poi_discovery_query(multipolygon)

        # Should have multiple poly: clauses
        poly_count = query.count("(poly:")
        assert poly_count >= 2

    def test_build_query_invalid_geometry(self):
        """Test error handling for invalid geometry types."""
        point = Point(0, 0)

        with pytest.raises(ValueError) as exc_info:
            build_poi_discovery_query(point)

        assert "must be a Polygon or MultiPolygon" in str(exc_info.value)


class TestPOIQuerying:
    """Test the main POI querying functions."""

    @patch('socialmapper.query.polygon_queries._query_overpass_with_polygon')
    def test_query_pois_in_polygon_basic(self, mock_query):
        """Test basic POI querying in a polygon."""
        # Mock Overpass response
        mock_result = Mock(spec=overpy.Result)
        mock_result.nodes = [
            Mock(id=1, lat=0.5, lon=0.5, tags={"amenity": "restaurant", "name": "Test Restaurant"}),
            Mock(id=2, lat=0.6, lon=0.6, tags={"shop": "supermarket", "name": "Test Shop"})
        ]
        mock_result.ways = []
        mock_result.relations = []
        mock_query.return_value = mock_result

        # Query POIs
        polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        result = query_pois_in_polygon(polygon)

        # Verify results
        assert result["poi_count"] == 2
        assert len(result["pois"]) == 2
        assert result["pois"][0]["id"] == 1
        assert result["pois"][0]["tags"]["amenity"] == "restaurant"
        assert result["query_info"]["geometry_type"] == "Polygon"

    @patch('socialmapper.query.polygon_queries._query_overpass_with_polygon')
    def test_query_pois_with_categories(self, mock_query):
        """Test POI querying with category filtering."""
        # Mock empty result
        mock_result = Mock(spec=overpy.Result)
        mock_result.nodes = []
        mock_result.ways = []
        mock_result.relations = []
        mock_query.return_value = mock_result

        polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        result = query_pois_in_polygon(polygon, categories=["food_and_drink"])

        # Verify query was called
        mock_query.assert_called_once()
        query_str = mock_query.call_args[0][0]

        # Should have amenity or shop tags in query
        assert "amenity" in query_str or "shop" in query_str

    @patch('socialmapper.query.polygon_queries._query_overpass_with_polygon')
    def test_query_pois_with_ways_and_relations(self, mock_query):
        """Test POI querying including ways and relations."""
        # Mock result with ways and relations
        mock_result = Mock(spec=overpy.Result)
        mock_result.nodes = []

        mock_way = Mock(id=100, tags={"building": "yes", "shop": "mall"})
        mock_way.center_lat = 0.5
        mock_way.center_lon = 0.5
        mock_result.ways = [mock_way]

        mock_relation = Mock(id=200, tags={"amenity": "university"})
        mock_relation.center_lat = 0.7
        mock_relation.center_lon = 0.7
        mock_result.relations = [mock_relation]

        mock_query.return_value = mock_result

        polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        result = query_pois_in_polygon(polygon)

        assert result["poi_count"] == 2
        assert result["pois"][0]["type"] == "way"
        assert result["pois"][1]["type"] == "relation"

    @patch('socialmapper.query.polygon_queries._query_overpass_with_polygon')
    def test_query_pois_invalid_geometry_fix(self, mock_query):
        """Test automatic fixing of invalid geometry."""
        # Create an invalid polygon (self-intersecting)
        coords = [(0, 0), (1, 1), (1, 0), (0, 1)]
        polygon = Polygon(coords)

        # Mock empty result
        mock_result = Mock(spec=overpy.Result)
        mock_result.nodes = []
        mock_result.ways = []
        mock_result.relations = []
        mock_query.return_value = mock_result

        # Should not raise an error
        result = query_pois_in_polygon(polygon)
        assert result["poi_count"] == 0

    @patch('socialmapper.query.polygon_queries._query_overpass_with_polygon')
    def test_query_pois_with_simplification(self, mock_query):
        """Test geometry simplification."""
        # Create a complex polygon
        import numpy as np
        angles = np.linspace(0, 2 * np.pi, 100)
        coords = [(np.cos(a), np.sin(a)) for a in angles]
        polygon = Polygon(coords)

        # Mock empty result
        mock_result = Mock(spec=overpy.Result)
        mock_result.nodes = []
        mock_result.ways = []
        mock_result.relations = []
        mock_query.return_value = mock_result

        # Query with simplification
        result = query_pois_in_polygon(polygon, simplify_tolerance=0.1)

        # Query should succeed
        assert "query_info" in result
        mock_query.assert_called_once()


class TestIsochroneIntegration:
    """Test isochrone-specific query functions."""

    @patch('socialmapper.query.polygon_queries.query_pois_in_polygon')
    def test_query_pois_from_isochrone(self, mock_query_func):
        """Test querying POIs from an isochrone GeoDataFrame."""
        # Create a mock isochrone GeoDataFrame
        polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        gdf = gpd.GeoDataFrame(
            {"travel_time": [10]},
            geometry=[polygon],
            crs="EPSG:4326"
        )

        # Mock the query function
        mock_query_func.return_value = {
            "poi_count": 5,
            "pois": [],
            "query_info": {}
        }

        # Query POIs
        result = query_pois_from_isochrone(gdf, categories=["shopping"])

        # Verify call
        mock_query_func.assert_called_once()
        call_args = mock_query_func.call_args
        # Check keyword arguments (function uses kwargs)
        assert "geometry" in call_args.kwargs
        assert isinstance(call_args.kwargs["geometry"], Polygon)
        assert call_args.kwargs["categories"] == ["shopping"]
        assert call_args.kwargs["simplify_tolerance"] == 0.001

    def test_query_pois_from_isochrone_empty_gdf(self):
        """Test error handling for empty isochrone."""
        empty_gdf = gpd.GeoDataFrame()

        with pytest.raises(ValueError) as exc_info:
            query_pois_from_isochrone(empty_gdf)

        assert "empty or None" in str(exc_info.value)

    @patch('socialmapper.query.polygon_queries.query_pois_in_polygon')
    def test_query_pois_from_isochrone_multiple_geometries(self, mock_query_func):
        """Test handling of isochrone with multiple geometries."""
        # Create multiple polygons
        poly1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        poly2 = Polygon([(1, 0), (2, 0), (2, 1), (1, 1)])
        gdf = gpd.GeoDataFrame(
            {"travel_time": [10, 20]},
            geometry=[poly1, poly2],
            crs="EPSG:4326"
        )

        # Mock the query function
        mock_query_func.return_value = {
            "poi_count": 10,
            "pois": [],
            "query_info": {}
        }

        # Query POIs - should use union of geometries
        result = query_pois_from_isochrone(gdf)

        # Verify union was used
        mock_query_func.assert_called_once()
        call_args = mock_query_func.call_args
        # Check keyword arguments
        assert "geometry" in call_args.kwargs
        geometry = call_args.kwargs["geometry"]
        # Union should create a single larger polygon or multipolygon
        assert isinstance(geometry, (Polygon, MultiPolygon))


class TestRetryLogic:
    """Test retry logic for API calls."""

    @patch('socialmapper.query.polygon_queries.overpy.Overpass')
    def test_query_with_overpass_api(self, mock_overpass_class):
        """Test basic query execution with Overpass API."""
        # Mock API
        mock_api = Mock()
        mock_result = Mock(spec=overpy.Result)
        mock_result.nodes = []
        mock_result.ways = []
        mock_result.relations = []
        mock_api.query.return_value = mock_result
        mock_overpass_class.return_value = mock_api

        from socialmapper.query.polygon_queries import _query_overpass_with_polygon

        # Should succeed
        result = _query_overpass_with_polygon("test query")

        # Verify API was called
        assert mock_api.query.call_count == 1
        assert result == mock_result


class TestRealAPIIntegration:
    """Integration tests with real Overpass API (marked for optional execution)."""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires real API access")
    def test_real_api_small_polygon(self):
        """Test with a real small polygon query."""
        # Small polygon in Manhattan
        polygon = Polygon([
            (-73.9851, 40.7589),
            (-73.9851, 40.7489),
            (-73.9751, 40.7489),
            (-73.9751, 40.7589)
        ])

        result = query_pois_in_polygon(
            polygon,
            categories=["food_and_drink"],
            timeout=30
        )

        # Should find some POIs
        assert result["poi_count"] > 0
        assert len(result["pois"]) > 0

        # Check POI structure
        first_poi = result["pois"][0]
        assert "id" in first_poi
        assert "lat" in first_poi
        assert "lon" in first_poi
        assert "tags" in first_poi
