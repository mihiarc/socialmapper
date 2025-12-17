"""Tests for SocialMapper core API functions.

These tests use real API calls as specified in the user's requirements.
Tests are marked appropriately for different execution scenarios.
"""

import pytest

from socialmapper import (
    SocialMapperError,
    ValidationError,
    create_isochrone,
    create_map,
    get_census_blocks,
    get_census_data,
    get_poi,
)


class TestCreateIsochrone:
    """Test create_isochrone function."""

    @pytest.mark.external
    @pytest.mark.slow
    def test_create_isochrone_with_string_location(self):
        """Test isochrone creation with city name."""
        result = create_isochrone("Portland, OR", travel_time=10, travel_mode="drive")

        assert result["type"] == "Feature"
        assert "geometry" in result
        assert result["geometry"]["type"] in ["Polygon", "MultiPolygon"]
        assert result["properties"]["travel_time"] == 10
        assert result["properties"]["travel_mode"] == "drive"
        assert "area_sq_km" in result["properties"]
        assert result["properties"]["area_sq_km"] > 0

    @pytest.mark.external
    @pytest.mark.slow
    def test_create_isochrone_with_coordinates(self, portland_coords):
        """Test isochrone creation with lat/lon tuple."""
        result = create_isochrone(portland_coords, travel_time=15)

        assert result["type"] == "Feature"
        assert "geometry" in result
        assert result["properties"]["travel_time"] == 15

    @pytest.mark.external
    @pytest.mark.slow
    def test_create_isochrone_walk_mode(self, portland_coords):
        """Test isochrone with walking mode."""
        result = create_isochrone(portland_coords, travel_time=10, travel_mode="walk")

        assert result["properties"]["travel_mode"] == "walk"
        # Walking isochrone should be smaller than driving
        assert result["properties"]["area_sq_km"] > 0

    @pytest.mark.external
    @pytest.mark.slow
    def test_create_isochrone_bike_mode(self, portland_coords):
        """Test isochrone with biking mode."""
        result = create_isochrone(portland_coords, travel_time=10, travel_mode="bike")

        assert result["properties"]["travel_mode"] == "bike"

    def test_create_isochrone_invalid_travel_time(self, portland_coords):
        """Test that invalid travel time raises error."""
        with pytest.raises(ValueError, match="Travel time must be between"):
            create_isochrone(portland_coords, travel_time=0)

        with pytest.raises(ValueError, match="Travel time must be between"):
            create_isochrone(portland_coords, travel_time=121)

    def test_create_isochrone_invalid_travel_mode(self, portland_coords):
        """Test that invalid travel mode raises error."""
        with pytest.raises(ValueError, match="Travel mode must be one of"):
            create_isochrone(portland_coords, travel_mode="fly")


class TestGetCensusBlocks:
    """Test get_census_blocks function."""

    @pytest.mark.external
    @pytest.mark.slow
    def test_get_census_blocks_with_location(self, portland_coords):
        """Test fetching census blocks around a point."""
        blocks = get_census_blocks(location=portland_coords, radius_km=2)

        assert isinstance(blocks, list)
        assert len(blocks) > 0

        # Check block structure
        block = blocks[0]
        assert "geoid" in block
        assert "state_fips" in block
        assert "county_fips" in block
        assert "tract" in block
        assert "block_group" in block
        assert "geometry" in block
        assert "area_sq_km" in block

        # GEOID should be 12 characters
        assert len(block["geoid"]) == 12

    @pytest.mark.external
    @pytest.mark.slow
    def test_get_census_blocks_with_polygon(self, sample_geojson_feature):
        """Test fetching census blocks within a polygon."""
        blocks = get_census_blocks(polygon=sample_geojson_feature)

        assert isinstance(blocks, list)
        # May be empty if polygon is small, but should return list

    def test_get_census_blocks_neither_provided(self):
        """Test that error is raised when no location specified."""
        with pytest.raises(ValueError, match="Must provide either"):
            get_census_blocks()

    def test_get_census_blocks_both_provided(self, portland_coords, sample_geojson_feature):
        """Test that error is raised when both location and polygon provided."""
        with pytest.raises(ValueError, match="not both"):
            get_census_blocks(polygon=sample_geojson_feature, location=portland_coords)


