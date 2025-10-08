"""Comprehensive tests for public API functions.

Tests the main user-facing API functions in api.py with focus on
create_isochrone, get_census_data, and get_census_blocks.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import geopandas as gpd
from shapely.geometry import Point, Polygon

from socialmapper.api import (
    create_isochrone,
    get_census_blocks,
    get_census_data,
    _resolve_geoids_from_location,
    create_map,
    _convert_data_to_geodataframe,
    get_poi,
    _create_search_area,
    _validate_and_filter_pois,
    _calculate_poi_distances,
    import_poi_csv,
    analyze_multiple_pois,
    _create_comparison_analysis,
    generate_report
)
import pandas as pd


class TestCreateIsochrone:
    """Test create_isochrone() - the flagship function."""

    @patch('socialmapper.isochrone.create_isochrone_from_poi')
    @patch('socialmapper.api.resolve_coordinates')
    def test_create_with_string_location(self, mock_resolve, mock_create_iso):
        """Test creating isochrone with string location."""
        # Mock coordinate resolution
        mock_resolve.return_value = ((45.5152, -122.6784), "Portland, OR")

        # Mock isochrone creation
        mock_gdf = gpd.GeoDataFrame({
            'geometry': [Polygon([
                (-122.7, 45.5), (-122.6, 45.5),
                (-122.6, 45.6), (-122.7, 45.6),
                (-122.7, 45.5)
            ])]
        }, crs="EPSG:4326")
        mock_create_iso.return_value = mock_gdf

        result = create_isochrone("Portland, OR", travel_time=15, travel_mode="drive")

        # Verify structure
        assert result["type"] == "Feature"
        assert "geometry" in result
        assert "properties" in result

        # Verify properties
        props = result["properties"]
        assert props["location"] == "Portland, OR"
        assert props["travel_time"] == 15
        assert props["travel_mode"] == "drive"
        assert "area_sq_km" in props
        assert isinstance(props["area_sq_km"], (int, float))

        # Verify resolve_coordinates was called correctly
        mock_resolve.assert_called_once_with("Portland, OR")

    @patch('socialmapper.isochrone.create_isochrone_from_poi')
    @patch('socialmapper.api.resolve_coordinates')
    def test_create_with_tuple_location(self, mock_resolve, mock_create_iso):
        """Test creating isochrone with coordinate tuple."""
        # Mock coordinate resolution
        mock_resolve.return_value = ((37.7749, -122.4194), "37.7749, -122.4194")

        # Mock isochrone creation
        mock_gdf = gpd.GeoDataFrame({
            'geometry': [Polygon([
                (-122.5, 37.7), (-122.4, 37.7),
                (-122.4, 37.8), (-122.5, 37.8),
                (-122.5, 37.7)
            ])]
        }, crs="EPSG:4326")
        mock_create_iso.return_value = mock_gdf

        result = create_isochrone(
            (37.7749, -122.4194),
            travel_time=20,
            travel_mode="walk"
        )

        assert result["type"] == "Feature"
        assert result["properties"]["travel_time"] == 20
        assert result["properties"]["travel_mode"] == "walk"

    @patch('socialmapper.isochrone.create_isochrone_from_poi')
    @patch('socialmapper.api.resolve_coordinates')
    def test_travel_mode_drive(self, mock_resolve, mock_create_iso):
        """Test isochrone with drive mode."""
        mock_resolve.return_value = ((40.7128, -74.0060), "New York, NY")
        mock_gdf = gpd.GeoDataFrame({
            'geometry': [Polygon([
                (-74.1, 40.7), (-74.0, 40.7),
                (-74.0, 40.8), (-74.1, 40.8),
                (-74.1, 40.7)
            ])]
        }, crs="EPSG:4326")
        mock_create_iso.return_value = mock_gdf

        result = create_isochrone("New York, NY", travel_time=15, travel_mode="drive")

        # Verify TravelMode.DRIVE was used
        assert mock_create_iso.called
        call_kwargs = mock_create_iso.call_args[1]
        assert call_kwargs["travel_mode"].name == "DRIVE"

    @patch('socialmapper.isochrone.create_isochrone_from_poi')
    @patch('socialmapper.api.resolve_coordinates')
    def test_travel_mode_walk(self, mock_resolve, mock_create_iso):
        """Test isochrone with walk mode."""
        mock_resolve.return_value = ((47.6062, -122.3321), "Seattle, WA")
        mock_gdf = gpd.GeoDataFrame({
            'geometry': [Polygon([
                (-122.4, 47.5), (-122.3, 47.5),
                (-122.3, 47.6), (-122.4, 47.6),
                (-122.4, 47.5)
            ])]
        }, crs="EPSG:4326")
        mock_create_iso.return_value = mock_gdf

        result = create_isochrone("Seattle, WA", travel_time=10, travel_mode="walk")

        call_kwargs = mock_create_iso.call_args[1]
        assert call_kwargs["travel_mode"].name == "WALK"

    @patch('socialmapper.isochrone.create_isochrone_from_poi')
    @patch('socialmapper.api.resolve_coordinates')
    def test_travel_mode_bike(self, mock_resolve, mock_create_iso):
        """Test isochrone with bike mode."""
        mock_resolve.return_value = ((42.3601, -71.0589), "Boston, MA")
        mock_gdf = gpd.GeoDataFrame({
            'geometry': [Polygon([
                (-71.1, 42.3), (-71.0, 42.3),
                (-71.0, 42.4), (-71.1, 42.4),
                (-71.1, 42.3)
            ])]
        }, crs="EPSG:4326")
        mock_create_iso.return_value = mock_gdf

        result = create_isochrone("Boston, MA", travel_time=15, travel_mode="bike")

        call_kwargs = mock_create_iso.call_args[1]
        assert call_kwargs["travel_mode"].name == "BIKE"

    @patch('socialmapper.isochrone.create_isochrone_from_poi')
    @patch('socialmapper.api.resolve_coordinates')
    def test_different_travel_times(self, mock_resolve, mock_create_iso):
        """Test isochrone with various travel times."""
        mock_resolve.return_value = ((33.4484, -112.0740), "Phoenix, AZ")
        mock_gdf = gpd.GeoDataFrame({
            'geometry': [Polygon([
                (-112.2, 33.4), (-112.0, 33.4),
                (-112.0, 33.5), (-112.2, 33.5),
                (-112.2, 33.4)
            ])]
        }, crs="EPSG:4326")
        mock_create_iso.return_value = mock_gdf

        # Test various valid travel times
        for travel_time in [5, 15, 30, 60, 120]:
            result = create_isochrone("Phoenix, AZ", travel_time=travel_time)
            assert result["properties"]["travel_time"] == travel_time

            call_kwargs = mock_create_iso.call_args[1]
            assert call_kwargs["travel_time_limit"] == travel_time

    def test_invalid_travel_time_zero(self):
        """Test that zero travel time raises error."""
        with pytest.raises(ValueError, match="Travel time must be between"):
            create_isochrone("Denver, CO", travel_time=0)

    def test_invalid_travel_time_negative(self):
        """Test that negative travel time raises error."""
        with pytest.raises(ValueError, match="Travel time must be between"):
            create_isochrone("Denver, CO", travel_time=-5)

    def test_invalid_travel_time_too_large(self):
        """Test that travel time > 120 raises error."""
        with pytest.raises(ValueError, match="Travel time must be between"):
            create_isochrone("Denver, CO", travel_time=150)

    def test_invalid_travel_mode(self):
        """Test that invalid travel mode raises error."""
        with pytest.raises(ValueError, match="Travel mode must be one of"):
            create_isochrone("Denver, CO", travel_mode="flying")

    @patch('socialmapper.helpers.resolve_coordinates')
    def test_location_geocoding_failure(self, mock_resolve):
        """Test handling of geocoding failures."""
        mock_resolve.side_effect = ValueError("Could not geocode location")

        with pytest.raises(ValueError, match="Could not geocode"):
            create_isochrone("Invalid Location XYZ123")

    @patch('socialmapper.isochrone.create_isochrone_from_poi')
    @patch('socialmapper.api.resolve_coordinates')
    def test_poi_structure_passed_to_isochrone(self, mock_resolve, mock_create_iso):
        """Test that POI dict is correctly constructed."""
        mock_resolve.return_value = ((39.7392, -104.9903), "Denver, CO")
        mock_gdf = gpd.GeoDataFrame({
            'geometry': [Polygon([
                (-105.0, 39.7), (-104.9, 39.7),
                (-104.9, 39.8), (-105.0, 39.8),
                (-105.0, 39.7)
            ])]
        }, crs="EPSG:4326")
        mock_create_iso.return_value = mock_gdf

        create_isochrone("Denver, CO", travel_time=15)

        # Verify POI structure
        call_args = mock_create_iso.call_args
        poi = call_args[1]["poi"]

        assert abs(poi["lat"] - 39.7392) < 0.001  # Approximate match
        assert abs(poi["lon"] - -104.9903) < 0.001
        assert poi["tags"]["name"] == "Denver, CO"
        assert poi["id"] == "api_location"

    @patch('socialmapper.isochrone.create_isochrone_from_poi')
    @patch('socialmapper.api.resolve_coordinates')
    def test_default_parameters(self, mock_resolve, mock_create_iso):
        """Test default travel_time and travel_mode."""
        mock_resolve.return_value = ((41.8781, -87.6298), "Chicago, IL")
        mock_gdf = gpd.GeoDataFrame({
            'geometry': [Polygon([
                (-87.7, 41.8), (-87.6, 41.8),
                (-87.6, 41.9), (-87.7, 41.9),
                (-87.7, 41.8)
            ])]
        }, crs="EPSG:4326")
        mock_create_iso.return_value = mock_gdf

        # Call with defaults
        result = create_isochrone("Chicago, IL")

        # Check defaults
        assert result["properties"]["travel_time"] == 15
        assert result["properties"]["travel_mode"] == "drive"

    @patch('socialmapper.isochrone.create_isochrone_from_poi')
    @patch('socialmapper.api.resolve_coordinates')
    def test_geometry_is_valid_geojson(self, mock_resolve, mock_create_iso):
        """Test that geometry conforms to GeoJSON spec."""
        mock_resolve.return_value = ((29.7604, -95.3698), "Houston, TX")
        mock_polygon = Polygon([
            (-95.4, 29.7), (-95.3, 29.7),
            (-95.3, 29.8), (-95.4, 29.8),
            (-95.4, 29.7)
        ])
        mock_gdf = gpd.GeoDataFrame({'geometry': [mock_polygon]}, crs="EPSG:4326")
        mock_create_iso.return_value = mock_gdf

        result = create_isochrone("Houston, TX")

        # Verify GeoJSON geometry structure
        geom = result["geometry"]
        assert "type" in geom
        assert geom["type"] == "Polygon"
        assert "coordinates" in geom
        # Coordinates can be list or tuple in __geo_interface__
        assert isinstance(geom["coordinates"], (list, tuple))

    @patch('socialmapper.isochrone.create_isochrone_from_poi')
    @patch('socialmapper.api.resolve_coordinates')
    def test_area_calculation(self, mock_resolve, mock_create_iso):
        """Test that area_sq_km is calculated and positive."""
        mock_resolve.return_value = ((33.7490, -84.3880), "Atlanta, GA")
        mock_gdf = gpd.GeoDataFrame({
            'geometry': [Polygon([
                (-84.4, 33.7), (-84.3, 33.7),
                (-84.3, 33.8), (-84.4, 33.8),
                (-84.4, 33.7)
            ])]
        }, crs="EPSG:4326")
        mock_create_iso.return_value = mock_gdf

        result = create_isochrone("Atlanta, GA")

        area = result["properties"]["area_sq_km"]
        assert isinstance(area, (int, float))
        assert area > 0

    @patch('socialmapper.isochrone.create_isochrone_from_poi')
    @patch('socialmapper.api.resolve_coordinates')
    def test_save_file_parameter_passed(self, mock_resolve, mock_create_iso):
        """Test that save_file=False is passed to isochrone generator."""
        mock_resolve.return_value = ((32.7157, -117.1611), "San Diego, CA")
        mock_gdf = gpd.GeoDataFrame({
            'geometry': [Polygon([
                (-117.2, 32.7), (-117.1, 32.7),
                (-117.1, 32.8), (-117.2, 32.8),
                (-117.2, 32.7)
            ])]
        }, crs="EPSG:4326")
        mock_create_iso.return_value = mock_gdf

        create_isochrone("San Diego, CA")

        # Verify save_file=False was passed
        call_kwargs = mock_create_iso.call_args[1]
        assert call_kwargs["save_file"] is False


class TestGetCensusBlocks:
    """Test get_census_blocks() function."""

    @patch('socialmapper._census.fetch_block_groups_for_area')
    def test_with_polygon_input(self, mock_fetch):
        """Test getting census blocks with polygon input."""
        # Mock block groups response
        mock_fetch.return_value = [
            {
                "geoid": "060750201001",
                "state_fips": "06",
                "county_fips": "075",
                "tract": "020100",
                "block_group": "1",
                "geometry": {"type": "Polygon", "coordinates": [[]]},
                "area_sq_km": 0.5
            }
        ]

        polygon = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-122.4, 37.7], [-122.3, 37.7],
                    [-122.3, 37.8], [-122.4, 37.8],
                    [-122.4, 37.7]
                ]]
            }
        }

        result = get_census_blocks(polygon=polygon)

        assert len(result) == 1
        assert result[0]["geoid"] == "060750201001"
        assert mock_fetch.called

    @patch('socialmapper._census.fetch_block_groups_for_area')
    def test_with_location_and_radius(self, mock_fetch):
        """Test getting census blocks with location and radius."""
        mock_fetch.return_value = [
            {
                "geoid": "371830501001",
                "state_fips": "37",
                "county_fips": "183",
                "tract": "050100",
                "block_group": "1",
                "geometry": {"type": "Polygon", "coordinates": [[]]},
                "area_sq_km": 0.8
            }
        ]

        result = get_census_blocks(location=(35.7796, -78.6382), radius_km=3)

        assert len(result) == 1
        assert result[0]["geoid"] == "371830501001"

    def test_neither_polygon_nor_location(self):
        """Test error when neither polygon nor location provided."""
        with pytest.raises(ValueError, match="Must provide either polygon or location"):
            get_census_blocks()

    def test_both_polygon_and_location(self):
        """Test error when both polygon and location provided."""
        polygon = {"type": "Feature", "geometry": {}}
        location = (37.7749, -122.4194)

        with pytest.raises(ValueError, match="Provide either polygon or location, not both"):
            get_census_blocks(polygon=polygon, location=location)


class TestGetCensusData:
    """Test get_census_data() function."""

    @patch('socialmapper._census.fetch_census_data')
    @patch('socialmapper.api._resolve_geoids_from_location')
    @patch('socialmapper._census.normalize_variable_names')
    def test_with_geoid_list(self, mock_normalize, mock_resolve, mock_fetch):
        """Test getting census data with list of GEOIDs."""
        mock_normalize.return_value = ["B01003_001E"]
        mock_resolve.return_value = ["060750201001"]
        mock_fetch.return_value = {
            "060750201001": {"B01003_001E": 1234}
        }

        result = get_census_data(
            location=["060750201001"],
            variables=["population"]
        )

        assert "060750201001" in result
        assert result["060750201001"]["B01003_001E"] == 1234

    @patch('socialmapper._census.fetch_census_data')
    @patch('socialmapper.api._resolve_geoids_from_location')
    @patch('socialmapper._census.normalize_variable_names')
    def test_with_coordinate_tuple(self, mock_normalize, mock_resolve, mock_fetch):
        """Test getting census data with coordinate tuple."""
        mock_normalize.return_value = ["B01003_001E"]
        mock_resolve.return_value = ["371830501001"]
        mock_fetch.return_value = {
            "371830501001": {"B01003_001E": 5678}
        }

        result = get_census_data(
            location=(35.7796, -78.6382),
            variables=["population"]
        )

        # For tuple input, should return single dict not nested
        assert "B01003_001E" in result
        assert result["B01003_001E"] == 5678

    @patch('socialmapper._census.fetch_census_data')
    @patch('socialmapper.api._resolve_geoids_from_location')
    @patch('socialmapper._census.normalize_variable_names')
    def test_with_polygon_dict(self, mock_normalize, mock_resolve, mock_fetch):
        """Test getting census data with polygon/isochrone dict."""
        mock_normalize.return_value = ["B01003_001E", "B19013_001E"]
        mock_resolve.return_value = ["060750201001", "060750201002"]
        mock_fetch.return_value = {
            "060750201001": {"B01003_001E": 1000, "B19013_001E": 50000},
            "060750201002": {"B01003_001E": 2000, "B19013_001E": 60000}
        }

        polygon = {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[]]}
        }

        result = get_census_data(
            location=polygon,
            variables=["population", "median_income"]
        )

        assert len(result) == 2
        assert "060750201001" in result
        assert "060750201002" in result


class TestResolveGeoidsFromLocation:
    """Test _resolve_geoids_from_location() helper."""

    def test_with_list_of_geoids(self):
        """Test that list of GEOIDs passes through unchanged."""
        geoids = ["060750201001", "060750201002"]
        result = _resolve_geoids_from_location(geoids)
        assert result == geoids

    @patch('socialmapper.api.get_census_blocks')
    def test_with_polygon_dict(self, mock_get_blocks):
        """Test resolving polygon to GEOIDs."""
        mock_get_blocks.return_value = [
            {"geoid": "371830501001"},
            {"geoid": "371830501002"}
        ]

        polygon = {"type": "Feature", "geometry": {}}
        result = _resolve_geoids_from_location(polygon)

        assert len(result) == 2
        assert "371830501001" in result
        assert "371830501002" in result

    @patch('socialmapper._geocoding.get_census_geography')
    def test_with_coordinate_tuple(self, mock_get_geo):
        """Test resolving coordinates to GEOID."""
        mock_get_geo.return_value = {"geoid": "060750201001"}

        result = _resolve_geoids_from_location((37.7749, -122.4194))

        assert len(result) == 1
        assert result[0] == "060750201001"

    @patch('socialmapper._geocoding.get_census_geography')
    def test_with_coordinate_tuple_no_geography(self, mock_get_geo):
        """Test error when coordinates can't be geocoded."""
        mock_get_geo.return_value = None

        with pytest.raises(ValueError, match="Could not identify census geography"):
            _resolve_geoids_from_location((0, 0))

    def test_with_invalid_type(self):
        """Test error with invalid location type."""
        with pytest.raises(ValueError, match="Location must be"):
            _resolve_geoids_from_location("invalid string")


