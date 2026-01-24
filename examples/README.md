# SocialMapper Examples

This directory contains example scripts demonstrating SocialMapper's capabilities.

## Quick Start

```bash
# Run the demo (no API key required)
uv run python examples/demo_quickstart.py

# Run the full quick start example
uv run python examples/quick_start.py
```

## Available Examples

| File | Description |
|------|-------------|
| `demo_quickstart.py` | Simple demo using pre-loaded data (no API key needed) |
| `quick_start.py` | Comprehensive example with multiple analysis types |
| `live_api_example.py` | Real API calls with Census key (requires CENSUS_API_KEY) |

## Sample Data

The `data/` directory contains sample CSV files for testing:

- `custom_coordinates.csv` - Simple POI format with lat/lon coordinates
- `sample_addresses.csv` - Addresses for geocoding examples
- `trail_heads.csv` - Trail head locations dataset

## Usage Patterns

### Basic Isochrone Analysis

```python
from socialmapper import create_isochrone, get_census_blocks, get_census_data

# Create isochrone from coordinates
iso = create_isochrone(
    location=(35.7796, -78.6382),  # Raleigh, NC
    travel_time=15,
    travel_mode="drive"
)

# Get census block groups in the area
blocks = get_census_blocks(polygon=iso)

# Get demographic data
data = get_census_data(
    location=[b['geoid'] for b in blocks[:30]],
    variables=['population', 'median_income']
)
```

### Demo Mode (No API Key)

```python
from socialmapper import demo

# List available demo cities
demo.list_available_demos()

# Run quick analysis
result = demo.quick_start("Portland, OR")
print(f"Found {result['poi_count']} libraries")
print(f"Population: {result['total_population']:,}")
```

### Multi-Mode Comparison

```python
from socialmapper import create_isochrone

location = "Chapel Hill, NC"
modes = ["drive", "bike", "walk"]

for mode in modes:
    iso = create_isochrone(location, travel_time=15, travel_mode=mode)
    print(f"{mode}: {iso['properties']['area_sq_km']:.2f} km²")
```

## Tips

- **Start with demo mode** - No API keys needed, instant results
- **Use short travel times** - 5-10 minutes for quick testing
- **Sample census blocks** - Limit to first 20-30 for faster API responses
- **Use coordinates** - More reliable than address geocoding

## Troubleshooting

- **Import errors**: Install SocialMapper with `uv add socialmapper`
- **Slow first run**: Normal - building network caches
- **Census API errors**: Check your API key is set correctly

## More Resources

- [Quick Start Guide](../docs/quick-start.md)
- [API Reference](../docs/api-reference.md)
- [GitHub Issues](https://github.com/mihiarc/socialmapper/issues)
