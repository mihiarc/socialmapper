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

SocialMapper supports many POI categories. Here are the main groups:

### Food & Drink

```python
# Find restaurants
restaurants = get_poi(
    location="New York, NY",
    categories=["restaurant"],
    limit=20
)

# Find cafes
cafes = get_poi(
    location="New York, NY",
    categories=["cafe"],
    limit=20
)

# Find multiple food categories at once
food_places = get_poi(
    location="New York, NY",
    categories=["restaurant", "cafe", "fast_food", "bar"],
    limit=50
)
```

### Healthcare

```python
# Find hospitals
hospitals = get_poi(
    location="Chicago, IL",
    categories=["hospital"],
    limit=10
)

# Find pharmacies
pharmacies = get_poi(
    location="Chicago, IL",
    categories=["pharmacy"],
    limit=20
)

# Find clinics
clinics = get_poi(
    location="Chicago, IL",
    categories=["clinic"],
    limit=15
)
```

### Education

```python
# Find schools
schools = get_poi(
    location="Boston, MA",
    categories=["school"],
    limit=20
)

# Find universities
universities = get_poi(
    location="Boston, MA",
    categories=["university"],
    limit=10
)

# Find libraries
libraries = get_poi(
    location="Boston, MA",
    categories=["library"],
    limit=15
)
```

### Shopping

```python
# Find grocery stores
groceries = get_poi(
    location="Los Angeles, CA",
    categories=["grocery"],
    limit=20
)

# Find supermarkets
supermarkets = get_poi(
    location="Los Angeles, CA",
    categories=["supermarket"],
    limit=15
)

# Find convenience stores
convenience = get_poi(
    location="Los Angeles, CA",
    categories=["convenience"],
    limit=20
)
```

### Recreation

```python
# Find parks
parks = get_poi(
    location="Denver, CO",
    categories=["park"],
    limit=20
)

# Find gyms
gyms = get_poi(
    location="Denver, CO",
    categories=["gym"],
    limit=15
)
```

### Available Categories

Here's a comprehensive list of supported categories:

| Category Group | Categories |
|---------------|------------|
| **Food & Drink** | `restaurant`, `cafe`, `fast_food`, `bar`, `pub`, `food_court` |
| **Shopping** | `grocery`, `supermarket`, `convenience`, `mall`, `marketplace` |
| **Healthcare** | `hospital`, `clinic`, `pharmacy`, `doctors`, `dentist` |
| **Education** | `school`, `university`, `college`, `library`, `kindergarten` |
| **Finance** | `bank`, `atm` |
| **Transportation** | `bus_station`, `train_station`, `subway`, `parking` |
| **Recreation** | `park`, `playground`, `gym`, `sports_centre`, `swimming_pool` |
| **Services** | `post_office`, `police`, `fire_station`, `community_centre` |
| **Accommodation** | `hotel`, `hostel`, `motel` |

## Travel-Time Bounded Search

Instead of a fixed radius, search within a travel-time boundary:

```python
from socialmapper import get_poi

# Find restaurants within 15-minute walk
walkable_restaurants = get_poi(
    location="San Francisco, CA",
    categories=["restaurant"],
    travel_time=15,  # Creates an isochrone internally
    limit=50
)

print(f"Restaurants within 15-min walk: {len(walkable_restaurants)}")
```

This is useful for accessibility analysis—finding what's actually reachable rather than just nearby.

## Understanding POI Results

Each POI result contains:

```python
poi = get_poi("Portland, OR", categories=["cafe"], limit=1)[0]

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

restaurants = get_poi("Austin, TX", categories=["restaurant"], limit=20)

for r in restaurants:
    name = r['name']
    distance = r['distance_km']
    cuisine = r['tags'].get('cuisine', 'Unknown')
    website = r['tags'].get('website', 'No website')

    print(f"{name}")
    print(f"  Cuisine: {cuisine}")
    print(f"  Distance: {distance:.2f} km")
    print(f"  Website: {website}")
    print()
```

## Practical Examples

### Example 1: Healthcare Access Analysis

Find the nearest hospital and pharmacies:

