# ZIP Code Analysis Tutorial

This tutorial introduces ZIP Code Tabulation Area (ZCTA) analysis, a powerful alternative to block group analysis for regional demographic studies. ZCTAs are statistical areas that approximate ZIP code boundaries, making them familiar and useful for business and marketing analysis.

## What You'll Learn

- Understanding ZCTAs and their advantages
- Fetching ZCTA boundaries and census data
- Comparing ZCTA vs block group analysis
- Batch processing multiple states
- Creating choropleth maps at the ZCTA level
- Choosing the right geographic unit for your analysis

## What are ZCTAs?

ZIP Code Tabulation Areas (ZCTAs) are statistical geographic units created by the U.S. Census Bureau that approximate the geographic areas covered by USPS ZIP codes. While not exactly the same as ZIP codes, they're close enough for most analytical purposes.

### Why Use ZCTAs?

**Advantages:**
- **Familiar**: Everyone knows ZIP codes
- **Larger areas**: Cover 5,000-50,000 people vs 600-3,000 for block groups
- **Faster processing**: Fewer units to analyze
- **Business-friendly**: Perfect for market analysis and service planning

**Best Use Cases:**
- Regional demographic trends
- Business market analysis
- Service area planning
- Mail-based outreach campaigns

## Getting Started

### Step 1: Import and Initialize

```python
from socialmapper import get_census_system
import pandas as pd
import geopandas as gpd

# Initialize the census system
census_system = get_census_system()
```

### Step 2: Fetch ZCTA Boundaries

Let's get all ZCTAs for North Carolina:

```python
# North Carolina FIPS code is 37
nc_zctas = census_system.get_zctas_for_state("37")
print(f"Found {len(nc_zctas)} ZCTAs in North Carolina")

# View available columns
print(f"Columns: {list(nc_zctas.columns)}")
# Sample ZCTAs
print(f"Sample ZCTAs: {', '.join(nc_zctas.head(3)['GEOID'].astype(str))}")
```

Output:
```
Found 373 ZCTAs in North Carolina
Columns: ['geometry', 'GEOID', 'ZCTA5', 'NAME', 'POP100', 'HU100', 'AREALAND', 'AREAWATER', 'CENTLAT', 'CENTLON', 'ZCTA5CE', 'STATEFP']
Sample ZCTAs: 27048, 27051, 27053
```

### Step 3: Find ZCTA for a Specific Location

```python
# Find which ZCTA contains a specific point
lat, lon = 35.7796, -78.6382  # Downtown Raleigh
zcta_code = census_system.get_zcta_for_point(lat, lon)
print(f"Location ({lat}, {lon}) is in ZCTA: {zcta_code}")
```

## Analyzing ZCTA Demographics

Let's analyze demographics for several ZCTAs across North Carolina:

```python
# Define ZCTAs to analyze
example_zctas = [
    "27601",  # Raleigh downtown
    "27605",  # Raleigh suburbs  
    "27609",  # North Raleigh
    "28202",  # Charlotte uptown
    "28204",  # South Charlotte
]

# Census variables
variables = [
    "B01003_001E",  # Total population
    "B19013_001E",  # Median household income
    "B25003_002E",  # Owner-occupied housing units
    "B25003_003E",  # Renter-occupied housing units
]

# Fetch census data
census_data = census_system.get_zcta_census_data(
    geoids=example_zctas,
    variables=variables
)

print(f"Retrieved {len(census_data)} data points")
```

### Processing and Displaying Results

