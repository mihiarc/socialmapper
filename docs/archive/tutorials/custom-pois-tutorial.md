# Custom POIs Tutorial

This tutorial demonstrates how to analyze your own points of interest instead of relying on OpenStreetMap data. This is particularly useful when you have specific locations like company offices, service locations, or custom datasets.

## What You'll Learn

- How to format your location data for SocialMapper
- Loading POIs from CSV files
- Analyzing multiple custom locations simultaneously
- Batch processing different POI types
- Comparing accessibility across custom locations

## Prerequisites

Before starting this tutorial:

1. **Complete Tutorial 01** to understand basic SocialMapper concepts
2. **Prepare your location data** in CSV format (or use our example)

## CSV Format Requirements

SocialMapper expects custom POI data in CSV format with specific columns:

### Required Columns
- **name**: The name of your point of interest
- **latitude**: Decimal latitude (e.g., 35.7796)
- **longitude**: Decimal longitude (e.g., -78.6382)

### Optional Columns
- **type**: Category or type of POI (e.g., "library", "office", "store")
- **address**: Street address for reference

### Example CSV File

Create a file named `custom_pois.csv`:

```csv
name,latitude,longitude,type,address
Central Library,35.7796,-78.6382,library,"201 E Main St"
City Park,35.7821,-78.6589,park,"500 Park Ave"
Community Center,35.7754,-78.6434,community_center,"100 Community Dr"
Food Bank,35.7889,-78.6444,social_service,"456 Help St"
Senior Center,35.7701,-78.6521,social_service,"789 Elder Way"
```

## Step-by-Step Guide

### Step 1: Import and Setup

```python
from socialmapper import SocialMapperClient, SocialMapperBuilder
```

### Step 2: Configure Your Analysis

```python
# Path to your CSV file
custom_coords_path = "custom_pois.csv"

# Analysis parameters
travel_time = 10  # 10-minute walk
census_variables = [
    "total_population",
    "median_age",
    "percent_poverty"
]
```

### Step 3: Run the Analysis

```python
with SocialMapperClient() as client:
    # Build configuration for custom POIs
    config = (SocialMapperBuilder()
        .with_custom_pois(custom_coords_path)
        .with_travel_time(travel_time)
        .with_census_variables(*census_variables)
        .with_exports(csv=True, isochrones=True)
        .build()
    )
    
    # Run analysis
    result = client.run_analysis(config)
    
    if result.is_ok():
        analysis_result = result.unwrap()
        print(f"Analyzed {analysis_result.poi_count} custom POIs")
```

## Understanding the Results

The analysis generates a CSV file with demographic data for each custom POI. Let's create a formatted comparison table:

```python
import pandas as pd
from tabulate import tabulate

# Read results
df = pd.read_csv('output/csv/custom_pois_analysis.csv')

# Create formatted comparison table
comparison_df = pd.DataFrame({
    'Location': df['poi_name'],
    'Population Reach': df['total_population'].map('{:,}'.format),
    'Median Age': df['median_age'].round(1),
    'Poverty Rate': df['percent_poverty'].map('{:.1f}%'.format)
})

print("Accessibility Comparison:")
print(tabulate(comparison_df, headers='keys', tablefmt='github', showindex=False))
```

Output:
```
Accessibility Comparison:
| Location         | Population Reach | Median Age | Poverty Rate |
|------------------|------------------|------------|--------------|
| Central Library  | 8,234           | 32.5       | 15.2%        |
| City Park        | 9,156           | 34.1       | 12.8%        |
| Community Center | 7,890           | 33.7       | 16.5%        |
| Food Bank        | 6,543           | 35.2       | 22.1%        |
| Senior Center    | 5,678           | 38.9       | 18.3%        |
```

## Advanced: Batch Processing Multiple POI Types

When you have different types of POIs, you might want to analyze them separately with different parameters:

```python
from socialmapper import SocialMapperClient, SocialMapperBuilder

# Define POI types and their analysis parameters
poi_configs = {
    'social_services': {
        'file': 'social_service_pois.csv',
        'travel_time': 15,  # Longer travel time for services
        'variables': ['total_population', 'percent_poverty', 'percent_no_vehicle']
    },
    'parks': {
        'file': 'park_pois.csv',
        'travel_time': 10,  # Shorter walk to parks
        'variables': ['total_population', 'median_age', 'percent_children']
    },
    'libraries': {
        'file': 'library_pois.csv',
        'travel_time': 20,  # People may travel further for libraries
        'variables': ['total_population', 'median_household_income', 'percent_college']
    }
}

# Process each POI type
with SocialMapperClient() as client:
    for poi_type, config_params in poi_configs.items():
        print(f"\nAnalyzing {poi_type}...")
        
        config = (SocialMapperBuilder()
            .with_custom_pois(config_params['file'])
            .with_travel_time(config_params['travel_time'])
            .with_census_variables(*config_params['variables'])
            .with_exports(csv=True)
            .build()
        )
        
        result = client.run_analysis(config)
        
        if result.is_ok():
            analysis = result.unwrap()
            print(f"✅ Analyzed {analysis.poi_count} {poi_type}")
        else:
            print(f"❌ Error: {result.unwrap_err().message}")
```

## Working with Large Datasets

For datasets with hundreds or thousands of POIs:

1. **Use chunking**: Process POIs in batches of 50-100
2. **Enable caching**: Geocoding results are cached automatically
3. **Skip visualization**: Set `isochrones=False` for faster processing
4. **Use parallel processing**: Run multiple analyses concurrently

```python
import pandas as pd
from pathlib import Path

# Read large dataset
all_pois = pd.read_csv('large_poi_dataset.csv')

# Process in chunks
chunk_size = 50
for i in range(0, len(all_pois), chunk_size):
    chunk = all_pois.iloc[i:i+chunk_size]
    chunk_file = f'temp_chunk_{i}.csv'
    chunk.to_csv(chunk_file, index=False)
    
    # Analyze this chunk
    with SocialMapperClient() as client:
        config = (SocialMapperBuilder()
            .with_custom_pois(chunk_file)
            .with_travel_time(15)
            .with_census_variables('total_population')
            .with_exports(csv=True, isochrones=False)  # Skip maps for speed
            .build()
        )
        
        client.run_analysis(config)
    
    # Clean up temp file
    Path(chunk_file).unlink()
```

## Tips for Custom POI Analysis

### Data Preparation
- **Validate coordinates**: Ensure latitude/longitude are in decimal degrees
- **Check coordinate order**: Latitude first (35.7796), then longitude (-78.6382)
- **Remove duplicates**: Multiple POIs at the same location can skew results
- **Use descriptive names**: Makes results easier to interpret

### Analysis Strategy
- **Group by type**: Analyze similar POIs together for better comparisons
- **Vary travel times**: Different POI types may warrant different travel times
- **Consider travel modes**: Some POIs might be primarily accessed by car
- **Select relevant variables**: Match census variables to your analysis goals

### Common Issues and Solutions

**Issue**: "No census data found"
- **Solution**: Ensure coordinates are within the United States

**Issue**: "Invalid coordinates"
- **Solution**: Check that latitude is between -90 and 90, longitude between -180 and 180

**Issue**: "CSV parsing error"
- **Solution**: Ensure CSV has proper headers and no special characters in the header row

## Next Steps

After completing this tutorial:

1. **Create your own dataset**: Export locations from your database or GIS system
2. **Compare with OSM data**: Run both custom and OSM analyses to see coverage gaps
3. **Explore travel modes**: See the [Travel Modes Tutorial](travel-modes-tutorial.md)
4. **Analyze by ZIP code**: Learn about [ZCTA Analysis](zcta-analysis-tutorial.md)

## Full Code

The complete tutorial script is available at:
[`examples/tutorials/02_custom_pois.py`](https://github.com/mihiarc/socialmapper/blob/main/examples/tutorials/02_custom_pois.py)

## Key Takeaways

- Custom POI analysis gives you full control over location data
- CSV format is simple: just name, latitude, and longitude required
- Batch processing helps analyze different POI types efficiently
- Results can reveal service gaps and demographic patterns
- Combine with OSM data for comprehensive accessibility analysis