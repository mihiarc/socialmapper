# Simple SocialMapper Tutorials

These tutorials demonstrate the **direct, simple API** of SocialMapper - no complex abstractions, just straightforward function calls.

## 🎯 Philosophy

- **Direct functions** - No unnecessary client classes
- **Simple imports** - Import only what you need
- **Composable** - Build complex analyses from simple parts
- **Fast to learn** - Get productive in minutes

## 📚 Tutorials

### 1. [Basic Isochrone Creation](01_basic_isochrone.py)
Learn the fundamentals of creating travel-time polygons.
- Creating isochrones from addresses or coordinates
- Different travel modes (drive, walk, bike)
- Output formats (GeoDataFrame vs dictionary)
- Comparing travel times

```python
from socialmapper.api import create_isochrone

isochrone = create_isochrone("Portland, OR", travel_time=15)
```

### 2. [Census Data Access](02_census_data.py)
Work directly with census and demographic data.
- Getting census data for geographic areas
- Using standard demographic variables
- Reverse geocoding locations
- Custom census variables

```python
from socialmapper import get_census_data_for_isochrone

demographics = get_census_data_for_isochrone(isochrone, variables=["B01003_001E"])
```

### 3. [Combining Analysis](03_combining_analysis.py)
Combine spatial and demographic analysis for insights.
- Merging isochrones with demographics
- Accessibility analysis
- Transportation mode comparison
- Custom analysis workflows

```python
# Create isochrone
isochrone = create_isochrone("Durham, NC", travel_time=15)

# Add demographics
demographics = get_demographics_for_isochrone(isochrone)
```

### 4. [Advanced Multi-Location](04_advanced_multi_location.py)
Advanced techniques for analyzing multiple locations.
- Batch processing locations
- Service area overlap analysis
- Gap analysis for underserved areas
- Accessibility matrices
- Time-distance relationships

```python
# Process multiple locations
for location in locations:
    iso = create_isochrone(location, travel_time=10)
    # Analyze each area
```

## 🚀 Quick Start

1. **Install SocialMapper:**
   ```bash
   pip install socialmapper
   ```

2. **Set Census API key (optional, for demographic data):**
   ```bash
   export CENSUS_API_KEY="your-key-here"
   ```
   Get a free key at: https://api.census.gov/data/key_signup.html

3. **Run a tutorial:**
   ```bash
   python 01_basic_isochrone.py
   ```

## 💡 Key Concepts

### Direct Function Calls
Instead of complex client classes, use functions directly:

```python
# ❌ Old way (unnecessary abstraction)
client = SocialMapper(api_key="...")
result = client.analyze_location(...)

# ✅ New way (simple and direct)
from socialmapper.api import create_isochrone
isochrone = create_isochrone("Portland, OR", travel_time=15)
```

### Composable Functions
Build complex analyses from simple parts:

```python
# Step 1: Create isochrone
iso = create_isochrone(location, time=15)

# Step 2: Get demographics
demo = get_census_data_for_isochrone(iso, variables)

# Step 3: Analyze results
population = demo['B01003_001E'].sum()
```

### Flexible Output Formats
Choose the format that works for you:

```python
# As GeoDataFrame (for spatial analysis)
gdf = create_isochrone(location, travel_time=15)

# As dictionary (for JSON/web APIs)
dict = create_isochrone(location, travel_time=15, return_type="dict")
```

## 📊 Common Use Cases

### Find 15-minute city amenities
```python
iso = create_isochrone("City Hall, Portland", travel_time=15, travel_mode="walk")
```

### Compare transportation options
```python
for mode in ["drive", "bike", "walk"]:
    iso = create_isochrone(location, travel_time=20, travel_mode=mode)
```

### Analyze demographic reach
```python
iso = create_isochrone(store_location, travel_time=10)
customers = get_census_data_for_isochrone(iso, ["B01003_001E"])
```

## 🛠️ Requirements

- Python 3.8+
- SocialMapper package
- Internet connection (for geocoding and OSM data)
- Census API key (optional, for demographic data)

## 📝 Notes

- Geocoding uses free services (Nominatim/Census)
- Isochrone generation uses OpenStreetMap data
- Census data requires free API key for best results
- All tutorials designed to run quickly (< 1 minute each)

## 🤝 Contributing

Found an issue or have suggestions? Please open an issue on GitHub!

## 📜 License

These tutorials are part of the SocialMapper project and follow the same license.