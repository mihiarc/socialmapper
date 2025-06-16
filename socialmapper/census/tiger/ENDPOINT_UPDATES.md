# TIGER Geometry Endpoint Updates

## Summary of Changes

The TIGER geometry submodule has been updated to use the correct REST API endpoints as provided:

### 1. Counties
- **Old**: `https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/1`
- **New**: `https://tigerweb.geo.census.gov/arcgis/rest/services/Generalized_ACS2023/State_County/MapServer/11`
- **Note**: Now uses the generalized ACS2023 version for better performance

### 2. Block Groups
- **Generalized (500k)**: `https://tigerweb.geo.census.gov/arcgis/rest/services/Generalized_ACS2023/Tracts_Blocks/MapServer/6`
  - Default option for better performance
  - Use with `fetch_block_groups(use_generalized=True)`
- **Detailed**: `https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/1`
  - For precise boundaries when needed
  - Use with `fetch_block_groups(use_generalized=False)`

### 3. ZCTAs
- **Old**: `https://tigerweb.geo.census.gov/arcgis/rest/services/Census2020/PUMA_TAD_TAZ_UGA_ZCTA/MapServer/2`
- **New**: `https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/PUMA_TAD_TAZ_UGA_ZCTA/MapServer/7`

## New Features

### Block Group Options
Users can now choose between generalized and detailed block group boundaries:

```python
# For better performance (default)
result = client.fetch_block_groups(
    state_fips="06",
    county_fips="001",
    use_generalized=True  # Uses 500k generalized boundaries
)

# For precise boundaries
result = client.fetch_block_groups(
    state_fips="06",
    county_fips="001",
    use_generalized=False  # Uses detailed boundaries
)
```

### New Geography Level
Added `GeographyLevel.BLOCK_GROUP_DETAILED` for direct access to detailed boundaries:

```python
query = GeometryQuery(
    geography_level=GeographyLevel.BLOCK_GROUP_DETAILED,
    state_fips="06",
    county_fips="075"
)
result = client.fetch_geometries(query)
```

## Performance Considerations

1. **Generalized boundaries** (500k) are recommended for:
   - Visualization at state or regional scale
   - Analysis where precise boundaries aren't critical
   - Faster loading times and smaller file sizes

2. **Detailed boundaries** are recommended for:
   - Local area analysis
   - Precise demographic calculations
   - High-resolution mapping

## Test Results

All endpoints have been tested and verified:
- ✅ Counties: 58 counties in California
- ✅ ZCTAs: 83 ZCTAs with prefix "945"
- ✅ Block Groups (Generalized): 1,133 in Alameda County
- ✅ Block Groups (Detailed): 1,134 in Alameda County
- ✅ Direct queries work with all geography levels