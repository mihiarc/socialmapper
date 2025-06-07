# 🚀 ZCTA Demo Quick Start Guide

This guide provides step-by-step instructions for testing the new ZCTA (ZIP Code Tabulation Area) feature in SocialMapper.

## ⚡ TL;DR - Run the Demo Now

```bash
# Full interactive demo (recommended)
python demo_zcta_feature.py

# Quick CLI tests
python test_zcta_cli.py
```

## 📋 Demo Options

### Option 1: 🎬 Full Interactive Demo (Recommended)

**What it does**: Side-by-side comparison of block groups vs ZCTAs with real Seattle library data

```bash
python demo_zcta_feature.py
```

**Expected runtime**: 3-5 minutes  
**Output**: 
- Rich interactive comparison tables
- Sample data files created automatically
- Complete analysis results in separate directories
- CLI usage examples

### Option 2: 🧪 Quick CLI Tests

**What it does**: Fast validation that ZCTA commands work properly

```bash
python test_zcta_cli.py
```

**Expected runtime**: 2-3 minutes  
**Output**: Pass/fail status for each CLI scenario

### Option 3: 💻 Manual CLI Testing

**Test individual commands manually:**

```bash
# Create test data first
mkdir test_data
echo "name,lat,lon,type
Library 1,47.6062,-122.3321,library
Library 2,47.6613,-122.3138,library" > test_data/coords.csv

# Test block groups (baseline)
python -m socialmapper.cli --custom-coords test_data/coords.csv \
  --travel-time 10 --geographic-level block-group

# Test ZCTAs (new feature) 
python -m socialmapper.cli --custom-coords test_data/coords.csv \
  --travel-time 10 --geographic-level zcta
```

## 🎯 What to Look For

### ✅ Success Indicators

1. **Processing Messages**: Look for "Finding ZIP Code Tabulation Areas" vs "Finding Census Block Groups"
2. **Unit Counts**: ZCTAs should show fewer units (larger geographic areas)
3. **Processing Speed**: ZCTAs may be faster due to fewer units
4. **Output Files**: Same structure but different data granularity

### 📊 Expected Differences

| Aspect | Block Groups | ZCTAs |
|--------|-------------|-------|
| **Geographic Units** | 50-200 units | 5-20 units |
| **Processing Time** | Longer | Shorter |
| **Data Granularity** | Fine-grained | Broader patterns |
| **Use Case** | Neighborhood analysis | ZIP code regions |

### 🔍 Files to Check

After running demos, examine these files:

```
📁 demo_output_libraries/          # Block group results
├── *_census_data.csv             # Fine-grained data
└── maps/                         # Detailed maps

📁 demo_output_libraries_zcta/     # ZCTA results  
├── *_census_data.csv             # ZIP code level data
└── maps/                         # Regional maps
```

## 🐛 Troubleshooting

### Common Issues & Solutions

**"Command not found"**
```bash
# Ensure SocialMapper is installed
pip install -e .
```

**"No ZCTAs found"**
- Use US coordinates only
- Check lat/lon format (latitude, longitude)
- Try larger travel times (15+ minutes)

**"Slow performance"**
```bash
# Optional: Add Census API key for faster performance
export CENSUS_API_KEY="your_key_here"
```

**"Import errors"**
```bash
# Install demo dependencies
pip install rich pandas geopandas
```

### 🔧 Quick Fixes

**Reset everything:**
```bash
rm -rf demo_zcta_data/ demo_output_* test_data/ output/
python demo_zcta_feature.py
```

**Test minimal case:**
```bash
python -m socialmapper.cli --poi --geocode-area "Seattle" --state "WA" \
  --poi-type "amenity" --poi-name "library" --geographic-level zcta \
  --travel-time 15 --export-csv --no-export-maps
```

## 📚 Understanding the Results

### Geographic Level Comparison

**Block Groups (Traditional)**
- ~1,500 people per unit
- Neighborhood-level precision
- More processing time
- Better for local community analysis

**ZCTAs (New Feature)**  
- ~30,000 people per unit
- ZIP code-level aggregation
- Faster processing
- Better for regional/mailing analysis

### Census Data Interpretation

The census totals will differ between levels because:
- **Scale**: ZCTAs cover larger areas
- **Boundaries**: Different aggregation methods
- **Use Cases**: Choose based on your analysis needs

## 🎉 Next Steps

After successful demo:

1. **Try your own data**: Replace demo coordinates with your POIs
2. **Experiment with variables**: Add more census variables
3. **Compare travel times**: Test 10, 15, 30 minute scenarios  
4. **Integrate workflows**: Use CSV outputs in your analysis tools

## 📞 Need Help?

If the demo fails:

1. **Check requirements**: Python 3.8+, required packages installed
2. **Verify installation**: `python -c "import socialmapper; print('OK')"`
3. **Internet access**: Needed for Census API calls
4. **Coordinates**: Ensure US locations only

**Still stuck?** Check the detailed README: `ZCTA_DEMO_README.md`

---

🎯 **Ready to test?** Run `python demo_zcta_feature.py` and explore the new ZCTA capabilities! 