class TestCreateMap:
    """Test create_map() visualization function."""

    @patch('socialmapper.api._create_image_map')
    def test_create_map_png_format(self, mock_image_map):
        """Test creating map with PNG format."""
        mock_image_map.return_value = b'fake_png_data'

        data = [
            {"geometry": Point(0, 0).__geo_interface__, "population": 100},
            {"geometry": Point(1, 1).__geo_interface__, "population": 200}
        ]

        result = create_map(data, "population", export_format="png")

        assert result == b'fake_png_data'
        mock_image_map.assert_called_once()
        assert mock_image_map.call_args[0][1] == "population"  # column
        assert mock_image_map.call_args[0][4] == "png"  # format

    @patch('socialmapper.api._create_image_map')
    def test_create_map_pdf_format(self, mock_image_map):
        """Test creating map with PDF format."""
        mock_image_map.return_value = b'fake_pdf_data'

        data = gpd.GeoDataFrame({
            'geometry': [Point(0, 0), Point(1, 1)],
            'value': [10, 20]
        }, crs="EPSG:4326")

        result = create_map(data, "value", export_format="pdf")

        assert result == b'fake_pdf_data'
        assert mock_image_map.call_args[0][4] == "pdf"

    @patch('socialmapper.api._create_image_map')
    def test_create_map_svg_format(self, mock_image_map):
        """Test creating map with SVG format."""
        mock_image_map.return_value = b'<svg>fake_svg</svg>'

        data = gpd.GeoDataFrame({
            'geometry': [Point(0, 0)],
            'metric': [42]
        }, crs="EPSG:4326")

        result = create_map(data, "metric", export_format="svg")

        assert result == b'<svg>fake_svg</svg>'
        assert mock_image_map.call_args[0][4] == "svg"

    def test_create_map_geojson_format(self):
        """Test creating map with GeoJSON format."""
        data = [
            {"geometry": Point(0, 0).__geo_interface__, "score": 5},
            {"geometry": Point(1, 1).__geo_interface__, "score": 10}
        ]

        result = create_map(data, "score", export_format="geojson")

        assert isinstance(result, dict)
        assert "features" in result
        assert len(result["features"]) == 2

    @patch('geopandas.GeoDataFrame.to_file')
    def test_create_map_shapefile_format(self, mock_to_file):
        """Test creating map with shapefile format."""
        data = [
            {"geometry": Point(0, 0).__geo_interface__, "rating": 1}
        ]

        result = create_map(
            data, 
            "rating",
            save_path="/tmp/test_output.shp",
            export_format="shapefile"
        )

        assert result is None
        mock_to_file.assert_called_once()
        assert mock_to_file.call_args[1]['driver'] == 'ESRI Shapefile'

    def test_create_map_shapefile_without_save_path(self):
        """Test that shapefile format requires save_path."""
        data = [{"geometry": Point(0, 0).__geo_interface__, "value": 1}]

        with pytest.raises(ValueError, match="save_path is required for shapefile export"):
            create_map(data, "value", export_format="shapefile")

    @patch('socialmapper.api._create_image_map')
    def test_create_map_with_title(self, mock_image_map):
        """Test creating map with custom title."""
        mock_image_map.return_value = b'map_data'

        data = [{"geometry": Point(0, 0).__geo_interface__, "count": 5}]

        create_map(data, "count", title="Test Map Title", export_format="png")

        assert mock_image_map.call_args[0][2] == "Test Map Title"  # title parameter

    @patch('socialmapper.api._create_image_map')
    def test_create_map_with_save_path(self, mock_image_map):
        """Test creating map with save path."""
        mock_image_map.return_value = None

        data = [{"geometry": Point(0, 0).__geo_interface__, "data": 99}]

        result = create_map(
            data,
            "data",
            save_path="/tmp/output.png",
            export_format="png"
        )

        assert result is None
        assert mock_image_map.call_args[0][3] == "/tmp/output.png"  # save_path

    def test_create_map_list_input(self):
        """Test create_map with list of dicts input."""
        data = [
            {"geometry": {"type": "Point", "coordinates": [0, 0]}, "val": 1},
            {"geometry": {"type": "Point", "coordinates": [1, 1]}, "val": 2}
        ]

        result = create_map(data, "val", export_format="geojson")

        assert isinstance(result, dict)
        assert len(result["features"]) == 2

    def test_create_map_dataframe_input(self):
        """Test create_map with pandas DataFrame input."""
        df = pd.DataFrame({
            'geometry': [Point(0, 0), Point(1, 1)],
            'metric': [100, 200]
        })

        result = create_map(df, "metric", export_format="geojson")

        assert isinstance(result, dict)
        assert len(result["features"]) == 2

    def test_create_map_geodataframe_input(self):
        """Test create_map with GeoDataFrame input."""
        gdf = gpd.GeoDataFrame({
            'geometry': [Point(0, 0), Point(1, 1)],
            'population': [1000, 2000]
        }, crs="EPSG:4326")

        result = create_map(gdf, "population", export_format="geojson")

        assert isinstance(result, dict)
        assert len(result["features"]) == 2

    def test_create_map_column_not_found(self):
        """Test error when specified column doesn't exist."""
        data = [{"geometry": Point(0, 0).__geo_interface__, "value": 1}]

        with pytest.raises(ValueError, match="Column 'nonexistent' not found"):
            create_map(data, "nonexistent", export_format="png")

    def test_create_map_invalid_export_format(self):
        """Test error with invalid export format."""
        data = [{"geometry": Point(0, 0).__geo_interface__, "value": 1}]

        with pytest.raises(ValueError, match="Export format must be one of"):
            create_map(data, "value", export_format="invalid_format")

    def test_create_map_default_format(self):
        """Test that default export format is PNG."""
        with patch('socialmapper.api._create_image_map') as mock_image:
            mock_image.return_value = b'data'
            data = [{"geometry": Point(0, 0).__geo_interface__, "val": 1}]

            create_map(data, "val")  # No format specified

            assert mock_image.call_args[0][4] == "png"


