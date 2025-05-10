# SocialMapper Changelog

## Version 0.2.0-alpha

### Performance & API Improvements
- **Data Handling**: Enhanced GeoDataFrame support for POIs
- Added PyOGRIO and PyArrow for optimized I/O operations
- Implemented GeoParquet format for intermediate outputs
- Added bounding box parameter for spatial filtering
- Added fallback for missing maxspeed in OpenStreetMaps
- Added progress tracking in blockgroups.py and census_data.py

### Enhanced Core Functionality
- Added support for custom coordinates in socialmapper.py
- Enhanced census data fetching and validation
- Added command-line interface support for selection modes
- Enhanced state extraction and handling

### Visualization Enhancements
- Added visualization package for SocialMapper
- Added single_map.py for individual choropleth and isochrone maps
- Added map_utils.py for census variable mapping
- Added scale bar and north arrow to maps

### User Experience Improvements
- Added support for listing available census variables
- Updated census variable mappings for clarity