# Mapping and Visualization

This tutorial teaches you how to create choropleth maps and export geographic data in various formats.

## Overview

SocialMapper's `create_map()` function generates choropleth maps—thematic maps where geographic areas are colored according to a data variable.

## Basic Map Creation

### Creating a Simple Map

```python
from socialmapper import get_census_blocks, get_census_data, create_map

# Step 1: Get geographic areas
blocks = get_census_blocks(location=(47.6062, -122.3321), radius_km=3)

# Step 2: Get data for those areas
geoids = [b['geoid'] for b in blocks]
census_result = get_census_data(geoids, variables=["population"])

# Step 3: Combine geometry with data
for block in blocks:
    data = census_result.data.get(block['geoid'], {})
    block['population'] = data.get('population', 0)

# Step 4: Create the map
map_result = create_map(
    data=blocks,
    column="population",
    title="Population by Census Block Group"
)

print(f"Map format: {map_result.format}")
print(f"Image size: {len(map_result.image_data)} bytes")
```

## Export Formats

### PNG (Default)

```python
result = create_map(data=blocks, column="population", export_format="png")

# Save to file
with open("population_map.png", "wb") as f:
    f.write(result.image_data)
```

### PDF

```python
result = create_map(data=blocks, column="population", export_format="pdf")

with open("population_map.pdf", "wb") as f:
    f.write(result.image_data)
```

### SVG

```python
result = create_map(data=blocks, column="population", export_format="svg")

# SVG is text-based
with open("population_map.svg", "w") as f:
    f.write(result.image_data.decode())
```

### GeoJSON

```python
result = create_map(data=blocks, column="population", export_format="geojson")

# Returns GeoJSON dict (not bytes)
geojson_data = result.geojson_data
print(geojson_data['type'])  # FeatureCollection
print(f"Features: {len(geojson_data['features'])}")
```

### Shapefile

```python
# Shapefile requires save_path
result = create_map(
    data=blocks,
    column="population",
    export_format="shapefile",
    save_path="population_map.shp"
)

print(f"Saved to: {result.file_path}")
```

## Saving Maps to Files

### Direct Save

```python
# Save directly during creation
result = create_map(
    data=blocks,
    column="population",
    save_path="my_map.png",
    export_format="png"
)

print(f"Saved to: {result.file_path}")  # Absolute path
```

### In-Memory Then Save

```python
# Get bytes first
result = create_map(data=blocks, column="population")

# Then save manually
with open("my_map.png", "wb") as f:
    f.write(result.image_data)
```

## Map Customization

### Adding a Title

```python
result = create_map(
    data=blocks,
    column="population",
    title="Seattle Area Population by Block Group"
)
```

### Map Metadata

```python
result = create_map(data=blocks, column="population", title="Population")

# Access metadata
print(result.metadata)
# {'column': 'population', 'title': 'Population', 'num_features': 42, 'column_type': 'int64'}
```

## Complete Mapping Workflows

### Example 1: Population Density Map

```python
from socialmapper import create_isochrone, get_census_blocks, get_census_data, create_map

# Create area of interest
isochrone = create_isochrone("Boston, MA", travel_time=20)

# Get census blocks
blocks = get_census_blocks(polygon=isochrone)
print(f"Found {len(blocks)} census block groups")

# Get population data
geoids = [b['geoid'] for b in blocks]
census_result = get_census_data(geoids, variables=["population"])

# Calculate population density
for block in blocks:
    data = census_result.data.get(block['geoid'], {})
    pop = data.get('population', 0) or 0
    area = block['area_sq_km'] or 0.01  # Avoid division by zero

    block['population'] = pop
    block['density'] = pop / area  # People per km²

# Create density map
result = create_map(
    data=blocks,
    column="density",
    title="Population Density (people/km²)",
    save_path="boston_density.png"
)

print(f"Map saved to: {result.file_path}")
```

### Example 2: Income Map

```python
from socialmapper import create_isochrone, get_census_blocks, get_census_data, create_map

# Define area
isochrone = create_isochrone("San Francisco, CA", travel_time=15)
blocks = get_census_blocks(polygon=isochrone)

# Get income data
geoids = [b['geoid'] for b in blocks]
census_result = get_census_data(geoids, variables=["median_income"])

# Add income to blocks
for block in blocks:
    data = census_result.data.get(block['geoid'], {})
    block['median_income'] = data.get('median_income', 0) or 0

# Filter out blocks with no income data
blocks_with_data = [b for b in blocks if b['median_income'] > 0]

# Create map
result = create_map(
    data=blocks_with_data,
    column="median_income",
    title="Median Household Income by Block Group",
    save_path="sf_income.png"
)
```

### Example 3: Multi-Variable Analysis

