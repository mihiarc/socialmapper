# 📍 Address Geocoding in SocialMapper

## Overview

Address geocoding is a core feature in SocialMapper that converts human-readable addresses into geographic coordinates (latitude/longitude). This enables you to analyze custom locations beyond what's available in OpenStreetMap, such as:

- Your organization's facilities
- Client locations
- Community resources not in OSM
- Historical addresses
- Survey respondent locations

## How It Works with SocialMapper

The geocoding system seamlessly integrates into SocialMapper's analysis workflow:

1. **Input addresses** via CSV file or API
2. **Convert to coordinates** using multiple geocoding providers
3. **Generate isochrones** around each location
4. **Analyze demographics** within travel time areas
5. **Export results** with full geographic context

### Example Workflow

```python
from socialmapper import run_socialmapper

# Analyze accessibility from your custom locations
results = run_socialmapper(
    addresses_path="my_facilities.csv",  # Your addresses
    travel_time=15,                      # 15-minute isochrones
    census_variables=["total_population", "median_income"],
    export_maps=True
)
```

## Key Features

### 🔄 Multiple Provider Support
- **OpenStreetMap Nominatim** - Free, global coverage
- **US Census Geocoder** - High accuracy for US addresses
- Extensible to add Google Maps, HERE, Mapbox

### ⚡ High Performance
- **Intelligent caching** - 96% storage reduction with Parquet
- **Batch processing** - Handle thousands of addresses efficiently
- **Automatic fallback** - Try multiple providers for best results

### 🎯 Quality Assurance
- **Quality scoring** - EXACT, INTERPOLATED, CENTROID, APPROXIMATE
- **Validation** - Ensure coordinates are within expected bounds
- **Geographic enrichment** - Add state, county, tract, block group

## 🚀 Quick Start

### Basic Usage

```python
from socialmapper.geocoding import geocode_address

# Simple address geocoding
result = geocode_address("123 Main St, Anytown, USA")
if result.success:
    print(f"Location: {result.latitude}, {result.longitude}")
    print(f"Quality: {result.quality.value}")
```

### Batch Processing

```python
from socialmapper.geocoding import geocode_addresses

# Geocode multiple addresses
addresses = [
    "123 Main St, City, State",
    "456 Oak Ave, Town, State",
    "789 Elm Blvd, Village, State"
]

results = geocode_addresses(addresses, progress=True)
successful = [r for r in results if r.success]
print(f"Geocoded {len(successful)} of {len(addresses)} addresses")
```

### CSV File Input

Create a CSV file with your addresses:
```csv
name,address,city,state,zip
Main Library,123 Main St,Springfield,IL,62701
Branch Library,456 Oak Ave,Springfield,IL,62702
Community Center,789 Elm St,Springfield,IL,62703
```

Then use with SocialMapper:
```bash
socialmapper analyze --addresses-file my_locations.csv --travel-time 15
```

## 🏗️ Architecture

The geocoding system follows a modular design:

```
socialmapper/geocoding/
├── __init__.py           # Public API
├── engine.py             # Core orchestration
├── providers.py          # Provider implementations
└── cache.py             # Caching system
```

### Key Components

1. **AddressGeocodingEngine** - Orchestrates the geocoding process
2. **GeocodingProviders** - Implement specific geocoding services
3. **AddressCache** - High-performance caching layer
4. **Quality Validation** - Ensures result accuracy

## ⚙️ Configuration

### Basic Configuration

```python
from socialmapper.geocoding import GeocodingConfig, AddressProvider

config = GeocodingConfig(
    primary_provider=AddressProvider.NOMINATIM,
    fallback_providers=[AddressProvider.CENSUS],
    enable_cache=True,
    min_quality_threshold="INTERPOLATED"
)
```

### Advanced Options

```python
config = GeocodingConfig(
    # Performance
    timeout_seconds=10,
    max_retries=3,
    batch_size=100,
    
    # Quality
    min_quality_threshold="EXACT",
    require_country_match=True,
    
    # Caching
    cache_ttl_hours=168,  # 1 week
    cache_max_size=10000
)
```

