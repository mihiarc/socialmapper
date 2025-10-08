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
    _convert_data_to_geodataframe
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
