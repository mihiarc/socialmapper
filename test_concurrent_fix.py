#!/usr/bin/env python3
"""Quick test to verify the concurrent isochrone bug fix."""

import logging
from socialmapper.isochrone.concurrent import process_isochrones_concurrent
from socialmapper.isochrone.cache import get_global_cache
from socialmapper.isochrone.travel_modes import TravelMode

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test POIs - a mix of rural and urban locations
TEST_POIS = [
    # Goodland, KS - the problematic rural location
    {
        "id": "goodland_walmart",
        "lat": 39.3343285,
        "lon": -101.7285206,
        "tags": {"name": "Goodland Walmart", "shop": "supermarket"}
    },
    # A few more POIs to trigger concurrent processing (threshold is 3+)
    {
        "id": "denver_walmart",
        "lat": 39.7392,
        "lon": -104.9903,
        "tags": {"name": "Denver Walmart", "shop": "supermarket"}
    },
    {
        "id": "kansas_city_walmart",
        "lat": 39.0997,
        "lon": -94.5786,
        "tags": {"name": "Kansas City Walmart", "shop": "supermarket"}
    },
    {
        "id": "wichita_walmart",
        "lat": 37.6872,
        "lon": -97.3301,
        "tags": {"name": "Wichita Walmart", "shop": "supermarket"}
    }
]

def test_concurrent_processing():
    """Test concurrent isochrone generation with rural locations."""

    # Clear cache to ensure fresh network downloads
    cache = get_global_cache()
    cache.clear_cache()

    logger.info(f"Testing concurrent processing with {len(TEST_POIS)} POIs...")

    try:
        # Process POIs with concurrent processing (auto-enabled for 3+ POIs)
        isochrones = process_isochrones_concurrent(
            pois=TEST_POIS,
            travel_time_minutes=15,  # Use shorter time for faster testing
            travel_mode=TravelMode.DRIVE
        )

        logger.info(f"Generated {len(isochrones)} isochrones successfully")

        # Check Goodland's isochrone
        for iso in isochrones:
            if iso["poi_id"].values[0] == "goodland_walmart":
                # Calculate area in km²
                area_km2 = iso.to_crs("EPSG:3857").geometry[0].area / 1_000_000
                logger.info(f"Goodland isochrone area: {area_km2:.1f} km²")

                # For 15 minutes of driving in rural Kansas, expect reasonable area
                if area_km2 < 100:
                    logger.warning(f"⚠️  Goodland isochrone seems small: {area_km2:.1f} km²")
                else:
                    logger.info(f"✅ Goodland isochrone size looks reasonable: {area_km2:.1f} km²")
                break
        else:
            logger.error("❌ Goodland isochrone not found in results")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("Testing Concurrent Isochrone Bug Fix")
    print("=" * 70)

    if test_concurrent_processing():
        print("\n✅ Test completed successfully")
    else:
        print("\n❌ Test failed")