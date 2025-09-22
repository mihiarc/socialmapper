#!/usr/bin/env python3
"""Test case for Issue #45: Concurrent Processing Produces Incorrect Isochrones.

This test verifies that the concurrent processing bug that produces severely
truncated isochrones for rural locations (particularly Goodland, KS) is fixed.
"""

import logging
import time
import geopandas as gpd
import pytest

from socialmapper.isochrone import create_isochrones_from_poi_list
from socialmapper.isochrone.concurrent import process_isochrones_concurrent
from socialmapper.isochrone.clustering import create_isochrone_from_poi_with_network
from socialmapper.isochrone.cache import download_and_cache_network, get_global_cache
from socialmapper.isochrone.travel_modes import TravelMode

# Set up logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Goodland, KS Walmart - the problematic location from Issue #45
GOODLAND_WALMART = {
    "id": "goodland_walmart",
    "lat": 39.3343285,
    "lon": -101.7285206,
    "tags": {
        "name": "Walmart Supercenter Goodland",
        "shop": "supermarket"
    }
}

# Additional POIs to trigger concurrent processing (threshold is 3+ POIs)
ADDITIONAL_POIS = [
    {
        "id": "colby_walmart",
        "lat": 39.3933,
        "lon": -101.0527,
        "tags": {"name": "Colby Walmart", "shop": "supermarket"}
    },
    {
        "id": "garden_city_walmart",
        "lat": 37.9717,
        "lon": -100.8727,
        "tags": {"name": "Garden City Walmart", "shop": "supermarket"}
    },
    {
        "id": "dodge_city_walmart",
        "lat": 37.7528,
        "lon": -100.0171,
        "tags": {"name": "Dodge City Walmart", "shop": "supermarket"}
    },
    {
        "id": "liberal_walmart",
        "lat": 37.0431,
        "lon": -100.9210,
        "tags": {"name": "Liberal Walmart", "shop": "supermarket"}
    },
    {
        "id": "hays_walmart",
        "lat": 38.8794,
        "lon": -99.3269,
        "tags": {"name": "Hays Walmart", "shop": "supermarket"}
    },
    {
        "id": "salina_walmart",
        "lat": 38.8403,
        "lon": -97.6114,
        "tags": {"name": "Salina Walmart", "shop": "supermarket"}
    },
    {
        "id": "manhattan_walmart",
        "lat": 39.1836,
        "lon": -96.5717,
        "tags": {"name": "Manhattan Walmart", "shop": "supermarket"}
    },
    {
        "id": "junction_city_walmart",
        "lat": 39.0286,
        "lon": -96.8314,
        "tags": {"name": "Junction City Walmart", "shop": "supermarket"}
    },
    {
        "id": "emporia_walmart",
        "lat": 38.4039,
        "lon": -96.1817,
        "tags": {"name": "Emporia Walmart", "shop": "supermarket"}
    }
]


def calculate_isochrone_area_km2(isochrone_gdf):
    """Calculate the area of an isochrone in square kilometers."""
    if isochrone_gdf is None or len(isochrone_gdf) == 0:
        return 0.0
    # Project to a suitable CRS for area calculation (Web Mercator)
    projected = isochrone_gdf.to_crs("EPSG:3857")
    area_m2 = projected.geometry[0].area
    return area_m2 / 1_000_000  # Convert to km²


def test_goodland_single_poi():
    """Test that Goodland produces a reasonable isochrone when processed alone."""
    logger.info("Testing Goodland Walmart isochrone (single POI)...")

    # Clear cache to ensure fresh download
    cache = get_global_cache()
    cache.clear_cache()

    # Process single POI
    poi_data = {"pois": [GOODLAND_WALMART]}
    travel_time = 30  # 30 minutes

    # Use the main API which will not trigger concurrent processing for single POI
    result = create_isochrones_from_poi_list(
        poi_data=poi_data,
        travel_time_limit=travel_time,
        output_dir="test_output",
        save_individual_files=False,
        combine_results=True,
        travel_mode=TravelMode.DRIVE
    )

    # Calculate area
    area_km2 = calculate_isochrone_area_km2(result)
    logger.info(f"Goodland single POI isochrone area: {area_km2:.1f} km²")

    # For 30 minutes of driving in rural Kansas, expect a large area
    # The issue reported ~3,761 km² for correct processing
    assert area_km2 > 2000, f"Goodland isochrone too small: {area_km2:.1f} km² (expected > 2000 km²)"

    return area_km2


