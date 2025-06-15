# SocialMapper Examples

Welcome to the SocialMapper examples! This directory contains tutorials, demos, and real-world case studies to help you get started with SocialMapper.

## 📚 Quick Start

New to SocialMapper? Start here:

```bash
# Install SocialMapper first
uv add socialmapper

# Run the getting started tutorial
python examples/tutorials/01_getting_started.py

# Try ZCTA analysis
python examples/zcta_analysis.py
```

## 📁 Directory Structure

```
examples/
├── tutorials/          # Step-by-step tutorials for beginners
├── demos/             # Comprehensive test demonstrations
├── core/              # Demonstrations of core features
├── case_studies/      # Real-world analysis examples
├── data/              # Sample datasets
├── zcta_analysis.py   # ZIP Code Tabulation Area example
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

## 🗺️ Geographic Analysis Examples

### **ZCTA Analysis** (`zcta_analysis.py`) ⭐️
Complete ZIP Code Tabulation Area analysis example.

```bash
python examples/zcta_analysis.py
```

**Features:**
- Fetch ZCTA boundaries for a state
- Get census demographics for specific ZCTAs
- Combine boundary and demographic data
- Generate analysis reports and CSV output

**Perfect for:**
- Business intelligence and market analysis
- Regional demographic studies
- ZIP code-level reporting
- Faster processing than block groups

## 🧪 Test Demos

Comprehensive demonstrations for testing and validation:

### **ZCTA Test Demos** (`demos/`)
Detailed test demonstrations for ZCTA functionality:

```bash
# Test ZCTA fundamentals
python examples/demos/zcta_fundamentals_demo.py

# Test POI integration
python examples/demos/zcta_poi_integration_demo.py

# Test modern Census API
python examples/demos/modern_zcta_api_demo.py

# Test TIGER boundary API
python examples/demos/tiger_api_boundaries_demo.py
```

See `demos/README_ZCTA_DEMOS.md` for detailed information.

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

### ZCTA Analysis
```python
from socialmapper import get_census_system

# Get census system
census_system = get_census_system()

# Fetch ZCTA boundaries
zctas = census_system._zcta_service.get_zctas_for_state("37")  # North Carolina

# Get census data
data = census_system._zcta_service.get_census_data(
    geoids=['27601', '27605', '27609'],
    variables=['B01003_001E', 'B19013_001E']
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
2. **Check Dependencies**: Ensure SocialMapper is installed: `uv add socialmapper`
3. **API Keys**: Some features work better with a Census API key (set `CENSUS_API_KEY` environment variable)
4. **Performance**: First runs may be slower due to cache building
5. **Visualizations**: Set `export_maps=True` to generate map outputs
6. **ZCTA vs Block Groups**: Use ZCTAs for faster regional analysis, block groups for detailed local analysis

## 🆘 Troubleshooting

### Common Issues

- **Import Errors**: Make sure SocialMapper is installed
- **No Results**: Check internet connection and API availability
- **Slow Performance**: Normal on first run - caches will speed up subsequent runs
- **Memory Issues**: Use smaller datasets or reduce the number of census variables
- **ZCTA Issues**: Ensure proper state FIPS codes and valid ZCTA identifiers

### Getting Help

- Check the [main documentation](../docs/)
- Review error messages - they often suggest solutions
- Open an issue on GitHub for bugs

## 📈 Next Steps

After exploring these examples:

1. Create your own analysis with local data
2. Experiment with different travel times and modes
3. Compare accessibility across different communities
4. Try ZCTA analysis for regional studies
5. Share your findings!

---

Happy mapping! 🗺️✨