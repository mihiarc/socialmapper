# Travel Modes Tutorial

This tutorial demonstrates how to use different travel modes (walk, bike, drive) in SocialMapper to analyze accessibility. Different modes create different isochrone shapes based on the available transportation networks.

## What You'll Learn

- Using walk, bike, and drive travel modes
- Understanding how travel modes affect isochrone shapes
- Choosing appropriate travel times for each mode
- Comparing accessibility across different transportation options
- Combining travel modes with custom POIs

## Understanding Travel Modes

SocialMapper supports three travel modes, each using different network data:

| Mode | Network Types | Typical Speed | Common Use Cases |
|------|--------------|---------------|------------------|
| **Walk** | Sidewalks, crosswalks, pedestrian paths | 3-4 mph | Neighborhood services, parks, schools |
| **Bike** | Bike lanes, shared roads, trails | 10-15 mph | Recreation, commuting, local services |
| **Drive** | Roads accessible by cars | Variable | Regional services, hospitals, shopping |

## Getting Started

### Import Required Libraries

```python
from socialmapper import SocialMapperBuilder, SocialMapperClient
from socialmapper.isochrone import TravelMode
```

You can specify travel modes either as strings (`"walk"`, `"bike"`, `"drive"`) or using the `TravelMode` enum. An enum (enumeration) is a set of named constants that make code more readable - instead of remembering that 0 means walk, 1 means bike, etc., you can use descriptive names like `TravelMode.WALK`.

## Example 1: Walking to Parks

Let's analyze 15-minute walking access to parks:

```python
config = (
    SocialMapperBuilder()
    .with_location("Chapel Hill", "NC")
    .with_osm_pois("leisure", "park")
    .with_travel_time(15)
    .with_travel_mode("walk")  # Walking mode
    .with_census_variables("total_population", "median_age")
    .limit_pois(3)  # Limit for demo
    .with_output_directory("output/walk_example")
    .build()
)

with SocialMapperClient() as client:
    result = client.run_analysis(config)
    
    if result.is_ok():
        data = result.unwrap()
        print(f"Found {data.poi_count} parks")
        print(f"Generated {data.isochrone_count} walking isochrones")
        print(f"Analyzed {data.census_units_analyzed} census units")
```

Output:
```
Found 3 parks
Generated 3 walking isochrones
Analyzed 46 census units
```

### Understanding Walking Isochrones

Walking isochrones typically:
- Cover 0.5-1 mile radius (15 minutes)
- Follow sidewalks and pedestrian paths
- Stop at major barriers (highways, rivers)
- Best for neighborhood-level analysis

## Example 2: Biking to Libraries

Analyze 10-minute bike access to libraries:

```python
config = (
    SocialMapperBuilder()
    .with_location("Chapel Hill", "NC")
    .with_osm_pois("amenity", "library")
    .with_travel_time(10)
    .with_travel_mode(TravelMode.BIKE)  # Using enum
    .with_census_variables("total_population", "median_household_income")
    .limit_pois(3)
    .with_output_directory("output/bike_example")
    .build()
)

with SocialMapperClient() as client:
    result = client.run_analysis(config)
    
    if result.is_ok():
        data = result.unwrap()
        print(f"Found {data.poi_count} libraries")
        print(f"Generated {data.isochrone_count} biking isochrones")
        print(f"Analyzed {data.census_units_analyzed} census units")
```

Output:
```
Found 3 libraries
Generated 3 biking isochrones
Analyzed 52 census units
```

### Biking Considerations

Biking isochrones:
- Cover 2-3 mile radius (10 minutes)
- Use bike lanes, trails, and bike-friendly roads
- Avoid highways but can cross at designated points
- Good for local commuting analysis

## Example 3: Driving to Hospitals

For regional services like hospitals, driving access is crucial:

```python
config = (
    SocialMapperBuilder()
    .with_location("Chapel Hill", "NC")
    .with_osm_pois("amenity", "hospital")
    .with_travel_time(20)
    .with_travel_mode("drive")  # Default mode
    .with_census_variables("total_population", "median_age")
    .limit_pois(2)
    .with_output_directory("output/drive_example")
    .build()
)

with SocialMapperClient() as client:
    result = client.run_analysis(config)
    
    if result.is_ok():
        data = result.unwrap()
        print(f"Found {data.poi_count} hospitals")
        print(f"Generated {data.isochrone_count} driving isochrones")
        print(f"Analyzed {data.census_units_analyzed} census units")
```

Output:
```
Found 2 hospitals
Generated 2 driving isochrones
Analyzed 105 census units
```

### Driving Analysis

Driving isochrones:
- Cover 10-20 mile radius (20 minutes)
- Follow road networks and speed limits
- Account for traffic patterns (when data available)
- Essential for regional service planning

## Example 4: Custom POIs with Travel Modes

You can combine custom POIs with different travel modes:

```python
from pathlib import Path

# Create custom POI file
custom_poi_file = Path("output/custom_pois.csv")
custom_poi_file.parent.mkdir(exist_ok=True)
custom_poi_file.write_text(
    "name,lat,lon\n"
    "UNC Campus,35.9049,-79.0482\n"
    "Franklin Street,35.9132,-79.0558\n"
    "Carrboro Plaza,35.9101,-79.0753\n"
)

# Analyze bike access to custom locations
config = (
    SocialMapperBuilder()
    .with_custom_pois(custom_poi_file)
    .with_travel_time(15)
    .with_travel_mode("bike")
    .with_census_variables("total_population", "median_age")
    .with_output_directory("output/custom_bike_example")
    .build()
)

with SocialMapperClient() as client:
    result = client.run_analysis(config)
```

