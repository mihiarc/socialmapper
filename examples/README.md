# SocialMapper Examples

Welcome to the SocialMapper examples! This directory contains a comprehensive tutorial series and sample data to help you master SocialMapper.

## 📚 Quick Start

New to SocialMapper? Start here:

```bash
# Install SocialMapper
uv add socialmapper

# Run the first tutorial
uv run python examples/tutorials/01_getting_started.py
```

## 📁 Directory Structure

```
examples/
├── tutorials/          # 8 progressive tutorials (START HERE!)
├── data/              # Sample datasets for testing
└── README.md          # This file
```

## 🎓 Tutorials

**8 progressive tutorials** covering everything from basics to advanced techniques.

See the [complete tutorial guide](tutorials/README.md) for detailed descriptions.

### Quick Tutorial Overview

1. **Getting Started** - Complete workflow with isochrones, POIs, and demographics
2. **Travel Modes** - Compare walk, bike, and drive accessibility
3. **Census Demographics** - Deep dive into demographic analysis
4. **Custom POIs** - Import and analyze your own locations from CSV
5. **Combining Analysis** - Build sophisticated multi-step workflows
6. **Multi-Location** - Batch processing and coverage comparisons
7. **ZIP Code Analysis** - Work with ZCTA boundaries
8. **Address Geocoding** - Convert addresses to coordinates

### Run All Tutorials

```bash
cd examples/tutorials
uv run python 01_getting_started.py
uv run python 02_travel_modes.py
uv run python 03_census_demographics.py
# ... and so on
```

## 📊 Sample Data

Example datasets for testing:

- **`data/custom_coordinates.csv`** - Simple POI format example
- **`data/sample_addresses.csv`** - Addresses for geocoding demos

## 🚀 Common Usage Patterns

### Basic Isochrone Analysis
```python
from socialmapper import create_isochrone, get_census_blocks, get_census_data

# Create isochrone
iso = create_isochrone(
    location=(35.7796, -78.6382),  # Raleigh, NC
    travel_time=15,
    travel_mode="drive"
)

# Get demographics
blocks = get_census_blocks(polygon=iso)
data = get_census_data(
    location=[b['geoid'] for b in blocks[:30]],
    variables=['population', 'median_income']
)
```

### Custom POIs from CSV
```python
from socialmapper.api import import_poi_csv

# Load your locations
pois = import_poi_csv("my_locations.csv")

# Analyze each location
for poi in pois:
    iso = create_isochrone(
        location=(poi['lat'], poi['lon']),
        travel_time=10
    )
```

### Multi-Mode Comparison
```python
modes = ["drive", "bike", "walk"]

for mode in modes:
    iso = create_isochrone(location, travel_time=15, travel_mode=mode)
    print(f"{mode}: {iso['properties']['area_sq_km']:.2f} km²")
```

## 💡 Tips for Learning

1. **Follow the tutorial sequence** - They build progressively
2. **Start with short travel times** - Use 5-10 minutes for quick testing
3. **Experiment freely** - Modify locations, parameters, and variables
4. **Read the code** - Tutorials are heavily commented
5. **Use coordinates** - More reliable than address geocoding

## 🆘 Troubleshooting

### Common Issues

- **Import Errors**: Ensure SocialMapper is installed: `uv add socialmapper`
- **Slow Performance**: Normal on first run (building caches)
- **Census API Limits**: Sample blocks (first 20-30) for faster testing
- **Geocoding Failures**: Use coordinates instead of addresses

### Getting Help

- Check tutorial READMEs for detailed guidance
- Review error messages - they suggest solutions
- Open an issue on GitHub for bugs

## 📈 Next Steps

After completing the tutorials:

1. Analyze locations that matter to you
2. Build custom workflows for your use case
3. Explore the main SocialMapper documentation
4. Contribute your own examples!

## 🤝 Contributing

Found an issue or have a new tutorial idea?
- Open an issue on GitHub
- Submit a pull request
- Share your analysis examples

---

Happy mapping! 🗺️✨