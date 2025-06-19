# Exporting Results

SocialMapper can export analysis results in multiple formats for use in reports, further analysis, or visualization in other tools.

## Output Directory Structure

By default, results are saved to the `output/` directory:

```
output/
├── csv/          # CSV data files
├── maps/         # Map images (if enabled)
└── isochrones/   # Isochrone data (if enabled)
```

## CSV Export (Default)

CSV export is enabled by default and creates detailed data files.

### Basic Usage

```python
from socialmapper import run_socialmapper

# CSV export is automatic
results = run_socialmapper(
    state="Ohio",
    county="Franklin County",
    place_type="library",
    travel_time=15,
    export_csv=True  # Default
)
```

### Output Files

For POI analysis, you'll get:
- `{location}_{type}_{time}min_census_data.csv` - Census demographics
- Location details and metadata

Example: `columbus_amenity_library_15min_census_data.csv`

### CSV Contents

The census data CSV includes:
- `GEOID` - Census block group identifier
- All requested census variables
- Geographic identifiers (state, county, tract)

## Map Export

Generate static map images showing isochrones and demographics.

### Enable Map Export

```python
results = run_socialmapper(
    custom_coords_path="locations.csv",
    travel_time=15,
    census_variables=["total_population"],
    export_maps=True  # Generate maps
)
```

### Map Types

SocialMapper creates:
1. **Isochrone maps** - Shows travel time areas
2. **Demographic maps** - Visualizes census data (one per variable)

### Command Line

```bash
socialmapper --custom-coords locations.csv --travel-time 15 \
  --export-csv --export-maps
```

## Isochrone Export

Export the actual isochrone geometries for use in GIS software.

### Modern API (Recommended)

```python
from socialmapper import SocialMapperClient, SocialMapperBuilder

with SocialMapperClient() as client:
    config = (SocialMapperBuilder()
        .with_custom_pois("locations.csv")
        .with_travel_time(15)
        .with_travel_mode("drive")
        .enable_isochrone_export()  # Enable isochrone export
        .build()
    )
    
    result = client.run_analysis(config)
    
    if result.is_ok():
        analysis = result.unwrap()
        # Access the isochrone file path
        isochrone_file = analysis.files_generated.get('isochrone_data')
        print(f"Isochrone saved to: {isochrone_file}")
```

### Legacy API

```python
results = run_socialmapper(
    custom_coords_path="locations.csv",
    travel_time=15,
    export_isochrones=True
)
# Creates output/isochrones/*.parquet files
```

### Output Format

Isochrones are exported as GeoParquet files with the following naming convention:
- Modern API: `{base_filename}_{travel_time}min_isochrones.geoparquet`
- Legacy API: `isochrone{time}_{location}.parquet`

Example: `portland_amenity_library_15min_isochrones.geoparquet`

### Working with Exported Isochrones

```python
import geopandas as gpd

# Load the exported isochrone
isochrones = gpd.read_parquet("output/isochrones/portland_amenity_library_15min_isochrones.geoparquet")

# View the data structure
print(isochrones.head())
print(f"CRS: {isochrones.crs}")
print(f"Number of isochrones: {len(isochrones)}")

# Plot the isochrones
isochrones.plot(alpha=0.5, edgecolor='black')

# Calculate total area covered
total_area_km2 = isochrones.to_crs('EPSG:3857').area.sum() / 1e6
print(f"Total area covered: {total_area_km2:.2f} km²")

# Export to other formats
isochrones.to_file("isochrones.shp")  # Shapefile
isochrones.to_file("isochrones.geojson", driver="GeoJSON")  # GeoJSON
```

## Custom Output Directory

Change where files are saved:

```python
results = run_socialmapper(
    custom_coords_path="locations.csv",
    travel_time=15,
    output_dir="my_analysis_results"
)
# Files saved to my_analysis_results/csv/, etc.
```

## Working with Exported Data

### Load CSV in Python

```python
import pandas as pd

# Load exported census data
df = pd.read_csv("output/csv/library_15min_census_data.csv")

# Analyze
total_pop = df['total_population'].sum()
print(f"Total population: {total_pop:,}")
```

### Load in Excel

1. Open Excel
2. Data → From Text/CSV
3. Select the CSV file
4. Review and load

### Use in GIS Software

The isochrone GeoParquet files can be loaded in:
- QGIS (with GeoParquet support)
- ArcGIS Pro
- Python with GeoPandas
- Any GIS software that supports GeoParquet format

```python
import geopandas as gpd

# Load isochrone from modern API
isochrone = gpd.read_parquet("output/isochrones/portland_amenity_library_15min_isochrones.geoparquet")

# Or from legacy API
isochrone = gpd.read_parquet("output/isochrones/isochrone15_location.parquet")
```

## File Naming Convention

Files are named systematically:

**Census Data CSV:**
`{location}_{poi_type}_{poi_name}_{travel_time}min_census_data.csv`

**Maps:**
`{location}_{poi_type}_{poi_name}_{travel_time}min_{variable}_map.png`

**Isochrones:**
`isochrone{time}_{location}.parquet`

## Tips for Using Exports

### For Reports
1. Use CSV files for data tables
2. Include map images for visualization
3. Calculate summary statistics from raw data

### For Further Analysis
1. Load CSVs into pandas/R
2. Join with other datasets using GEOID
3. Create custom visualizations

### For GIS
1. Use isochrone exports
2. Join census data by GEOID
3. Create custom map layouts

## Example: Complete Export

```python
# Full export example
results = run_socialmapper(
    state="Washington",
    county="King County",
    place_type="hospital",
    travel_time=20,
    census_variables=[
        "total_population",
        "median_age",
        "percent_poverty"
    ],
    export_csv=True,
    export_maps=True,
    export_isochrones=True,
    output_dir="hospital_analysis"
)

print("Export complete!")
print("Files saved to:")
print("- hospital_analysis/csv/")
print("- hospital_analysis/maps/") 
print("- hospital_analysis/isochrones/")
```

## Limitations

- Maps are static PNG images
- Large areas may produce large files
- Map generation takes additional time

## Next Steps

- Learn about [command line usage](cli-usage.md)
- Explore [custom locations](custom-locations.md)
- Understand [census variables](demographics.md)