```python
from tabulate import tabulate

# Transform data for analysis
analysis_data = []
for zcta in example_zctas:
    zcta_data = census_data[census_data['GEOID'] == zcta]
    
    if not zcta_data.empty:
        # Extract values for each variable
        data_dict = {'ZCTA': zcta}
        
        for _, row in zcta_data.iterrows():
            var_code = row['variable_code']
            value = row['value']
            
            if var_code == 'B01003_001E':
                data_dict['Population'] = f"{int(value):,}" if value else "N/A"
            elif var_code == 'B19013_001E':
                data_dict['Median Income'] = f"${int(value):,}" if value else "N/A"
            elif var_code == 'B25003_002E':
                owner = int(value) if value else 0
                data_dict['_owner'] = owner
            elif var_code == 'B25003_003E':
                renter = int(value) if value else 0
                data_dict['_renter'] = renter
        
        # Calculate owner occupancy percentage
        total = data_dict.get('_owner', 0) + data_dict.get('_renter', 0)
        if total > 0:
            data_dict['% Owner Occupied'] = f"{(data_dict['_owner'] / total) * 100:.1f}%"
        else:
            data_dict['% Owner Occupied'] = "N/A"
        
        # Remove temporary fields
        data_dict.pop('_owner', None)
        data_dict.pop('_renter', None)
        
        analysis_data.append(data_dict)

# Display results
df = pd.DataFrame(analysis_data)
print("\nZCTA Demographics Summary:")
print(tabulate(df, headers='keys', tablefmt='github', showindex=False))
```

Output:
```
ZCTA Demographics Summary:
| ZCTA  | Population | Median Income | % Owner Occupied |
|-------|------------|---------------|------------------|
| 27601 | 9,702      | $70,433       | 27.7%            |
| 27605 | 6,121      | $63,267       | 31.8%            |
| 27609 | 35,548     | $81,538       | 51.1%            |
| 28202 | 16,855     | $101,711      | 26.7%            |
| 28204 | 9,744      | $89,207       | 25.9%            |
```

## Batch Processing Multiple States

For large-scale analysis across multiple states:

```python
# Define states to analyze
states = {
    "37": "North Carolina",
    "45": "South Carolina", 
    "13": "Georgia"
}

print(f"Processing ZCTAs for {len(states)} states:")
for fips, name in states.items():
    print(f"   • {name} (FIPS: {fips})")

# Batch fetch ZCTAs
state_fips_list = list(states.keys())
all_zctas = census_system.batch_get_zctas(
    state_fips_list=state_fips_list,
    batch_size=2  # Process 2 states at a time
)

print(f"\nSuccessfully processed {len(all_zctas)} total ZCTAs")

# Show state-by-state breakdown
print("\nZCTAs by State:")
for fips, name in states.items():
    state_zctas = all_zctas[all_zctas['STATEFP'] == fips]
    print(f"   • {name}: {len(state_zctas)} ZCTAs")
```

Output:
```
Processing ZCTAs for 3 states:
   • North Carolina (FIPS: 37)
   • South Carolina (FIPS: 45)
   • Georgia (FIPS: 13)

Successfully processed 1517 total ZCTAs

ZCTAs by State:
   • North Carolina: 373 ZCTAs
   • South Carolina: 424 ZCTAs
   • Georgia: 720 ZCTAs
```

## ZCTA vs Block Group Comparison

Understanding when to use ZCTAs versus block groups is crucial:

| Aspect          | Block Groups      | ZCTAs            |
|-----------------|-------------------|------------------|
| **Size**        | ~600-3,000 people | ~5,000-50,000    |
| **Precision**   | Very High         | Moderate         |
| **Processing**  | Slower            | Faster           |
| **Familiarity** | Technical         | Everyone knows   |
| **Use Case**    | Local analysis    | Regional trends  |

### When to Use Block Groups
- Walking distance analysis
- Neighborhood-level demographics
- Urban planning studies
- Environmental justice analysis

### When to Use ZCTAs
- Business market analysis
- Service area definition
- Regional demographic trends
- Mail-based service delivery

## Advanced Features

### Custom Configuration

Build a census system with specific settings:

```python
from socialmapper.census import CensusSystemBuilder, CacheStrategy

census_system = (CensusSystemBuilder()
    .with_api_key('your_key')
    .with_cache_strategy(CacheStrategy.FILE)
    .with_rate_limit(2.0)  # 2 requests per second
    .build()
)
```

### Direct Shapefile URLs

Get direct download links for ZCTA shapefiles:

```python
urls = census_system.get_zcta_urls(year=2020)
for name, url in urls.items():
    print(f"{name}: {url}")
```

Output:
```
national_zcta: https://www2.census.gov/geo/tiger/TIGER2020/ZCTA520/tl_2020_us_zcta520.zip
```


## Integration with SocialMapper

