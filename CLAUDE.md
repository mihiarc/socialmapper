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

# Linting and formatting (using Ruff - replaces black, flake8, isort)
./scripts/ruff_check.sh all  # Run complete linting and formatting
uv run ruff check socialmapper/  # Lint only
uv run ruff format socialmapper/  # Format only

# Type checking (using ty - ultra-fast Rust-based type checker)
uv run python scripts/type_check.py
uv run python scripts/type_check.py --strict  # Strict mode

# Build package
uv run hatch build

# Documentation
uv run mkdocs serve  # Serve docs locally at http://localhost:8000
uv run mkdocs build  # Build docs

# Run CLI
uv run socialmapper --help
```

## Architecture Overview

The codebase follows an ETL (Extract-Transform-Load) pipeline pattern with modern API design:

### Core Components

- `socialmapper/api/`: Modern API with builder pattern and Result types for error handling
  - `builder.py`: Fluent builder pattern for configuration
  - `client.py`: Main client interface with context manager support
  - `models.py`: Pydantic models for type safety
  - `results.py`: Rust-inspired Ok/Err result types
- `socialmapper/pipeline/`: Modular ETL pipeline implementation
  - `extractor.py`: Data extraction from OpenStreetMap and Census
  - `transformer.py`: Isochrone generation and data processing
  - `loader.py`: Visualization and export functionality
- `socialmapper/census/`: Domain-driven census integration
  - `services/`: Business logic layer
  - `repositories/`: Data access layer
  - `infrastructure/`: External API integration
  - `models/`: Domain models
- `socialmapper/isochrone/`: Travel time area generation using OSMnx
- `socialmapper/geocoding/`: Address geocoding with caching
- `socialmapper/export/`: Multi-format export (CSV, Parquet, GeoParquet, GeoJSON)
- `socialmapper/ui/`: User interfaces (CLI, Rich terminal UI)

### Key Architectural Patterns

1. **Builder Pattern**: For configuration (`SocialMapperBuilder`)
2. **Result Types**: Rust-inspired error handling with `Ok`/`Err` types
3. **Domain-Driven Design**: Especially in the census module
4. **Neighbor System**: Efficient parquet-based system for census block group lookups that reduces storage from 118MB to ~0.1MB
5. **Caching**: Extensive caching for geocoding results and isochrone calculations
6. **Progress Tracking**: Rich terminal UI with real-time progress updates

### Testing Strategy

- Tests are configured in `pyproject.toml` with pytest markers for different test types
- Test markers include: unit, integration, slow, api, async, performance, external
- Mock external API calls (Census, OpenStreetMap) in tests
- Use `uv run pytest -m unit` for fast unit tests only

### External Dependencies

- **Census API**: Requires `CENSUS_API_KEY` environment variable
- **OpenStreetMap**: Uses Overpass API and OSMnx for POI queries
- **Maps**: Matplotlib with contextily for static map generation

### Environment Variables

Create a `.env` file from `env.example`:
- `CENSUS_API_KEY`: Required for Census data (get free at https://api.census.gov/data/key_signup.html)
- `CENSUS_CACHE_ENABLED`: Enable/disable caching (default: true)
- `CENSUS_RATE_LIMIT`: API rate limit in requests per minute (default: 60)
- `LOG_LEVEL`: Logging level (default: INFO)

## Development Standards

### Code Quality Tools

1. **Ruff** (linting and formatting):
   - Line length: 100 characters
   - Comprehensive rule sets enabled (see pyproject.toml)
   - Google-style docstrings
   - Use `./scripts/ruff_check.sh all` for complete check

2. **ty** (type checking):
   - Ultra-fast Rust-based type checker from Astral
   - Use `uv run python scripts/type_check.py`
   - Add `--strict` for comprehensive checking

3. **Rich** for terminal output:
   - Always use Rich for formatted output, never plain print()
   - Progress bars for long operations
   - Structured logging with colors

### Modern Python Patterns

- **Python 3.11+** required (supports 3.11, 3.12, 3.13)
- **Pydantic v2** for all data validation
- **Async support** where applicable
- **Type hints** throughout the codebase
- **Polars** preferred over pandas for data processing

### Travel Speed Handling

SocialMapper uses OSMnx 2.0's sophisticated speed assignment system for accurate travel time calculations:

#### Speed Assignment Hierarchy

When generating isochrones, OSMnx assigns edge speeds using this priority:

1. **OSM maxspeed tags**: Uses actual speed limits from OpenStreetMap data when available
2. **Highway-type speeds**: Falls back to our configured speeds for each road type (e.g., motorway: 110 km/h, residential: 30 km/h)
3. **Statistical imputation**: For unmapped highway types, uses the mean speed of similar roads in the network
4. **Mode-specific fallback**: As a last resort, uses the travel mode's default speed (walk: 5 km/h, bike: 15 km/h, drive: 50 km/h)

#### Highway-Specific Speeds

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

## Recent Changes

### v0.6.1
- Fixed isochrone export functionality (`enable_isochrone_export()`)
- Isochrones now properly export to GeoParquet format
- Enhanced API documentation with isochrone export examples

### v0.6.0
- Streamlined codebase by removing experimental features
- Enhanced core ETL pipeline for better maintainability
- Improved neighbor system performance
- Enhanced Rich terminal UI
- Focused on core demographic and accessibility analysis
- Enhanced travel speed handling for more accurate isochrones

## Example Usage

```python
# Simple analysis with context manager
from socialmapper import SocialMapperClient

with SocialMapperClient() as client:
    result = client.analyze(
        location="San Francisco, CA",
        poi_type="amenity",
        poi_name="library",
        travel_time=15
    )
    
    if result.is_ok():
        analysis = result.unwrap()
        print(f"Found {analysis.poi_count} libraries")
        print(f"Analyzed {analysis.census_units_analyzed} census units")

# Advanced usage with builder pattern
from socialmapper import SocialMapperBuilder

analysis = (
    SocialMapperBuilder()
    .location("San Francisco, CA")
    .poi_type("amenity")
    .poi_name("library")
    .travel_time(15)
    .travel_mode("walk")
    .enable_isochrone_export()
    .build()
    .analyze()
)
```

## Project Structure

```
socialmapper/
├── api/              # Modern API with builder pattern
├── census/           # Domain-driven census integration
├── pipeline/         # ETL pipeline components
├── isochrone/        # Travel time calculations
├── geocoding/        # Address geocoding
├── export/           # Multi-format data export
├── visualization/    # Map generation
├── ui/               # User interfaces
├── data/             # Data files and neighbor system
├── exceptions/       # Custom exception hierarchy
└── utils/            # Utility functions
```