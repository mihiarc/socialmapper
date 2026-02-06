# Welcome to SocialMapper

SocialMapper helps you understand how people connect with important places in their community by analyzing travel times and demographics.

## What is SocialMapper?

SocialMapper is a Python tool that answers questions like:
- Who can reach the local library within a 15-minute walk?
- What areas are within 20 minutes of the nearest hospital?
- How many seniors live within driving distance of grocery stores?

It combines travel time analysis with demographic data to help you understand community accessibility.

## Key Features

### 🗺️ **Find Places**
Discover libraries, schools, hospitals, parks, and other community resources from OpenStreetMap. Or use the geocoding feature with a street address. 

### ⏱️ **Calculate Travel Times**
Generate isochrones (travel time areas) for walking, driving, or biking. [Walking and Biking functionality still under development]

### 📊 **Analyze Demographics**
Understand who lives within reach of your point of interest using Census data like population, income, and age.

### 📍 **Use Your Own Locations**
Analyze accessibility from your organization's facilities or any custom addresses.

## Quick Example

```python
from socialmapper import create_isochrone, get_census_data

# Create a 15-minute driving isochrone from downtown Raleigh
isochrone = create_isochrone(
    location=(35.7796, -78.6382),
    travel_time=15,
    travel_mode="drive"
)

# Get demographic data for the area
census_data = get_census_data(
    location=isochrone,
    variables=["population", "median_income"]
)

# Calculate total population
total_pop = sum(d.get('population', 0) for d in census_data.values())
print(f"Population within 15 minutes: {total_pop:,}")
```

## Get Started

Install SocialMapper and start analyzing:

```bash
pip install socialmapper
```

See the [API Reference](api-reference.md) for full documentation.

## Common Use Cases

### Urban Planning
- Analyze access to public facilities
- Identify underserved areas
- Plan new service locations

### Public Health
- Map healthcare accessibility
- Study food desert patterns
- Evaluate emergency service coverage

### Education
- Assess school accessibility
- Plan bus routes
- Identify transportation barriers

### Community Development
- Evaluate access to parks and recreation
- Study retail accessibility
- Support grant applications with data

### Rural Community Mapping
- Define communities by travel patterns instead of county lines
- Identify service gaps in the Great Plains, Mountain West, and rural South
- Understand the true service area of rural towns, hospitals, and schools
- [Read the full guide →](rural-community-mapping.md)

## Why SocialMapper?

- **Free and Open Source** - No licensing fees or restrictions
- **Easy to Use** - Simple 5-function Python API
- **Reliable Data** - Uses OpenStreetMap and US Census Bureau
- **Fast** - Valhalla routing returns isochrones in 1-2 seconds with built-in caching
- **Flexible** - Analyze any location type at any scale
- **Production Ready** - Comprehensive error handling, retry mechanisms, and monitoring

Ready to explore your community? [Get started now →](getting-started/installation.md)