def test_goodland_concurrent_processing():
    """Test that Goodland produces consistent isochrone with concurrent processing."""
    logger.info("Testing Goodland Walmart with concurrent processing (10+ POIs)...")

    # Clear cache to ensure fresh download
    cache = get_global_cache()
    cache.clear_cache()

    # Create POI list with Goodland and additional POIs to trigger concurrent processing
    all_pois = [GOODLAND_WALMART] + ADDITIONAL_POIS
    travel_time = 30  # 30 minutes

    # Process concurrently (will auto-enable for 3+ POIs)
    isochrones = process_isochrones_concurrent(
        pois=all_pois,
        travel_time_minutes=travel_time,
        travel_mode=TravelMode.DRIVE
    )

    # Find Goodland's isochrone
    goodland_isochrone = None
    for iso in isochrones:
        if iso["poi_id"].values[0] == "goodland_walmart":
            goodland_isochrone = iso
            break

    assert goodland_isochrone is not None, "Goodland isochrone not found in results"

    # Calculate area
    area_km2 = calculate_isochrone_area_km2(goodland_isochrone)
    logger.info(f"Goodland concurrent processing isochrone area: {area_km2:.1f} km²")

    # The bug reported 57.9 km² for incorrect concurrent processing
    # We should get a similar area to single POI processing
    assert area_km2 > 2000, f"Goodland isochrone too small with concurrent: {area_km2:.1f} km² (expected > 2000 km²)"

    return area_km2


def test_consistency_between_single_and_concurrent():
    """Test that single and concurrent processing produce similar results."""
    logger.info("Testing consistency between single and concurrent processing...")

    # Get areas from both processing methods
    single_area = test_goodland_single_poi()
    concurrent_area = test_goodland_concurrent_processing()

    # Calculate difference
    difference_percent = abs(single_area - concurrent_area) / single_area * 100

    logger.info(f"Single POI area: {single_area:.1f} km²")
    logger.info(f"Concurrent area: {concurrent_area:.1f} km²")
    logger.info(f"Difference: {difference_percent:.1f}%")

    # Allow for some variation but not the 65x difference reported in the bug
    assert difference_percent < 20, (
        f"Too much variation between single and concurrent: {difference_percent:.1f}% "
        f"(single: {single_area:.1f} km², concurrent: {concurrent_area:.1f} km²)"
    )


def test_rural_area_detection():
    """Test that rural areas get appropriate network buffers."""
    logger.info("Testing rural area network buffer calculation...")

    # Clear cache
    cache = get_global_cache()
    cache.clear_cache()

    # Download network for Goodland
    bbox = (
        GOODLAND_WALMART["lat"] - 0.5,
        GOODLAND_WALMART["lon"] - 0.5,
        GOODLAND_WALMART["lat"] + 0.5,
        GOODLAND_WALMART["lon"] + 0.5
    )

    network = download_and_cache_network(
        bbox=bbox,
        travel_time_minutes=30,
        travel_mode=TravelMode.DRIVE,
        cache=cache
    )

    assert network is not None, "Failed to download network"

    # Check network size - rural areas should have reasonable node counts
    node_count = len(network.nodes)
    edge_count = len(network.edges)

    logger.info(f"Goodland network: {node_count} nodes, {edge_count} edges")

    # The bug reported networks with too few nodes
    # For a 30-minute drive area in rural Kansas, expect decent coverage
    assert node_count > 1000, f"Network too small: {node_count} nodes (expected > 1000)"
    assert edge_count > 1500, f"Network too small: {edge_count} edges (expected > 1500)"


def test_isochrone_validation():
    """Test that small isochrones are properly detected and flagged."""
    logger.info("Testing isochrone size validation...")

    # Create a small test POI that might produce a small isochrone
    # Using a location that might have limited road access
    remote_poi = {
        "id": "remote_location",
        "lat": 39.0,  # Middle of nowhere Kansas
        "lon": -101.0,
        "tags": {"name": "Remote Location"}
    }

    poi_data = {"pois": [remote_poi]}

    # Process with validation
    result = create_isochrone_map(
        poi_data=poi_data,
        travel_time_limit=5,  # Only 5 minutes to potentially create small isochrone
        output_dir="test_output",
        save_individual_files=False,
        combine_results=True,
        travel_mode=TravelMode.DRIVE
    )

    if result is not None and len(result) > 0:
        area_km2 = calculate_isochrone_area_km2(result)
        logger.info(f"Small travel time isochrone area: {area_km2:.1f} km²")

        # Check if validation flag is set for small isochrones
        if "needs_validation" in result.columns:
            if area_km2 < 10:  # If area is suspiciously small
                assert result["needs_validation"].values[0] == True, (
                    "Small isochrone should be flagged for validation"
                )


if __name__ == "__main__":
    # Run tests
    print("=" * 70)
    print("Testing Issue #45: Concurrent Processing Isochrone Bug")
    print("=" * 70)

    try:
        test_goodland_single_poi()
        print("✓ Single POI test passed")
    except AssertionError as e:
        print(f"✗ Single POI test failed: {e}")

    try:
        test_goodland_concurrent_processing()
        print("✓ Concurrent processing test passed")
    except AssertionError as e:
        print(f"✗ Concurrent processing test failed: {e}")

    try:
        test_consistency_between_single_and_concurrent()
        print("✓ Consistency test passed")
    except AssertionError as e:
        print(f"✗ Consistency test failed: {e}")

    try:
        test_rural_area_detection()
        print("✓ Rural area detection test passed")
    except AssertionError as e:
        print(f"✗ Rural area detection test failed: {e}")

    try:
        test_isochrone_validation()
        print("✓ Isochrone validation test passed")
    except AssertionError as e:
        print(f"✗ Isochrone validation test failed: {e}")

    print("=" * 70)
    print("All tests completed!")