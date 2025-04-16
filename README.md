# Community Mapper Project Overview

The project uses Python-based GIS tools to process spatial data, conduct network analysis for travel time calculations, and merge this with census demographic information to understand the relationship between population centers and access to National Forest hiking trails. The focus is on understanding community access to natural resources, particularly in the Southern Region of the National Forest Service.

## Project Structure and Components:

1. Code Directory
    - Contains Python scripts for processing trail data, generating isochrones (travel time zones), analyzing census data, and creating maps
    - Follows a numbered workflow (`01_process_trails.py`, `02_generate_isochrones.py`, etc.)
    - Uses libraries like GeoPandas, OSMNX, NetworkX, and Matplotlib for spatial analysis and visualization

2. Notebooks Directory
    - Contains Jupyter notebooks used for exploratory data analysis and visualization
    - Includes analysis of specific areas (e.g., "mog-south" appears to be related to Morgantown South)
    - Shows travel time analysis, catchment areas, and county-level analyses

2. Data Directory
    - Stores processed data files, primarily in GeoPackage (.gpkg) and GeoJSON formats
    - Includes census block group population data, which appears to be a key demographic dataset

3. Maps Directory
    - Contains output map files in HTML (interactive) and PNG (static) formats
    - Visualizes trail starting points, regional overviews, and population distributions

4. Other Directories
    - `hiking_trails/` and `hiking-trails/`: Store trail data
    - `forest_access_maps/`: Likely contains specialized maps showing access to forest areas
    - `tim_database/`: Possibly related to timber resource management data
    - `cache/`: Stores temporary or intermediate processed data

## Project Purpose:

1. Analyze Trail Accessibility:
    - Identify hiking trail starting points in National Forests
    - Generate isochrones (travel time zones) around these points to show accessibility
    - Focus on trails under 5 miles in length in Region 8 of the National Forest System

2. Demographic Analysis:
    - Map population data from census block groups
    - Relate population demographics to trail access
    - Analyze which populations have access to trails within specific travel time thresholds (e.g., 45 minutes)

3. Visualization and Reporting:
    - Create both interactive web maps and static maps for reporting
    - Visualize forest boundaries, trail networks, and demographic data together