# Community Mapper Project Overview

The project uses Python-based GIS tools to process spatial data, conduct network analysis for travel time calculations, and merge this with census demographic information to understand the relationship between population centers and points of interest. The purpose is to define community boundaries based on where people live and interact with the social network irrespective of administrative boundaries which may be arbitrary in rural areas. 

## Project Structure and Components:

1. Code Directory
    - Contains Python scripts written for an example use case (access to hiking trails), generating isochrones (travel time zones), analyzing census data, and creating maps
    - Follows a numbered workflow (`01_process_trails.py`, `02_generate_isochrones.py`, etc.)
    - Uses libraries like GeoPandas, OSMNX, NetworkX, and Matplotlib for spatial analysis and visualization

2. nfs-access
    - This folder contains all the development code, data, and output from the trail access use case. See the powerpoint for more information about that project.

3. srr-nrcs
    - The Sustainable Rangleland Roundtable and Natural Resource Conservation Service collaboration to access community attachment to rangeland ecosystems. This project focuses on conservation efforts for the lessor prairie chicken of the southern great plains region.

## General Workflow:

1. Define community boundaries:
    - Identify points of interest that serve as central locations around which communities tend to gather
    - Generate isochrones (travel time zones) around these points
    - Potential points of interest may be schools, markets, churches, etc.

2. Intersect community boundary with census administrative boundaries
    - For example, selecting all the census block groups that are within a certain driving distance from the point of interest

2. Demographic Analysis:
    - Map population data from census block groups
    - Characterize the community demographics

3. Visualization and Reporting:
    - Create both interactive web maps and static maps for reporting
    - Visualize forest boundaries, trail networks, and demographic data together