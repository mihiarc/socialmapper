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

<div class="grid cards" markdown>

-   :material-download:{ .lg .middle } **Installation**

    ---

    Install SocialMapper in minutes

    [:octicons-arrow-right-24: Installation guide](getting-started/installation.md)

-   :material-rocket:{ .lg .middle } **Quick Start**

    ---

    Your first analysis in 5 minutes

    [:octicons-arrow-right-24: Quick start tutorial](getting-started/quick-start.md)

-   :material-map-marker:{ .lg .middle } **Examples**

    ---

    Learn from practical examples

    [:octicons-arrow-right-24: View examples](https://github.com/mihiarc/socialmapper/tree/main/examples)

-   :material-help-circle:{ .lg .middle } **Get Help**

    ---

    Documentation and support

    [:octicons-arrow-right-24: User guide](user-guide/index.md)

</div>

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

## Why SocialMapper?

- **Free and Open Source** - No licensing fees or restrictions
- **Easy to Use** - Simple Python API and command line interface
- **Reliable Data** - Uses OpenStreetMap and US Census Bureau
- **Fast** - Optimized caching and efficient algorithms
- **Flexible** - Analyze any location type at any scale

Ready to explore your community? [Get started now →](getting-started/installation.md)