# SocialMapper Tutorials

A comprehensive, progressive tutorial series to master SocialMapper's geospatial analysis capabilities for urban planning, public health, and social equity research.

## 🎯 Tutorial Collection Overview

**Total Tutorials:** 13 (8 core + 5 advanced)
**Total Learning Time:** 8-10 hours
**Skill Levels:** Beginner → Intermediate → Advanced → Expert
**Prerequisites:** Basic Python knowledge

## 📚 Learning Paths

Choose a learning path based on your goals and experience:

### 🚀 Path 1: Quick Start (2-3 hours)
**For:** Getting productive quickly
1. Tutorial 01: Getting Started (20 min)
2. Tutorial 02: Travel Modes (25 min)
3. Tutorial 05: Combining Analysis (30 min)
4. Selected exercises from EXERCISES.md

### 🏛️ Path 2: Urban Planning Focus (4-5 hours)
**For:** Urban planners and policy makers
1. Tutorials 01-03: Core concepts (1 hour)
2. Tutorial 06: Multi-Location Analysis (30 min)
3. Tutorial 07: ZIP Code Analysis (25 min)
4. Tutorial 09: Equity Analysis (35 min)
5. Tutorial 10: Food Desert Analysis (40 min)

### 🏥 Path 3: Public Health Research (5-6 hours)
**For:** Public health professionals and researchers
1. Tutorials 01-03: Foundation (1 hour)
2. Tutorial 09: Equity Analysis (35 min)
3. Tutorial 10: Food Desert Analysis (40 min)
4. Tutorial 11: Healthcare Accessibility (35 min)
5. Tutorial 13: Reproducible Research (45 min)

### 📊 Path 4: Data Science Applications (6-7 hours)
**For:** Data scientists and analysts
1. All core tutorials (01-08): 3 hours
2. Tutorial 12: Comparative Analysis (40 min)
3. Tutorial 13: Reproducible Research (45 min)
4. Advanced exercises and challenges

### 🎓 Path 5: Complete Mastery (8-10 hours)
**For:** Comprehensive understanding
- All 13 tutorials in sequence
- Complete exercise set
- Challenge problems

---

## 📖 Core Tutorials (Beginner-Intermediate)

### Tutorial 1: Getting Started ⭐
**File:** `01_getting_started.py`
**Time:** 15-20 minutes
**Learning Objectives:**
- Create travel-time isochrones from any location
- Discover points of interest within accessible areas
- Retrieve and analyze census demographics
- Visualize accessibility patterns on maps

**Key Concepts:** Isochrones, POIs, Census blocks, Choropleth maps

```bash
uv run python examples/tutorials/01_getting_started.py
```

### Tutorial 2: Travel Modes ⭐
**File:** `02_travel_modes.py`
**Time:** 20-25 minutes
**Learning Objectives:**
- Generate and compare isochrones for walk, bike, and drive
- Calculate coverage multipliers between modes
- Analyze equity implications of transportation
- Understand multi-modal accessibility

**Key Concepts:** Modal choice, Network distance, Accessibility equity

```bash
uv run python examples/tutorials/02_travel_modes.py
```

### Tutorial 3: Census Demographics ⭐⭐
**File:** `03_census_demographics.py`
**Time:** 20-25 minutes
**Learning Objectives:**
- Master Census Bureau data retrieval
- Work with demographic variables
- Aggregate and analyze population data
- Create demographic visualizations

**Key Concepts:** ACS data, GEOIDs, Variable selection, Data aggregation

```bash
uv run python examples/tutorials/03_census_demographics.py
```

### Tutorial 4: Custom POIs ⭐⭐
**File:** `04_custom_pois.py`
**Time:** 15-20 minutes
**Learning Objectives:**
- Import custom POI data from CSV
- Perform batch accessibility analysis
- Compare multiple locations
- Generate comparative reports

**Key Concepts:** CSV import, Batch processing, Comparative analysis

```bash
uv run python examples/tutorials/04_custom_pois.py
```

### Tutorial 5: Combining Analysis ⭐⭐
**File:** `05_combining_analysis.py`
**Time:** 25-30 minutes
**Learning Objectives:**
- Build complex analytical workflows
- Merge spatial and demographic data
- Create composite accessibility metrics
- Design reusable analysis patterns

**Key Concepts:** Workflow composition, Data integration, Metrics design

