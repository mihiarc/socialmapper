# SocialMapper Census Module (DuckDB-based)

This is the new, modern census module for SocialMapper that replaces both the old `census` and `blockgroups` modules. It uses DuckDB for efficient census data analytics and streams boundary data as needed, optimizing for both performance and storage efficiency.

## Key Features

### 🚀 **Performance Improvements**
- **DuckDB backend**: Fast analytical queries on census data
- **Streaming boundaries**: No storage overhead for large geometries
- **Smart caching**: Optional boundary caching for frequently used areas
- **Lightweight metadata**: Fast lookups without storing full geometries

### 🗺️ **Efficient Boundary Management**
- **Stream-first approach**: Boundaries fetched on-demand from Census APIs
- **Multiple data sources**: Cartographic files, TIGER GeoJSON, and ESRI JSON support
- **Optional caching**: Enable boundary caching only when needed
- **ESRI JSON conversion**: Proper handling of Census API geometry formats

### 📊 **Enhanced Data Analytics**
- **Optimized schema**: DuckDB focused on census data, not geometries
- **Fast joins**: Efficient linking of census data to geographic units
- **Data views**: Create custom analytical views without geometry overhead
- **Multi-year support**: Handle different census years and datasets

### 🔄 **Backward Compatibility**
- **Drop-in replacement**: Same API as old modules
- **Migration tools**: Automated migration from old cache files
- **Gradual transition**: Use alongside existing code

## Installation

The new module is included with SocialMapper. Make sure you have DuckDB installed:

```bash
# DuckDB is included in the updated dependencies
pip install socialmapper>=0.4.1-beta
```

## Quick Start

### Basic Usage (Streaming Mode - Recommended)

```python
from socialmapper.census_new import get_census_block_groups, get_census_data_for_block_groups

# Stream block groups for California and New York (no persistent storage)
block_groups = get_census_block_groups(['06', '36'])  # CA and NY

# Get census data for those block groups (stored in DuckDB for analytics)
census_data = get_census_data_for_block_groups(
    block_groups, 
    variables=['total_population', 'median_income']
)
```

### With Boundary Caching (Optional)

```python
from socialmapper.census_new import get_census_database

# Enable boundary caching for frequently accessed areas
db = get_census_database(cache_boundaries=True)
block_groups = db.get_or_stream_block_groups(['06'])  # Will cache after first fetch
```

### Working with Isochrones

```python
from socialmapper.census_new import isochrone_to_block_groups

# Find block groups that intersect with isochrones (streaming)
intersecting_bgs = isochrone_to_block_groups(
    isochrone_gdf,  # Your isochrone GeoDataFrame
    state_fips=['06'],  # States to search in
    selection_mode='intersect'  # 'intersect', 'contain', or 'clip'
)
```

### Advanced Analytics with DuckDB

```python
from socialmapper.census_new import get_census_database, CensusDataManager

# Get database optimized for analytics
db = get_census_database()

# Create a data manager for advanced operations
data_manager = CensusDataManager(db)

# Create a custom analytical view (no geometries stored)
view_name = data_manager.create_census_view(
    geoids=['060010001001', '060010001002'],
    variables=['B01003_001E', 'B19013_001E'],
    year=2021
)

# Query the view with SQL
result_df = db.conn.execute(f"SELECT * FROM {view_name}").df()
```

## Architecture Overview

### Database Schema (Optimized for Analytics)

The DuckDB database focuses on efficient census data storage and analysis:

#### `geographic_units` (Lightweight Reference)
- `geoid` (VARCHAR): Geographic identifier
- `unit_type` (VARCHAR): 'state', 'county', 'tract', 'block_group'
- `state_fips`, `county_fips`, `tract_code`, `block_group`: Geographic hierarchy
- `name` (VARCHAR): Human-readable name
- `area_land`, `area_water` (BIGINT): Area measurements
- **No geometry stored** - keeps table lightweight

#### `census_data` (Main Analytics Table)
- `geoid` (VARCHAR): Links to geographic_units
- `variable_code` (VARCHAR): Census variable (e.g., 'B01003_001E')
- `variable_name` (VARCHAR): Human-readable variable name
- `value` (DOUBLE): Census value
- `year` (INTEGER): Census year
- `dataset` (VARCHAR): Census dataset (e.g., 'acs5')

#### `boundary_cache` (Optional)
- Only created when `cache_boundaries=True`
- `geoid` (VARCHAR): Geographic identifier
- `geometry` (GEOMETRY): Cached boundary geometry
- `cache_date` (TIMESTAMP): When cached

### Streaming vs Caching

| Mode | Use Case | Storage | Performance |
|------|----------|---------|-------------|
| **Streaming** (Default) | Most workflows | Minimal | Fast for one-time use |
| **Caching** | Repeated analysis | Higher | Fast for repeated use |

```python
# Streaming mode (default) - no boundary storage
db = get_census_database()  # cache_boundaries=False

# Caching mode - stores boundaries in database
db = get_census_database(cache_boundaries=True)
```

