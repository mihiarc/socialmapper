# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SocialMapper is an open-source Python toolkit that analyzes community connections by mapping demographics and access to points of interest (POIs). It creates isochrones (travel time areas) and integrates census data to provide insights about equitable access to community resources.

Key capabilities:
- Query OpenStreetMap for POIs (libraries, schools, parks, etc.)
- Generate travel time isochrones (walk/drive/bike)
- Integrate US Census demographic data
- Create static maps for analysis
- Export data for further analysis in other tools

## Common Development Commands

```bash
# Install for development with all dependencies
uv pip install -e ".[dev]"

# Run tests
uv run pytest
uv run pytest -m unit  # Unit tests only
uv run pytest -m "not slow"  # Skip slow tests

# Format code
uv run black socialmapper/
uv run isort socialmapper/

# Lint code
uv run ruff check socialmapper/

# Type checking (uses ty - Rust-based type checker)
uv run ty check socialmapper/

# Build package
uv run hatch build

# Run CLI
uv run socialmapper --help

# Run examples
uv run python examples/census_analysis.py
```

## Architecture Overview

The codebase follows an ETL (Extract-Transform-Load) pipeline pattern with modern software engineering practices:

1. **Extract**: Pull data from OpenStreetMap and Census APIs
2. **Transform**: Generate isochrones, calculate distances, process demographics
3. **Load**: Create visualizations and export data

### Core Components

- `socialmapper/core.py`: Main API entry point that delegates to pipeline components
- `socialmapper/pipeline/`: Modular ETL pipeline with `PipelineOrchestrator` coordinating extraction, transformation, and loading stages
- `socialmapper/api/`: Modern API layer with Result types, builder pattern, and context manager support
- `socialmapper/census/`: Domain-driven census system with entities, services, and infrastructure layers
- `socialmapper/data/`: Data management including the efficient neighbor system
- `socialmapper/ui/`: User interfaces (CLI with Rich terminal UI)
- `socialmapper/isochrone/`: Travel time area generation using OSMnx
- `socialmapper/geocoding/`: Address geocoding with caching

### Key Architectural Patterns

1. **Domain-Driven Design**: Clear separation of domain entities, services, and infrastructure
2. **Neighbor System**: Efficient parquet-based system for census block group lookups that reduces storage from 118MB to ~0.1MB
3. **Result Types**: Explicit error handling with `Ok` and `Err` types throughout the API
4. **Protocol-Based Interfaces**: Python protocols for flexible implementations (cache strategies, repositories)
5. **Streaming Support**: Memory-efficient processing of large census datasets
6. **Multi-Level Caching**: In-memory, file-based, and hybrid cache strategies for performance
7. **Dependency Injection**: No global state, all dependencies injected through constructors
8. **Builder Pattern**: Type-safe configuration through `SocialMapperBuilder`

### Testing Strategy

- Unit tests in `tests/` directory
- Use pytest with markers: `unit`, `integration`, `slow`, `api`, `async`, `performance`
- Mock external API calls (Census, OpenStreetMap) for unit tests
- Use real API calls only for integration tests
- Test data fixtures for reproducible tests

### External Dependencies

- **Census API**: Requires `CENSUS_API_KEY` environment variable
- **OpenStreetMap**: Uses Overpass API and OSMnx for POI queries (no auth required)
- **Maps**: Matplotlib for static map generation, contextily for basemaps

### Environment Variables

Key environment variables (see `env.example`):
- `CENSUS_API_KEY`: Required for Census Bureau API
- `CENSUS_RATE_LIMIT`: Default 60 requests/minute
- `CENSUS_CACHE_ENABLED`: Default true
- `CENSUS_LOG_LEVEL`: Default INFO

### Geographic Levels

- **Block Groups**: Default, provides detailed local analysis
- **ZCTA**: ZIP Code Tabulation Areas for faster regional analysis

### Recent Changes (v0.6.1)

- Fixed isochrone export functionality (`enable_isochrone_export()`)
- Isochrones now properly export to GeoParquet format
- Enhanced API documentation with isochrone export examples

### Previous Changes (v0.6.0)

- Streamlined codebase by removing experimental features
- Enhanced core ETL pipeline for better maintainability
- Improved neighbor system performance (1000x size reduction)
- Enhanced Rich terminal UI with progress tracking
- Focused on core demographic and accessibility analysis
- Enhanced travel speed handling for more accurate isochrones

## Travel Speed Handling

SocialMapper uses OSMnx 2.0's sophisticated speed assignment system for accurate travel time calculations:

### Speed Assignment Hierarchy

When generating isochrones, OSMnx assigns edge speeds using this priority:

1. **OSM maxspeed tags**: Uses actual speed limits from OpenStreetMap data when available
2. **Highway-type speeds**: Falls back to our configured speeds for each road type (e.g., motorway: 110 km/h, residential: 30 km/h)
3. **Statistical imputation**: For unmapped highway types, uses the mean speed of similar roads in the network
4. **Mode-specific fallback**: As a last resort, uses the travel mode's default speed (walk: 5 km/h, bike: 15 km/h, drive: 50 km/h)

### Highway-Specific Speeds

The system defines realistic speeds for different road types:

**Driving speeds (km/h)**:
- Motorway: 110 (highways/freeways)
- Trunk: 90 (major roads)
- Primary: 65 (primary roads)
- Secondary: 55 (secondary roads)
- Residential: 30 (neighborhood streets)
- Living street: 20 (shared spaces)

**Walking speeds (km/h)**:
- Footway/sidewalk: 5.0
- Path: 4.5
- Steps: 1.5 (stairs)
- Residential: 4.8

**Biking speeds (km/h)**:
- Cycleway: 18 (dedicated bike lanes)
- Primary/secondary: 18-20
- Residential: 15
- Footway: 8 (shared with pedestrians)

These speeds ensure more accurate isochrone boundaries that reflect real-world travel times based on road infrastructure.

## Data Flow Architecture

The pipeline follows this data flow:

1. **Input Stage**: User provides location (coordinates/address) or POI query
2. **Geocoding**: Convert addresses to coordinates with caching
3. **Extraction**:
   - Query OpenStreetMap for POIs via Overpass API
   - Fetch census block group/ZCTA boundaries
4. **Transformation**:
   - Generate isochrones using OSMnx network analysis
   - Intersect isochrones with census units
   - Calculate travel distances and demographics
5. **Loading**:
   - Export results to CSV/GeoParquet
   - Generate static maps with matplotlib
   - Display Rich terminal UI with results

## Performance Considerations

- **Neighbor System**: Uses Parquet format for 1000x storage reduction
- **Streaming Census Data**: Process large datasets without loading into memory
- **Concurrent Processing**: Isochrone generation can run in parallel
- **Smart Caching**: Multiple cache levels to avoid repeated API calls
- **Batch Processing**: Configurable chunk sizes for large operations

## API Usage Patterns

### Modern API with Result Types
```python
from socialmapper.api import SocialMapperClient

with SocialMapperClient() as client:
    result = client.poi_query("library", geographic_level="zcta")
    if result.is_ok():
        data = result.unwrap()
```

### Builder Pattern
```python
from socialmapper.api import SocialMapperBuilder

result = (SocialMapperBuilder()
    .poi_query("library")
    .set_travel_mode("walk")
    .set_travel_time(15)
    .enable_isochrone_export()
    .build()
    .run())
```