```bash
uv run python examples/tutorials/05_combining_analysis.py
```

### Tutorial 6: Multi-Location Analysis ⭐⭐
**File:** `06_multi_location_analysis.py`
**Time:** 25-30 minutes
**Learning Objectives:**
- Analyze multiple locations simultaneously
- Detect service area overlaps
- Identify gaps in coverage
- Create accessibility matrices

**Key Concepts:** Batch analysis, Overlap detection, Gap analysis

```bash
uv run python examples/tutorials/06_multi_location_analysis.py
```

### Tutorial 7: ZIP Code Analysis ⭐⭐
**File:** `07_zipcode_analysis.py`
**Time:** 20-25 minutes
**Learning Objectives:**
- Work with ZIP Code Tabulation Areas
- Perform regional-scale analysis
- Compare ZCTA vs block group approaches
- Optimize for performance

**Key Concepts:** ZCTAs, Regional analysis, Geographic hierarchies

```bash
uv run python examples/tutorials/07_zipcode_analysis.py
```

### Tutorial 8: Address Geocoding ⭐⭐
**File:** `08_address_geocoding.py`
**Time:** 15-20 minutes
**Learning Objectives:**
- Convert addresses to coordinates
- Use multiple geocoding providers
- Implement batch geocoding
- Handle geocoding failures gracefully

**Key Concepts:** Geocoding, Address validation, Error handling

```bash
uv run python examples/tutorials/08_address_geocoding.py
```

---

## 🚀 Advanced Tutorials (Intermediate-Expert)

### Tutorial 9: Transit Equity Analysis ⭐⭐⭐
**File:** `09_equity_analysis.py`
**Time:** 30-35 minutes
**Learning Objectives:**
- Analyze service access across income levels
- Calculate equity metrics (Gini coefficient)
- Identify underserved communities
- Generate policy recommendations

**Key Concepts:** Environmental justice, Disparity ratios, Spatial equity

```bash
uv run python examples/tutorials/09_equity_analysis.py
```

### Tutorial 10: Food Desert Analysis ⭐⭐⭐
**File:** `10_food_desert_analysis.py`
**Time:** 35-40 minutes
**Learning Objectives:**
- Identify food deserts using USDA criteria
- Analyze food access by demographics
- Assess food environment quality
- Model intervention impacts

**Key Concepts:** Food security, USDA definitions, Health impacts

```bash
uv run python examples/tutorials/10_food_desert_analysis.py
```

### Tutorial 11: Healthcare Accessibility ⭐⭐⭐
**File:** `11_healthcare_accessibility.py`
**Time:** 30-35 minutes
**Learning Objectives:**
- Map healthcare facility access
- Analyze emergency response times
- Identify vulnerable populations
- Optimize service locations

**Key Concepts:** Healthcare equity, Emergency services, Facility planning

```bash
# Coming soon
uv run python examples/tutorials/11_healthcare_accessibility.py
```

### Tutorial 12: Multi-City Comparison ⭐⭐⭐
**File:** `12_comparative_analysis.py`
**Time:** 35-40 minutes
**Learning Objectives:**
- Compare accessibility across cities
- Create benchmarking metrics
- Identify best practices
- Generate comparison visualizations

**Key Concepts:** Benchmarking, Cross-city analysis, Best practices

```bash
# Coming soon
uv run python examples/tutorials/12_comparative_analysis.py
```

### Tutorial 13: Reproducible Research ⭐⭐⭐⭐
**File:** `13_reproducible_research.py`
**Time:** 40-45 minutes
**Learning Objectives:**
- Build reproducible workflows
- Implement data validation
- Create publication-ready outputs
- Document research methods

**Key Concepts:** Reproducibility, Validation, Documentation

```bash
# Coming soon
uv run python examples/tutorials/13_reproducible_research.py
```

---

## 💡 Prerequisites & Setup

### System Requirements
- Python 3.11 or higher
- 4GB RAM minimum (8GB recommended)
- Internet connection for API calls

### Installation
```bash
# Install SocialMapper
uv add socialmapper

# Set Census API key (free from census.gov)
export CENSUS_API_KEY="your-key-here"

# Create .env file (optional)
echo "CENSUS_API_KEY=your-key-here" > .env
```

Get your free Census API key: https://api.census.gov/data/key_signup.html

---

## 📊 Tutorial Features Matrix

