# Real Satellite Imagery Integration with geoai

## Overview

SocialMapper's community module has been enhanced with **real satellite imagery integration** using the cutting-edge `geoai` package. This integration automatically fetches high-quality NAIP, Sentinel-2, and Landsat imagery for computer vision analysis, eliminating the need for manual data procurement and preprocessing.

## Key Features

### 🛰️ Automatic Data Fetching
- **NAIP Imagery**: High-resolution (1m) aerial imagery from USDA
- **Sentinel-2**: Medium-resolution (10m) multispectral satellite data
- **Landsat**: Historical and current imagery for temporal analysis
- **Smart Selection**: Automatically chooses best available imagery based on cloud cover and recency

### 💾 Intelligent Caching
- Local caching prevents redundant downloads
- Automatic cache management with configurable retention
- Optimized storage with band combination and compression

### ☁️ Quality Filtering
- Cloud cover filtering (configurable thresholds)
- Date range selection for temporal consistency
- Resolution and quality prioritization

### 🔄 Graceful Fallback
- Automatically falls back to simulation when real data unavailable
- Clear user feedback about data sources and quality
- Confidence weighting based on data source

## Installation

Add the geoai package to your environment:

```bash
# Using pip
pip install geoai-py

# Using uv (recommended)
uv add geoai-py

# Using conda
conda install -c conda-forge geoai-py
```

## Quick Start

### Basic Usage

```python
from socialmapper.community import analyze_satellite_imagery

# Define your area of interest (bounds in WGS84)
bounds = (-71.1, 42.35, -71.08, 42.37)  # Cambridge, MA

# Analyze with automatic data fetching
patches_gdf = analyze_satellite_imagery(
    bounds=bounds,
    imagery_type="naip",  # or "sentinel2", "landsat"
    patch_size=512
)

print(f"Analyzed {len(patches_gdf)} patches")
print(f"Land use types: {patches_gdf['land_use'].unique()}")
print(f"Data source: {patches_gdf['analysis_method'].iloc[0]}")
```

### Advanced Usage with Direct Fetcher

```python
from socialmapper.community import SatelliteDataFetcher

# Initialize fetcher with custom settings
fetcher = SatelliteDataFetcher(
    cache_dir="./satellite_cache",
    max_cloud_cover=10.0,  # Strict cloud filtering
    preferred_resolution=1.0  # 1m preferred resolution
)

# Fetch specific imagery
image_path = fetcher.get_best_imagery_for_bounds(
    bounds=bounds,
    imagery_type="sentinel2",
    time_range="2023-01-01/2023-12-31"
)

if image_path:
    print(f"Downloaded imagery: {image_path}")
else:
    print("No suitable imagery found")
```

### Integration with Building Data

```python
import geopandas as gpd
from socialmapper.community import fetch_satellite_imagery_for_community_analysis

# Load your building footprints
buildings_gdf = gpd.read_file("buildings.geojson")

# Automatically fetch imagery covering all buildings
image_path = fetch_satellite_imagery_for_community_analysis(
    buildings_gdf=buildings_gdf,
    imagery_type="naip",
    cache_dir="./cache"
)

if image_path:
    # Use the imagery for analysis
    from socialmapper.community import discover_community_boundaries
    
    boundaries = discover_community_boundaries(
        buildings_gdf=buildings_gdf,
        satellite_image=image_path
    )
```

## Supported Imagery Types

### NAIP (National Agriculture Imagery Program)
- **Resolution**: 1 meter
- **Coverage**: United States
- **Update Frequency**: Every 2-3 years
- **Best for**: High-detail urban analysis, building detection
- **Bands**: RGB (3-band) or RGBN (4-band with near-infrared)

```python
# Fetch NAIP imagery
naip_path = fetcher.get_best_imagery_for_bounds(
    bounds=bounds,
    imagery_type="naip"
)
```

### Sentinel-2
- **Resolution**: 10-20 meters
- **Coverage**: Global
- **Update Frequency**: Every 5 days
- **Best for**: Land cover classification, vegetation analysis
- **Bands**: 13 spectral bands (RGB + multispectral)

```python
# Fetch Sentinel-2 with cloud filtering
sentinel_path = fetcher.get_best_imagery_for_bounds(
    bounds=bounds,
    imagery_type="sentinel2",
    time_range="2024-01-01/2024-12-31"
)
```

### Landsat
- **Resolution**: 30 meters
- **Coverage**: Global
- **Update Frequency**: Every 16 days
- **Best for**: Historical analysis, change detection
- **Bands**: 11 spectral bands

```python
# Fetch Landsat imagery
landsat_path = fetcher.get_best_imagery_for_bounds(
    bounds=bounds,
    imagery_type="landsat",
    time_range="2020-01-01/2024-12-31"
)
```

## Configuration Options

### Cache Management

```python
# Configure cache location and retention
fetcher = SatelliteDataFetcher(
    cache_dir="/path/to/cache",
    max_cloud_cover=15.0,
    preferred_resolution=2.0
)

# Clear old cached files
fetcher.clear_cache(older_than_days=30)

# Clear all cache
fetcher.clear_cache()
```