## Comparing Travel Modes

Let's compare accessibility across modes for the same location:

```python
import pandas as pd
from tabulate import tabulate

# Run analysis for each mode
modes_data = []

for mode in ["walk", "bike", "drive"]:
    travel_time = {"walk": 15, "bike": 15, "drive": 15}[mode]
    
    config = (
        SocialMapperBuilder()
        .with_location("Downtown Raleigh", "NC")
        .with_osm_pois("amenity", "library")
        .with_travel_time(travel_time)
        .with_travel_mode(mode)
        .with_census_variables("total_population")
        .build()
    )
    
    with SocialMapperClient() as client:
        result = client.run_analysis(config)
        if result.is_ok():
            data = result.unwrap()
            modes_data.append({
                'Mode': mode.capitalize(),
                'Travel Time': f"{travel_time} min",
                'Population Reach': f"{data.total_population:,}",
                'Census Units': data.census_units_analyzed
            })

# Display comparison
df = pd.DataFrame(modes_data)
print("Travel Mode Comparison (15 minutes):")
print(tabulate(df, headers='keys', tablefmt='github', showindex=False))
```

Output:
```
Travel Mode Comparison (15 minutes):
| Mode  | Travel Time | Population Reach | Census Units |
|-------|-------------|------------------|--------------|
| Walk  | 15 min      | 12,500           | 18           |
| Bike  | 15 min      | 45,200           | 52           |
| Drive | 15 min      | 125,000          | 143          |
```

## Choosing the Right Mode and Time

### Recommended Travel Times by Mode and POI Type

| POI Type | Walk | Bike | Drive |
|----------|------|------|-------|
| Parks, Playgrounds | 10-15 min | 10-15 min | - |
| Schools | 15-20 min | 15 min | 10 min |
| Libraries | 15-20 min | 15-20 min | 15 min |
| Grocery Stores | 10-15 min | 15 min | 10-15 min |
| Hospitals | - | 30 min | 20-30 min |
| Regional Services | - | - | 30-45 min |

### Mode Selection Guidelines

**Use Walking when analyzing:**
- Neighborhood walkability
- Local community services
- Environmental justice (car-free populations)
- Urban planning initiatives

**Use Biking when analyzing:**
- Active transportation infrastructure
- Recreation access
- University/campus areas
- Bike-share service areas

**Use Driving when analyzing:**
- Regional services (hospitals, airports)
- Suburban accessibility
- Emergency service coverage
- Retail catchment areas

## Network Considerations

Different modes use different network data:

```python
# The network type is automatically selected based on travel mode
# You can see this in the network cache files:
# - walk_network_[hash].pkl.gz
# - bike_network_[hash].pkl.gz
# - drive_network_[hash].pkl.gz
```

### Network Characteristics

**Walking Networks include:**
- Sidewalks and footpaths
- Pedestrian crossings
- Parks and plazas
- Stairs and ramps

**Biking Networks include:**
- Bike lanes and paths
- Shared roadways
- Multi-use trails
- Low-traffic streets

**Driving Networks include:**
- All vehicle-accessible roads
- Highways and ramps
- Turn restrictions
- One-way streets

## Performance Tips

1. **Network Caching**: First run downloads network data; subsequent runs are much faster
2. **Mode-Specific Caching**: Each mode caches its own network data
3. **Appropriate Times**: Longer travel times exponentially increase computation
4. **POI Limits**: Use `.limit_pois()` for testing and demos

## Common Issues and Solutions

**Issue**: "No network data available"
- **Solution**: Ensure the area has OSM coverage; try a different location

**Issue**: "Isochrone generation timeout"
- **Solution**: Reduce travel time or limit POIs; check network connectivity

**Issue**: "Unexpected isochrone shapes"
- **Solution**: Verify the correct travel mode; check for network barriers

## Advanced Usage

### Custom Speed Settings

While not exposed in the current API, you can modify walking/biking speeds in the configuration for specialized analysis (e.g., elderly populations, e-bikes).

### Multi-Modal Analysis

Combine modes for comprehensive accessibility studies:

```python
# Analyze both walk and drive access to hospitals
# Useful for equity analysis
for mode in ["walk", "drive"]:
    # Run analysis for each mode
    # Compare populations with/without car access
```

## Next Steps

After completing this tutorial:

1. Compare isochrone shapes between modes for your area
2. Analyze equity by comparing walk vs drive accessibility
3. Study bike infrastructure gaps using bike mode
4. Combine with demographic analysis for transportation planning

## Full Code

The complete tutorial script is available at:
[`examples/tutorials/03_travel_modes.py`](https://github.com/mihiarc/socialmapper/blob/main/examples/tutorials/03_travel_modes.py)

## Key Takeaways

- Travel modes dramatically affect accessibility analysis
- Walking: neighborhood scale, environmental justice
- Biking: active transportation, medium-range access
- Driving: regional services, suburban analysis
- Always consider your population when choosing modes
- Network data quality affects results