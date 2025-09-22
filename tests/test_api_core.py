"""Comprehensive tests for core SocialMapper API functions with real API calls.

Tests all five core API functions:
- create_isochrone
- get_census_blocks
- get_census_data
- create_map
- get_poi
"""

import os
import tempfile
from pathlib import Path
from unittest import TestCase

import geopandas as gpd
import pandas as pd
import pytest

from socialmapper.api import (
    create_isochrone,
    create_map,
    get_census_blocks,
    get_census_data,
    get_poi,
)


class TestCreateIsochrone(TestCase):
    """Test create_isochrone function with real API calls."""

    def test_create_isochrone_with_coordinates(self):
        """Test isochrone creation with latitude/longitude coordinates."""
        result = create_isochrone(
            origin=(35.9132, -79.0558),  # Chapel Hill, NC
            travel_time=10,
            travel_mode="drive"
        )

        self.assertIsNotNone(result)
        self.assertIn("geometry", result)
        self.assertIn("center_lat", result)
        self.assertIn("center_lon", result)
        self.assertIn("travel_time", result)
        self.assertEqual(result["travel_time"], 10)
        self.assertIn("travel_mode", result)
        self.assertEqual(result["travel_mode"], "drive")

    def test_create_isochrone_with_address(self):
        """Test isochrone creation with address string."""
        result = create_isochrone(
            origin="Chapel Hill, NC",
            travel_time=5,
            travel_mode="walk"
        )

        self.assertIsNotNone(result)
        self.assertIn("geometry", result)
        self.assertIn("travel_time", result)
        self.assertEqual(result["travel_time"], 5)
        self.assertEqual(result["travel_mode"], "walk")

    def test_create_isochrone_invalid_travel_time(self):
        """Test error handling for invalid travel time."""
        with self.assertRaises(ValueError):
            create_isochrone(
                origin=(35.9132, -79.0558),
                travel_time=0,  # Invalid: too small
                travel_mode="drive"
            )

        with self.assertRaises(ValueError):
            create_isochrone(
                origin=(35.9132, -79.0558),
                travel_time=61,  # Invalid: too large
                travel_mode="drive"
            )

    def test_create_isochrone_invalid_travel_mode(self):
        """Test error handling for invalid travel mode."""
        with self.assertRaises(ValueError):
            create_isochrone(
                origin=(35.9132, -79.0558),
                travel_time=10,
                travel_mode="invalid_mode"
            )

    def test_create_isochrone_bike_mode(self):
        """Test isochrone with bike travel mode."""
        result = create_isochrone(
            origin=(35.9132, -79.0558),
            travel_time=15,
            travel_mode="bike"
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["travel_mode"], "bike")
        self.assertEqual(result["travel_time"], 15)


class TestGetCensusBlocks(TestCase):
    """Test get_census_blocks function with real Census API calls."""

    def test_get_census_blocks_with_isochrone(self):
        """Test getting census blocks for an isochrone area."""
        # First create an isochrone
        isochrone = create_isochrone(
            origin=(35.9132, -79.0558),
            travel_time=10,
            travel_mode="drive"
        )

        # Get census blocks for the isochrone
        blocks = get_census_blocks(area=isochrone)

        self.assertIsInstance(blocks, gpd.GeoDataFrame)
        self.assertGreater(len(blocks), 0)
        self.assertIn("GEOID", blocks.columns)
        self.assertIn("geometry", blocks.columns)

    def test_get_census_blocks_with_bbox(self):
        """Test getting census blocks for a bounding box."""
        # Define a small bounding box around Chapel Hill
        bbox = {
            "min_lon": -79.07,
            "max_lon": -79.04,
            "min_lat": 35.90,
            "max_lat": 35.93
        }

        blocks = get_census_blocks(area=bbox)

        self.assertIsInstance(blocks, gpd.GeoDataFrame)
        self.assertGreater(len(blocks), 0)
        self.assertIn("GEOID", blocks.columns)

    def test_get_census_blocks_invalid_area(self):
        """Test error handling for invalid area input."""
        with self.assertRaises((ValueError, TypeError)):
            get_census_blocks(area="invalid_area")

        with self.assertRaises((ValueError, TypeError)):
            get_census_blocks(area=123)