class TestConvertDataToGeoDataFrame:
    """Test _convert_data_to_geodataframe() helper function."""

    def test_convert_list_of_dicts(self):
        """Test converting list of dicts to GeoDataFrame."""
        data = [
            {"geometry": Point(0, 0), "value": 10},
            {"geometry": Point(1, 1), "value": 20}
        ]

        result = _convert_data_to_geodataframe(data)

        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) == 2
        assert "value" in result.columns
        assert result.crs == "EPSG:4326"

    def test_convert_list_with_geojson_geometry(self):
        """Test converting list with GeoJSON geometry dicts."""
        data = [
            {"geometry": {"type": "Point", "coordinates": [0, 0]}, "name": "A"},
            {"geometry": {"type": "Point", "coordinates": [1, 1]}, "name": "B"}
        ]

        result = _convert_data_to_geodataframe(data)

        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) == 2
        assert "name" in result.columns

    def test_convert_pandas_dataframe(self):
        """Test converting pandas DataFrame to GeoDataFrame."""
        df = pd.DataFrame({
            'geometry': [Point(0, 0), Point(1, 1)],
            'population': [100, 200]
        })

        result = _convert_data_to_geodataframe(df)

        assert isinstance(result, gpd.GeoDataFrame)
        assert "population" in result.columns
        assert result.crs == "EPSG:4326"

    def test_convert_geodataframe_passthrough(self):
        """Test that GeoDataFrame passes through unchanged."""
        gdf = gpd.GeoDataFrame({
            'geometry': [Point(0, 0)],
            'value': [42]
        }, crs="EPSG:4326")

        result = _convert_data_to_geodataframe(gdf)

        # Function returns the same GeoDataFrame
        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) == len(gdf)
        assert "value" in result.columns

    def test_convert_list_missing_geometry(self):
        """Test error when list items missing geometry field."""
        data = [
            {"value": 10},  # Missing geometry
            {"geometry": Point(1, 1), "value": 20}
        ]

        with pytest.raises(ValueError, match="Each item must have a 'geometry' field"):
            _convert_data_to_geodataframe(data)

    def test_convert_dataframe_missing_geometry(self):
        """Test error when DataFrame missing geometry column."""
        df = pd.DataFrame({
            'value': [10, 20]  # No geometry column
        })

        with pytest.raises(ValueError, match="DataFrame must have a 'geometry' column"):
            _convert_data_to_geodataframe(df)

    def test_convert_invalid_data_type(self):
        """Test error with invalid data type."""
        with pytest.raises(ValueError, match="Data must be a list of dicts"):
            _convert_data_to_geodataframe("invalid string")

    def test_convert_preserves_attributes(self):
        """Test that all non-geometry attributes are preserved."""
        data = [
            {
                "geometry": Point(0, 0),
                "name": "Location A",
                "value": 100,
                "category": "Type1"
            }
        ]

        result = _convert_data_to_geodataframe(data)

        assert "name" in result.columns
        assert "value" in result.columns
        assert "category" in result.columns
        assert result["name"].iloc[0] == "Location A"
        assert result["value"].iloc[0] == 100


