# NRCS Conservation Study Area Analysis

This project analyzes Walmart store locations within a specific study area defined for NRCS conservation efforts. The analysis covers selected counties across Kansas, New Mexico, Oklahoma, and Texas.

## Data Processing Pipeline

```mermaid
graph TD
    A[study_area_config.yaml] --> B[fetch_county_boundaries.py]
    B --> C[county_boundaries.geojson]
    B --> D[study_area_bbox.json]
    B --> E[county_metadata.csv]
    
    D --> F[fetch_walmart_locations.py]
    F --> G[walmart_stores_bbox.csv]
    
    G --> H[process_walmart_locations.py]
    H --> I[walmart_locations_consolidated.csv]
    
    C --> J[create_maps.py]
    I --> J
    J --> K[study_area_overview.png]
    J --> L[walmart_density.png]
```

## Pipeline Steps

1. **County Boundaries** (`fetch_county_boundaries.py`)
   - Reads study area configuration from `study_area_config.yaml`
   - Fetches county boundaries from Census TIGER/Web service
   - Outputs:
     - `county_boundaries.geojson`: County geometries
     - `study_area_bbox.json`: Bounding box for the study area
     - `county_metadata.csv`: County attributes

2. **Walmart Locations** (`fetch_walmart_locations.py`)
   - Uses bounding box from previous step
   - Fetches Walmart locations from OpenStreetMap
   - Outputs `walmart_stores_bbox.csv` with raw store data

3. **Location Processing** (`process_walmart_locations.py`)
   - Consolidates multiple services at same location
   - Extracts service types from store names
   - Outputs `walmart_locations_consolidated.csv`

4. **Map Creation** (`create_maps.py`)
   - Creates two visualization maps:
     - `study_area_overview.png`: Shows Walmart locations by type
     - `walmart_density.png`: Shows store distribution by county

## Data Files

### Input
- `study_area_config.yaml`: Defines study area counties and states

### Intermediate
- `county_boundaries.geojson`: County boundary geometries
- `study_area_bbox.json`: Study area extent
- `county_metadata.csv`: County attributes
- `walmart_stores_bbox.csv`: Raw Walmart store data
- `walmart_locations_consolidated.csv`: Processed store data

### Output
- `study_area_overview.png`: Map of Walmart locations by type
- `walmart_density.png`: Map of store distribution by county

## Dependencies

- `pandas`: Data processing
- `geopandas`: Spatial data handling
- `requests`: API requests
- `overpy`: OpenStreetMap API wrapper
- `matplotlib`: Mapping
- `contextily`: Basemaps
- `PyYAML`: Configuration file parsing

## Usage

Run the scripts in sequence:

```bash
# 1. Fetch county boundaries
python fetch_county_boundaries.py

# 2. Fetch Walmart locations
python fetch_walmart_locations.py

# 3. Process Walmart locations
python process_walmart_locations.py

# 4. Create maps
python create_maps.py
``` 