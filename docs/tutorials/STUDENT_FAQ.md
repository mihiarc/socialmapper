# SocialMapper Student FAQ

## Frequently Asked Questions for Students

Welcome to SocialMapper! This FAQ addresses common questions from students learning spatial accessibility analysis. Can't find your answer? Ask in the course forum or during office hours.

---

## 🚀 Getting Started

### Q: How do I install SocialMapper?

**A:** SocialMapper can be installed using pip or uv:

```bash
# Using pip
pip install socialmapper

# Using uv (recommended)
uv add socialmapper

# For development/latest version
pip install git+https://github.com/mihiarc/socialmapper.git
```

**Troubleshooting:**
- Make sure you have Python 3.11 or higher
- Use a virtual environment to avoid conflicts
- On Mac/Linux, you might need `pip3` instead of `pip`

---

### Q: Do I need a Census API key?

**A:** A Census API key is recommended but not required:

- **Without key:** Limited to 500 requests per day
- **With key:** Unlimited requests (free)
- **Get one here:** https://api.census.gov/data/key_signup.html

To use your key:
```python
import os
os.environ['CENSUS_API_KEY'] = 'your-key-here'
```

Or create a `.env` file:
```
CENSUS_API_KEY=your-key-here
```

---

### Q: What if I get import errors?

**A:** Common solutions:

1. **Check installation:**
```bash
pip list | grep socialmapper
```

2. **Reinstall:**
```bash
pip uninstall socialmapper
pip install socialmapper --upgrade
```

3. **Check Python version:**
```bash
python --version  # Should be 3.11+
```

4. **Virtual environment issues:**
```bash
# Make sure you're in the right environment
which python
# Activate your environment
source venv/bin/activate  # Mac/Linux
# or
venv\Scripts\activate  # Windows
```

---

### Q: Why is the code running slowly?

**A:** First runs are slower because SocialMapper is:
- Building local caches
- Downloading map data
- Fetching census information

**Speed tips:**
- **First run:** Can take 30-60 seconds
- **Subsequent runs:** Much faster (5-10 seconds)
- **For testing:** Use smaller parameters:
  ```python
  # Faster for testing
  iso = create_isochrone(location, travel_time=5)  # 5 min instead of 15
  blocks = get_census_blocks(iso)[:10]  # Only first 10 blocks
  ```

---

## 📚 Using Tutorials

### Q: Which tutorial should I start with?

**A:** Follow this path based on your experience:

**Complete Beginner:**
1. Start with Tutorial 01 (Getting Started)
2. Do them in order (01-08)
3. Take breaks between tutorials

**Some GIS Experience:**
1. Skim Tutorial 01 for API overview
2. Focus on Tutorials 03-06
3. Jump to advanced topics of interest

**Python Expert, New to GIS:**
1. Read Tutorial 01 carefully (concepts)
2. Focus on spatial concepts in 02-03
3. Move quickly through Python parts

---

### Q: Can I use my own data?

**A:** Yes! SocialMapper is designed for custom data:

**For locations:**
```python
# Use any coordinates
my_home = (latitude, longitude)

# Or geocode addresses
from socialmapper import geocode_address
coords = geocode_address("123 Main St, City, State")
```

**For POIs (Tutorial 04):**
```python
# Create a CSV with columns: name, latitude, longitude
# Then import and analyze your POIs
```

**For demographics:**
```python
# Specify any census variables you need
variables = ["population", "median_age", "your_variable_here"]
```

---

### Q: How long will tutorials take?

**A:** Estimated completion times:

| Tutorial | Reading | Coding | Exercises | Total |
|----------|---------|---------|-----------|-------|
| 01: Getting Started | 5 min | 10 min | 15 min | 30 min |
| 02: Travel Modes | 5 min | 10 min | 15 min | 30 min |
| 03: Census Data | 10 min | 15 min | 20 min | 45 min |
| 04: Custom POIs | 5 min | 10 min | 15 min | 30 min |
| 05: Combining | 10 min | 15 min | 20 min | 45 min |
| 06: Multi-Location | 10 min | 15 min | 20 min | 45 min |
| 07: ZIP Codes | 10 min | 15 min | 20 min | 45 min |
| 08: Geocoding | 5 min | 10 min | 15 min | 30 min |