class TestGetPoi:
    """Test get_poi() function."""

    @patch('socialmapper._osm.query_pois')
    @patch('socialmapper.api.resolve_coordinates')
    def test_get_poi_with_string_location(self, mock_resolve, mock_query):
        """Test getting POIs with string location."""
        mock_resolve.return_value = ((47.6062, -122.3321), "Seattle, WA")
        mock_query.return_value = [
            {
                "name": "Coffee Shop",
                "category": "cafe",
                "lat": 47.6065,
                "lon": -122.3330,
                "tags": {"amenity": "cafe"}
            },
            {
                "name": "Restaurant",
                "category": "restaurant",
                "lat": 47.6070,
                "lon": -122.3340,
                "tags": {"amenity": "restaurant"}
            }
        ]

        result = get_poi("Seattle, WA", categories=["cafe", "restaurant"])

        assert len(result) == 2
        assert result[0]["name"] == "Coffee Shop"
        assert "distance_km" in result[0]
        mock_resolve.assert_called_once_with("Seattle, WA")

    @patch('socialmapper._osm.query_pois')
    @patch('socialmapper.api.resolve_coordinates')
    def test_get_poi_with_coordinate_tuple(self, mock_resolve, mock_query):
        """Test getting POIs with coordinate tuple."""
        mock_resolve.return_value = ((37.7749, -122.4194), "37.7749, -122.4194")
        mock_query.return_value = [
            {
                "name": "Park",
                "category": "park",
                "lat": 37.7750,
                "lon": -122.4190,
                "tags": {"leisure": "park"}
            }
        ]

        result = get_poi((37.7749, -122.4194))

        assert len(result) == 1
        assert result[0]["name"] == "Park"

    @patch('socialmapper._osm.query_pois')
    @patch('socialmapper.api.resolve_coordinates')
    def test_get_poi_with_categories(self, mock_resolve, mock_query):
        """Test POI filtering by categories."""
        mock_resolve.return_value = ((40.7128, -74.0060), "New York, NY")
        mock_query.return_value = [
            {
                "name": "School A",
                "category": "school",
                "lat": 40.7130,
                "lon": -74.0065,
                "tags": {"amenity": "school"}
            }
        ]

        result = get_poi("New York, NY", categories=["school"])

        # Verify categories were passed to query_pois
        assert mock_query.call_args[0][1] == ["school"]

    @patch('socialmapper.api.create_isochrone')
    @patch('socialmapper._osm.query_pois')
    @patch('socialmapper.api.resolve_coordinates')
    def test_get_poi_with_travel_time(self, mock_resolve, mock_query, mock_isochrone):
        """Test POI search using travel time (isochrone)."""
        mock_resolve.return_value = ((42.3601, -71.0589), "Boston, MA")
        mock_isochrone.return_value = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-71.1, 42.3], [-71.0, 42.3],
                    [-71.0, 42.4], [-71.1, 42.4],
                    [-71.1, 42.3]
                ]]
            }
        }
        mock_query.return_value = [
            {
                "name": "Library",
                "category": "library",
                "lat": 42.3605,
                "lon": -71.0590,
                "tags": {"amenity": "library"}
            }
        ]

        result = get_poi("Boston, MA", travel_time=15)

        # Verify create_isochrone was called
        mock_isochrone.assert_called_once()
        assert mock_isochrone.call_args[1]["travel_time"] == 15

    @patch('socialmapper.api.create_circular_geometry')
    @patch('socialmapper._osm.query_pois')
    @patch('socialmapper.api.resolve_coordinates')
    def test_get_poi_without_travel_time(self, mock_resolve, mock_query, mock_circular):
        """Test POI search using default radius."""
        mock_resolve.return_value = ((33.4484, -112.0740), "Phoenix, AZ")
        mock_circular.return_value = Polygon([
            (-112.1, 33.4), (-112.0, 33.4),
            (-112.0, 33.5), (-112.1, 33.5),
            (-112.1, 33.4)
        ])
        mock_query.return_value = [
            {
                "name": "Hospital",
                "category": "hospital",
                "lat": 33.4490,
                "lon": -112.0745,
                "tags": {"amenity": "hospital"}
            }
        ]

        result = get_poi("Phoenix, AZ")

        # Verify circular geometry was created (no travel_time)
        mock_circular.assert_called_once()

    @patch('socialmapper._osm.query_pois')
    @patch('socialmapper.api.resolve_coordinates')
    def test_get_poi_limit_parameter(self, mock_resolve, mock_query):
        """Test limiting number of returned POIs."""
        mock_resolve.return_value = ((39.7392, -104.9903), "Denver, CO")
        # Create 10 POIs
        mock_pois = [
            {
                "name": f"POI {i}",
                "category": "restaurant",
                "lat": 39.7392 + (i * 0.001),
                "lon": -104.9903,
                "tags": {}
            }
            for i in range(10)
        ]
        mock_query.return_value = mock_pois

        result = get_poi("Denver, CO", limit=5)

        assert len(result) == 5

    @patch('socialmapper._validation.validate_coordinates')
    @patch('socialmapper._osm.query_pois')
    @patch('socialmapper.api.resolve_coordinates')
    def test_get_poi_validate_coords_true(self, mock_resolve, mock_query, mock_validate):
        """Test POI validation with validate_coords=True."""
        mock_resolve.return_value = ((47.6062, -122.3321), "Seattle, WA")
        mock_query.return_value = [
            {
                "name": "Valid POI",
                "category": "cafe",
                "lat": 47.6065,
                "lon": -122.3330,
                "tags": {}
            },
            {
                "name": "Invalid POI",
                "category": "cafe",
                "lat": 999.0,  # Invalid
                "lon": -122.3330,
                "tags": {}
            }
        ]

        # First call succeeds, second raises ValueError
        mock_validate.side_effect = [
            (47.6065, -122.3330),  # Valid
            ValueError("Invalid coordinates")  # Invalid
        ]

        result = get_poi("Seattle, WA", validate_coords=True)

        # Only valid POI should be returned
        assert len(result) == 1
        assert result[0]["name"] == "Valid POI"

    @patch('socialmapper._osm.query_pois')
    @patch('socialmapper.api.resolve_coordinates')
    def test_get_poi_validate_coords_false(self, mock_resolve, mock_query):
        """Test POI validation with validate_coords=False."""
        mock_resolve.return_value = ((47.6062, -122.3321), "Seattle, WA")
        mock_query.return_value = [
            {
                "name": "POI 1",
                "category": "cafe",
                "lat": 47.6065,
                "lon": -122.3330,
                "tags": {}
            },
            {
                "name": "POI 2",
                "category": "cafe",
                "lat": 47.6070,
                "lon": -122.3340,
                "tags": {}
            }
        ]

        result = get_poi("Seattle, WA", validate_coords=False)

        # All POIs should be returned
        assert len(result) == 2

    @patch('socialmapper._osm.query_pois')
    @patch('socialmapper.api.resolve_coordinates')
    def test_get_poi_sorted_by_distance(self, mock_resolve, mock_query):
        """Test that POIs are sorted by distance from origin."""
        mock_resolve.return_value = ((47.6062, -122.3321), "Seattle, WA")
        mock_query.return_value = [
            {
                "name": "Far POI",
                "category": "cafe",
                "lat": 47.6100,  # Further away
                "lon": -122.3400,
                "tags": {}
            },
            {
                "name": "Near POI",
                "category": "cafe",
                "lat": 47.6063,  # Closer
                "lon": -122.3322,
                "tags": {}
            }
        ]

        result = get_poi("Seattle, WA")

        # Nearest POI should be first
        assert result[0]["name"] == "Near POI"
        assert result[1]["name"] == "Far POI"
        assert result[0]["distance_km"] < result[1]["distance_km"]

    def test_get_poi_invalid_travel_time(self):
        """Test error with invalid travel time."""
        with pytest.raises(ValueError, match="Travel time must be between"):
            get_poi("Seattle, WA", travel_time=0)

    def test_get_poi_invalid_travel_time_negative(self):
        """Test error with negative travel time."""
        with pytest.raises(ValueError, match="Travel time must be between"):
            get_poi("Seattle, WA", travel_time=-10)

    def test_get_poi_invalid_travel_time_too_large(self):
        """Test error with travel time exceeding maximum."""
        with pytest.raises(ValueError, match="Travel time must be between"):
            get_poi("Seattle, WA", travel_time=150)

    @patch('socialmapper._osm.query_pois')
    @patch('socialmapper.api.resolve_coordinates')
    def test_get_poi_empty_results(self, mock_resolve, mock_query):
        """Test handling of empty POI results."""
        mock_resolve.return_value = ((47.6062, -122.3321), "Seattle, WA")
        mock_query.return_value = []

        result = get_poi("Seattle, WA")

        assert len(result) == 0

    @patch('socialmapper._osm.query_pois')
    @patch('socialmapper.api.resolve_coordinates')
    def test_get_poi_default_parameters(self, mock_resolve, mock_query):
        """Test get_poi with default parameters."""
        mock_resolve.return_value = ((47.6062, -122.3321), "Seattle, WA")
        mock_query.return_value = [
            {
                "name": "POI",
                "category": "cafe",
                "lat": 47.6065,
                "lon": -122.3330,
                "tags": {}
            }
        ]

        result = get_poi("Seattle, WA")

        # Defaults: no categories filter, no travel_time, limit=100, validate_coords=True
        assert len(result) <= 100
        assert mock_query.call_args[0][1] is None  # categories=None

    @patch('socialmapper._validation.validate_coordinates')
    @patch('socialmapper._osm.query_pois')
    @patch('socialmapper.api.resolve_coordinates')
    def test_get_poi_filters_null_island(self, mock_resolve, mock_query, mock_validate):
        """Test that null island (0,0) coordinates are filtered out."""
        mock_resolve.return_value = ((47.6062, -122.3321), "Seattle, WA")
        mock_query.return_value = [
            {
                "name": "Valid POI",
                "category": "cafe",
                "lat": 47.6065,
                "lon": -122.3330,
                "tags": {}
            },
            {
                "name": "Null Island POI",
                "category": "cafe",
                "lat": 0.0,
                "lon": 0.0,
                "tags": {}
            }
        ]

        # Return coordinates as-is (valid validation)
        mock_validate.side_effect = lambda lat, lon: (lat, lon)

        result = get_poi("Seattle, WA", validate_coords=True)

        # Null island should be filtered out
        assert len(result) == 1
        assert result[0]["name"] == "Valid POI"


