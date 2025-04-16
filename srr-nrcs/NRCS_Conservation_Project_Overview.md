# NRCS Conservation Study Area Analysis

## Project Overview

This project analyzes Walmart store locations within a specific study area defined for NRCS (Natural Resources Conservation Service) conservation efforts. The study area encompasses selected counties across four states: Kansas, New Mexico, Oklahoma, and Texas.

## Purpose

The analysis aims to understand the distribution of Walmart stores across rural and semi-rural counties in the central United States, potentially to:

1. Analyze retail accessibility in agricultural regions
2. Support conservation planning by understanding commercial development patterns
3. Assess the relationship between retail infrastructure and land use patterns

## Technical Implementation

The project follows a data processing pipeline with several key steps:

### 1. County Boundary Acquisition

The script `fetch_county_boundaries.py` retrieves geographic boundaries for all counties in the study area:

- Reads county configurations from `study_area_config.yaml`
- Uses Census TIGER/Web service to fetch county geometries
- Outputs:
  - `county_boundaries.geojson`: Geographic data for all counties
  - `study_area_bbox.json`: Bounding box coordinates for the entire study area
  - `county_metadata.csv`: County attributes and statistics

### 2. Walmart Location Data Collection

The script `fetch_walmart_locations.py` gathers Walmart store information:

- Uses OpenStreetMap (OSM) data via the Overpy API
- Queries for all Walmart-branded stores within the study area
- Handles both point (node) and polygon (way) representations
- Extracts store details including:
  - Geographic coordinates
  - Store names
  - Address information
  - Additional metadata (phone, website, hours)
- Outputs `walmart_stores_bbox.csv` with raw store data

### 3. Data Processing and Consolidation

The script `process_walmart_locations.py` refines the raw data:

- Consolidates duplicate entries for the same physical location
- Extracts store types (Supercenter, Neighborhood Market, etc.) from store names
- Standardizes service categorization
- Outputs `walmart_locations_consolidated.csv` with cleaned data

### 4. Visualization Generation

The script `create_maps.py` produces visualization maps:

- **Study Area Overview**: Shows Walmart locations by store type with color coding:
  - Supercenters (red)
  - Neighborhood Markets (green)
  - General Stores (blue)
  
- **Walmart Density Map**: Creates a choropleth map showing store distribution by county:
  - Color gradient indicating store density
  - County labels showing store counts
  - Base maps from CartoDB for geographic context

## Data Files

The project organizes data into several categories:

### Input Configuration
- `cfg/study_area_config.yaml`: Defines the 24 counties across 4 states in the study area

### Intermediate Data
- County boundary data in GeoJSON format
- Study area bounding box coordinates
- Raw Walmart store information

### Output Results
- `output/maps/study_area_overview.png`: Map showing Walmart locations by store type
- `output/maps/walmart_density.png`: Map showing store distribution density by county
- `output/walmart_locations/`: Directory with processed store data

## Technical Stack

The project uses Python with several key libraries:

- **GeoPandas**: For spatial data handling and analysis
- **Pandas**: For general data processing and manipulation
- **Matplotlib**: For creating visualizations
- **Contextily**: For adding basemaps to the visualizations
- **Overpy**: For accessing OpenStreetMap data
- **Requests**: For API calls to Census TIGER/Web service
- **PyYAML**: For parsing configuration files

## Workflow Process

To run the complete analysis:

1. Configure study area parameters in `cfg/study_area_config.yaml`
2. Run `fetch_county_boundaries.py` to get geographic boundaries
3. Run `fetch_walmart_locations.py` to collect store data
4. Run `process_walmart_locations.py` to clean and consolidate data
5. Run `create_maps.py` to generate visualizations

The scripts are designed to work sequentially, with each step using outputs from previous steps. 