# SocialMapper Examples

This directory contains example files that demonstrate how to use the SocialMapper.

## Custom Coordinates Files

When using your own coordinates instead of querying OpenStreetMap, you need to provide the coordinates in a CSV or JSON file. These example files show the minimal required fields:

### CSV Format (`custom_coordinates.csv`)

```
id,name,lat,lon,state
1,"Main Library Downtown",37.7749,-122.4194,CA
2,"Central Park",40.7829,-73.9654,NY
...
```

Required fields:
- `lat`, `lon`: The latitude and longitude coordinates
- `state`: Two-letter state abbreviation or full state name

Optional fields:
- `id`: A unique identifier (will be auto-generated if missing)
- `name`: A descriptive name (will be auto-generated if missing)
- Any other columns will be added as tags

### JSON Format (`custom_coordinates.json`)

```json
[
  {
    "id": "lib-001",
    "name": "Main Library Downtown",
    "lat": 37.7749,
    "lon": -122.4194,
    "state": "CA"
  },
  ...
]
```

Required fields:
- `lat`, `lon`: The latitude and longitude coordinates
- `state`: Two-letter state abbreviation or full state name

Optional fields:
- `id`: A unique identifier (will be auto-generated if missing)
- `name`: A descriptive name (will be auto-generated if missing)
- `tags`: An object with additional metadata

## Running with Custom Coordinates

To use these custom coordinates files:

```bash
# Using CSV format
python socialmapper.py --custom-coords examples/custom_coordinates.csv --travel-time 15 --census-variables total_population

# Using JSON format
python socialmapper.py --custom-coords examples/custom_coordinates.json --travel-time 15 --census-variables total_population median_income
```