class TestCreateSearchArea:
    """Test _create_search_area() helper function."""

    @patch('socialmapper.api.create_isochrone')
    def test_create_search_area_with_travel_time(self, mock_isochrone):
        """Test creating search area with travel time (isochrone)."""
        mock_isochrone.return_value = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-122.4, 47.5], [-122.3, 47.5],
                    [-122.3, 47.6], [-122.4, 47.6],
                    [-122.4, 47.5]
                ]]
            }
        }

        coords = (47.6062, -122.3321)
        result = _create_search_area(coords, travel_time=15)

        # Verify isochrone was created
        mock_isochrone.assert_called_once()
        assert mock_isochrone.call_args[0][0] == coords
        assert mock_isochrone.call_args[1]["travel_time"] == 15
        assert isinstance(result, Polygon)

    @patch('socialmapper.api.create_circular_geometry')
    def test_create_search_area_without_travel_time(self, mock_circular):
        """Test creating search area without travel time (radius)."""
        mock_circular.return_value = Polygon([
            (-122.4, 47.5), (-122.3, 47.5),
            (-122.3, 47.6), (-122.4, 47.6),
            (-122.4, 47.5)
        ])

        coords = (37.7749, -122.4194)
        result = _create_search_area(coords, travel_time=None)

        # Verify circular geometry was created with default radius
        mock_circular.assert_called_once()
        assert mock_circular.call_args[0][0] == coords
        # Should use DEFAULT_SEARCH_RADIUS_KM
        assert isinstance(result, Polygon)

    @patch('socialmapper.api.create_circular_geometry')
    def test_create_search_area_zero_travel_time(self, mock_circular):
        """Test that 0 travel time is treated as None (uses radius)."""
        mock_circular.return_value = Polygon([
            (-122.4, 47.5), (-122.3, 47.5),
            (-122.3, 47.6), (-122.4, 47.6),
            (-122.4, 47.5)
        ])

        coords = (40.7128, -74.0060)
        result = _create_search_area(coords, travel_time=0)

        # travel_time=0 is falsy, so should use circular geometry
        mock_circular.assert_called_once()


class TestValidateAndFilterPois:
    """Test _validate_and_filter_pois() helper function."""

    @patch('socialmapper._validation.validate_coordinates')
    def test_validate_and_filter_valid_pois(self, mock_validate):
        """Test filtering keeps valid POIs."""
        pois = [
            {"name": "POI 1", "lat": 47.6065, "lon": -122.3330},
            {"name": "POI 2", "lat": 37.7749, "lon": -122.4194}
        ]

        # All coordinates are valid
        mock_validate.side_effect = lambda lat, lon: (lat, lon)

        result = _validate_and_filter_pois(pois)

        assert len(result) == 2
        assert result[0]["name"] == "POI 1"
        assert result[1]["name"] == "POI 2"

    @patch('socialmapper._validation.validate_coordinates')
    def test_validate_and_filter_invalid_coordinates(self, mock_validate):
        """Test filtering removes POIs with invalid coordinates."""
        pois = [
            {"name": "Valid POI", "lat": 47.6065, "lon": -122.3330},
            {"name": "Invalid POI", "lat": 999.0, "lon": -122.3330}
        ]

        # First succeeds, second raises ValueError
        mock_validate.side_effect = [
            (47.6065, -122.3330),
            ValueError("Invalid latitude")
        ]

        result = _validate_and_filter_pois(pois)

        assert len(result) == 1
        assert result[0]["name"] == "Valid POI"

    @patch('socialmapper._validation.validate_coordinates')
    def test_validate_and_filter_null_island(self, mock_validate):
        """Test filtering removes null island (0, 0) coordinates."""
        pois = [
            {"name": "Valid POI", "lat": 47.6065, "lon": -122.3330},
            {"name": "Null Island", "lat": 0.0, "lon": 0.0}
        ]

        # Both validate successfully, but (0,0) should be filtered
        mock_validate.side_effect = lambda lat, lon: (lat, lon)

        result = _validate_and_filter_pois(pois)

        assert len(result) == 1
        assert result[0]["name"] == "Valid POI"

    @patch('socialmapper._validation.validate_coordinates')
    def test_validate_and_filter_missing_coordinates(self, mock_validate):
        """Test filtering handles missing lat/lon fields."""
        pois = [
            {"name": "Valid POI", "lat": 47.6065, "lon": -122.3330},
            {"name": "Missing Coords"}  # Missing lat/lon
        ]

        # First succeeds, second raises KeyError
        def validate_side_effect(lat, lon):
            if lat == 47.6065:
                return (lat, lon)
            raise KeyError("Missing coordinate field")

        mock_validate.side_effect = validate_side_effect

        result = _validate_and_filter_pois(pois)

        assert len(result) == 1
        assert result[0]["name"] == "Valid POI"

    @patch('socialmapper._validation.validate_coordinates')
    def test_validate_and_filter_all_invalid(self, mock_validate):
        """Test filtering returns empty list when all POIs invalid."""
        pois = [
            {"name": "Invalid 1", "lat": 999.0, "lon": -122.3330},
            {"name": "Invalid 2", "lat": 47.6065, "lon": 999.0}
        ]

        # All validations fail
        mock_validate.side_effect = ValueError("Invalid coordinates")

        result = _validate_and_filter_pois(pois)

        assert len(result) == 0


