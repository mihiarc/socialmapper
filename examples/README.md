# SocialMapper Examples

Welcome to the SocialMapper examples! This directory contains tutorials, demos, and real-world case studies to help you get started with SocialMapper.

## 📚 Quick Start

New to SocialMapper? Start here:

```bash
# Install SocialMapper first
pip install socialmapper

# Run the getting started tutorial
python examples/tutorials/01_getting_started.py
```

## 📁 Directory Structure

```
examples/
├── tutorials/          # Step-by-step tutorials for beginners
├── core/              # Demonstrations of core features
├── case_studies/      # Real-world analysis examples
├── data/              # Sample datasets
└── example_output/    # Sample output files
```

## 🎓 Tutorials (Start Here!)

Perfect for beginners - learn SocialMapper step by step:

### 1. **Getting Started** (`tutorials/01_getting_started.py`)
Learn the basics: finding POIs, generating isochrones, and analyzing demographics.

```bash
python examples/tutorials/01_getting_started.py
```

### 2. **Custom POIs** (`tutorials/02_custom_pois.py`)
Use your own points of interest from CSV files.

```bash
python examples/tutorials/02_custom_pois.py
```

## 🔧 Core Feature Demos

Explore specific SocialMapper capabilities:

### **Address Geocoding** (`core/address_geocoding.py`)
Convert addresses to coordinates with multiple geocoding providers.
- Batch geocoding
- Provider comparison
- Caching strategies

### **Neighbor System** (`core/neighbor_system.py`)
Efficient census block group lookups using the parquet-based system.
- Performance comparisons
- API usage examples
- Memory efficiency

### **OSMnx Integration** (`core/osmnx_integration.py`)
Advanced OpenStreetMap queries and network analysis.
- Custom OSM queries
- Network statistics
- Multi-modal routing

### **ZCTA Analysis** (`core/zcta_analysis.py`)
Compare block group vs ZIP code level analysis.
- ZCTA boundaries
- Trade-offs in geographic resolution
- Use case examples

### **Cary Police ZCTA Demo** (`core/cary_zcta_demo.py`)
Real-world ZCTA service demonstration using Cary, NC police station.
- Municipal planning use case
- ZCTA census data retrieval
- Service area analysis
- Local government applications

**CLI Usage Examples:**
```bash
# Run the demo
python examples/core/cary_zcta_demo.py

# Use the generated coordinates with ZCTA analysis
socialmapper --custom-coords output/cary_police_coords.csv --geographic-level zcta --travel-time 15

# Compare with block group analysis
socialmapper --custom-coords output/cary_police_coords.csv --geographic-level block-group --travel-time 15
```

### **Cold Cache Test** (`core/cold_cache_test.py`)
Test SocialMapper with no cached data.
- Fresh installation simulation
- Performance benchmarks
- Cache building strategies

### **Rich UI Demo** (`core/rich_ui_demo.py`)
Beautiful terminal output with progress tracking.
- Progress bars and spinners
- Formatted tables
- Status updates

## 🌍 Case Studies

Real-world examples with complete workflows:

### **Fuquay-Varina Library Analysis** (`case_studies/fuquay_varina_library.py`)
A complete accessibility analysis of a community library in North Carolina.
- Real location data
- Multiple census variables
- Performance optimization techniques

## 📊 Sample Data

Example datasets for testing:

- **`data/custom_coordinates.csv`** - Simple POI format example
- **`data/sample_addresses.csv`** - Addresses for geocoding demos
- **`data/trail_heads.csv`** - Large dataset (2,661 trails) for performance testing

## 🚀 Common Usage Patterns

### Basic Analysis
```python
from socialmapper import run_socialmapper

results = run_socialmapper(
    state="North Carolina",
    county="Wake County",
    place_type="library",
    travel_time=15,
    census_variables=['total_population', 'median_income']
)
```

### Custom POIs
```python
results = run_socialmapper(
    custom_coords_path="my_locations.csv",
    travel_time=10,
    census_variables=['total_population'],
    export_maps=True
)
```

### Batch Processing
```python
# Analyze multiple POI types
for poi_type in ['library', 'school', 'park']:
    results = run_socialmapper(
        state="California",
        county="Los Angeles County",
        place_type=poi_type,
        travel_time=15
    )
```

## 💡 Tips for Examples

1. **Start Simple**: Begin with tutorials before moving to advanced demos
2. **Check Dependencies**: Ensure SocialMapper is installed: `pip install socialmapper`
3. **API Keys**: Some features work better with a Census API key (set `CENSUS_API_KEY` environment variable)
4. **Performance**: First runs may be slower due to cache building
5. **Visualizations**: Set `export_maps=True` to generate map outputs

## 🆘 Troubleshooting

### Common Issues

- **Import Errors**: Make sure SocialMapper is installed
- **No Results**: Check internet connection and API availability
- **Slow Performance**: Normal on first run - caches will speed up subsequent runs
- **Memory Issues**: Use smaller datasets or reduce the number of census variables

### Getting Help

- Check the [main documentation](../docs/)
- Review error messages - they often suggest solutions
- Open an issue on GitHub for bugs

## 📈 Next Steps

After exploring these examples:

1. Create your own analysis with local data
2. Experiment with different travel times and modes
3. Compare accessibility across different communities
4. Share your findings!

---

Happy mapping! 🗺️✨