**Tips:**
- Budget 2x time for your first tutorial
- Exercises are optional but recommended
- Take breaks between tutorials

---

## 💡 Concepts

### Q: What is an isochrone?

**A:** An isochrone is a polygon showing all areas reachable within a specific travel time.

**Key points:**
- **Not a circle:** Follows actual roads/paths
- **Mode matters:** Walking ≠ driving coverage
- **Time-based:** 15-minute isochrone = everywhere you can reach in 15 minutes

**Visual example:**
```
      Regular circle          Isochrone
      (distance only)         (follows roads)

          * * *                   * *
        *       *               *     *
       *    X    *             *   X   *
        *       *               *     *
          * * *                   * * *
                                    *
                                  * * *
```

---

### Q: What is a census block group?

**A:** Census block groups are statistical divisions used by the U.S. Census Bureau:

**Hierarchy:**
```
Nation
  ↓
States
  ↓
Counties
  ↓
Census Tracts (2,500-8,000 people)
  ↓
Block Groups (600-3,000 people)  ← We use these
  ↓
Blocks (smallest, limited data)
```

**Why block groups?**
- Good balance of detail and privacy
- Rich demographic data available
- Standard unit for analysis

---

### Q: What are POIs?

**A:** POIs (Points of Interest) are specific locations of importance:

**Common POI types in SocialMapper:**
- Essential services: grocery, pharmacy, hospital
- Education: schools, libraries, universities
- Recreation: parks, restaurants, gyms
- Transportation: bus stops, subway stations
- Financial: banks, ATMs

**Finding POIs:**
```python
# Search for specific type
pharmacies = get_poi(polygon=iso, poi_type="pharmacy")

# Common types:
types = ["supermarket", "hospital", "school", "park", "restaurant"]
```

---

### Q: What's the difference between equity and equality?

**A:** Important distinction for accessibility analysis:

**Equality:** Everyone gets the same thing
- Example: Every neighborhood gets one bus stop

**Equity:** Everyone gets what they need to reach the same outcome
- Example: More bus stops in areas with lower car ownership

**In accessibility:**
- Equality: Same travel time for everyone
- Equity: Accounting for mobility differences, income, age, etc.

---

## 🛠️ Technical Questions

### Q: How do I find coordinates for a location?

**A:** Several methods:

1. **Google Maps:**
   - Right-click any location
   - Select "What's here?"
   - Copy coordinates from popup

2. **Online tools:**
   - https://www.latlong.net/
   - https://www.gps-coordinates.net/

3. **In Python:**
```python
from socialmapper import geocode_address
coords = geocode_address("Empire State Building, New York, NY")
print(coords)  # (40.7484, -73.9857)
```

4. **Common cities (for testing):**
```python
cities = {
    "New York": (40.7128, -74.0060),
    "Los Angeles": (34.0522, -118.2437),
    "Chicago": (41.8781, -87.6298)
}
```

---

### Q: Why is my code slow?

**A:** Common causes and solutions:

1. **Large travel times:**
```python
# Slow
iso = create_isochrone(location, travel_time=30)

# Faster (for testing)
iso = create_isochrone(location, travel_time=10)
```

2. **Too many census blocks:**
```python
# Slow
blocks = get_census_blocks(polygon=iso)  # All blocks

# Faster
blocks = get_census_blocks(polygon=iso)[:20]  # First 20 only
```

3. **Multiple API calls:**
```python
# Slow (multiple calls)
for geoid in geoids:
    data = get_census_data([geoid], variables)

# Fast (single batch call)
data = get_census_data(geoids, variables)
```

---

### Q: How do I export my results?

**A:** Multiple export options:

**Save maps:**
```python
map_obj = create_map(polygon=iso, pois=pois)
map_obj.save("my_map.html")
```

**Export to CSV:**
```python
import pandas as pd

# Convert to DataFrame
df = pd.DataFrame(results)

# Save to CSV
df.to_csv("results.csv", index=False)
```

**Export to GeoJSON:**
```python
import json

geojson = {
    "type": "Feature",
    "geometry": iso['geometry'],
    "properties": iso['properties']
}

with open("isochrone.geojson", "w") as f:
    json.dump(geojson, f)
```

