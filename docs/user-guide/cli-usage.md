# Command Line Usage

SocialMapper provides a command-line interface for running analyses without writing Python code.

## Basic Syntax

```bash
socialmapper [options]
```

## Input Methods

### POI Search

Find and analyze points of interest from OpenStreetMap:

```bash
socialmapper --poi --state "Texas" --county "Harris County" \
  --poi-type "amenity" --poi-name "library" --travel-time 15
```

### Custom Locations

Analyze your own locations from a CSV file:

```bash
socialmapper --custom-coords my_locations.csv --travel-time 15
```

### Address Geocoding

Convert addresses to coordinates and analyze:

```bash
socialmapper --addresses --address-file addresses.csv \
  --travel-time 20 --geocoding-provider census
```

## Common Options

### Travel Time
```bash
# Set travel time (1-120 minutes)
socialmapper --poi --state "California" --county "Los Angeles County" \
  --place-type "hospital" --travel-time 20
```

### Census Variables
```bash
# Add demographic variables
socialmapper --custom-coords locations.csv \
  --census-variables total_population median_age median_income
```

### Geographic Level
```bash
# Use ZIP codes instead of block groups
socialmapper --custom-coords locations.csv \
  --geographic-level zcta
```

### Export Options
```bash
# Export CSV and maps
socialmapper --custom-coords locations.csv \
  --export-csv --export-maps
```

## POI Search Parameters

When using `--poi`, specify:

- `--state` - State name or abbreviation
- `--county` - County name (include "County")
- `--poi-type` - OpenStreetMap type (e.g., "amenity")
- `--poi-name` - Specific name (e.g., "library")

Or use simplified:
- `--place-type` - Common place type (e.g., "library", "school")

### Examples

```bash
# Find libraries
socialmapper --poi --state "Illinois" --county "Cook County" \
  --place-type "library" --travel-time 15

# Find all amenities named "hospital"
socialmapper --poi --state "Florida" --county "Miami-Dade County" \
  --poi-type "amenity" --poi-name "hospital" --travel-time 20
```

## Custom Coordinates

Required CSV format:
```csv
name,latitude,longitude
Location 1,35.7796,-78.6382
Location 2,35.8934,-78.8637
```

Usage:
```bash
socialmapper --custom-coords my_locations.csv \
  --travel-time 15 --export-csv
```

## Address Geocoding

For address-based analysis:

```bash
# Basic address geocoding
socialmapper --addresses --address-file addresses.csv

# With specific provider
socialmapper --addresses --address-file addresses.csv \
  --geocoding-provider census

# With quality threshold
socialmapper --addresses --address-file addresses.csv \
  --geocoding-quality exact
```

## Output Control

### Output Directory
```bash
# Custom output location
socialmapper --custom-coords locations.csv \
  --output-dir my_results
```

### Export Formats
```bash
# CSV only (default)
socialmapper --custom-coords locations.csv --export-csv

# Add maps
socialmapper --custom-coords locations.csv \
  --export-csv --export-maps

# Add isochrones
socialmapper --custom-coords locations.csv \
  --export-csv --export-isochrones
```

## Advanced Options

### Census API Key
```bash
# Provide API key
socialmapper --custom-coords locations.csv \
  --api-key YOUR_CENSUS_API_KEY

# Or set environment variable
export CENSUS_API_KEY=YOUR_KEY
socialmapper --custom-coords locations.csv
```

### Quiet Mode
```bash
# Reduce output verbosity
socialmapper --custom-coords locations.csv --quiet
```

### Version Information
```bash
# Check version
socialmapper --version
```

## Complete Examples

### Urban Library Analysis
```bash
socialmapper --poi \
  --state "New York" \
  --county "New York County" \
  --place-type "library" \
  --travel-time 15 \
  --census-variables total_population median_income \
  --export-csv \
  --export-maps
```

### Rural Healthcare Access
```bash
socialmapper --poi \
  --state "Montana" \
  --county "Yellowstone County" \
  --place-type "hospital" \
  --travel-time 45 \
  --geographic-level zcta \
  --census-variables total_population percent_poverty \
  --export-csv
```

### Custom Facility Analysis
```bash
socialmapper --custom-coords facilities.csv \
  --travel-time 20 \
  --census-variables total_population median_age percent_without_vehicle \
  --export-csv \
  --export-maps \
  --output-dir facility_analysis
```

## Getting Help

```bash
# Show all options
socialmapper --help

# Show version
socialmapper --version
```

## Tips

1. **Use quotes** around multi-word values: `--state "New York"`
2. **Include "County"** in county names: `--county "Los Angeles County"`
3. **Check spelling** of place names and types
4. **Start simple** with fewer options, then add more
5. **Use --quiet** for scripting and automation

## Next Steps

- Explore [available census variables](demographics.md)
- Learn about [travel time options](travel-time.md)
- Understand [output formats](exporting-results.md)