class TestGetCensusData:
    """Test get_census_data function."""

    @pytest.mark.external
    @pytest.mark.slow
    def test_get_census_data_with_geoids(self, census_api_key):
        """Test fetching census data with GEOID list."""
        # Using a known Oregon GEOID (Multnomah County, tract 000101, block group 1)
        geoids = ["410510001011"]  # Multnomah County, OR
        result = get_census_data(geoids, variables=["population"])

        assert result.location_type == "geoids"
        assert len(result.data) > 0
        assert "year" in result.query_info

    @pytest.mark.external
    @pytest.mark.slow
    def test_get_census_data_with_point(self, census_api_key, portland_coords):
        """Test fetching census data for a point location."""
        result = get_census_data(portland_coords, variables=["population"])

        assert result.location_type == "point"
        assert len(result.data) > 0

    @pytest.mark.external
    @pytest.mark.slow
    def test_get_census_data_multiple_variables(self, census_api_key):
        """Test fetching multiple census variables."""
        geoids = ["410510001011"]
        result = get_census_data(
            geoids,
            variables=["population", "median_income"]
        )

        assert len(result.query_info["variables"]) == 2

    @pytest.mark.external
    @pytest.mark.slow
    def test_get_census_data_with_year(self, census_api_key):
        """Test fetching census data for specific year."""
        geoids = ["410510001011"]
        result = get_census_data(geoids, variables=["population"], year=2022)

        assert result.query_info["year"] == 2022


class TestCreateMap:
    """Test create_map function."""

    @pytest.mark.external
    @pytest.mark.slow
    def test_create_map_png(self, sample_census_block):
        """Test creating PNG map."""
        data = [sample_census_block]
        # Add a numeric column for visualization
        data[0]["population"] = 1000

        result = create_map(data, column="population", export_format="png")

        assert result.format == "png"
        assert result.image_data is not None
        assert isinstance(result.image_data, bytes)
        assert len(result.image_data) > 0

    @pytest.mark.external
    @pytest.mark.slow
    def test_create_map_geojson(self, sample_census_block):
        """Test creating GeoJSON export."""
        data = [sample_census_block]
        data[0]["value"] = 42

        result = create_map(data, column="value", export_format="geojson")

        assert result.format == "geojson"
        assert result.geojson_data is not None
        assert result.geojson_data["type"] == "FeatureCollection"

    @pytest.mark.external
    @pytest.mark.slow
    def test_create_map_with_title(self, sample_census_block):
        """Test creating map with title."""
        data = [sample_census_block]
        data[0]["density"] = 500

        result = create_map(
            data,
            column="density",
            title="Population Density"
        )

        assert result.metadata["title"] == "Population Density"

    def test_create_map_missing_column(self, sample_census_block):
        """Test that error is raised for missing column."""
        data = [sample_census_block]

        with pytest.raises(ValueError, match="Column.*not found"):
            create_map(data, column="nonexistent")

    def test_create_map_invalid_format(self, sample_census_block):
        """Test that error is raised for invalid format."""
        data = [sample_census_block]
        data[0]["value"] = 1

        with pytest.raises(ValueError, match="Export format must be one of"):
            create_map(data, column="value", export_format="jpeg")