---

### Q: What coordinate system does SocialMapper use?

**A:** SocialMapper uses:
- **Input:** WGS84 (latitude, longitude) - standard GPS coordinates
- **Format:** `(latitude, longitude)` - note the order!
- **Range:** Latitude: -90 to 90, Longitude: -180 to 180

**Common mistake:**
```python
# Wrong (longitude, latitude)
location = (-78.6382, 35.7796)  # ❌

# Correct (latitude, longitude)
location = (35.7796, -78.6382)  # ✅
```

---

## 📊 Analysis Questions

### Q: How do I choose the right travel time?

**A:** Consider your analysis goals:

| Travel Time | Use Case | Rationale |
|-------------|----------|-----------|
| 5 minutes | Walkable neighborhood services | Very local access |
| 10 minutes | Biking range, quick drives | Common trip threshold |
| 15 minutes | Standard accessibility measure | Widely used benchmark |
| 20 minutes | Extended service areas | Regional services |
| 30 minutes | Commute analysis | Employment access |

**Research standard:** 15 minutes is most common in literature

---

### Q: What census variables are available?

**A:** Common variables for accessibility analysis:

**Demographics:**
- `population` - Total population
- `median_age` - Median age
- `percent_over_65` - Elderly population
- `percent_under_18` - Youth population

**Economic:**
- `median_household_income` - Income level
- `percent_poverty` - Poverty rate
- `unemployment_rate` - Job availability

**Housing:**
- `housing_units` - Total units
- `percent_renter` - Rental vs. owned
- `median_home_value` - Property values

**Transportation:**
- `percent_no_vehicle` - Car-free households
- `commute_time` - Average commute

---

### Q: How do I handle missing data?

**A:** Common strategies:

1. **Check for None values:**
```python
if data[geoid]['population'] is not None:
    # Use the value
    pop = data[geoid]['population']
else:
    # Handle missing
    pop = 0  # or skip this block
```

2. **Filter out missing:**
```python
valid_data = {
    geoid: values
    for geoid, values in data.items()
    if values['median_income'] is not None
}
```

3. **Use defaults:**
```python
income = data[geoid].get('median_income', 50000)  # Default to 50k
```

---

## 🎓 Projects and Research

### Q: Can I use SocialMapper for my thesis/dissertation?

**A:** Absolutely! SocialMapper is designed for research:

**Good for:**
- Accessibility studies
- Equity analysis
- Policy evaluation
- Urban planning research
- Public health studies

**Citation format:**
```
SocialMapper: A Python Library for Accessibility Analysis. (2024).
GitHub repository, https://github.com/mihiarc/socialmapper
```

**Tips:**
- Document your methodology thoroughly
- Save all code for reproducibility
- Consider sensitivity analysis
- Acknowledge limitations

---

### Q: How do I cite SocialMapper in academic work?

**A:** Use these formats:

**APA:**
```
SocialMapper Development Team. (2024). SocialMapper: A Python library
for accessibility analysis (Version 0.9.0) [Computer software].
https://github.com/mihiarc/socialmapper
```

**MLA:**
```
SocialMapper Development Team. SocialMapper: A Python Library for
Accessibility Analysis. Version 0.9.0, 2024,
github.com/mihiarc/socialmapper.
```

**BibTeX:**
```bibtex
@software{socialmapper2024,
  title = {SocialMapper: A Python Library for Accessibility Analysis},
  author = {{SocialMapper Development Team}},
  year = {2024},
  version = {0.9.0},
  url = {https://github.com/mihiarc/socialmapper}
}
```

---

### Q: Where can I find datasets?

**A:** Useful data sources:

**Demographics:**
- U.S. Census: https://data.census.gov
- Census API: https://www.census.gov/data/developers

**Geographic:**
- OpenStreetMap: https://www.openstreetmap.org
- Natural Earth: https://www.naturalearthdata.com
- Census TIGER: https://www.census.gov/geographies/mapping-files

**POI Data:**
- OpenStreetMap (via SocialMapper)
- Google Places API (paid)
- Yelp API (limited free tier)
- Local government open data portals

**Health Data:**
- CDC: https://data.cdc.gov
- County Health Rankings: https://www.countyhealthrankings.org

