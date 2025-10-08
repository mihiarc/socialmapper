# Travel Time Analysis

Travel time analysis is at the heart of SocialMapper. It creates isochrones - areas reachable within a specific time - to understand accessibility.

## What are Isochrones?

Isochrones are geographic areas showing all locations reachable within a given travel time from a starting point. For example, a 15-minute isochrone shows everywhere you can reach in 15 minutes.

## Setting Travel Time

### Basic Usage

```python
from socialmapper import run_socialmapper

# 15-minute analysis (default)
results = run_socialmapper(
    state="Texas",
    county="Harris County",
    place_type="library",
    travel_time=15
)
```

### Different Time Intervals

```python
# 5-minute walk (tight urban area)
results = run_socialmapper(
    custom_coords_path="locations.csv",
    travel_time=5
)

# 30-minute drive (suburban/rural)
results = run_socialmapper(
    custom_coords_path="locations.csv", 
    travel_time=30
)
```

### Command Line

```bash
# Set travel time
socialmapper --poi --state "California" --county "Los Angeles County" \
  --place-type "hospital" --travel-time 20
```

## Travel Time Ranges

SocialMapper supports travel times from 1 to 120 minutes:

- **1-5 minutes**: Very local, walkable neighborhoods
- **10-15 minutes**: Standard urban accessibility
- **20-30 minutes**: Suburban reach
- **45-60 minutes**: Regional analysis
- **60+ minutes**: Large area coverage

## How It Works

1. **Starting Points**: Your POIs or custom locations
2. **Road Network**: Uses OpenStreetMap road data
3. **Travel Calculation**: Follows actual roads, not straight lines
4. **Area Generation**: Creates polygon showing reachable area
5. **Census Integration**: Finds all census blocks within the area

## Understanding Results

The travel time analysis affects what census data you receive:

```python
# Smaller area = fewer census blocks
results_5min = run_socialmapper(
    custom_coords_path="store.csv",
    travel_time=5
)

# Larger area = more census blocks
results_20min = run_socialmapper(
    custom_coords_path="store.csv",
    travel_time=20
)

print(f"5-min blocks: {len(results_5min['census_data'])}")
print(f"20-min blocks: {len(results_20min['census_data'])}")
```

## Practical Examples

### Compare Different Times

```python
# Analyze population reach at different intervals
for minutes in [5, 10, 15, 20, 30]:
    results = run_socialmapper(
        state="Illinois",
        county="Cook County",
        place_type="grocery_store",
        travel_time=minutes
    )
    
    total_pop = sum(
        row.get('total_population', 0) 
        for row in results['census_data']
    )
    
    print(f"{minutes} minutes: {total_pop:,} people")
```

### Service Area Planning

```python
# Find optimal service time
results_10 = run_socialmapper(
    custom_coords_path="new_clinic.csv",
    travel_time=10,
    census_variables=["total_population", "percent_poverty"]
)

results_20 = run_socialmapper(
    custom_coords_path="new_clinic.csv",
    travel_time=20,
    census_variables=["total_population", "percent_poverty"]
)

# Compare coverage
pop_10 = sum(r['total_population'] for r in results_10['census_data'])
pop_20 = sum(r['total_population'] for r in results_20['census_data'])

print(f"10-min reach: {pop_10:,} people")
print(f"20-min reach: {pop_20:,} people")
print(f"Additional reach: {pop_20 - pop_10:,} people")
```

## Performance Considerations

Larger travel times require more processing:

- **5-10 minutes**: Fast processing
- **15-20 minutes**: Moderate processing time
- **30+ minutes**: May take longer, especially in dense areas

Tips for better performance:
1. Start with smaller travel times for testing
2. Use fewer census variables
3. Analyze fewer locations at once
4. Enable caching (default)

## Common Use Cases

### Walking Distance (5-15 minutes)
- Neighborhood services
- Local parks
- Elementary schools
- Corner stores

### Short Drive (15-30 minutes)
- Shopping centers
- High schools
- Medical clinics
- Restaurants

### Longer Trips (30-60 minutes)
- Regional hospitals
- Airports
- Specialty services
- Employment centers

## Limitations

- Assumes normal traffic conditions
- Uses estimated travel speeds
- Doesn't account for:
  - Traffic congestion
  - Public transit
  - Barriers (rivers, highways)
  - Seasonal conditions

## Next Steps

- Choose appropriate [census variables](demographics.md)
- Learn to [export results](exporting-results.md)
- Understand [finding places](finding-places.md)