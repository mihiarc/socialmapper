# 2-Minute Quick Start

**No API keys needed!** Try SocialMapper with built-in demo data in under 2 minutes.

## Step 1: Install SocialMapper (30 seconds)

```bash
pip install socialmapper
```

## Step 2: Run Your First Analysis (60 seconds)

Open Python and run this complete example:

```python
from socialmapper import demo

# See available demo cities
demo.list_available_demos()

# Run instant analysis - no API keys required!
result = demo.quick_start("Portland, OR")

# That's it! You've analyzed:
# ✓ 15-minute drive from downtown Portland
# ✓ Found 4 libraries
# ✓ Reached 29,000+ people
# ✓ Analyzed demographics
```

## Step 3: See Visual Results (30 seconds)

The demo shows you:
- **Travel area**: 15-minute walk isochrone
- **Libraries found**: Names and distances
- **Population reached**: Total and demographics
- **Key insights**: Formatted analysis summary

## What Just Happened?

In 2 minutes, you've:

1. **Created an isochrone** - A travel-time polygon showing the area reachable in 15 minutes
2. **Found points of interest** - Located libraries within walking distance
3. **Analyzed demographics** - Retrieved population and income data
4. **Generated insights** - Produced actionable accessibility metrics

## Try More Examples

### Analyze Different Cities

```python
# Chapel Hill - College town
result = demo.quick_start("Chapel Hill, NC")

# Durham - Growing tech hub
result = demo.quick_start("Durham, NC")
```

**Available demo cities:** Portland OR, Chapel Hill NC, Durham NC

### Explore Specific Use Cases

```python
# Library accessibility analysis
demo.show_libraries("Portland, OR", travel_time=15)

# Food access analysis
demo.show_food_access("Durham, NC")
```

## Customize Your Analysis

### Change Travel Parameters

```python
result = demo.quick_start(
    location="Portland, OR",
    travel_time=20,        # 20 minutes instead of 15
    travel_mode="bike"     # Bike instead of walk
)
```

### Available Options

| Parameter | Options | Default |
|-----------|---------|---------|
| `travel_time` | 5, 10, 15, 20, 30 minutes | 15 |
| `travel_mode` | "walk", "bike", "drive" | "drive" |

## Understanding the Output

The demo returns a dictionary with:

```python
{
    "location": "Portland, OR",
    "area_sq_km": 125.4,
    "poi_count": 4,
    "pois": [...],           # List of POIs with names and distances
    "total_population": 29118,
    "median_income": 74746,
    "census_blocks": [...],  # Census block group data
    "isochrone": {...}       # GeoJSON travel-time polygon
}
```

## Ready for Real Data?

Once you've explored the demos, you can analyze any location with live data:

### Step 1: Get a Census API Key (Free)

1. Visit: https://api.census.gov/data/key_signup.html
2. Enter your email
3. Check email for your key

### Step 2: Set Your API Key

```bash
# Option 1: Environment variable
export CENSUS_API_KEY=your_key_here

# Option 2: .env file
echo "CENSUS_API_KEY=your_key_here" > .env
```

### Step 3: Use Live Data

```python
from socialmapper import create_isochrone, get_poi, get_census_data

# Now works with ANY location in the US
isochrone = create_isochrone("Seattle, WA", travel_time=15)
pois = get_poi("Seattle, WA", categories=["education"])
census = get_census_data(location=isochrone, variables=["population"])
```

## Common Questions

### "What cities are available in demo mode?"

Run `demo.list_available_demos()` to see all available cities with descriptions.

### "Can I save the results?"

Yes! The demo returns standard Python dictionaries that you can save:

```python
import json

result = demo.quick_start("Portland, OR")
with open("portland_analysis.json", "w") as f:
    json.dump(result, f, indent=2)
```

### "How accurate is the demo data?"

Demo data is pre-computed from real 2023 sources but simplified for speed. Live mode provides:
- Real-time OSM data
- Latest Census (2023 ACS)
- Precise network routing

### "What if I get an error?"

Demo mode requires no setup, so errors are rare. Common issues:

- **ModuleNotFoundError**: Run `pip install socialmapper`
- **ImportError**: Upgrade Python to 3.11+
- **Other**: Check our [GitHub Issues](https://github.com/mihiarc/socialmapper/issues)

## Next Steps

You've successfully run your first SocialMapper analysis! Here's where to go next:

### 1. Explore More Demos
- Try all available cities
- Test different travel modes
- Compare various POI types

### 2. Read the Documentation
- [API Reference](api-reference.md) - Complete function documentation
- [Installation Guide](getting-started/installation.md) - Detailed setup instructions

### 3. Build Something
- Analyze your own city
- Create accessibility reports
- Build interactive maps

### 4. Join the Community
- [GitHub Discussions](https://github.com/mihiarc/socialmapper/discussions)
- [Report Issues](https://github.com/mihiarc/socialmapper/issues)

---

**Remember**: You got from zero to analysis in 2 minutes. With live data, you can analyze any location in the United States with the same simple commands.