class TestGetCensusData(TestCase):
    """Test get_census_data function with real Census API calls."""

    @classmethod
    def setUpClass(cls):
        """Set up test data once for all tests."""
        # Create a small isochrone for testing
        cls.test_isochrone = create_isochrone(
            origin=(35.9132, -79.0558),
            travel_time=5,
            travel_mode="walk"
        )
        cls.test_blocks = get_census_blocks(area=cls.test_isochrone)

    def test_get_census_data_basic(self):
        """Test getting basic census data."""
        if len(self.test_blocks) == 0:
            self.skipTest("No census blocks available for testing")

        data = get_census_data(
            blocks=self.test_blocks,
            variables=["B01001_001E"]  # Total population
        )

        self.assertIsInstance(data, pd.DataFrame)
        self.assertIn("B01001_001E", data.columns)
        self.assertIn("GEOID", data.columns)
        self.assertGreater(len(data), 0)

    def test_get_census_data_multiple_variables(self):
        """Test getting multiple census variables."""
        if len(self.test_blocks) == 0:
            self.skipTest("No census blocks available for testing")

        variables = [
            "B01001_001E",  # Total population
            "B19013_001E",  # Median household income
            "B25001_001E"   # Total housing units
        ]

        data = get_census_data(
            blocks=self.test_blocks,
            variables=variables
        )

        self.assertIsInstance(data, pd.DataFrame)
        for var in variables:
            self.assertIn(var, data.columns)

    def test_get_census_data_invalid_variable(self):
        """Test handling of invalid census variables."""
        if len(self.test_blocks) == 0:
            self.skipTest("No census blocks available for testing")

        # Invalid variable should be handled gracefully
        data = get_census_data(
            blocks=self.test_blocks,
            variables=["INVALID_VAR_999"]
        )

        # Should return empty or handle error appropriately
        self.assertIsInstance(data, pd.DataFrame)

    def test_get_census_data_empty_blocks(self):
        """Test handling of empty blocks GeoDataFrame."""
        empty_blocks = gpd.GeoDataFrame()

        with self.assertRaises((ValueError, KeyError)):
            get_census_data(
                blocks=empty_blocks,
                variables=["B01001_001E"]
            )


class TestCreateMap(TestCase):
    """Test create_map function."""

    @classmethod
    def setUpClass(cls):
        """Set up test data once for all tests."""
        # Create test data
        cls.test_isochrone = create_isochrone(
            origin=(35.9132, -79.0558),
            travel_time=10,
            travel_mode="drive"
        )
        cls.test_blocks = get_census_blocks(area=cls.test_isochrone)
        if len(cls.test_blocks) > 0:
            cls.test_census_data = get_census_data(
                blocks=cls.test_blocks,
                variables=["B01001_001E"]
            )
        else:
            cls.test_census_data = pd.DataFrame()

    def test_create_map_basic(self):
        """Test basic map creation."""
        if len(self.test_census_data) == 0:
            self.skipTest("No census data available for testing")

        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
            map_path = tmp.name

        try:
            result = create_map(
                data=self.test_census_data,
                variable="B01001_001E",
                output_file=map_path
            )

            self.assertIsNotNone(result)
            self.assertTrue(Path(map_path).exists())
            self.assertGreater(Path(map_path).stat().st_size, 0)
        finally:
            # Clean up
            if Path(map_path).exists():
                Path(map_path).unlink()

    def test_create_map_with_title(self):
        """Test map creation with custom title."""
        if len(self.test_census_data) == 0:
            self.skipTest("No census data available for testing")

        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
            map_path = tmp.name

        try:
            result = create_map(
                data=self.test_census_data,
                variable="B01001_001E",
                title="Population Distribution",
                output_file=map_path
            )

            self.assertIsNotNone(result)
            self.assertTrue(Path(map_path).exists())

            # Check if title is in the HTML
            with open(map_path, 'r') as f:
                html_content = f.read()
                self.assertIn("Population", html_content)
        finally:
            # Clean up
            if Path(map_path).exists():
                Path(map_path).unlink()

    def test_create_map_invalid_variable(self):
        """Test error handling for invalid variable."""
        if len(self.test_census_data) == 0:
            self.skipTest("No census data available for testing")

        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
            map_path = tmp.name

        try:
            with self.assertRaises((ValueError, KeyError)):
                create_map(
                    data=self.test_census_data,
                    variable="INVALID_COLUMN",
                    output_file=map_path
                )
        finally:
            # Clean up
            if Path(map_path).exists():
                Path(map_path).unlink()