class TestCalculatePOIDistances:
    """Test _calculate_poi_distances() helper function."""

    def test_calculate_poi_distances_valid(self):
        """Test distance calculation for valid coordinates."""
        pois = [
            {"name": "POI 1", "lat": 47.6065, "lon": -122.3330},
            {"name": "POI 2", "lat": 47.6100, "lon": -122.3400}
        ]
        origin = (47.6062, -122.3321)

        _calculate_poi_distances(pois, origin, validate_coords=True)

        # Verify distances were calculated
        assert "distance_km" in pois[0]
        assert "distance_km" in pois[1]
        assert isinstance(pois[0]["distance_km"], float)
        assert isinstance(pois[1]["distance_km"], float)
        assert pois[0]["distance_km"] > 0
        assert pois[1]["distance_km"] > 0

    def test_calculate_poi_distances_validate_true(self):
        """Test distance calculation with validate_coords=True."""
        pois = [
            {"name": "Valid", "lat": 47.6065, "lon": -122.3330},
            {"name": "Invalid", "lat": "invalid", "lon": -122.3330}  # String will cause error
        ]
        origin = (47.6062, -122.3321)

        _calculate_poi_distances(pois, origin, validate_coords=True)

        # Valid POI should have distance
        assert isinstance(pois[0]["distance_km"], float)
        # Invalid POI should have infinity
        assert pois[1]["distance_km"] == float('inf')

    def test_calculate_poi_distances_validate_false(self):
        """Test distance calculation with validate_coords=False."""
        pois = [
            {"name": "Valid", "lat": 47.6065, "lon": -122.3330},
            {"name": "Invalid", "lat": "invalid", "lon": -122.3330}  # String will cause error
        ]
        origin = (47.6062, -122.3321)

        _calculate_poi_distances(pois, origin, validate_coords=False)

        # Valid POI should have distance
        assert isinstance(pois[0]["distance_km"], float)
        # Invalid POI should have None
        assert pois[1]["distance_km"] is None

    def test_calculate_poi_distances_zero_distance(self):
        """Test distance calculation when POI is at origin."""
        pois = [
            {"name": "At Origin", "lat": 47.6062, "lon": -122.3321}
        ]
        origin = (47.6062, -122.3321)

        _calculate_poi_distances(pois, origin, validate_coords=True)

        # Distance should be ~0
        assert pois[0]["distance_km"] < 0.001  # Very close to 0

    def test_calculate_poi_distances_updates_in_place(self):
        """Test that distances are added to original POI dicts."""
        pois = [
            {"name": "POI", "lat": 47.6065, "lon": -122.3330, "category": "cafe"}
        ]
        origin = (47.6062, -122.3321)

        # Store original POI reference
        original_poi = pois[0]

        _calculate_poi_distances(pois, origin, validate_coords=True)

        # Same object should be modified
        assert original_poi is pois[0]
        assert "distance_km" in original_poi
        # Original fields preserved
        assert original_poi["name"] == "POI"
        assert original_poi["category"] == "cafe"


class TestImportPoiCsv:
    """Test import_poi_csv() function."""

    @patch('socialmapper._csv_import.parse_csv_pois')
    def test_import_poi_csv_default_fields(self, mock_parse):
        """Test importing CSV with default field names."""
        mock_parse.return_value = [
            {
                "name": "Coffee Shop",
                "lat": 47.6062,
                "lon": -122.3321,
                "type": "cafe",
                "tags": {}
            },
            {
                "name": "Restaurant",
                "lat": 47.6100,
                "lon": -122.3400,
                "type": "restaurant",
                "tags": {}
            }
        ]

        result = import_poi_csv("test_locations.csv")

        assert len(result) == 2
        assert result[0]["name"] == "Coffee Shop"
        assert result[1]["name"] == "Restaurant"

        # Verify parse_csv_pois was called with default parameters
        mock_parse.assert_called_once_with(
            "test_locations.csv",
            "name",
            "latitude",
            "longitude",
            "type"
        )

    @patch('socialmapper._csv_import.parse_csv_pois')
    def test_import_poi_csv_custom_fields(self, mock_parse):
        """Test importing CSV with custom field names."""
        mock_parse.return_value = [
            {
                "name": "Park",
                "lat": 37.7749,
                "lon": -122.4194,
                "type": "recreation",
                "tags": {}
            }
        ]

        result = import_poi_csv(
            "custom.csv",
            name_field="place_name",
            lat_field="lat_coord",
            lon_field="lon_coord",
            type_field="category"
        )

        assert len(result) == 1
        assert result[0]["name"] == "Park"

        # Verify custom field names were passed
        mock_parse.assert_called_once_with(
            "custom.csv",
            "place_name",
            "lat_coord",
            "lon_coord",
            "category"
        )

    @patch('socialmapper._csv_import.parse_csv_pois')
    def test_import_poi_csv_file_not_found(self, mock_parse):
        """Test error when CSV file doesn't exist."""
        mock_parse.side_effect = FileNotFoundError("CSV file not found: missing.csv")

        with pytest.raises(FileNotFoundError, match="CSV file not found"):
            import_poi_csv("missing.csv")

    @patch('socialmapper._csv_import.parse_csv_pois')
    def test_import_poi_csv_invalid_extension(self, mock_parse):
        """Test error when file is not a CSV."""
        mock_parse.side_effect = ValueError("File must have .csv extension, got: .txt")

        with pytest.raises(ValueError, match="File must have .csv extension"):
            import_poi_csv("data.txt")

    @patch('socialmapper._csv_import.parse_csv_pois')
    def test_import_poi_csv_missing_columns(self, mock_parse):
        """Test error when required columns are missing."""
        mock_parse.side_effect = ValueError(
            "Could not find latitude/longitude columns. "
            "Looking for lat: ['latitude', 'lat'], lon: ['longitude', 'lon']. "
            "Available columns: name, address"
        )

        with pytest.raises(ValueError, match="Could not find latitude/longitude columns"):
            import_poi_csv("incomplete.csv")

    @patch('socialmapper._csv_import.parse_csv_pois')
    def test_import_poi_csv_empty_result(self, mock_parse):
        """Test error when no valid POIs are found."""
        mock_parse.side_effect = ValueError("No valid POIs found in empty.csv")

        with pytest.raises(ValueError, match="No valid POIs found"):
            import_poi_csv("empty.csv")

    @patch('socialmapper._csv_import.parse_csv_pois')
    def test_import_poi_csv_structure_validation(self, mock_parse):
        """Test that imported POIs have correct structure."""
        mock_parse.return_value = [
            {
                "name": "School",
                "lat": 40.7128,
                "lon": -74.0060,
                "type": "education",
                "tags": {"address": "123 Main St", "city": "New York"}
            }
        ]

        result = import_poi_csv("schools.csv")

        # Verify POI structure
        poi = result[0]
        assert "name" in poi
        assert "lat" in poi
        assert "lon" in poi
        assert "type" in poi
        assert "tags" in poi
        assert isinstance(poi["tags"], dict)

    @patch('socialmapper._csv_import.parse_csv_pois')
    def test_import_poi_csv_with_tags(self, mock_parse):
        """Test that additional CSV columns become tags."""
        mock_parse.return_value = [
            {
                "name": "Hospital",
                "lat": 42.3601,
                "lon": -71.0589,
                "type": "healthcare",
                "tags": {
                    "phone": "555-1234",
                    "hours": "24/7",
                    "beds": "200"
                }
            }
        ]

        result = import_poi_csv("hospitals.csv")

        assert result[0]["tags"]["phone"] == "555-1234"
        assert result[0]["tags"]["hours"] == "24/7"
        assert result[0]["tags"]["beds"] == "200"

    @patch('socialmapper._csv_import.parse_csv_pois')
    def test_import_poi_csv_multiple_pois(self, mock_parse):
        """Test importing multiple POIs from CSV."""
        mock_pois = [
            {
                "name": f"Location {i}",
                "lat": 40.0 + (i * 0.1),
                "lon": -120.0 + (i * 0.1),
                "type": "custom",
                "tags": {}
            }
            for i in range(10)
        ]
        mock_parse.return_value = mock_pois

        result = import_poi_csv("multiple.csv")

        assert len(result) == 10
        # Verify ordering is preserved
        assert result[0]["name"] == "Location 0"
        assert result[9]["name"] == "Location 9"

    @patch('socialmapper._csv_import.parse_csv_pois')
    def test_import_poi_csv_coordinate_types(self, mock_parse):
        """Test that coordinates are returned as floats."""
        mock_parse.return_value = [
            {
                "name": "Point",
                "lat": 47.6062,
                "lon": -122.3321,
                "type": "marker",
                "tags": {}
            }
        ]

        result = import_poi_csv("coords.csv")

        assert isinstance(result[0]["lat"], float)
        assert isinstance(result[0]["lon"], float)