class TestGetPOI:
    """Test get_poi function."""

    @pytest.mark.external
    @pytest.mark.slow
    def test_get_poi_basic(self, portland_coords):
        """Test basic POI retrieval."""
        pois = get_poi(portland_coords, limit=10)

        assert isinstance(pois, list)
        # Should find some POIs in Portland
        if len(pois) > 0:
            poi = pois[0]
            assert "name" in poi or "category" in poi
            assert "lat" in poi
            assert "lon" in poi
            assert "distance_km" in poi

    @pytest.mark.external
    @pytest.mark.slow
    def test_get_poi_with_categories(self, portland_coords):
        """Test POI retrieval with category filter."""
        pois = get_poi(
            portland_coords,
            categories=["food_and_drink"],
            limit=20
        )

        assert isinstance(pois, list)
        # All returned POIs should be food_and_drink category
        for poi in pois:
            assert poi.get("category") == "food_and_drink" or "food" in str(poi).lower()

    @pytest.mark.external
    @pytest.mark.slow
    def test_get_poi_with_travel_time(self, portland_coords):
        """Test POI retrieval with travel time boundary."""
        pois = get_poi(
            portland_coords,
            travel_time=10,
            limit=50
        )

        assert isinstance(pois, list)

    @pytest.mark.external
    @pytest.mark.slow
    def test_get_poi_sorted_by_distance(self, portland_coords):
        """Test that POIs are sorted by distance."""
        pois = get_poi(portland_coords, limit=20)

        if len(pois) >= 2:
            distances = [p["distance_km"] for p in pois if p.get("distance_km") is not None]
            # Should be sorted ascending
            assert distances == sorted(distances)

    @pytest.mark.external
    @pytest.mark.slow
    def test_get_poi_string_location(self):
        """Test POI retrieval with string location."""
        pois = get_poi("Portland, OR", limit=5)

        assert isinstance(pois, list)

    def test_get_poi_invalid_category(self, portland_coords):
        """Test that invalid category raises error."""
        from socialmapper import InvalidPOICategoryError

        with pytest.raises(InvalidPOICategoryError):
            get_poi(portland_coords, categories=["invalid_category_xyz"])

    def test_get_poi_invalid_travel_time(self, portland_coords):
        """Test that invalid travel time raises error."""
        with pytest.raises(ValueError, match="Travel time must be between"):
            get_poi(portland_coords, travel_time=0)

        with pytest.raises(ValueError, match="Travel time must be between"):
            get_poi(portland_coords, travel_time=121)


class TestAPIIntegration:
    """Integration tests combining multiple API functions."""

    @pytest.mark.external
    @pytest.mark.slow
    @pytest.mark.integration
    def test_isochrone_to_census_blocks_workflow(self, census_api_key, portland_coords):
        """Test workflow: create isochrone -> get census blocks."""
        # Create isochrone
        iso = create_isochrone(portland_coords, travel_time=10)

        # Get census blocks within isochrone
        blocks = get_census_blocks(polygon=iso)

        assert isinstance(blocks, list)
        assert len(blocks) > 0

    @pytest.mark.external
    @pytest.mark.slow
    @pytest.mark.integration
    def test_isochrone_to_census_data_workflow(self, census_api_key, portland_coords):
        """Test workflow: create isochrone -> get census data."""
        # Create isochrone
        iso = create_isochrone(portland_coords, travel_time=10)

        # Get census data for area
        result = get_census_data(iso, variables=["population"])

        assert result.location_type == "polygon"
        assert len(result.data) > 0

    @pytest.mark.external
    @pytest.mark.slow
    @pytest.mark.integration
    def test_full_analysis_workflow(self, census_api_key, portland_coords):
        """Test complete analysis workflow."""
        # 1. Create isochrone
        iso = create_isochrone(portland_coords, travel_time=15)
        assert iso["type"] == "Feature"

        # 2. Get census blocks
        blocks = get_census_blocks(polygon=iso)
        assert len(blocks) > 0

        # 3. Get census data for blocks
        geoids = [b["geoid"] for b in blocks]
        census_result = get_census_data(geoids[:10], variables=["population"])  # Limit for speed
        assert len(census_result.data) > 0

        # 4. Get POIs in area
        pois = get_poi(portland_coords, travel_time=15, limit=20)
        assert isinstance(pois, list)


class TestErrorHandling:
    """Test error handling across API functions."""

    def test_all_errors_inherit_from_base(self):
        """Verify all errors can be caught with base exception."""
        # This is a structural test - errors should inherit from SocialMapperError
        from socialmapper import (
            AnalysisError,
            APIError,
            DataError,
        )

        assert issubclass(ValidationError, SocialMapperError)
        assert issubclass(APIError, SocialMapperError)
        assert issubclass(DataError, SocialMapperError)
        assert issubclass(AnalysisError, SocialMapperError)