## Migration from Old System

The migration script now handles the transition to the streaming architecture:

```bash
# Run the migration script
python -m socialmapper.census_new.migrate

# With options
python -m socialmapper.census_new.migrate --force --cleanup
```

### Migration Benefits

- **Reduced storage**: Old GeoJSON files replaced with lightweight metadata
- **Faster queries**: DuckDB optimized for census data analytics
- **Flexible boundaries**: Stream from multiple sources as needed
- **Better performance**: No file I/O bottlenecks

## API Reference

### Core Classes

#### `CensusDatabase`
Main database interface optimized for census data analytics.

```python
from socialmapper.census_new import CensusDatabase

# Streaming mode (recommended)
db = CensusDatabase()

# With boundary caching
db = CensusDatabase(cache_boundaries=True)

# Custom database location
db = CensusDatabase("/path/to/custom.duckdb", cache_boundaries=False)
```

#### Key Methods

- `get_or_stream_block_groups()`: Stream boundaries from APIs
- `find_intersecting_block_groups()`: Spatial analysis with streaming
- `_store_geographic_metadata()`: Store lightweight geographic references
- `_cache_boundaries()`: Optional boundary caching

### Data Sources and Fallbacks

The system tries multiple data sources in order of preference:

1. **Census Cartographic Boundary Files** (Shapefiles) - Preferred
2. **TIGER/Web API with GeoJSON** - Fallback
3. **TIGER/Web API with ESRI JSON** - Last resort with conversion

### ESRI JSON Conversion

The module includes robust ESRI JSON to Shapely geometry conversion:

```python
# Automatic conversion from ESRI JSON format
gdf = db._fetch_from_tiger_esri_json(state_fips)

# Handles complex polygons with holes
geometry = db._convert_esri_geometry_to_shapely(esri_geom)
```

## Performance Optimization

### Storage Efficiency

| Component | Old System | New System |
|-----------|------------|------------|
| Boundaries | Individual GeoJSON files | Streamed on-demand |
| Census Data | Mixed with boundaries | Optimized DuckDB tables |
| Metadata | File-based | Lightweight database records |
| Caching | Always on | Optional and configurable |

### Query Performance

```python
# Fast analytical queries on census data
db.conn.execute("""
    SELECT 
        state_fips,
        AVG(value) as avg_population
    FROM census_data cd
    JOIN geographic_units gu ON cd.geoid = gu.geoid
    WHERE variable_code = 'B01003_001E'
    GROUP BY state_fips
""").df()
```

### Memory Usage

- **Streaming**: Boundaries loaded only when needed
- **Caching**: Boundaries stored only for frequently used areas
- **Analytics**: DuckDB optimized for in-memory operations

## Best Practices

### When to Use Streaming (Default)
- One-time analysis
- Large geographic areas
- Storage-constrained environments
- Exploratory data analysis

### When to Enable Caching
- Repeated analysis of same areas
- Interactive applications
- Performance-critical workflows
- Offline analysis requirements

```python
# For repeated analysis of the same areas
db = get_census_database(cache_boundaries=True)

# For one-time analysis or large areas
db = get_census_database()  # streaming mode
```

### Optimizing Performance

1. **Specify states**: Always provide state_fips when possible
2. **Use analytics views**: Create views for repeated queries
3. **Batch operations**: Process multiple variables at once
4. **Cache selectively**: Only cache frequently used boundaries

## Troubleshooting

### Common Issues

**Slow performance with large areas**
```python
# Specify states to limit search area
intersecting = db.find_intersecting_block_groups(
    geometry, 
    state_fips=['06', '36']  # Limit to CA and NY
)
```

**Memory issues with large datasets**
```python
# Use streaming mode (default)
db = get_census_database(cache_boundaries=False)
```

**ESRI JSON conversion errors**
```python
# The system automatically falls back through multiple data sources
# Check logs for specific conversion issues
```

## Comparison with Old System

| Feature | Old System | New System |
|---------|------------|------------|
| **Storage** | GeoJSON files per state | Lightweight metadata + streaming |
| **Performance** | File I/O bottlenecks | Fast DuckDB analytics |
| **Flexibility** | Fixed file format | Multiple data sources |
| **Scalability** | Limited by file system | Scales with DuckDB |
| **Memory** | All boundaries in memory | Stream as needed |
| **Analytics** | External tools needed | Built-in SQL analytics |

## Future Enhancements

- **Intelligent caching**: Auto-cache based on usage patterns
- **Parallel streaming**: Concurrent boundary fetching
- **Advanced analytics**: Built-in demographic analysis functions
- **Cloud integration**: Support for cloud-based databases
- **Real-time updates**: Automatic updates from Census APIs

## Contributing

To contribute to the census module:

1. Follow the streaming-first architecture
2. Optimize for analytics performance
3. Add tests for ESRI JSON conversion
4. Update documentation for new features
5. Ensure backward compatibility

## License

This module is part of SocialMapper and follows the same MIT license. 