class TestAnalyzeMultiplePois:
    """Test analyze_multiple_pois() function."""

    @patch('socialmapper.api.get_census_data')
    @patch('socialmapper.api.create_isochrone')
    def test_analyze_multiple_string_locations(self, mock_isochrone, mock_census):
        """Test analyzing multiple string locations."""
        # Mock isochrone returns
        mock_isochrone.side_effect = [
            {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[]]}},
            {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[]]}}
        ]

        # Mock census data returns
        mock_census.side_effect = [
            {
                "geoid1": {"population": 1000, "median_income": 50000},
                "geoid2": {"population": 2000, "median_income": 60000}
            },
            {
                "geoid3": {"population": 1500, "median_income": 55000},
                "geoid4": {"population": 2500, "median_income": 65000}
            }
        ]

        result = analyze_multiple_pois(
            ["Seattle, WA", "Portland, OR"],
            travel_time=15,
            variables=["population", "median_income"]
        )

        # Verify structure
        assert "locations" in result
        assert "metadata" in result
        assert "comparison" in result
        assert len(result["locations"]) == 2

        # Verify metadata
        assert result["metadata"]["travel_time"] == 15
        assert result["metadata"]["travel_mode"] == "drive"
        assert result["metadata"]["variables"] == ["population", "median_income"]

        # Verify location results
        loc1 = result["locations"][0]
        assert loc1["location"] == "Seattle, WA"
        assert "isochrone" in loc1
        assert "census_data" in loc1
        assert "aggregated" in loc1
        assert loc1["block_group_count"] == 2

    @patch('socialmapper.api.get_census_data')
    @patch('socialmapper.api.create_isochrone')
    def test_analyze_multiple_coordinate_tuples(self, mock_isochrone, mock_census):
        """Test analyzing multiple coordinate tuple locations."""
        mock_isochrone.side_effect = [
            {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[]]}},
            {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[]]}}
        ]

        mock_census.side_effect = [
            {"geoid1": {"population": 1000}},
            {"geoid2": {"population": 2000}}
        ]

        result = analyze_multiple_pois(
            [(47.6062, -122.3321), (45.5152, -122.6784)],
            variables=["population"]
        )

        # Verify coordinate formatting
        assert result["locations"][0]["location"] == "47.6062, -122.3321"
        assert result["locations"][1]["location"] == "45.5152, -122.6784"

    @patch('socialmapper.api.get_census_data')
    @patch('socialmapper.api.create_isochrone')
    def test_analyze_aggregation_calculations(self, mock_isochrone, mock_census):
        """Test that aggregation statistics are correctly calculated."""
        mock_isochrone.return_value = {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[]]}
        }

        mock_census.return_value = {
            "geoid1": {"population": 100},
            "geoid2": {"population": 200},
            "geoid3": {"population": 300}
        }

        result = analyze_multiple_pois(
            ["Test City"],
            variables=["population"]
        )

        # Verify aggregation
        agg = result["locations"][0]["aggregated"]["population"]
        assert agg["total"] == 600
        assert agg["mean"] == 200
        assert agg["min"] == 100
        assert agg["max"] == 300
        assert agg["count"] == 3

    @patch('socialmapper.api.get_census_data')
    @patch('socialmapper.api.create_isochrone')
    def test_analyze_default_variables(self, mock_isochrone, mock_census):
        """Test that default variable is 'population'."""
        mock_isochrone.return_value = {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[]]}
        }

        mock_census.return_value = {"geoid1": {"population": 1000}}

        result = analyze_multiple_pois(["City"])

        # Should use default population variable
        assert result["metadata"]["variables"] == ["population"]
        assert "population" in result["locations"][0]["aggregated"]

    @patch('socialmapper.api.get_census_data')
    @patch('socialmapper.api.create_isochrone')
    def test_analyze_travel_mode_parameter(self, mock_isochrone, mock_census):
        """Test that travel_mode is passed to create_isochrone."""
        mock_isochrone.return_value = {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[]]}
        }

        mock_census.return_value = {"geoid1": {"population": 1000}}

        result = analyze_multiple_pois(
            ["City"],
            travel_time=20,
            travel_mode="walk"
        )

        # Verify create_isochrone was called with correct mode
        mock_isochrone.assert_called_once_with("City", 20, "walk")
        assert result["metadata"]["travel_mode"] == "walk"
        assert result["metadata"]["travel_time"] == 20

    @patch('socialmapper.api.get_census_data')
    @patch('socialmapper.api.create_isochrone')
    def test_analyze_comparison_enabled(self, mock_isochrone, mock_census):
        """Test that comparison is included when compare=True."""
        mock_isochrone.side_effect = [
            {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[]]}},
            {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[]]}}
        ]

        mock_census.side_effect = [
            {"geoid1": {"population": 1000}},
            {"geoid2": {"population": 2000}}
        ]

        result = analyze_multiple_pois(
            ["City A", "City B"],
            variables=["population"],
            compare=True
        )

        # Comparison should be present
        assert "comparison" in result
        assert "population" in result["comparison"]

    @patch('socialmapper.api.get_census_data')
    @patch('socialmapper.api.create_isochrone')
    def test_analyze_comparison_disabled(self, mock_isochrone, mock_census):
        """Test that comparison is excluded when compare=False."""
        mock_isochrone.side_effect = [
            {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[]]}},
            {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[]]}}
        ]

        mock_census.side_effect = [
            {"geoid1": {"population": 1000}},
            {"geoid2": {"population": 2000}}
        ]

        result = analyze_multiple_pois(
            ["City A", "City B"],
            variables=["population"],
            compare=False
        )

        # Comparison should not be present
        assert "comparison" not in result

    @patch('socialmapper.api.get_census_data')
    @patch('socialmapper.api.create_isochrone')
    def test_analyze_single_location_no_comparison(self, mock_isochrone, mock_census):
        """Test that single location doesn't get comparison."""
        mock_isochrone.return_value = {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[]]}
        }

        mock_census.return_value = {"geoid1": {"population": 1000}}

        result = analyze_multiple_pois(
            ["Single City"],
            variables=["population"],
            compare=True  # Even with compare=True
        )

        # Comparison should not be present for single location
        assert "comparison" not in result

    @patch('socialmapper.api.get_census_data')
    @patch('socialmapper.api.create_isochrone')
    def test_analyze_error_handling(self, mock_isochrone, mock_census):
        """Test error handling for failed locations."""
        # First location succeeds
        mock_isochrone.side_effect = [
            {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[]]}},
            ValueError("Geocoding failed")  # Second location fails
        ]

        mock_census.return_value = {"geoid1": {"population": 1000}}

        result = analyze_multiple_pois(
            ["Valid City", "Invalid City"],
            variables=["population"]
        )

        # Both locations should be in results
        assert len(result["locations"]) == 2

        # First location should succeed
        assert "aggregated" in result["locations"][0]

        # Second location should have error
        assert "error" in result["locations"][1]
        assert "Geocoding failed" in result["locations"][1]["error"]

    @patch('socialmapper.api.get_census_data')
    @patch('socialmapper.api.create_isochrone')
    def test_analyze_multiple_variables(self, mock_isochrone, mock_census):
        """Test analysis with multiple census variables."""
        mock_isochrone.return_value = {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[]]}
        }

        mock_census.return_value = {
            "geoid1": {"population": 1000, "median_income": 50000, "median_age": 35},
            "geoid2": {"population": 2000, "median_income": 60000, "median_age": 40}
        }

        result = analyze_multiple_pois(
            ["City"],
            variables=["population", "median_income", "median_age"]
        )

        agg = result["locations"][0]["aggregated"]
        assert "population" in agg
        assert "median_income" in agg
        assert "median_age" in agg

    @patch('socialmapper.api.get_census_data')
    @patch('socialmapper.api.create_isochrone')
    def test_analyze_skips_none_values(self, mock_isochrone, mock_census):
        """Test that None values are filtered from aggregation."""
        mock_isochrone.return_value = {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[]]}
        }

        mock_census.return_value = {
            "geoid1": {"population": 1000},
            "geoid2": {"population": None},  # None value
            "geoid3": {"population": 2000}
        }

        result = analyze_multiple_pois(
            ["City"],
            variables=["population"]
        )

        # Only non-None values should be aggregated
        agg = result["locations"][0]["aggregated"]["population"]
        assert agg["count"] == 2  # Only 2 values (None excluded)
        assert agg["total"] == 3000
        assert agg["mean"] == 1500


