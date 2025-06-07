# 📮 SocialMapper ZCTA Feature Demo

Welcome to the **ZIP Code Tabulation Area (ZCTA)** feature demo for SocialMapper! This demo showcases the new geographic analysis capabilities that allow you to analyze communities at the ZIP code level alongside the existing block group analysis.

## 🎯 What are ZCTAs?

**ZIP Code Tabulation Areas (ZCTAs)** are statistical geographic units created by the U.S. Census Bureau that approximate postal ZIP code areas. They provide:

- **Larger geographic units** than census block groups
- **Better ZIP code approximation** for regional analysis  
- **Same census variables** as block groups (population, income, demographics, etc.)
- **Complementary analysis** - use both levels depending on your needs

### 📊 Block Groups vs ZCTAs

| Feature | Block Groups | ZCTAs |
|---------|--------------|-------|
| **Size** | ~1,500 people | ~30,000 people |
| **Count (US)** | ~220,000 units | ~33,000 units |
| **Use Case** | Neighborhood analysis | ZIP code / regional analysis |
| **Data Detail** | High granularity | Moderate granularity |
| **Processing** | More units to process | Fewer units to process |

## 🚀 Quick Start

### Prerequisites

1. **Install SocialMapper** (if not already installed):
   ```bash
   pip install -e .
   ```

2. **Install demo dependencies**:
   ```bash
   pip install rich pandas geopandas
   ```

3. **Optional: Census API Key** (recommended for better performance):
   ```bash
   export CENSUS_API_KEY="your_api_key_here"
   ```

### Run the Demo

```bash
python demo_zcta_feature.py
```

## 📋 What the Demo Does

The demo performs a **side-by-side comparison** of the same analysis using both geographic levels:

### 🏗️ Demo Steps

1. **Creates Sample Data**: 5 Seattle library locations
2. **Runs Block Group Analysis**: Traditional fine-grained analysis  
3. **Runs ZCTA Analysis**: New ZIP code-level analysis
4. **Compares Results**: Processing time, geographic units, census data
5. **Shows CLI Examples**: How to use the new `--geographic-level` option

### 📊 Expected Results

You'll see comparisons like:

```
📊 Block Groups vs ZCTAs Comparison
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Metric           ┃ Block Groups ┃ ZCTAs   ┃ Difference  ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━┩
│ Processing Time  │ 45.2s        │ 23.1s   │ -22.1s      │
│ Geographic Units │ 156          │ 12      │ -144        │
│ POIs Analyzed    │ 5            │ 5       │ Same        │
└──────────────────┴──────────────┴─────────┴─────────────┘
```

## 💻 CLI Usage Examples

After running the demo, you can try these commands:

### 1. **Custom Coordinates with ZCTAs**
```bash
python -m socialmapper.cli \
  --custom-coords demo_zcta_data/seattle_libraries.csv \
  --travel-time 15 \
  --geographic-level zcta
```

### 2. **POI Search with ZCTAs**
```bash
python -m socialmapper.cli \
  --poi \
  --geocode-area "Seattle" \
  --state "WA" \
  --poi-type "amenity" \
  --poi-name "library" \
  --geographic-level zcta
```

### 3. **Address Geocoding with ZCTAs**
```bash
python -m socialmapper.cli \
  --addresses \
  --address-file demo_zcta_data/sample_addresses.csv \
  --geographic-level zcta
```

### 4. **Compare Both Levels**
```bash
# Block groups (default)
python -m socialmapper.cli \
  --custom-coords demo_zcta_data/seattle_libraries.csv \
  --travel-time 15 \
  --output-dir output_blockgroups

# ZCTAs  
python -m socialmapper.cli \
  --custom-coords demo_zcta_data/seattle_libraries.csv \
  --travel-time 15 \
  --geographic-level zcta \
  --output-dir output_zctas
```

## 📁 Demo Output Structure

After running the demo, you'll find:

```
📁 demo_zcta_data/
├── seattle_libraries.csv      # Sample POI coordinates
├── seattle_libraries.json     # Same data in JSON format  
└── sample_addresses.csv       # Sample addresses for geocoding

📁 demo_output_libraries/      # Block group results
├── seattle_libraries_15min_census_data.csv
├── seattle_libraries_15min_isochrones.geojson
└── maps/

📁 demo_output_libraries_zcta/ # ZCTA results  
├── seattle_libraries_15min_census_data.csv
├── seattle_libraries_15min_isochrones.geojson
└── maps/
```

## 🔍 Understanding the Results

### Census Data Differences

ZCTAs and block groups will show different census totals because:

- **Aggregation Level**: ZCTAs aggregate larger areas
- **Boundary Differences**: ZCTA boundaries don't exactly match ZIP codes or block groups
- **Population Distribution**: Different ways of grouping the same underlying population

### When to Use Each Level

**Use Block Groups when:**
- You need fine-grained neighborhood analysis
- Studying local community characteristics  
- Working with small geographic areas
- Maximum spatial precision is important

**Use ZCTAs when:**
- You need ZIP code-level insights
- Working with mailing lists or marketing data
- Studying broader regional patterns
- Faster processing is desired

## 🛠️ Advanced Usage

### Custom Census Variables

```bash
python -m socialmapper.cli \
  --custom-coords demo_zcta_data/seattle_libraries.csv \
  --geographic-level zcta \
  --census-variables total_population median_household_income median_age poverty_rate
```

### Different Travel Times

```bash
# Quick access (10 minutes)
python -m socialmapper.cli \
  --custom-coords demo_zcta_data/seattle_libraries.csv \
  --geographic-level zcta \
  --travel-time 10

# Extended access (30 minutes)  
python -m socialmapper.cli \
  --custom-coords demo_zcta_data/seattle_libraries.csv \
  --geographic-level zcta \
  --travel-time 30
```

## 🐛 Troubleshooting

### Common Issues

**"No ZCTAs found"**
- Ensure your POIs are in the United States
- Check that travel time isn't too restrictive
- Verify coordinates are valid (lat/lon format)

**Slow Performance**
- Consider using a Census API key
- Try smaller geographic areas
- Use shorter travel times for initial testing

**Import Errors**
- Ensure SocialMapper is properly installed: `pip install -e .`
- Install required packages: `pip install rich pandas geopandas`

### Getting Help

If you encounter issues:

1. Check the console output for specific error messages
2. Verify your input data format matches the examples
3. Ensure internet connectivity for Census API access
4. Try with a smaller dataset first

## 📚 Next Steps

After exploring the demo:

1. **Analyze Your Own Data**: Use your own POI coordinates or addresses
2. **Experiment with Variables**: Try different census variables for your analysis
3. **Compare Geographic Levels**: Run the same analysis with both levels to understand the differences
4. **Integrate with Your Workflow**: Use the CSV outputs in your existing analysis tools

## 🎉 Conclusion

The ZCTA feature adds powerful ZIP code-level analysis capabilities to SocialMapper while maintaining full backward compatibility. Whether you need fine-grained neighborhood insights (block groups) or broader regional patterns (ZCTAs), SocialMapper now supports both approaches seamlessly.

Happy mapping! 🗺️ 