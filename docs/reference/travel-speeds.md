# Travel Speed Reference

This page provides detailed information about how SocialMapper assigns travel speeds for accurate isochrone generation.

## Overview

SocialMapper uses [OSMnx 2.0's](https://osmnx.readthedocs.io/) sophisticated speed assignment system to calculate realistic travel times. The system considers both real-world speed limit data from OpenStreetMap and intelligent fallbacks based on road types and travel modes.

## Speed Assignment Hierarchy

When generating isochrones, OSMnx assigns edge speeds using this priority order:

1. **OSM maxspeed tags** - Uses actual speed limits from OpenStreetMap data when available
2. **Highway-type speeds** - Falls back to our configured speeds for each road type
3. **Statistical imputation** - For unmapped highway types, uses the mean speed of similar roads in the network
4. **Mode-specific fallback** - As a last resort, uses the travel mode's default speed

## Travel Mode Speeds

### Driving Mode

Default fallback speed: **50 km/h** (31 mph)

| Highway Type | Speed (km/h) | Speed (mph) | Description |
|-------------|--------------|-------------|-------------|
| motorway | 110 | 68 | Highways/freeways |
| motorway_link | 70 | 43 | Highway on/off ramps |
| trunk | 90 | 56 | Major arterial roads |
| trunk_link | 50 | 31 | Major road ramps |
| primary | 65 | 40 | Primary roads |
| primary_link | 40 | 25 | Primary road connectors |
| secondary | 55 | 34 | Secondary roads |
| secondary_link | 35 | 22 | Secondary road connectors |
| tertiary | 45 | 28 | Local connector roads |
| tertiary_link | 30 | 19 | Tertiary road connectors |
| residential | 30 | 19 | Neighborhood streets |
| living_street | 20 | 12 | Shared residential spaces |
| service | 25 | 16 | Service/access roads |
| unclassified | 40 | 25 | Unclassified roads |
| road | 40 | 25 | Unknown road types |

### Walking Mode

Default fallback speed: **5 km/h** (3.1 mph)

| Path Type | Speed (km/h) | Speed (mph) | Description |
|-----------|--------------|-------------|-------------|
| footway | 5.0 | 3.1 | Dedicated pedestrian paths |
| sidewalk | 5.0 | 3.1 | Sidewalks along roads |
| pedestrian | 5.0 | 3.1 | Pedestrian areas |
| residential | 4.8 | 3.0 | Residential streets (may lack sidewalks) |
| tertiary | 4.8 | 3.0 | Less busy roads |
| path | 4.5 | 2.8 | General paths (may be rough) |
| living_street | 4.5 | 2.8 | Shared spaces, need caution |
| service | 4.5 | 2.8 | Service roads |
| primary | 4.5 | 2.8 | Busy roads may slow walking |
| secondary | 4.5 | 2.8 | Busy roads |
| trunk | 4.0 | 2.5 | Very busy roads, often no sidewalk |
| motorway | 3.0 | 1.9 | Highways (rarely walkable) |
| steps | 1.5 | 0.9 | Stairs are very slow |

### Biking Mode

Default fallback speed: **15 km/h** (9.3 mph)

| Path Type | Speed (km/h) | Speed (mph) | Description |
|-----------|--------------|-------------|-------------|
| primary | 20.0 | 12.4 | Good roads, higher speeds |
| cycleway | 18.0 | 11.2 | Dedicated bike lanes |
| secondary | 18.0 | 11.2 | Moderate traffic |
| tertiary | 16.0 | 9.9 | Light traffic |
| residential | 15.0 | 9.3 | Residential streets |
| trunk | 15.0 | 9.3 | May be dangerous/restricted |
| path | 12.0 | 7.5 | Shared paths |
| service | 12.0 | 7.5 | Service roads |
| living_street | 10.0 | 6.2 | Shared spaces |
| motorway | 10.0 | 6.2 | Highways (if allowed) |
| footway | 8.0 | 5.0 | Shared with pedestrians |
| pedestrian | 8.0 | 5.0 | Pedestrian areas |

## Implementation Details

### Code Example

Here's how travel speeds are applied during network processing:

```python
from socialmapper.isochrone.travel_modes import (
    TravelMode, 
    get_highway_speeds,
    get_default_speed
)
import osmnx as ox

# Get mode-specific configuration
travel_mode = TravelMode.DRIVE
highway_speeds = get_highway_speeds(travel_mode)
fallback_speed = get_default_speed(travel_mode)

# Download and process network
G = ox.graph_from_point(
    (latitude, longitude),
    network_type="drive",
    dist=5000
)

# Apply speeds with OSMnx 2.0's intelligent assignment
G = ox.add_edge_speeds(
    G, 
    hwy_speeds=highway_speeds,  # Our highway-type speeds
    fallback=fallback_speed     # Last resort fallback
)
G = ox.add_edge_travel_times(G)
```

### Speed Data Quality

The accuracy of isochrone boundaries depends on the quality of OpenStreetMap data in your area:

- **Areas with good coverage**: Most edges will have actual speed limits, resulting in highly accurate isochrones
- **Areas with sparse coverage**: The system falls back to highway-type speeds, which still provide reasonable estimates
- **Rural or unmapped areas**: May rely more heavily on statistical imputation and fallback speeds

## Customizing Speeds

While SocialMapper's default speeds are based on typical real-world conditions, you may need to adjust them for specific use cases:

- **Urban congestion**: Reduce speeds during peak hours
- **Rural areas**: May have higher actual speeds than defaults
- **Special conditions**: Weather, construction, or events affecting travel

Currently, speed customization requires modifying the source code in `socialmapper/isochrone/travel_modes.py`.

## Speed Validation

SocialMapper enforces speed limits for each travel mode:

| Mode | Minimum Speed | Maximum Speed |
|------|--------------|---------------|
| Walk | 3.0 km/h (1.9 mph) | 7.0 km/h (4.3 mph) |
| Bike | 8.0 km/h (5.0 mph) | 30.0 km/h (18.6 mph) |
| Drive | 20.0 km/h (12.4 mph) | 130.0 km/h (80.8 mph) |

These limits prevent unrealistic speed assignments that could distort isochrone boundaries.

## See Also

- [Travel Time Analysis](../user-guide/travel-time.md) - Using isochrones in analysis
- [Travel Modes Tutorial](../tutorials/travel-modes-tutorial.md) - Practical examples
- [OSMnx Documentation](https://osmnx.readthedocs.io/) - Detailed routing information