class TestCreateComparisonAnalysis:
    """Test _create_comparison_analysis() helper function."""

    def test_comparison_basic_ranking(self):
        """Test basic comparison ranking."""
        locations = [
            {
                "location": "City A",
                "aggregated": {"population": {"total": 1000, "mean": 500}}
            },
            {
                "location": "City B",
                "aggregated": {"population": {"total": 2000, "mean": 1000}}
            },
            {
                "location": "City C",
                "aggregated": {"population": {"total": 1500, "mean": 750}}
            }
        ]

        result = _create_comparison_analysis(locations, ["population"])

        # Verify ranking (sorted by total, descending)
        ranked = result["population"]["ranked"]
        assert len(ranked) == 3
        assert ranked[0]["location"] == "City B"  # Highest
        assert ranked[1]["location"] == "City C"
        assert ranked[2]["location"] == "City A"  # Lowest

        # Verify highest/lowest
        assert result["population"]["highest"] == "City B"
        assert result["population"]["lowest"] == "City A"

    def test_comparison_multiple_variables(self):
        """Test comparison with multiple variables."""
        locations = [
            {
                "location": "City A",
                "aggregated": {
                    "population": {"total": 1000, "mean": 500},
                    "median_income": {"total": 50000, "mean": 50000}
                }
            },
            {
                "location": "City B",
                "aggregated": {
                    "population": {"total": 2000, "mean": 1000},
                    "median_income": {"total": 60000, "mean": 60000}
                }
            }
        ]

        result = _create_comparison_analysis(
            locations,
            ["population", "median_income"]
        )

        # Both variables should be compared
        assert "population" in result
        assert "median_income" in result
        assert result["population"]["highest"] == "City B"
        assert result["median_income"]["highest"] == "City B"

    def test_comparison_with_errors(self):
        """Test comparison skips locations with errors."""
        locations = [
            {
                "location": "Valid City",
                "aggregated": {"population": {"total": 1000, "mean": 500}}
            },
            {
                "location": "Failed City",
                "error": "Geocoding failed"
            }
        ]

        result = _create_comparison_analysis(locations, ["population"])

        # Only valid location should be in comparison
        assert len(result["population"]["ranked"]) == 1
        assert result["population"]["ranked"][0]["location"] == "Valid City"

    def test_comparison_missing_variable(self):
        """Test comparison when variable is missing from some locations."""
        locations = [
            {
                "location": "City A",
                "aggregated": {
                    "population": {"total": 1000, "mean": 500}
                }
            },
            {
                "location": "City B",
                "aggregated": {
                    # Missing population
                    "median_income": {"total": 50000, "mean": 50000}
                }
            }
        ]

        result = _create_comparison_analysis(
            locations,
            ["population"]
        )

        # Only City A should appear in population comparison
        assert len(result["population"]["ranked"]) == 1
        assert result["population"]["ranked"][0]["location"] == "City A"

    def test_comparison_preserves_all_stats(self):
        """Test that comparison preserves all aggregation stats."""
        locations = [
            {
                "location": "City A",
                "aggregated": {
                    "population": {
                        "total": 1000,
                        "mean": 250,
                        "min": 100,
                        "max": 400,
                        "count": 4
                    }
                }
            }
        ]

        result = _create_comparison_analysis(locations, ["population"])

        ranked_item = result["population"]["ranked"][0]
        assert ranked_item["total"] == 1000
        assert ranked_item["mean"] == 250
        assert ranked_item["min"] == 100
        assert ranked_item["max"] == 400
        assert ranked_item["count"] == 4


class TestGenerateReport:
    """Test generate_report() function."""

    @patch('socialmapper._reporting.create_analysis_report')
    def test_generate_report_html_format(self, mock_create_report):
        """Test generating HTML report."""
        mock_create_report.return_value = "<html><body>Test Report</body></html>"

        analysis_data = {
            "isochrone": {"type": "Feature", "geometry": {}},
            "census_data": {"geoid1": {"population": 1000}}
        }

        result = generate_report(analysis_data, format="html")

        # Verify HTML string returned
        assert isinstance(result, str)
        assert "<html>" in result
        assert "Test Report" in result

        # Verify create_analysis_report was called correctly
        mock_create_report.assert_called_once_with(
            analysis_data,
            "html",
            "default",
            True
        )

    @patch('socialmapper._reporting.create_analysis_report')
    def test_generate_report_pdf_format(self, mock_create_report):
        """Test generating PDF report."""
        mock_create_report.return_value = b'%PDF-1.4 fake pdf content'

        analysis_data = {
            "isochrone": {"type": "Feature", "geometry": {}},
            "census_data": {"geoid1": {"population": 1000}}
        }

        result = generate_report(analysis_data, format="pdf")

        # Verify bytes returned
        assert isinstance(result, bytes)
        assert result.startswith(b'%PDF')

        # Verify create_analysis_report was called with pdf format
        mock_create_report.assert_called_once_with(
            analysis_data,
            "pdf",
            "default",
            True
        )

    @patch('socialmapper._reporting.create_analysis_report')
    def test_generate_report_custom_template(self, mock_create_report):
        """Test generating report with custom template."""
        mock_create_report.return_value = "<html>Custom Template</html>"

        analysis_data = {"data": "test"}

        result = generate_report(
            analysis_data,
            format="html",
            template="custom_template"
        )

        # Verify template parameter passed
        mock_create_report.assert_called_once_with(
            analysis_data,
            "html",
            "custom_template",
            True
        )

    @patch('socialmapper._reporting.create_analysis_report')
    def test_generate_report_include_maps_true(self, mock_create_report):
        """Test generating report with maps included."""
        mock_create_report.return_value = "<html>Report with Maps</html>"

        analysis_data = {"data": "test"}

        result = generate_report(
            analysis_data,
            include_maps=True
        )

        # Verify include_maps=True passed
        assert mock_create_report.call_args[0][3] is True

    @patch('socialmapper._reporting.create_analysis_report')
    def test_generate_report_include_maps_false(self, mock_create_report):
        """Test generating report without maps."""
        mock_create_report.return_value = "<html>Report without Maps</html>"

        analysis_data = {"data": "test"}

        result = generate_report(
            analysis_data,
            include_maps=False
        )

        # Verify include_maps=False passed
        assert mock_create_report.call_args[0][3] is False

    @patch('socialmapper._reporting.create_analysis_report')
    def test_generate_report_default_parameters(self, mock_create_report):
        """Test generating report with all defaults."""
        mock_create_report.return_value = "<html>Default Report</html>"

        analysis_data = {"data": "test"}

        result = generate_report(analysis_data)

        # Verify defaults: format=html, template=default, include_maps=True
        mock_create_report.assert_called_once_with(
            analysis_data,
            "html",
            "default",
            True
        )

    def test_generate_report_invalid_format(self):
        """Test error with invalid report format."""
        analysis_data = {"data": "test"}

        with pytest.raises(ValueError, match="Report format must be one of"):
            generate_report(analysis_data, format="invalid")

    def test_generate_report_invalid_format_xml(self):
        """Test error with unsupported XML format."""
        analysis_data = {"data": "test"}

        with pytest.raises(ValueError, match="Report format must be one of"):
            generate_report(analysis_data, format="xml")

    @patch('socialmapper._reporting.create_analysis_report')
    def test_generate_report_with_isochrone_data(self, mock_create_report):
        """Test generating report with isochrone analysis data."""
        mock_create_report.return_value = "<html>Isochrone Report</html>"

        analysis_data = {
            "isochrone": {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": []},
                "properties": {
                    "location": "Seattle, WA",
                    "travel_time": 15,
                    "travel_mode": "drive",
                    "area_sq_km": 25.5
                }
            },
            "census_data": {
                "geoid1": {"population": 1000, "median_income": 50000}
            }
        }

        result = generate_report(analysis_data)

        # Verify analysis_data was passed correctly
        call_args = mock_create_report.call_args[0]
        assert call_args[0] == analysis_data
        assert "isochrone" in call_args[0]
        assert "census_data" in call_args[0]

    @patch('socialmapper._reporting.create_analysis_report')
    def test_generate_report_with_multiple_poi_data(self, mock_create_report):
        """Test generating report with multiple POI analysis data."""
        mock_create_report.return_value = "<html>Multi-POI Report</html>"

        analysis_data = {
            "locations": [
                {
                    "location": "City A",
                    "aggregated": {"population": {"total": 1000, "mean": 500}}
                },
                {
                    "location": "City B",
                    "aggregated": {"population": {"total": 2000, "mean": 1000}}
                }
            ],
            "comparison": {
                "population": {
                    "highest": "City B",
                    "lowest": "City A"
                }
            },
            "metadata": {
                "travel_time": 15,
                "travel_mode": "drive",
                "variables": ["population"]
            }
        }

        result = generate_report(analysis_data)

        # Verify complex data structure passed
        call_args = mock_create_report.call_args[0]
        assert "locations" in call_args[0]
        assert "comparison" in call_args[0]
        assert "metadata" in call_args[0]