```python
from socialmapper import create_isochrone, get_census_blocks, get_census_data, create_map

location = "Chicago, IL"
isochrone = create_isochrone(location, travel_time=20)
blocks = get_census_blocks(polygon=isochrone)

# Get multiple variables
geoids = [b['geoid'] for b in blocks]
census_result = get_census_data(
    geoids,
    variables=["population", "median_income", "median_age"]
)

# Add all variables to blocks
for block in blocks:
    data = census_result.data.get(block['geoid'], {})
    block['population'] = data.get('population', 0) or 0
    block['median_income'] = data.get('median_income', 0) or 0
    block['median_age'] = data.get('median_age', 0) or 0

# Create maps for each variable
variables = ['population', 'median_income', 'median_age']
titles = ['Population', 'Median Income', 'Median Age']

for var, title in zip(variables, titles):
    # Filter blocks with data for this variable
    valid_blocks = [b for b in blocks if b[var] > 0]

    if valid_blocks:
        result = create_map(
            data=valid_blocks,
            column=var,
            title=f"{title} - Chicago Area",
            save_path=f"chicago_{var}.png"
        )
        print(f"Created {result.file_path}")
```

## Working with GeoDataFrames

### Converting to GeoDataFrame

```python
import geopandas as gpd
from shapely.geometry import shape
from socialmapper import get_census_blocks, get_census_data

# Get data
blocks = get_census_blocks(location=(40.7128, -74.0060), radius_km=2)
geoids = [b['geoid'] for b in blocks]
census_result = get_census_data(geoids, variables=["population"])

# Add census data
for block in blocks:
    data = census_result.data.get(block['geoid'], {})
    block['population'] = data.get('population', 0)

# Convert to GeoDataFrame
geometries = [shape(b['geometry']) for b in blocks]
properties = [{k: v for k, v in b.items() if k != 'geometry'} for b in blocks]

gdf = gpd.GeoDataFrame(properties, geometry=geometries, crs="EPSG:4326")
print(gdf.head())
```

### Using create_map with GeoDataFrame

```python
# create_map accepts GeoDataFrames directly
result = create_map(
    data=gdf,
    column="population",
    title="Population Map"
)
```

## Exporting for Web Maps

### GeoJSON for Leaflet/Mapbox

```python
from socialmapper import create_map

# Export as GeoJSON
result = create_map(
    data=blocks,
    column="population",
    export_format="geojson"
)

# Save for web
import json
with open("map_data.geojson", "w") as f:
    json.dump(result.geojson_data, f)

# Now you can use this with Leaflet, Mapbox, etc.
```

### Example: Folium Integration

```python
import folium
from shapely.geometry import shape
from socialmapper import get_census_blocks, get_census_data

# Get data
location = (47.6062, -122.3321)
blocks = get_census_blocks(location=location, radius_km=2)
geoids = [b['geoid'] for b in blocks]
census_result = get_census_data(geoids, variables=["population"])

# Add population to blocks
for block in blocks:
    data = census_result.data.get(block['geoid'], {})
    block['population'] = data.get('population', 0)

# Create Folium map
m = folium.Map(location=list(location), zoom_start=13)

# Add each block as a polygon
for block in blocks:
    geom = shape(block['geometry'])
    pop = block['population']

    # Simple color scale
    if pop > 3000:
        color = 'red'
    elif pop > 1500:
        color = 'orange'
    else:
        color = 'green'

    folium.GeoJson(
        block['geometry'],
        style_function=lambda x, c=color: {
            'fillColor': c,
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0.6
        },
        tooltip=f"Population: {pop:,}"
    ).add_to(m)

# Save
m.save("interactive_map.html")
```

## Best Practices

### 1. Filter Out Missing Data

```python
# Remove blocks with no data before mapping
valid_blocks = [b for b in blocks if b.get('population', 0) > 0]
result = create_map(data=valid_blocks, column="population")
```

### 2. Handle Zero Values

```python
# Calculate density safely
for block in blocks:
    area = block['area_sq_km'] if block['area_sq_km'] > 0 else 0.01
    block['density'] = block.get('population', 0) / area
```

### 3. Choose Appropriate Columns

```python
# Verify column exists before mapping
if 'population' in blocks[0]:
    result = create_map(data=blocks, column="population")
else:
    print("Column not found in data")
```

### 4. Use Descriptive Titles

```python
# Good titles describe what the map shows
create_map(data=blocks, column="density", title="Population Density (people/km²)")
create_map(data=blocks, column="median_income", title="Median Household Income ($)")
```

## Map Result Reference

```python
result = create_map(data=blocks, column="population")

# MapResult attributes
result.format        # 'png', 'pdf', 'svg', 'geojson', 'shapefile'
result.image_data    # bytes (for image formats)
result.geojson_data  # dict (for geojson format)
result.file_path     # Path (when save_path is provided)
result.metadata      # dict with column info, title, etc.
```

## Next Steps

Now that you can create maps:

- **[Complete Workflow](06-complete-workflow.md)** - Full analysis from start to finish
- **[Food Desert Case Study](07-food-desert-case-study.md)** - Real-world mapping application
