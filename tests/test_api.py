"""Tests for SocialMapper core API functions.

These tests use real API calls as specified in the user's requirements.
Tests are marked appropriately for different execution scenarios.
"""

import pytest

from socialmapper import (
    SocialMapperError,
    ValidationError,
    analyze_multiple_pois,
    create_isochrone,
    create_map,
    generate_report,
    get_census_blocks,
    get_census_data,
    get_poi,
    import_poi_csv,
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

    @pytest.mark.external
    @pytest.mark.slow
    def test_create_map_with_basemap(self, sample_census_block):
        """Test creating map with different basemap providers."""
        data = [sample_census_block]
        data[0]["population"] = 1000

        # Test with default basemap (CartoDB.Voyager)
        result = create_map(data, column="population")
        assert result.format == "png"
        assert result.image_data is not None

        # Test with Positron basemap
        result = create_map(data, column="population", basemap="CartoDB.Positron")
        assert result.image_data is not None

        # Test with no basemap
        result = create_map(data, column="population", basemap=None)
        assert result.image_data is not None

    @pytest.mark.external
    @pytest.mark.slow
    def test_create_map_with_custom_cmap(self, sample_census_block):
        """Test creating map with custom colormap."""
        data = [sample_census_block]
        data[0]["population"] = 1000

        result = create_map(data, column="population", cmap="viridis")
        assert result.format == "png"
        assert result.image_data is not None

    @pytest.mark.external
    @pytest.mark.slow
    def test_create_map_with_stats_box(self, sample_census_block):
        """Test creating map with statistics box."""
        data = [sample_census_block]
        data[0]["population"] = 1000

        result = create_map(data, column="population", show_stats=True)
        assert result.format == "png"
        assert result.image_data is not None

    @pytest.mark.external
    @pytest.mark.slow
    def test_create_map_with_custom_stats(self, sample_census_block):
        """Test creating map with custom statistics dictionary."""
        data = [sample_census_block]
        data[0]["population"] = 1000

        custom_stats = {
            "Total Population": "1,000",
            "Area": "1.5 sq km",
            "Density": "667/sq km"
        }
        result = create_map(
            data, column="population",
            show_stats=True, stats_dict=custom_stats
        )
        assert result.format == "png"
        assert result.image_data is not None

    @pytest.mark.external
    @pytest.mark.slow
    def test_create_map_with_overlay_points(self, sample_census_block):
        """Test creating map with point overlays."""
        data = [sample_census_block]
        data[0]["population"] = 1000

        points = [
            {"lat": 45.515, "lon": -122.675, "name": "Center"},
            {"lat": 45.520, "lon": -122.680},  # Point without name
        ]
        result = create_map(
            data, column="population",
            overlay_points=points
        )
        assert result.format == "png"
        assert result.image_data is not None

    @pytest.mark.external
    @pytest.mark.slow
    def test_create_map_with_overlay_boundary(self, sample_census_block, sample_geojson_feature):
        """Test creating map with boundary overlay."""
        data = [sample_census_block]
        data[0]["population"] = 1000

        result = create_map(
            data, column="population",
            overlay_boundary=sample_geojson_feature
        )
        assert result.format == "png"
        assert result.image_data is not None

    @pytest.mark.external
    @pytest.mark.slow
    def test_create_map_all_features(self, sample_census_block, sample_geojson_feature):
        """Test creating map with all new features combined."""
        data = [sample_census_block]
        data[0]["population"] = 1000

        points = [{"lat": 45.515, "lon": -122.675, "name": "Origin"}]
        custom_stats = {"Count": 1, "Value": 1000}

        result = create_map(
            data, column="population",
            title="Full Feature Test",
            basemap="CartoDB.Voyager",
            cmap="YlGnBu",
            overlay_boundary=sample_geojson_feature,
            overlay_points=points,
            show_stats=True,
            stats_dict=custom_stats
        )
        assert result.format == "png"
        assert result.image_data is not None
        assert len(result.image_data) > 0

    def test_create_map_html(self, sample_census_block):
        """Test creating an interactive HTML map."""
        data = [sample_census_block]
        data[0]["population"] = 1000

        result = create_map(data, column="population", export_format="html")

        assert result.format == "html"
        assert result.html_content is not None
        assert isinstance(result.html_content, str)
        assert "leaflet" in result.html_content.lower()

    def test_create_map_html_with_title(self, sample_census_block):
        """Test that title appears in HTML map content."""
        data = [sample_census_block]
        data[0]["population"] = 1000

        result = create_map(
            data, column="population",
            title="Test Population Map",
            export_format="html",
        )

        assert result.format == "html"
        assert "Test Population Map" in result.html_content

    def test_create_map_html_with_overlays(self, sample_census_block, sample_geojson_feature):
        """Test HTML map with boundary and point overlays."""
        data = [sample_census_block]
        data[0]["population"] = 1000

        points = [
            {"lat": 45.515, "lon": -122.675, "name": "Center"},
            {"lat": 45.520, "lon": -122.680},
        ]

        result = create_map(
            data, column="population",
            export_format="html",
            overlay_boundary=sample_geojson_feature,
            overlay_points=points,
        )

        assert result.format == "html"
        assert result.html_content is not None
        assert "Center" in result.html_content

    def test_create_map_html_with_stats(self, sample_census_block):
        """Test HTML map with statistics panel."""
        data = [sample_census_block]
        data[0]["population"] = 1000

        custom_stats = {
            "Total Population": "1,000",
            "Area": "1.5 sq km",
        }
        result = create_map(
            data, column="population",
            export_format="html",
            show_stats=True,
            stats_dict=custom_stats,
        )

        assert result.format == "html"
        assert "Total Population" in result.html_content
        assert "1,000" in result.html_content

    def test_create_map_html_save_to_file(self, sample_census_block, tmp_path):
        """Test saving HTML map to file."""
        data = [sample_census_block]
        data[0]["population"] = 1000

        output_file = tmp_path / "test_map.html"
        result = create_map(
            data, column="population",
            export_format="html",
            save_path=str(output_file),
        )

        assert result.format == "html"
        assert result.file_path is not None
        assert result.file_path.exists()
        content = result.file_path.read_text()
        assert "leaflet" in content.lower()

    def test_create_map_html_all_features(self, sample_census_block, sample_geojson_feature):
        """Test HTML map with all features combined."""
        data = [sample_census_block]
        data[0]["population"] = 1000

        points = [{"lat": 45.515, "lon": -122.675, "name": "Origin"}]
        custom_stats = {"Count": "1", "Value": "1,000"}

        result = create_map(
            data, column="population",
            title="Full Interactive Test",
            basemap="CartoDB.Voyager",
            export_format="html",
            overlay_boundary=sample_geojson_feature,
            overlay_points=points,
            show_stats=True,
            stats_dict=custom_stats,
        )

        assert result.format == "html"
        assert result.html_content is not None
        assert "Full Interactive Test" in result.html_content
        assert "Origin" in result.html_content
        assert "Count" in result.html_content
        assert "leaflet" in result.html_content.lower()


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

    @pytest.mark.external
    @pytest.mark.slow
    def test_get_poi_within_search_area(self, portland_coords):
        """With travel_time, all POIs should fall within the isochrone polygon."""
        from shapely.geometry import Point, shape

        pois = get_poi(portland_coords, travel_time=10, limit=30)
        assert isinstance(pois, list)

        if len(pois) > 0:
            # Recreate the isochrone to verify containment
            iso = create_isochrone(portland_coords, travel_time=10)
            polygon = shape(iso["geometry"])

            for poi in pois:
                point = Point(poi["lon"], poi["lat"])
                assert polygon.contains(point) or polygon.touches(point), (
                    f"POI '{poi.get('name')}' at ({poi['lat']}, {poi['lon']}) "
                    f"is outside the isochrone"
                )

    @pytest.mark.external
    @pytest.mark.slow
    def test_get_poi_travel_time_fields(self, portland_coords):
        """With travel_time, POIs should have travel_time_minutes and travel_distance_km."""
        pois = get_poi(portland_coords, travel_time=10, limit=20)
        assert isinstance(pois, list)

        if len(pois) > 0:
            for poi in pois:
                assert "travel_time_minutes" in poi
                assert "travel_distance_km" in poi

            # Results should be sorted by travel_time_minutes (None at end)
            travel_times = [
                p["travel_time_minutes"] for p in pois
                if p["travel_time_minutes"] is not None
            ]
            assert travel_times == sorted(travel_times)

    @pytest.mark.external
    @pytest.mark.slow
    def test_get_poi_geodesic_without_travel_time(self, portland_coords):
        """Without travel_time, POIs sorted by distance_km, no travel_time_minutes field."""
        pois = get_poi(portland_coords, limit=20)
        assert isinstance(pois, list)

        if len(pois) >= 2:
            distances = [
                p["distance_km"] for p in pois
                if p.get("distance_km") is not None
            ]
            assert distances == sorted(distances)

            # travel_time_minutes should NOT be present
            for poi in pois:
                assert "travel_time_minutes" not in poi

    @pytest.mark.external
    @pytest.mark.slow
    def test_get_poi_address_field_present(self, portland_coords):
        """Every POI should have an 'address' key (may be None)."""
        pois = get_poi(portland_coords, limit=20)
        assert isinstance(pois, list)

        for poi in pois:
            assert "address" in poi


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


class TestImportPOICSV:
    """Test import_poi_csv function."""

    def test_import_csv_basic(self, tmp_path):
        """Test importing a CSV with standard column names."""
        csv_file = tmp_path / "pois.csv"
        csv_file.write_text(
            "name,latitude,longitude,type\n"
            "Library,45.5,-122.6,library\n"
            "Cafe,45.51,-122.61,cafe\n"
        )

        pois = import_poi_csv(str(csv_file))

        assert len(pois) == 2
        assert pois[0]["name"] == "Library"
        assert pois[0]["lat"] == 45.5
        assert pois[0]["lon"] == -122.6
        assert pois[0]["category"] == "library"
        assert pois[1]["name"] == "Cafe"
        assert pois[1]["category"] == "cafe"

    def test_import_csv_custom_fields(self, tmp_path):
        """Test importing a CSV with custom column names."""
        csv_file = tmp_path / "custom.csv"
        csv_file.write_text(
            "loc_name,lat,lng,category\n"
            "Park,45.52,-122.62,park\n"
        )

        pois = import_poi_csv(
            str(csv_file),
            name_field="loc_name",
            lat_field="lat",
            lon_field="lng",
            type_field="category",
        )

        assert len(pois) == 1
        assert pois[0]["name"] == "Park"
        assert pois[0]["lat"] == 45.52
        assert pois[0]["lon"] == -122.62
        assert pois[0]["category"] == "park"

    def test_import_csv_missing_type_field(self, tmp_path):
        """Test that missing type column defaults category to 'unknown'."""
        csv_file = tmp_path / "no_type.csv"
        csv_file.write_text(
            "name,latitude,longitude\n"
            "School,45.53,-122.63\n"
        )

        pois = import_poi_csv(str(csv_file))

        assert len(pois) == 1
        assert pois[0]["category"] == "unknown"

    def test_import_csv_file_not_found(self):
        """Test that a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            import_poi_csv("/nonexistent/path/to/file.csv")

    def test_import_csv_missing_required_columns(self, tmp_path):
        """Test that a CSV missing required columns raises ValueError."""
        csv_file = tmp_path / "bad.csv"
        csv_file.write_text(
            "name,longitude\n"
            "Test,-122.6\n"
        )

        with pytest.raises(ValueError, match="Missing required columns"):
            import_poi_csv(str(csv_file))


class TestGenerateReport:
    """Test generate_report function."""

    def test_generate_report_html_basic(self):
        """Test generating an HTML report from empty data."""
        html = generate_report({})

        assert isinstance(html, str)
        assert "<html>" in html
        assert "</html>" in html

    def test_generate_report_html_with_metadata(self):
        """Test that metadata key/value pairs appear in HTML output."""
        data = {
            "metadata": {
                "travel_time": 15,
                "travel_mode": "drive",
            }
        }
        html = generate_report(data)

        assert "travel_time" in html
        assert "15" in html
        assert "travel_mode" in html
        assert "drive" in html

    def test_generate_report_html_with_locations(self):
        """Test that locations with aggregated stats appear in HTML output."""
        data = {
            "locations": [
                {
                    "location": "Portland, OR",
                    "aggregated": {
                        "population": {"total": 50000, "mean": 1250.5}
                    },
                },
            ]
        }
        html = generate_report(data)

        assert "Portland, OR" in html
        assert "<table" in html
        assert "population" in html

    def test_generate_report_html_with_comparison(self):
        """Test that comparison data with highest/lowest appears in HTML."""
        data = {
            "comparison": {
                "population": {
                    "highest": "Portland, OR",
                    "lowest": "Bend, OR",
                }
            }
        }
        html = generate_report(data)

        assert "Highest" in html
        assert "Portland, OR" in html
        assert "Lowest" in html
        assert "Bend, OR" in html

    def test_generate_report_pdf_raises(self):
        """Test that PDF format raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            generate_report({}, format="pdf")

    def test_generate_report_invalid_format(self):
        """Test that an unsupported format raises ValueError."""
        with pytest.raises(ValueError, match="Report format must be one of"):
            generate_report({}, format="docx")


class TestAnalyzeMultiplePOIs:
    """Test analyze_multiple_pois function with real API calls."""

    @pytest.mark.external
    @pytest.mark.slow
    def test_analyze_single_location(self):
        """Test analysis with a single location returns one entry, no comparison."""
        results = analyze_multiple_pois(
            ["Portland, OR"],
            travel_time=10,
        )

        assert len(results["locations"]) == 1
        assert "comparison" not in results
        assert results["metadata"]["travel_time"] == 10

    @pytest.mark.external
    @pytest.mark.slow
    def test_analyze_multiple_locations(self):
        """Test analysis with two locations returns comparison data."""
        results = analyze_multiple_pois(
            ["Portland, OR", "Seattle, WA"],
            travel_time=10,
            variables=["population"],
        )

        assert len(results["locations"]) == 2
        assert "comparison" in results
        assert "population" in results["comparison"]
        assert "highest" in results["comparison"]["population"]
        assert "lowest" in results["comparison"]["population"]

    @pytest.mark.external
    @pytest.mark.slow
    def test_analyze_default_variables(self):
        """Test that default variables is ['population'] when none specified."""
        results = analyze_multiple_pois(
            ["Portland, OR"],
            travel_time=10,
        )

        assert results["metadata"]["variables"] == ["population"]

    @pytest.mark.external
    @pytest.mark.slow
    def test_analyze_compare_false(self):
        """Test that compare=False omits comparison even with multiple locations."""
        results = analyze_multiple_pois(
            ["Portland, OR", "Seattle, WA"],
            travel_time=10,
            compare=False,
        )

        assert len(results["locations"]) == 2
        assert "comparison" not in results


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
