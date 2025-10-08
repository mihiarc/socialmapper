# SocialMapper Tutorials

A comprehensive, progressive tutorial series to master SocialMapper's geospatial analysis capabilities.

## 🎯 Learning Path

These tutorials build progressively from basic concepts to advanced techniques. Follow them in order for the best learning experience.

### Tutorial 1: Getting Started
**File:** `01_getting_started.py`
**Duration:** ~5 minutes
**Concepts:** Complete workflow, isochrones, POIs, census data, visualization

Your first complete SocialMapper analysis combining all core features:
- Creating travel-time isochrones
- Finding Points of Interest (POIs)
- Analyzing census demographics
- Creating choropleth maps

```bash
uv run python examples/tutorials/01_getting_started.py
```

### Tutorial 2: Travel Modes
**File:** `02_travel_modes.py`
**Duration:** ~3 minutes
**Concepts:** Walk, bike, drive modes, area comparison

Compare how different transportation modes affect accessibility:
- Walking isochrones (pedestrian paths)
- Biking isochrones (bike lanes and paths)
- Driving isochrones (road networks)
- Coverage area analysis

```bash
uv run python examples/tutorials/02_travel_modes.py
```

### Tutorial 3: Census Demographics
**File:** `03_census_demographics.py`
**Duration:** ~4 minutes
**Concepts:** Census API, demographic variables, aggregation

Deep dive into demographic analysis:
- Getting census block groups
- Fetching population, income, age data
- Working with housing statistics
- Aggregating and analyzing demographics

```bash
uv run python examples/tutorials/03_census_demographics.py
```

### Tutorial 4: Custom POIs
**File:** `04_custom_pois.py`
**Duration:** ~3 minutes
**Concepts:** CSV import, batch processing, comparative analysis

Analyze your own points of interest:
- CSV file format and requirements
- Importing custom POI locations
- Batch isochrone generation
- Comparing multiple locations

```bash
uv run python examples/tutorials/04_custom_pois.py
```

### Tutorial 5: Combining Analysis
**File:** `05_combining_analysis.py`
**Duration:** ~4 minutes
**Concepts:** Workflow composition, accessibility metrics

Build sophisticated analyses by combining features:
- Merging spatial and demographic data
- Accessibility analysis workflows
- Transportation mode comparison
- Custom analysis patterns

```bash
uv run python examples/tutorials/05_combining_analysis.py
```

### Tutorial 6: Multi-Location Analysis
**File:** `06_multi_location_analysis.py`
**Duration:** ~5 minutes
**Concepts:** Batch processing, overlap analysis, accessibility matrices

Advanced techniques for analyzing multiple locations:
- Batch processing multiple POIs
- Service area overlap detection
- Gap analysis for underserved areas
- Accessibility comparison matrices

```bash
uv run python examples/tutorials/06_multi_location_analysis.py
```

### Tutorial 7: ZIP Code Analysis
**File:** `07_zipcode_analysis.py`
**Duration:** ~4 minutes
**Concepts:** ZCTA boundaries, regional analysis

Work with ZIP Code Tabulation Areas (ZCTAs):
- ZCTA vs block group analysis
- Fetching ZCTA boundaries
- Regional demographic patterns
- Performance considerations

```bash
uv run python examples/tutorials/07_zipcode_analysis.py
```

### Tutorial 8: Address Geocoding
**File:** `08_address_geocoding.py`
**Duration:** ~3 minutes
**Concepts:** Geocoding services, address standardization, batch geocoding

Convert addresses to coordinates:
- Multiple geocoding providers
- Address validation and standardization
- Batch address geocoding
- Caching strategies for efficiency

```bash
uv run python examples/tutorials/08_address_geocoding.py
```

## 🚀 Quick Start

### Prerequisites

```bash
# Install SocialMapper
uv add socialmapper

# Set Census API key (optional but recommended)
export CENSUS_API_KEY="your-key-here"
```

Get a free Census API key at: https://api.census.gov/data/key_signup.html

### Run Your First Tutorial

```bash
uv run python examples/tutorials/01_getting_started.py
```

## 💡 API Philosophy

All tutorials use SocialMapper's **direct functional API**:

```python
from socialmapper import (
    create_isochrone,      # Generate travel-time polygons
    get_census_blocks,     # Find census block groups
    get_census_data,       # Fetch demographic data
    get_poi,               # Search for POIs
    create_map,            # Create choropleth maps
)

# Simple, direct function calls - no client classes needed
isochrone = create_isochrone(
    location=(35.7796, -78.6382),
    travel_time=15,
    travel_mode="drive"
)
```

**Key principles:**
- Direct functions, no abstractions
- Simple imports
- Composable building blocks
- Standard Python data structures (dicts, lists)
- Fast learning curve

## 📊 Common Patterns

### Basic Accessibility Analysis
```python
# 1. Create isochrone
iso = create_isochrone(location, travel_time=15, travel_mode="drive")

# 2. Get demographics
blocks = get_census_blocks(polygon=iso)
data = get_census_data(
    location=[b['geoid'] for b in blocks],
    variables=["population", "median_income"]
)

# 3. Analyze
total_population = sum(d['population'] for d in data.values())
```

### Multi-Location Comparison
```python
locations = [(35.7796, -78.6382), (35.9940, -78.8986)]

for loc in locations:
    iso = create_isochrone(loc, travel_time=10)
    # Compare coverage areas, demographics, etc.
```

### Transportation Mode Analysis
```python
modes = ["drive", "bike", "walk"]

for mode in modes:
    iso = create_isochrone(location, travel_time=15, travel_mode=mode)
    print(f"{mode}: {iso['properties']['area_sq_km']:.2f} km²")
```

## 🎓 Learning Tips

1. **Follow the sequence** - Tutorials build on each other
2. **Experiment** - Modify parameters and locations
3. **Read the code** - Each tutorial is heavily commented
4. **Check outputs** - Many tutorials create maps and visualizations
5. **Start small** - Use short travel times (5-10 min) while learning

## ⚡ Performance Tips

- **Cache warming**: First runs may be slower due to data downloads
- **Sample census blocks**: Limit to 20-30 blocks for faster API calls
- **Short travel times**: Use 5-10 minutes for quick testing
- **ZCTA vs blocks**: ZCTAs are faster for regional analysis

## 🆘 Troubleshooting

### Import Errors
```bash
# Ensure SocialMapper is installed
uv add socialmapper
```

### Slow Performance
- Normal on first run (building caches)
- Use smaller travel times while learning
- Sample census blocks (first 20-30)

### No Census Data
- Set `CENSUS_API_KEY` environment variable
- Check internet connection
- Verify location is in the United States

### Geocoding Failures
- Use coordinates instead of addresses for reliability
- Tutorial files include coordinate dictionaries for common cities

## 📚 Next Steps

After completing these tutorials:

1. **Try your own locations** - Analyze areas you care about
2. **Custom analyses** - Build workflows for your use case
3. **Explore the API** - Check the main documentation
4. **Share insights** - Contribute examples back to the community

## 🤝 Contributing

Have ideas for new tutorials? Found an issue?
- Open an issue on GitHub
- Submit a pull request with improvements
- Share your own analysis examples

## 📖 Additional Resources

- **Main Documentation**: `/docs`
- **API Reference**: Check function docstrings
- **Example Data**: `/examples/data`
- **Project README**: `/README.md`

---

Happy mapping! 🗺️✨