## 🎯 Quality Levels

| Quality | Description | Use Case |
|---------|-------------|----------|
| **EXACT** | Rooftop/exact match | Precise analysis |
| **INTERPOLATED** | Street-level | Neighborhood studies |
| **CENTROID** | ZIP/city center | Regional analysis |
| **APPROXIMATE** | Low precision | Exploratory work |

## 📊 Integration Examples

### With Travel Time Analysis

```python
# Geocode addresses and analyze accessibility
from socialmapper import run_socialmapper

results = run_socialmapper(
    addresses_path="health_clinics.csv",
    travel_time=20,
    travel_mode="drive",
    census_variables=["total_population", "percent_uninsured"]
)

# Results include full demographic analysis for each clinic's service area
```

### With Custom POI Data

```python
from socialmapper.geocoding import addresses_to_poi_format

# Convert addresses to POI format
addresses = [
    {"name": "Clinic A", "address": "123 Main St, City, State"},
    {"name": "Clinic B", "address": "456 Oak Ave, Town, State"}
]

poi_data = addresses_to_poi_format(addresses)

# Use with standard SocialMapper workflow
from socialmapper import run_socialmapper
results = run_socialmapper(
    custom_coords_data=poi_data,
    travel_time=15
)
```

## 💾 Caching System

The geocoding cache dramatically improves performance:

- **Persistent storage** - Results saved between sessions
- **Automatic deduplication** - Same address never geocoded twice
- **TTL expiration** - Configurable cache lifetime
- **Compact format** - Parquet files use 96% less space than JSON

### Cache Location
```
cache/geocoding/
└── address_cache.parquet
```

## 🔧 Troubleshooting

### Common Issues

**"No results found"**
- Check address format and spelling
- Try including more details (city, state, ZIP)
- Verify internet connection

**"Quality below threshold"**
- Lower the quality threshold for exploratory analysis
- Add more address details for better matches
- Try a different provider

**"Rate limit exceeded"**
- Enable caching to reduce API calls
- Reduce batch size
- Add delays between requests

### Debug Mode

```python
import logging
logging.getLogger('socialmapper.geocoding').setLevel(logging.DEBUG)

# Now geocoding will show detailed progress
result = geocode_address("123 Main St")
```

## 📋 Best Practices

1. **Always use caching** - Reduces API calls and improves speed
2. **Batch similar addresses** - Group by city/state for efficiency
3. **Set appropriate quality thresholds** - EXACT for precise analysis, CENTROID for regional
4. **Include full addresses** - More details = better results
5. **Handle failures gracefully** - Some addresses may not geocode

## 🎓 Complete Example

Here's a full workflow using address geocoding:

```python
from socialmapper import run_socialmapper
from socialmapper.geocoding import GeocodingConfig, AddressProvider

# Configure geocoding
geocoding_config = GeocodingConfig(
    primary_provider=AddressProvider.CENSUS,  # Best for US addresses
    enable_cache=True,
    min_quality_threshold="INTERPOLATED"
)

# Run analysis on your facilities
results = run_socialmapper(
    addresses_path="our_facilities.csv",
    travel_time=15,
    travel_mode="walk",
    census_variables=[
        "total_population",
        "median_age", 
        "percent_poverty",
        "percent_without_vehicle"
    ],
    geocoding_config=geocoding_config,
    export_csv=True,
    export_maps=True
)

# Examine results
print(f"Successfully geocoded {results['geocoding_stats']['success_count']} addresses")
print(f"Population within walking distance: {results['total_population']:,}")
```

## 🔮 Future Enhancements

- Google Maps and HERE provider support
- International address formats
- Fuzzy matching for misspelled addresses
- Address standardization and validation
- Async processing for large batches

---

*The address geocoding system in SocialMapper provides reliable, cached, and quality-assured location lookup to enable demographic analysis of any custom location.*