```python
from socialmapper import get_poi

location = "Atlanta, GA"

# Find hospitals
hospitals = get_poi(location, categories=["hospital"], limit=5)
print("Nearest Hospitals:")
for h in hospitals:
    print(f"  {h['name']}: {h['distance_km']:.2f} km")

# Find pharmacies
pharmacies = get_poi(location, categories=["pharmacy"], limit=10)
print(f"\nNearest Pharmacies ({len(pharmacies)} found):")
for p in pharmacies[:5]:
    print(f"  {p['name']}: {p['distance_km']:.2f} km")
```

### Example 2: School Proximity Analysis

Find schools near a residential address:

```python
from socialmapper import get_poi

# Example residential location
home = (41.8781, -87.6298)  # Chicago

# Find schools within walking distance (1.5 km radius is default)
schools = get_poi(home, categories=["school"], limit=20)

# Categorize by distance
walking = [s for s in schools if s['distance_km'] <= 1.0]
short_drive = [s for s in schools if 1.0 < s['distance_km'] <= 3.0]

print(f"Schools within 1 km (walking): {len(walking)}")
for s in walking:
    print(f"  {s['name']}: {s['distance_km']:.2f} km")

print(f"\nSchools within 3 km (short drive): {len(short_drive)}")
```

### Example 3: Food Desert Identification

Check if an area has adequate grocery access:

```python
from socialmapper import get_poi, create_isochrone

location = "Detroit, MI"

# Find grocery stores within 15-minute walk
groceries = get_poi(
    location,
    categories=["grocery", "supermarket"],
    travel_time=15,
    limit=50
)

print(f"Grocery stores within 15-min walk: {len(groceries)}")

if len(groceries) < 3:
    print("WARNING: This area may be a food desert")
else:
    print("Good grocery access")

# List the stores
for g in groceries[:5]:
    print(f"  {g['name']}: {g['distance_km']:.2f} km")
```

### Example 4: Business Competition Analysis

Find competitors near a potential business location:

```python
from socialmapper import get_poi

# Potential location for new coffee shop
new_location = (47.6062, -122.3321)  # Seattle

# Find existing coffee shops nearby
competitors = get_poi(
    new_location,
    categories=["cafe"],
    limit=30
)

# Analyze competition density
within_500m = [c for c in competitors if c['distance_km'] <= 0.5]
within_1km = [c for c in competitors if c['distance_km'] <= 1.0]

print(f"Competition Analysis:")
print(f"  Within 500m: {len(within_500m)} coffee shops")
print(f"  Within 1km: {len(within_1km)} coffee shops")

if len(within_500m) > 5:
    print("  High competition - consider another location")
elif len(within_500m) < 2:
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

# Get POIs (larger search area)
restaurants = get_poi("Minneapolis, MN", categories=["restaurant"], limit=100)

# Filter to only those inside the isochrone
accessible = []
for r in restaurants:
    point = Point(r['lon'], r['lat'])
    if polygon.contains(point):
        accessible.append(r)

print(f"Restaurants within 10-min walk: {len(accessible)}")
```

## Importing Custom POIs

Load your own POI data from a CSV file:

```python
from socialmapper import import_poi_csv

# CSV format: name, latitude, longitude, type
# Example: "Coffee House", 47.6062, -122.3321, "cafe"

custom_pois = import_poi_csv(
    csv_path="my_locations.csv",
    name_field="name",
    lat_field="latitude",
    lon_field="longitude",
    type_field="type"
)

print(f"Loaded {len(custom_pois)} custom POIs")
```

## Best Practices

### 1. Use Appropriate Limits

```python
# For analysis: get more POIs
pois = get_poi(location, categories=["restaurant"], limit=100)

# For display: limit results
pois = get_poi(location, categories=["restaurant"], limit=10)
```

### 2. Combine Categories Strategically

```python
# Food access analysis - combine all food-related categories
food_access = get_poi(
    location,
    categories=["grocery", "supermarket", "convenience", "marketplace"],
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

### 4. Validate Coordinates

```python
# SocialMapper validates by default, but you can disable for speed
pois = get_poi(location, validate_coords=False)  # Faster but riskier
```

## Next Steps

Now that you can find POIs:

- **[Census Data](04-census-data.md)** - Add demographic context
- **[Mapping](05-mapping-visualization.md)** - Visualize your POIs
- **[Complete Workflow](06-complete-workflow.md)** - Full analysis examples
