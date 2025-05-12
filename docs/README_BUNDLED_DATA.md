# County Spatial Index with Bundled Data

This document describes the bundled county spatial index feature, which significantly enhances the performance of county lookups in SocialMapper.

## Overview

The county spatial index feature allows for fast determination of which county a geographic point (latitude/longitude) belongs to. This is a critical operation in SocialMapper that occurs very frequently when processing POIs.

The bundled data enhancement provides:

1. **Improved Performance**: Eliminates the need for API calls to Census servers
2. **Offline Operation**: Allows SocialMapper to work without internet connectivity
3. **Consistent Results**: Provides reliable lookups without API rate limits or service outages
4. **Reduced Wait Times**: No more waiting for API responses when processing large datasets

## Implementation Details

The implementation consists of:

1. **Bundled County Geometries**: The complete US county boundary geometries are packaged directly with the library
2. **R-tree Spatial Index**: An efficient spatial indexing structure for fast point-in-polygon lookups
3. **Automatic Fallback**: If the bundled data cannot be loaded, the system falls back to API calls

The bundled data is stored in two formats:
- **GeoJSON**: For maximum compatibility
- **Parquet**: For smaller file size and faster loading

## Performance Results

Tests show significant performance improvements with the bundled data approach:

- **Initial Load Time**: Slight increase (approximately 0.35s) when first initializing
- **Lookup Speed**: After initialization, lookups are 1000-2000x faster than API calls
- **Accuracy**: 100% match with API results in test cases

## Using the Feature

The bundled data is used automatically by default. When you call:

```python
from socialmapper.counties import get_county_fips_from_point

# This will automatically use the bundled spatial index
state_fips, county_fips = get_county_fips_from_point(lat, lon)
```

## Customizing Behavior

You can customize the behavior through the lower-level API:

```python
from socialmapper.counties import _init_county_spatial_index

# Disable bundled data and force API usage
idx, counties_gdf = _init_county_spatial_index(use_bundled_data=False)

# Enable debug mode for more detailed logging
idx, counties_gdf = _init_county_spatial_index(debug=True)

# Disable the mock fallback
idx, counties_gdf = _init_county_spatial_index(use_mock_on_failure=False)
```

## Updating the Bundled Data

The bundled county data is generated from the Census Bureau's TIGER/Line shapefiles. To update it:

1. Run the bundling script:
```
python scripts/bundle_county_data.py
```

This will:
- Download the latest county geometries (if necessary)
- Process and optimize the geometries
- Save them in both GeoJSON and Parquet formats in `socialmapper/counties/data/`

## Space Requirements

The bundled data adds approximately:
- 30MB to the package size
- 100MB to memory usage during runtime when loaded

The performance benefits generally outweigh this memory cost, especially when processing large POI datasets.

## Future Enhancements

Planned improvements to the bundled data feature:

1. **On-demand Loading**: Load only regions that are actively needed
2. **Versioned Data**: Allow specific versions of boundary data to be selected
3. **Custom Data Sources**: Support user-provided boundary files 