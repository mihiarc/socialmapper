# SocialMapper Architecture

## Overview

SocialMapper is a Python toolkit for spatial analysis and demographic mapping, designed with simplicity, performance, and extensibility in mind. The architecture follows clean design principles with clear separation of concerns across distinct layers.

## Design Philosophy

### Core Principles

1. **Simplicity First**: Public API provides just 5 core functions
2. **Performance Optimized**: Multi-level caching and concurrent processing
3. **Clean Architecture**: Clear separation between API, business logic, and data layers
4. **Extensible Design**: Modular structure allows easy feature additions
5. **Type Safety**: Comprehensive type hints and Pydantic validation

### API Design

The public API intentionally minimizes cognitive load:

```python
from socialmapper import (
    create_isochrone,    # Generate travel-time polygons
    get_poi,             # Find points of interest
    get_census_blocks,   # Fetch census geographies
    get_census_data,     # Get demographic data
    create_map,          # Generate visualizations
)
```

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Public API Layer                        │
│                    (api.py - 5 functions)                    │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│                   Business Logic Layer                       │
├──────────────────────────────────────────────────────────────┤
│  Isochrone   │ Geocoding │  Census  │   POI    │  Export    │
│  Generation  │  Engine   │  Client  │  Query   │  Formats   │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│                      Data Access Layer                       │
├──────────────────────────────────────────────────────────────┤
│   Census API  │  OpenStreetMap  │  Nominatim  │  TIGERweb   │
└──────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│                       Cache Layer                            │
├──────────────────────────────────────────────────────────────┤
│   Network     │  Geocoding   │  Census    │   Neighbor      │
│   Cache       │  Cache       │  Cache     │   Manager       │
└──────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. API Layer (`api.py`)

**Purpose**: Provides the public interface with parameter validation

**Key Functions**:
- `create_isochrone()` - Travel-time polygon generation
- `get_poi()` - Point of interest discovery
- `get_census_blocks()` - Census geography retrieval
- `get_census_data()` - Demographic data fetching
- `create_map()` - Choropleth visualization

**Responsibilities**:
- Input validation using validators
- Parameter normalization
- Coordinate resolution (address → lat/lon)
- Error handling and user-friendly messages

### 2. Isochrone Module (`isochrone/`)

**Purpose**: High-performance travel-time polygon generation

**Architecture**:
```
isochrone/
├── __init__.py          # Main API and orchestration
├── cache.py             # Network caching with SQLite
├── clustering.py        # DBSCAN spatial clustering
├── concurrent.py        # Parallel processing
└── travel_modes.py      # Travel mode configurations
```

**Key Features**:
- **Intelligent Clustering**: Groups nearby POIs using DBSCAN
- **Network Caching**: SQLite-based road network caching
- **Concurrent Processing**: Parallel network downloads and isochrone generation
- **Auto-optimization**: Automatically selects best strategy based on data

**Performance Optimizations**:
- Shared network graphs for nearby locations (clustering)
- Persistent SQLite cache with spatial indexing
- Concurrent downloads (4-8x speedup for multiple POIs)
- Adaptive buffering based on travel time

### 3. Geocoding Module (`geocoding/`)

**Purpose**: Multi-provider address geocoding with intelligent fallback

**Architecture**:
```
geocoding/
├── __init__.py          # Public interface
├── engine.py            # Orchestration and fallback logic
├── providers.py         # Provider implementations
├── models.py            # Pydantic models
└── cache.py             # Result caching
```

**Providers**:
- **Nominatim** (OpenStreetMap): Free, rate-limited, global coverage
- **Census Bureau**: Free, US-only, high accuracy
- **Extensible**: Easy to add Google, Mapbox, etc.

**Features**:
- Automatic provider fallback
- Quality-based filtering
- Persistent disk caching
- Rate limiting and retry logic
- Census geography enrichment (FIPS codes, block groups)

### 4. Census Integration (`census.py`)

**Purpose**: US Census data retrieval and processing

**Key Classes**:
- `CensusClient`: Simple HTTP client for Census API
- Variable normalization (friendly names → Census codes)
- Batch processing for multiple geographies

**Supported Geographies**:
- Census Block Groups (primary)
- Census Tracts
- ZCTAs (ZIP Code Tabulation Areas)
- Counties and States