### Quality Parameters

```python
# Customize quality filtering
items = geoai.pc_stac_search(
    collection="sentinel-2-l2a",
    bbox=bounds,
    time_range="2024-01-01/2024-06-01",
    query={
        "eo:cloud_cover": {"lt": 5.0},  # Very strict cloud filtering
        "s2:degraded_msi_data_percentage": {"lt": 1.0}  # Quality filtering
    },
    max_items=20
)
```

## Error Handling and Fallbacks

The system provides graceful degradation when real imagery is unavailable:

```python
try:
    # Attempt to use real imagery
    patches_gdf = analyze_satellite_imagery(
        bounds=bounds,
        imagery_type="naip"
    )
    
    # Check data source
    if 'real_satellite_imagery' in patches_gdf['analysis_method'].values:
        print("✅ Using real satellite imagery")
        confidence = "high"
    else:
        print("⚠️ Using simulated data")
        confidence = "medium"
        
except Exception as e:
    print(f"❌ Analysis failed: {e}")
    # Handle error appropriately
```

## Performance Optimization

### Efficient Patch Processing

```python
# Optimize for speed vs quality
patches_gdf = analyze_satellite_imagery(
    bounds=bounds,
    patch_size=256,  # Smaller patches = faster processing
    imagery_type="sentinel2"  # Medium resolution = faster download
)
```

### Parallel Processing

```python
# The geoai package supports parallel downloads
downloaded = geoai.pc_stac_download(
    items,
    output_dir=cache_dir,
    assets=["image"],
    max_workers=4  # Parallel download
)
```

## Integration with Community Detection

### Full Pipeline Example

```python
from socialmapper.community import (
    SatelliteDataFetcher,
    analyze_satellite_imagery,
    discover_community_boundaries
)
import geopandas as gpd

# 1. Load building data
buildings = gpd.read_file("buildings.geojson")

# 2. Get bounds
bounds = buildings.total_bounds

# 3. Fetch satellite imagery
fetcher = SatelliteDataFetcher()
image_path = fetcher.get_imagery_for_buildings(
    buildings_gdf=buildings,
    imagery_type="naip"
)

# 4. Analyze imagery patterns
patches_gdf = analyze_satellite_imagery(
    bounds=bounds,
    image_path=image_path,
    patch_size=512
)

# 5. Detect community boundaries
boundaries = discover_community_boundaries(
    buildings_gdf=buildings,
    satellite_image=image_path
)

print(f"Discovered {len(boundaries)} communities")
```

## Troubleshooting

### Common Issues

1. **No imagery found**: Try different time ranges or imagery types
2. **Cloud cover too high**: Reduce `max_cloud_cover` threshold
3. **Download failures**: Check internet connection and try smaller areas
4. **Import errors**: Ensure `geoai-py` is installed: `pip install geoai-py`

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.INFO)

# Enable detailed logging
fetcher = SatelliteDataFetcher()
# Will show detailed fetch attempts and results
```

### Area Coverage Check

```python
# Check what imagery is available for your area
collections = geoai.pc_collection_list()
print("Available collections:", [c['id'] for c in collections])

# Search without downloading
items = geoai.pc_stac_search(
    collection="naip",
    bbox=bounds,
    max_items=1
)
print(f"Found {len(items)} NAIP items for area")
```

## Advanced Features

### Custom Time Series Analysis

```python
# Fetch imagery across multiple time periods
time_periods = [
    "2020-01-01/2020-12-31",
    "2021-01-01/2021-12-31", 
    "2022-01-01/2022-12-31"
]

for period in time_periods:
    image_path = fetcher.get_best_imagery_for_bounds(
        bounds=bounds,
        imagery_type="sentinel2",
        time_range=period
    )
    
    if image_path:
        patches = analyze_satellite_imagery(
            bounds=bounds,
            image_path=image_path
        )
        print(f"Period {period}: {len(patches)} patches analyzed")
```

### Multi-Source Fusion

```python
# Combine multiple imagery sources
naip_patches = analyze_satellite_imagery(bounds, imagery_type="naip")
sentinel_patches = analyze_satellite_imagery(bounds, imagery_type="sentinel2")

# Merge and compare results
combined_analysis = pd.concat([
    naip_patches.assign(source="naip"),
    sentinel_patches.assign(source="sentinel2")
])
```

## Future Enhancements

The satellite imagery integration is actively developed with planned features:

- **Automatic cloud masking** for improved analysis quality
- **Multi-temporal change detection** for community evolution tracking
- **Custom model training** on fetched imagery
- **Real-time imagery monitoring** for dynamic analysis
- **Integration with additional data sources** (Maxar, Planet, etc.)

## Contributing

We welcome contributions to improve the satellite imagery integration:

1. **Report issues** with specific geographic areas or imagery types
2. **Suggest new features** for different satellite data sources
3. **Contribute improvements** to image processing algorithms
4. **Share test cases** from different regions and use cases

---

*The satellite imagery integration leverages the excellent [geoai](https://geoai.gishub.org/) package by Dr. Qiusheng Wu and the Microsoft Planetary Computer STAC API for seamless access to Earth observation data.* 