---

## 🆘 Getting Help

### Q: Where can I get help with errors?

**A:** Try these resources in order:

1. **Error messages:** Read carefully - they often explain the problem
2. **This FAQ:** Check if your issue is covered
3. **Documentation:** Review relevant tutorial
4. **Quick Reference:** Check the [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
5. **Course forum:** Post with error message and code
6. **Office hours:** Bring your code for debugging help
7. **GitHub Issues:** For library bugs (not homework help)

**When asking for help, include:**
- Complete error message
- Code that causes the error
- What you expected to happen
- What you've already tried

---

### Q: What if my analysis seems wrong?

**A:** Debugging checklist:

1. **Check coordinates:**
```python
# Print to verify
print(f"Location: {location}")
# Should be (latitude, longitude)
```

2. **Visualize results:**
```python
# Create map to see if it looks right
map_obj = create_map(polygon=iso)
map_obj.save("debug.html")
```

3. **Check data ranges:**
```python
# Look for unrealistic values
print(f"Area: {iso['properties']['area_sq_km']} km²")
print(f"Population: {total_population}")
```

4. **Verify parameters:**
```python
# Make sure units are correct
travel_time = 15  # Should be minutes, not seconds
```

---

### Q: How do I know if my results are reasonable?

**A:** Validation strategies:

**Reality checks:**
- 15-min walk ≈ 1-2 km² in cities
- 15-min drive ≈ 50-200 km² depending on area
- Population density varies widely (100-10,000+ per km²)

**Compare with known values:**
- Check against city statistics
- Compare with published studies
- Validate with local knowledge

**Sensitivity analysis:**
```python
# Test different parameters
for time in [5, 10, 15, 20]:
    iso = create_isochrone(location, time)
    print(f"{time} min: {iso['properties']['area_sq_km']:.1f} km²")
```

---

## 💼 Career and Applications

### Q: What careers use these skills?

**A:** Many fields use accessibility analysis:

**Public Sector:**
- Urban planner
- Transportation analyst
- Public health researcher
- Policy analyst
- GIS specialist

**Private Sector:**
- Location intelligence analyst
- Real estate analyst
- Retail site selection
- Logistics planning
- Consulting

**Non-Profit:**
- Community development
- Advocacy research
- Environmental justice
- Social services planning

**Academic:**
- Geography research
- Urban studies
- Public health research
- Social science research

---

### Q: What other tools should I learn?

**A:** Complementary skills:

**GIS Software:**
- QGIS (free, open source)
- ArcGIS (industry standard)
- PostGIS (spatial databases)

**Programming:**
- GeoPandas (spatial data)
- Folium (mapping)
- Matplotlib/Seaborn (visualization)
- Scikit-learn (machine learning)

**Statistics:**
- Spatial statistics
- R for spatial analysis
- Regression modeling

**Domain Knowledge:**
- Urban planning theory
- Transportation planning
- Public health frameworks
- Census data products

---

## 📚 Additional Resources

### Learning Resources
- **Official Docs:** https://github.com/mihiarc/socialmapper
- **Census API Guide:** https://www.census.gov/data/developers/guidance
- **OpenStreetMap Wiki:** https://wiki.openstreetmap.org
- **Python GIS:** https://automating-gis-processes.github.io

### Communities
- **GIS Stack Exchange:** https://gis.stackexchange.com
- **r/gis subreddit:** https://reddit.com/r/gis
- **Python Discord:** Geographic channels
- **Local GIS meetups:** Check Meetup.com

### Tutorials and Courses
- **Automating GIS Processes:** Free Python GIS course
- **Coursera:** GIS specializations
- **YouTube:** "Python GIS" tutorials
- **LinkedIn Learning:** GIS and Python courses

---

## 🤔 Still Have Questions?

If your question isn't answered here:

1. **Check the documentation:** Other guides might help
2. **Ask in class:** Others probably have the same question
3. **Post in forum:** Include code and error messages
4. **Office hours:** Bring specific examples
5. **Create an issue:** If it's a bug in SocialMapper

Remember: There are no stupid questions! Everyone starts somewhere, and the community is here to help you learn.

---

*Last updated: January 2025 | Version 1.0*