**Features**:
- Automatic FIPS code resolution
- Year-based ACS 5-year estimates
- Error code handling (-666666666, etc.)
- Retry logic for transient failures

### 5. POI Discovery (`_osm.py`, `query/`)

**Purpose**: OpenStreetMap point of interest querying

**Architecture**:
```
query/
├── __init__.py          # Public interface
├── osmnx_query.py       # OSMnx-based queries
└── polygon_queries.py   # Polygon-based spatial queries
```

**Features**:
- 10 POI categories (libraries, schools, parks, healthcare, etc.)
- 338+ OSM tag mappings
- Polygon-based and radius-based queries
- Distance calculations to census block groups

**Query Types**:
- Point + radius search
- Polygon-based search
- Network-constrained search (isochrone-based)

### 6. Export Module (`export/`)

**Purpose**: Multi-format data export

**Architecture**:
```
export/
├── __init__.py          # Public API
├── base.py              # Base classes and config
├── preparation.py       # Data preparation utilities
├── utils.py             # Helper functions
└── formats/
    ├── csv.py           # CSV exporter
    ├── parquet.py       # Parquet exporter
    └── geoparquet.py    # GeoParquet exporter
```

**Supported Formats**:
- CSV (legacy, human-readable)
- Parquet (efficient, columnar)
- GeoParquet (geospatial + efficient)

**Features**:
- Automatic format selection based on data size
- Geometry serialization
- Metadata inclusion
- Deduplication

### 7. Visualization (`visualization/`)

**Purpose**: Static choropleth map generation

**Architecture**:
```
visualization/
├── __init__.py          # Public interface
├── chloropleth.py       # Map creation
├── config.py            # Configuration defaults
└── utils.py             # Helper utilities
```

**Features**:
- Census data visualization
- Overlay support (POIs, isochrones)
- Multiple classification schemes (quantiles, jenks, etc.)
- Basemap integration (contextily)
- Professional styling options

### 8. Distance Module (`distance/`)

**Purpose**: Network-based distance calculations

**Features**:
- Road network distance computation
- POI to census block group distances
- Batch distance calculations

### 9. Neighbor System (`neighbors.py`)

**Purpose**: Fast geographic lookups using pre-computed spatial indices

**Features**:
- Census geography reverse lookup (point → block group)
- State/county FIPS resolution
- Parquet-based spatial index
- Sub-millisecond lookups

## Data Flow

### Example: Creating an Isochrone with Census Data

```
1. User Request
   └─> create_isochrone("Portland, OR", travel_time=15)

2. API Layer (api.py)
   ├─> Validate inputs
   ├─> Resolve address to coordinates (geocoding)
   └─> Call isochrone generation

3. Isochrone Generation (isochrone/)
   ├─> Check network cache
   ├─> Download road network if needed (OSMnx)
   ├─> Calculate travel-time polygon
   └─> Return GeoJSON

4. Census Integration (census.py)
   ├─> Identify intersecting block groups
   ├─> Fetch census data for block groups
   └─> Return structured data

5. Response
   └─> Return results to user
```

### Caching Strategy

SocialMapper implements multi-level caching for optimal performance:

#### 1. Network Cache (SQLite)
- **Location**: `~/.cache/socialmapper/networks/`
- **Purpose**: Cache road network graphs
- **Benefit**: Avoid repeated OSM downloads
- **TTL**: Persistent (manual clearing)

#### 2. Geocoding Cache (JSON + Memory)
- **Location**: `~/.cache/socialmapper/geocoding/`
- **Purpose**: Cache geocoding results
- **Benefit**: Reduce API calls
- **TTL**: 30 days (configurable)

#### 3. Census Cache (Neighbors Parquet)
- **Location**: Embedded in package
- **Purpose**: Fast geographic lookups
- **Benefit**: Sub-millisecond census geography resolution
- **Format**: Pre-computed spatial index

#### 4. Neighbor Manager (In-Memory)
- **Purpose**: Cache block group lookups
- **Benefit**: O(log n) spatial queries
- **Implementation**: R-tree spatial index

## Design Decisions

### Why 5-Function API?

**Rationale**: Reduce cognitive load and improve discoverability

- Most users need just 2-3 functions for their workflow
- Clear, memorable function names
- Consistent parameter patterns
- Easy to learn and teach