| Tutorial | Isochrones | POIs | Census | Maps | Equity | Batch | Advanced |
|----------|------------|------|---------|------|--------|-------|----------|
| 01 Getting Started | ✅ | ✅ | ✅ | ✅ | | | |
| 02 Travel Modes | ✅ | ✅ | ✅ | | ✅ | | |
| 03 Census Demographics | | | ✅ | ✅ | | | |
| 04 Custom POIs | ✅ | ✅ | | | | ✅ | |
| 05 Combining Analysis | ✅ | ✅ | ✅ | ✅ | | | ✅ |
| 06 Multi-Location | ✅ | ✅ | ✅ | | | ✅ | ✅ |
| 07 ZIP Code Analysis | | | ✅ | ✅ | | | ✅ |
| 08 Address Geocoding | | | | | | ✅ | |
| 09 Equity Analysis | ✅ | ✅ | ✅ | ✅ | ✅ | | ✅ |
| 10 Food Desert | ✅ | ✅ | ✅ | ✅ | ✅ | | ✅ |

---

## 🎯 Learning Resources

### 📚 Documentation
- **[Exercise Compilation](EXERCISES.md)** - All exercises with solutions
- **[API Reference](../../docs/api.md)** - Complete API documentation
- **[Best Practices](../../docs/best_practices.md)** - Tips and patterns

### 🛠️ Practice Datasets
- **Sample POIs**: `examples/data/sample_pois.csv`
- **Test Locations**: Pre-configured coordinates for major cities
- **Demo Mode**: Run without API keys for learning

### 💬 Getting Help
- **Issues**: GitHub Issues for bugs/questions
- **Discussions**: Community forum for help
- **Examples**: Share your analyses

---

## ⚡ Quick Reference

### Core API Functions
```python
from socialmapper import (
    create_isochrone,      # Travel-time areas
    get_poi,              # Find points of interest
    get_census_blocks,    # Get census geography
    get_census_data,      # Fetch demographics
    create_map,           # Generate visualizations
)
```

### Common Patterns

**Basic Analysis:**
```python
# 1. Define area
iso = create_isochrone(location, travel_time=15)

# 2. Find services
pois = get_poi(location, categories=["library"])

# 3. Get demographics
blocks = get_census_blocks(polygon=iso)
data = get_census_data(location=[b['geoid'] for b in blocks])

# 4. Visualize
map = create_map(data=map_data, column="population")
```

**Multi-Modal Comparison:**
```python
modes = ["walk", "bike", "drive"]
results = {}

for mode in modes:
    iso = create_isochrone(location, 15, mode)
    results[mode] = iso['properties']['area_sq_km']
```

---

## 🏆 Tutorial Completion Checklist

Track your progress through the tutorial series:

### Core Tutorials
- [ ] 01 Getting Started
- [ ] 02 Travel Modes
- [ ] 03 Census Demographics
- [ ] 04 Custom POIs
- [ ] 05 Combining Analysis
- [ ] 06 Multi-Location
- [ ] 07 ZIP Code Analysis
- [ ] 08 Address Geocoding

### Advanced Tutorials
- [ ] 09 Equity Analysis
- [ ] 10 Food Desert Analysis
- [ ] 11 Healthcare Accessibility
- [ ] 12 Comparative Analysis
- [ ] 13 Reproducible Research

### Exercises
- [ ] Complete 5 Beginner exercises
- [ ] Complete 3 Intermediate exercises
- [ ] Complete 1 Advanced exercise
- [ ] Complete 1 Challenge problem

---

## 🚀 Next Steps

After completing the tutorials:

1. **Apply to Your Area**: Analyze your city or region
2. **Extend the Analysis**: Add new metrics or data sources
3. **Build Applications**: Create web apps or dashboards
4. **Share Results**: Publish findings or contribute examples
5. **Contribute**: Improve tutorials or add new ones

---

## 🤝 Contributing

We welcome contributions to improve and expand the tutorials:

- **Bug Fixes**: Report issues or submit fixes
- **New Tutorials**: Propose new topics
- **Improvements**: Enhance existing tutorials
- **Translations**: Help translate tutorials

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

---

## 📄 License

These tutorials are part of the SocialMapper project and are available under the same license. See [LICENSE](../../LICENSE) for details.

---

*Happy learning! For questions and discussions, visit our community forums.* 🗺️✨