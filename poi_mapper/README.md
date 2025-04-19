# OpenStreetMap POI Query Tool

This tool allows you to query Points of Interest (POIs) from OpenStreetMap using the Overpass API.

## Prerequisites

- Python 3.7+
- `uv` package manager

## Setup

1. Create a virtual environment and install dependencies:

```bash
cd poi_mapper
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

If you don't have a requirements.txt file, you can install the dependencies directly:

```bash
uv pip install overpy pyyaml
```

## Usage

The tool takes a YAML configuration file and outputs POI data as JSON:

```bash
python poi_query.py YAML_CONFIG_FILE -o OUTPUT_FILE.json
```

Example:

```bash
python poi_query.py pharmacy_query.yml -o pharmacies.json
```

## Example: Pharmacy Query in Dodge City, Kansas

The `pharmacy_query.yml` file demonstrates how to query pharmacies in Dodge City, Kansas. It includes:

- POI type specification (`amenity`)
- Tag filtering for pharmacies (`amenity=pharmacy`)
- Bounding box coordinates for Dodge City
- Query timeout settings

## YAML Configuration Format

```yaml
# Main POI type (optional)
type: amenity

# Tags to filter the query (at least one tag required)
tags:
  amenity: pharmacy
  # Add more tags as needed

# Optional: Search for specific names (case insensitive)
# name: Walgreens

# Bounding box (south,west,north,east)
bbox: 37.7253,-100.0332,37.7872,-99.9391

# Query timeout in seconds
timeout: 30
```

## Output

The script outputs a JSON file with sections for:

- `nodes`: Point features
- `ways`: Line or area features
- `relations`: Complex features or collections

Each section contains the OSM ID, geographic coordinates, and associated tags. 