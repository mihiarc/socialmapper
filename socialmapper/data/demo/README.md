# SocialMapper Demo Data

This directory contains sample data for the SocialMapper demo module, enabling users to explore the library without requiring Census API keys.

## Purpose

The demo data reduces onboarding friction by allowing users to:
- Experience SocialMapper's capabilities immediately (<2 minutes)
- See realistic results without API setup
- Understand the library's value before configuration

## Available Locations

### Portland, Oregon
- **Coordinates**: (45.5152, -122.6784)
- **Population**: ~29,000 in demo area
- **Features**: Excellent library coverage, diverse food options
- **Sample Data**: 15 census blocks, 20 POIs

### Chapel Hill, North Carolina
- **Coordinates**: (35.9132, -79.0558)
- **Population**: ~15,600 in demo area
- **Features**: College town with strong community amenities
- **Sample Data**: 10 census blocks, 15 POIs

### Durham, North Carolina
- **Coordinates**: (35.9940, -78.8986)
- **Population**: ~22,700 in demo area
- **Features**: Bull City with vibrant food scene
- **Sample Data**: 12 census blocks, 22 POIs

## Data Structure

Each location has three JSON files:

### 1. Isochrone Data (`{location}_isochrone.json`)
Pre-generated travel-time polygons:
- `15min_drive`: 15-minute driving isochrone
- `20min_drive`: 20-minute driving isochrone
- `15min_walk`: 15-minute walking isochrone

### 2. Census Data (`{location}_census.json`)
Demographic data for census block groups:
- Population
- Median household income
- Median age
- Geographic boundaries

### 3. POI Data (`{location}_pois.json`)
Points of interest including:
- Libraries
- Grocery stores and supermarkets
- Restaurants and cafes
- Hospitals and pharmacies
- Parks

## Data Sources

All data is synthetic but based on realistic patterns from:
- OpenStreetMap for POI locations and attributes
- US Census Bureau for demographic patterns
- OSMnx for isochrone geometries

## File Size

Total size: ~48KB (well under 1MB limit)
- Optimized for package distribution
- Fast loading times
- No network requests required

## Usage

```python
from socialmapper import demo

# Quick start demo
result = demo.quick_start("Portland, OR")

# Library accessibility
result = demo.show_libraries("Chapel Hill, NC")

# Food access analysis
result = demo.show_food_access("Durham, NC")

# List available demos
demo.list_available_demos()
```

## Data Freshness

Demo data represents typical conditions as of 2023-2024. For real-time, location-specific analysis:

1. Get a free Census API key at https://api.census.gov/data/key_signup.html
2. Set `CENSUS_API_KEY` environment variable
3. Use main SocialMapper API functions with any location

## Notes

- Demo data is read-only
- Real API calls provide more detailed and current information
- Isochrones are simplified for faster loading
- POI data focuses on key amenity categories
