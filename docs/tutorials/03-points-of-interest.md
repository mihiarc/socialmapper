# Finding Points of Interest

This tutorial teaches you how to discover and analyze points of interest (POIs) using OpenStreetMap data.

## What is a Point of Interest?

A POI is any location that might be useful or interesting: restaurants, hospitals, schools, parks, stores, etc. OpenStreetMap contains millions of these, and SocialMapper makes it easy to query them.

## Basic POI Queries

### Finding POIs Near a Location

```python
from socialmapper import get_poi

# Find POIs near Seattle
pois = get_poi(
    location="Seattle, WA",
    limit=20
)

print(f"Found {len(pois)} points of interest")
for poi in pois[:5]:
    print(f"  {poi['name']}: {poi['category']} ({poi['distance_km']:.2f} km)")
```

### Using Coordinates

```python
# Space Needle coordinates
pois = get_poi(
    location=(47.6205, -122.3493),
    limit=10
)
```

## Filtering by Category

SocialMapper supports the following POI categories:

| Category | Description | Examples |
|----------|-------------|----------|
| `food_and_drink` | Restaurants, cafes, bars | Restaurants, coffee shops, pubs |
| `healthcare` | Medical facilities | Hospitals, clinics, pharmacies |
| `education` | Educational institutions | Schools, universities, libraries |
| `shopping` | Retail stores | Grocery stores, supermarkets, malls |
| `recreation` | Leisure facilities | Parks, gyms, sports centers |
| `accommodation` | Lodging | Hotels, hostels, motels |
| `transportation` | Transit | Bus stations, train stations |
| `services` | General services | Banks, post offices, police |
| `religious` | Places of worship | Churches, mosques, temples |
| `utilities` | Infrastructure | Gas stations, EV charging |

### Food & Drink

```python
# Find restaurants, cafes, and bars
food_places = get_poi(
    location="New York, NY",
    categories=["food_and_drink"],
    limit=50
)

print(f"Found {len(food_places)} food & drink places")
for place in food_places[:5]:
    print(f"  {place['name']}: {place['distance_km']:.2f} km")
```

### Healthcare

```python
# Find hospitals, clinics, pharmacies
healthcare = get_poi(
    location="Chicago, IL",
    categories=["healthcare"],
    limit=20
)

print(f"Found {len(healthcare)} healthcare facilities")
for h in healthcare[:5]:
    print(f"  {h['name']}: {h['distance_km']:.2f} km")
```

### Education

```python
# Find schools, universities, libraries
education = get_poi(
    location="Boston, MA",
    categories=["education"],
    limit=20
)

print(f"Found {len(education)} educational institutions")
```

### Shopping

```python
# Find grocery stores, supermarkets, etc.
shopping = get_poi(
    location="Los Angeles, CA",
    categories=["shopping"],
    limit=30
)

print(f"Found {len(shopping)} shopping locations")
```

### Recreation

```python
# Find parks, gyms, sports facilities
recreation = get_poi(
    location="Denver, CO",
    categories=["recreation"],
    limit=20
)

print(f"Found {len(recreation)} recreation spots")
```

### Multiple Categories

```python
# Query multiple categories at once
pois = get_poi(
    location="Seattle, WA",
    categories=["food_and_drink", "shopping"],
    limit=50
)

print(f"Found {len(pois)} food and shopping places")
```

## Travel-Time Bounded Search

Instead of a fixed radius, search within a travel-time boundary:

```python
from socialmapper import get_poi

# Find food places within 15-minute walk
walkable_food = get_poi(
    location="San Francisco, CA",
    categories=["food_and_drink"],
    travel_time=15,  # Creates an isochrone internally
    limit=50
)

print(f"Food places within 15-min walk: {len(walkable_food)}")
```

This is useful for accessibility analysis—finding what's actually reachable rather than just nearby.

## Understanding POI Results

Each POI result contains:

```python
poi = get_poi("Portland, OR", categories=["food_and_drink"], limit=1)[0]

print(poi.keys())
# dict_keys(['name', 'category', 'lat', 'lon', 'distance_km', 'address', 'tags'])

# Basic info
print(f"Name: {poi['name']}")
print(f"Category: {poi['category']}")
print(f"Location: ({poi['lat']}, {poi['lon']})")
print(f"Distance: {poi['distance_km']:.2f} km")

# Address (if available)
print(f"Address: {poi.get('address', 'Not available')}")

# Additional OSM tags
print(f"Tags: {poi['tags']}")
```