### Why Dual Cache Strategy?

**Network Cache (Persistent SQLite)**:
- Road networks change infrequently
- Download is expensive (time + bandwidth)
- Shared across projects

**Geocoding Cache (JSON + TTL)**:
- Addresses can change
- Balance freshness vs. performance
- Provider-specific caching

### Why NumPy Docstrings?

**Rationale**: Scientific Python ecosystem standard

- Better for scientific libraries
- Clear parameter documentation
- Consistent with NumPy, SciPy, pandas
- Excellent Sphinx integration

### Why Pydantic v2?

**Benefits**:
- Runtime validation
- Type safety
- Clear error messages
- Performance (Rust core)

### Why Ruff over Black?

**Rationale**: Modern, fast, comprehensive

- 10-100x faster than Black + Flake8
- Single tool replaces multiple
- Active development (Astral)
- Comprehensive rule sets

## Performance Characteristics

### Isochrone Generation

| Scenario | Strategy | Performance |
|----------|----------|-------------|
| Single POI | Standard | 2-5 seconds |
| 5-10 POIs (scattered) | Clustering | 4-8x speedup |
| 10+ POIs (clustered) | Concurrent | 6-10x speedup |
| Cached network | Cache hit | <1 second |

### Geocoding

| Provider | Latency | Coverage | Accuracy |
|----------|---------|----------|----------|
| Cache hit | <1ms | All | Perfect |
| Nominatim | 100-500ms | Global | Good |
| Census | 200-800ms | US only | Excellent |

### Census Data

| Operation | Typical Time |
|-----------|-------------|
| Block group lookup | <10ms |
| Census API call | 200-1000ms |
| 50 block groups | 500-1500ms |

## Extensibility

### Adding New Geocoding Providers

1. Implement `GeocodingProvider` abstract class
2. Add to `providers.py`
3. Configure in `GeocodingConfig`
4. Provider automatically integrated into fallback chain

### Adding New Export Formats

1. Create exporter in `export/formats/`
2. Implement base export interface
3. Add to `export/__init__.py`
4. Automatic format selection available

### Adding New POI Categories

1. Define OSM tag mappings
2. Add to category mappings
3. Update documentation
4. Query system automatically supports

## Testing Strategy

### Test Pyramid

```
        ┌───────────┐
        │    E2E    │  (Few)
        └─────────────┘
      ┌───────────────┐
      │  Integration  │  (Some)
      └─────────────────┘
    ┌───────────────────┐
    │      Unit         │  (Many)
    └───────────────────┘
```

### Test Categories

- **Unit Tests**: Fast, isolated, no external deps
- **Integration Tests**: Test external APIs (marked `external`)
- **Regression Tests**: Prevent known bugs
- **Performance Tests**: Measure optimization impact

### Coverage Goals

- Overall: >80%
- Core API (`api.py`): >90%
- Critical paths (isochrone, geocoding): >85%

## Security Considerations

### API Key Management

- Environment variables (.env)
- Secure keyring storage (optional)
- Never logged or committed

### Data Privacy

- No user data collection
- All caching is local
- Census data is public
- OSM data is open

### Input Validation

- Pydantic models for type safety
- Range checking (travel times, coordinates)
- SQL injection prevention (parameterized queries)

## Future Architecture Considerations

### Potential Enhancements

1. **Async/Await Support**: Non-blocking I/O for concurrent operations
2. **Streaming API**: Large dataset handling without memory overflow
3. **Plugin System**: Third-party extensions
4. **Cloud Deployment**: Docker + Kubernetes patterns
5. **Web API**: FastAPI REST endpoint wrapper

### Scalability

Current architecture scales to:
- 1000s of POIs (with clustering)
- State-level analysis (millions of block groups)
- Year-long batch processing

For larger scales, consider:
- Database-backed caching (PostgreSQL/PostGIS)
- Distributed processing (Dask/Ray)
- Cloud storage (S3/GCS)

## Conclusion

SocialMapper's architecture balances simplicity with performance, providing a clean API while leveraging sophisticated optimization techniques behind the scenes. The modular design allows for easy maintenance and extension while keeping the user experience straightforward.

For implementation details, see the inline code documentation (NumPy-style docstrings) and the API reference.