Use ZCTAs with the main SocialMapper API:

```python
from socialmapper import SocialMapperBuilder, SocialMapperClient
from socialmapper.api.builder import GeographicLevel

with SocialMapperClient() as client:
    config = (SocialMapperBuilder()
        .with_location("Wake County", "North Carolina")
        .with_osm_pois("amenity", "library")
        .with_travel_time(15)
        .with_census_variables("total_population", "median_household_income")
        .with_geographic_level(GeographicLevel.ZCTA)  # Use ZCTA instead of block group
        .with_exports(csv=True, maps=True)  # Enable choropleth maps
        .build()
    )
    
    result = client.run_analysis(config)
```

## ZCTA Choropleth Maps

SocialMapper can generate choropleth maps at the ZCTA level, providing clear visualization of regional patterns:

### Map Types Generated

When you enable map exports with `.with_exports(maps=True)`, SocialMapper creates:

1. **Population Maps**: Visualize population density across ZCTAs
2. **Income Maps**: Show median household income patterns
3. **Age Maps**: Display median age demographics
4. **Distance Maps**: Illustrate travel distance to nearest POI
5. **Accessibility Maps**: Highlight ZCTAs within your specified travel time

### Example: Full Pipeline with Maps

```python
from socialmapper import SocialMapperBuilder, SocialMapperClient
from socialmapper.api.builder import GeographicLevel

# Run ZCTA analysis with map generation
with SocialMapperClient() as client:
    config = (SocialMapperBuilder()
        .with_location("Wake County", "North Carolina")
        .with_osm_pois("amenity", "library")
        .with_travel_time(15)
        .with_census_variables(
            "total_population",
            "median_household_income",
            "median_age"
        )
        .with_geographic_level(GeographicLevel.ZCTA)
        .with_exports(csv=True, maps=True)
        .build()
    )
    
    result = client.run_analysis(config)
    
    if result.is_ok():
        analysis = result.unwrap()
        print(f"Analyzed {analysis.census_units_analyzed} ZCTAs")
        print("Check output/maps/ for choropleth visualizations")
```

### Benefits of ZCTA Maps

- **Regional Patterns**: ZCTAs show broader patterns than block groups
- **Business-Friendly**: Perfect for market analysis presentations
- **Faster Processing**: Fewer units mean quicker map generation
- **Familiar Boundaries**: Stakeholders understand ZIP code areas


## Performance Tips

1. **Use caching**: ZCTA boundaries are cached automatically after first download
2. **Batch processing**: Process multiple states together to reduce API calls
3. **Variable selection**: Only request the census variables you need
4. **Consider rate limits**: The census system handles rate limiting automatically

## Common Issues and Solutions

**Issue**: "ZCTA not found for location"
- **Solution**: Some locations may fall outside ZCTA boundaries (water bodies, unpopulated areas)

**Issue**: "Slow performance with many ZCTAs"
- **Solution**: Use batch processing and enable caching

**Issue**: "Census data missing for some ZCTAs"
- **Solution**: Some ZCTAs may have suppressed data for privacy; check variable availability

## Pro Tips

- **ZCTAs ≈ ZIP codes**: Close but not exactly the same
- **Great for business**: Everyone understands ZIP codes
- **Faster analysis**: Fewer geographic units to process
- **Regional perspective**: Better for area-wide trends than precise local analysis

## Next Steps

After completing this tutorial:

1. Try analyzing ZCTAs in your own state
2. Compare ZCTA vs block group results for the same area
3. Explore additional census variables for business analysis
4. Build a market analysis tool using ZCTA demographics
5. Check out the POI integration example for combining ZCTAs with location analysis

## Full Code

The complete tutorial script is available at:
[`examples/tutorials/04_zipcode_analysis.py`](https://github.com/mihiarc/socialmapper/blob/main/examples/tutorials/04_zipcode_analysis.py)

## Key Takeaways

- ZCTAs approximate ZIP codes and are perfect for regional analysis
- They process much faster than block groups due to fewer units
- Ideal for business, marketing, and service area planning
- Trade precision for speed and familiarity
- Can be integrated seamlessly with SocialMapper's POI analysis