class TestGetPOI(TestCase):
    """Test get_poi function with real OSM API calls."""

    def test_get_poi_basic(self):
        """Test basic POI retrieval."""
        pois = get_poi(
            location=(35.9132, -79.0558),  # Chapel Hill, NC
            radius=1000,  # 1km radius
            poi_type="restaurant"
        )

        self.assertIsInstance(pois, gpd.GeoDataFrame)
        self.assertIn("name", pois.columns)
        self.assertIn("geometry", pois.columns)
        # Chapel Hill should have at least some restaurants
        self.assertGreater(len(pois), 0)

    def test_get_poi_with_address(self):
        """Test POI retrieval with address."""
        pois = get_poi(
            location="Chapel Hill, NC",
            radius=500,
            poi_type="coffee"
        )

        self.assertIsInstance(pois, gpd.GeoDataFrame)
        self.assertIn("geometry", pois.columns)

    def test_get_poi_multiple_types(self):
        """Test POI retrieval with multiple types."""
        pois = get_poi(
            location=(35.9132, -79.0558),
            radius=1000,
            poi_type=["restaurant", "cafe", "bar"]
        )

        self.assertIsInstance(pois, gpd.GeoDataFrame)
        if len(pois) > 0:
            self.assertIn("amenity", pois.columns)

    def test_get_poi_large_radius(self):
        """Test POI retrieval with large radius."""
        pois = get_poi(
            location=(35.9132, -79.0558),
            radius=5000,  # 5km radius
            poi_type="grocery"
        )

        self.assertIsInstance(pois, gpd.GeoDataFrame)

    def test_get_poi_invalid_location(self):
        """Test error handling for invalid location."""
        with self.assertRaises((ValueError, Exception)):
            get_poi(
                location="Invalid Location That Does Not Exist 12345",
                radius=1000,
                poi_type="restaurant"
            )

    def test_get_poi_invalid_radius(self):
        """Test error handling for invalid radius."""
        with self.assertRaises(ValueError):
            get_poi(
                location=(35.9132, -79.0558),
                radius=-100,  # Negative radius
                poi_type="restaurant"
            )

        with self.assertRaises(ValueError):
            get_poi(
                location=(35.9132, -79.0558),
                radius=0,  # Zero radius
                poi_type="restaurant"
            )


class TestAPIIntegration(TestCase):
    """Integration tests combining multiple API functions."""

    def test_full_workflow(self):
        """Test complete workflow from isochrone to map creation."""
        # Step 1: Create isochrone
        isochrone = create_isochrone(
            origin="Durham, NC",
            travel_time=15,
            travel_mode="drive"
        )
        self.assertIsNotNone(isochrone)

        # Step 2: Get census blocks
        blocks = get_census_blocks(area=isochrone)
        self.assertIsInstance(blocks, gpd.GeoDataFrame)

        if len(blocks) == 0:
            self.skipTest("No census blocks found for test area")

        # Step 3: Get census data
        census_data = get_census_data(
            blocks=blocks,
            variables=["B01001_001E", "B19013_001E"]
        )
        self.assertIsInstance(census_data, pd.DataFrame)

        # Step 4: Create map
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
            map_path = tmp.name

        try:
            map_result = create_map(
                data=census_data,
                variable="B01001_001E",
                title="Population in 15-minute drive from Durham, NC",
                output_file=map_path
            )
            self.assertIsNotNone(map_result)
            self.assertTrue(Path(map_path).exists())
        finally:
            if Path(map_path).exists():
                Path(map_path).unlink()

        # Step 5: Get POIs in the same area
        center = (isochrone["center_lat"], isochrone["center_lon"])
        pois = get_poi(
            location=center,
            radius=2000,
            poi_type=["restaurant", "school", "hospital"]
        )
        self.assertIsInstance(pois, gpd.GeoDataFrame)

    def test_multi_location_analysis(self):
        """Test analysis for multiple locations."""
        locations = [
            "Raleigh, NC",
            "Durham, NC",
            "Chapel Hill, NC"
        ]

        for location in locations:
            # Create isochrone for each location
            isochrone = create_isochrone(
                origin=location,
                travel_time=10,
                travel_mode="drive"
            )
            self.assertIsNotNone(isochrone)

            # Get POIs for each location
            pois = get_poi(
                location=location,
                radius=1000,
                poi_type="restaurant"
            )
            self.assertIsInstance(pois, gpd.GeoDataFrame)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])