### Example: Extracting Useful Information

```python
from socialmapper import get_poi

food_places = get_poi("Austin, TX", categories=["food_and_drink"], limit=20)

for place in food_places[:5]:
    name = place['name']
    distance = place['distance_km']
    cuisine = place['tags'].get('cuisine', 'Unknown')
    website = place['tags'].get('website', 'No website')

    print(f"{name}")
    print(f"  Cuisine: {cuisine}")
    print(f"  Distance: {distance:.2f} km")
    print(f"  Website: {website}")
    print()
```

## Practical Examples

### Example 1: Healthcare Access Analysis

Find healthcare facilities near a location:

```python
from socialmapper import get_poi

location = "Atlanta, GA"

# Find healthcare facilities
healthcare = get_poi(location, categories=["healthcare"], limit=20)

print(f"Healthcare facilities near {location}:")
for h in healthcare[:10]:
    print(f"  {h['name']}: {h['distance_km']:.2f} km")
```

### Example 2: Food Access Analysis

Check grocery access for an area:

```python
from socialmapper import get_poi

location = "Detroit, MI"

# Find shopping (includes grocery stores)
shopping = get_poi(
    location,
    categories=["shopping"],
    travel_time=15,
    limit=50
)

print(f"Shopping within 15-min walk: {len(shopping)}")

if len(shopping) < 3:
    print("WARNING: Limited shopping access")
else:
    print("Good shopping access")
```

### Example 3: Education Proximity Analysis

Find schools near a residential address:

```python
from socialmapper import get_poi

# Example residential location
home = (41.8781, -87.6298)  # Chicago

# Find educational institutions
education = get_poi(home, categories=["education"], limit=20)

# Categorize by distance
walking = [s for s in education if s['distance_km'] <= 1.0]
short_drive = [s for s in education if 1.0 < s['distance_km'] <= 3.0]

print(f"Within 1 km (walking): {len(walking)}")
for s in walking:
    print(f"  {s['name']}: {s['distance_km']:.2f} km")

print(f"\nWithin 3 km (short drive): {len(short_drive)}")
```

### Example 4: Business Competition Analysis

Find competitors near a potential business location:

```python
from socialmapper import get_poi

# Potential location for new coffee shop
new_location = (47.6062, -122.3321)  # Seattle

# Find existing food & drink places
competitors = get_poi(
    new_location,
    categories=["food_and_drink"],
    limit=50
)

# Analyze competition density
within_500m = [c for c in competitors if c['distance_km'] <= 0.5]
within_1km = [c for c in competitors if c['distance_km'] <= 1.0]

print(f"Competition Analysis:")
print(f"  Within 500m: {len(within_500m)} food places")
print(f"  Within 1km: {len(within_1km)} food places")

if len(within_500m) > 10:
    print("  High competition - consider another location")
elif len(within_500m) < 3:
    print("  Low competition - good opportunity")
```

## Combining POIs with Isochrones

Find POIs within a specific travel-time boundary:

```python
from socialmapper import create_isochrone, get_poi
from shapely.geometry import shape, Point

# Create isochrone
isochrone = create_isochrone("Minneapolis, MN", travel_time=10, travel_mode="walk")
polygon = shape(isochrone['geometry'])

# Get food places (larger search area)
food = get_poi("Minneapolis, MN", categories=["food_and_drink"], limit=100)

# Filter to only those inside the isochrone
accessible = []
for f in food:
    point = Point(f['lon'], f['lat'])
    if polygon.contains(point):
        accessible.append(f)

print(f"Food places within 10-min walk: {len(accessible)}")
```

## Best Practices

### 1. Use Appropriate Limits

```python
# For analysis: get more POIs
pois = get_poi(location, categories=["food_and_drink"], limit=100)

# For display: limit results
pois = get_poi(location, categories=["food_and_drink"], limit=10)
```

### 2. Combine Categories Strategically

```python
# Essential services analysis
essential = get_poi(
    location,
    categories=["healthcare", "shopping", "education"],
    limit=50
)
```

### 3. Handle Missing Data

```python
for poi in pois:
    name = poi.get('name', 'Unnamed')
    address = poi.get('address', 'Address not available')
    phone = poi['tags'].get('phone', 'No phone listed')
```

## Next Steps

Now that you can find POIs:

- **[Census Data](04-census-data.md)** - Add demographic context
- **[Mapping](05-mapping-visualization.md)** - Visualize your POIs
- **[Complete Workflow](06-complete-workflow.md)** - Full analysis examples
