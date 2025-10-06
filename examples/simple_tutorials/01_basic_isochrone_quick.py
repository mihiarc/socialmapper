#!/usr/bin/env python3
"""
Quick test version of Tutorial 01 with minimal examples.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from socialmapper import create_isochrone

print("🗺️ QUICK ISOCHRONE TEST")
print("=" * 40)

# Test with very short travel time
lat, lon = 35.7796, -78.6382  # Raleigh, NC

print(f"\nCreating 3-minute isochrone at ({lat}, {lon})...")

try:
    iso = create_isochrone(
        location=(lat, lon),
        travel_time=3,  # Very short for quick test
        travel_mode="drive"
    )
    print(f"✅ Success! Isochrone created")
    print(f"   Type: {iso['type']}")  # GeoJSON Feature
    print(f"   Travel time: {iso['properties']['travel_time']} minutes")
    print(f"   Travel mode: {iso['properties']['travel_mode']}")
    print(f"   Area: {iso['properties']['area_sq_km']:.2f} km²")

except Exception as e:
    print(f"❌ Failed: {e}")

print("\n✨ Quick test complete!")