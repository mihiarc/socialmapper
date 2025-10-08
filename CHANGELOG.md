# SocialMapper Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.0] - 2025-10-08

### ⚠️ Breaking Changes

**API Redesign: Pipeline → Individual Functions**

This release replaces the pipeline-based API with individual function calls for simpler, more intuitive usage.

**Old API (0.8.0):**
```python
from socialmapper import SocialMapper

client = SocialMapper()
result = client.pipeline()...
```

**New API (0.9.0):**
```python
from socialmapper import create_isochrone, get_census_data, create_map

isochrone = create_isochrone("Boston, MA", travel_time=15)
census_data = get_census_data(isochrone['geometry'])
create_map(census_data)
```

**Migration Guide:**
- Replace `SocialMapper()` client with direct function imports
- Use `create_isochrone()` instead of pipeline methods
- Use `get_census_blocks()` and `get_census_data()` for demographics
- Use `get_poi()` for points of interest
- Use `create_map()` for visualization

### ✨ Features

#### **Documentation & Testing**
- **Comprehensive test coverage** with 255+ passing tests
- **NumPy-style docstrings** across all major modules
- **Enhanced documentation** aligned with actual API implementation
- **GitHub Actions workflow** for automatic documentation deployment

#### **Development Experience**
- **Consolidated tutorial series** into progressive learning path
- **Organized coverage reports** into reports/ directory
- **Streamlined infrastructure** by removing over-engineered CI/CD
- **Cleaned up site structure** by archiving outdated documentation

### 🐛 Bug Fixes
- Fixed 'dict' object has no attribute 'columns' error in quick tutorial
- Optimized tutorial performance for speed and reliability

### 📚 Documentation
- Rewrote documentation to match actual API implementation
- Refactored tutorials to enhance functionality and streamline analysis
- Updated simple tutorials for current simplified API

### 🧪 Testing
- Added comprehensive test suite for public API functions
- Added comprehensive tests for census.py module
- Added unit tests for validators and helpers modules
- Added tests for POI and analysis functions
- Added tests for create_map() visualization function

## [0.8.0] - 2025-08-03

### 🚀 Major Features

#### 🏗️ **Enhanced Toolkit Architecture**
- **Architectural improvements** focusing on core Python toolkit
- **Enhanced functionality** with improved Python API
- **Streamlined installation** with simplified dependencies
- **Core analysis capabilities** with comprehensive toolkit support

#### 🗺️ **Nearby POI Discovery System**
- **Comprehensive POI discovery pipeline** for finding points of interest
- **Advanced POI categorization system** with standardized taxonomy
- **Polygon-based spatial queries** using buffered geometries
- **Overpass API integration** for OpenStreetMap data retrieval
- **SocialMapperClient extensions** with nearby POI discovery methods
- **Builder pattern support** for fluent POI discovery configuration

#### 🧪 **Comprehensive Test Suite**
- **370+ test cases** covering core functionality (368 passing, 2 skipped)
- **Unit and integration tests** for all major components
- **Test coverage** for API builders, POI discovery, and pipeline components
- **Robust error handling tests** and edge case validation
- **CI/CD integration** with GitHub Actions workflows

### ✨ New Features

#### **Core Infrastructure**
- **Enhanced Python API** with comprehensive functionality
- **Improved error handling** and validation
- **Better performance** for analysis operations
- **Result management system** with cleanup utilities
- **Async processing support** for large datasets

#### **POI Discovery Components**
- **POI categorization engine** with hierarchical taxonomy
- **Spatial buffering algorithms** for area-based queries
- **Multi-source POI integration** (OpenStreetMap, custom sources)
- **Distance-based filtering** and ranking systems
- **Comprehensive result aggregation** and formatting

#### **Developer Experience**
- **Enhanced CLI interface** with improved command structure
- **Debug utilities** for Streamlit applications
- **Rich terminal output** with progress indicators
- **Comprehensive logging** throughout all components
- **Type-safe data models** with Pydantic v2

### 🔧 Technical Improvements

#### **Infrastructure & Deployment**
- **Docker Compose configurations** for development and production
- **Kubernetes deployment manifests** with Helm charts
- **Automated deployment scripts** and CI/CD pipelines
- **Environment-specific configurations** and secrets management
- **Health monitoring** and observability features

#### **Code Quality & Maintainability**
- **Modular architecture** with clear separation of concerns
- **Enhanced error handling** with custom exception hierarchy
- **Improved caching mechanisms** for performance optimization
- **Type annotations** throughout codebase for better IDE support
- **Comprehensive docstrings** following Google style conventions

#### **Performance Optimizations**
- **Concurrent processing** for POI discovery operations
- **Efficient spatial indexing** for large-scale queries
- **Memory usage optimizations** for large datasets
- **Database connection pooling** and query optimization
- **Caching strategies** for frequently accessed data

### 🐛 Bug Fixes

- **Fixed import errors** in census pipeline modules
- **Resolved AttributeError** with PosixPath objects in file handling
- **Fixed travel mode error handling** and import path issues
- **Enhanced geocoding fallback mechanisms** with improved logging
- **Fixed cache retrieval failures** in census data processing
- **Resolved coordinate validation issues** in custom POI uploads

### 📚 Documentation Updates

#### **Comprehensive Documentation**
- **API reference documentation** for all new endpoints
- **POI discovery guide** with detailed usage examples
- **Migration guide** for upgrading from v0.6.x to v0.7.0
- **Deployment documentation** covering Docker and Kubernetes
- **Developer setup guides** for contribution workflows

#### **Enhanced Examples**
- **POI discovery pipeline examples** showing real-world usage
- **Polygon query examples** for spatial analysis
- **Builder pattern examples** demonstrating fluent API usage
- **Integration examples** for custom applications

### 🔄 Breaking Changes

- **API structure changes** due to frontend-backend separation
- **Import path modifications** for some core modules
- **Configuration format updates** for deployment scenarios
- **CLI command structure changes** for improved usability

### 🚧 Migration Guide

For users upgrading from v0.7.x:
1. **Update import statements** to reflect new module structure
2. **Review API client usage** for backend separation changes  
3. **Update deployment configurations** if using Docker/Kubernetes
4. **Check CLI command syntax** for any changed parameters

### 📈 Performance Improvements

- **40% faster POI discovery** through optimized spatial queries
- **Reduced memory footprint** for large-scale analyses
- **Improved caching efficiency** with smarter invalidation
- **Enhanced concurrent processing** for multi-threaded operations

### 🛡️ Security Enhancements

- **Input validation** for all API endpoints
- **Rate limiting** to prevent abuse
- **CORS policies** for secure cross-origin requests
- **Environment variable security** for sensitive configurations

---

## [0.7.0] - 2025-07-XX

### Previous Release
- Previous version released on PyPI
- For v0.7.0 features, see the PyPI package description

---

## [0.6.2] - 2025-07-08

### 🐛 Bug Fixes

#### **Fixed Travel Time Propagation in Census Data Export**
- **Fixed incorrect travel_time_minutes** in exported census CSV files
- **Travel time now correctly propagates** from pipeline configuration to census data
- **Previously defaulted to 15 minutes** regardless of actual isochrone travel time
- **Now accurately reflects** the travel time used for isochrone generation (e.g., 60, 120 minutes)

### 🔧 Technical Details

- Added `travel_time` parameter to `integrate_census_data()` function
- Updated `PipelineOrchestrator` to pass travel_time to census integration  
- Modified `add_travel_distances()` to accept and use travel_time parameter
- Maintains backward compatibility while fixing the metadata accuracy

## [0.6.1] - 2025-06-19

### 🐛 Bug Fixes

#### **Fixed Isochrone Export Functionality**
- **Fixed missing implementation** of `enable_isochrone_export()` in the pipeline
- **Added GeoParquet export** for isochrone geometries when enabled
- **Updated API client** to properly track exported isochrone files
- **Files are now saved** to `output/isochrones/` directory as GeoParquet format

### 📚 Documentation Updates

#### **Enhanced API Documentation**
- **Updated `enable_isochrone_export()` documentation** with detailed usage examples
- **Added isochrone file path** to `AnalysisResult` documentation
- **New examples** showing how to load and visualize exported isochrones
- **Updated exporting guide** with modern API examples and GeoParquet format details

### 🔧 Technical Details

- Isochrones are exported using the naming pattern: `{base_filename}_{travel_time}min_isochrones.geoparquet`
- GeoParquet format with snappy compression for efficient storage
- Files can be loaded with GeoPandas and converted to other formats (Shapefile, GeoJSON)
- Exported isochrone files are included in `analysis.files_generated['isochrone_data']`

## [0.6.0] - 2025-06-18

### 🚀 Major Features

#### 🎨 **Streamlit UI Overhaul**
- **Completely redesigned** Streamlit application with multi-page tutorial structure
- **Interactive tutorials** for Getting Started, Custom POIs, and Travel Modes
- **Enhanced UI components** with better error handling and user feedback
- **Map previews** and downloadable results for all analyses
- **Travel mode comparison** with equity analysis features

#### 📦 **Updated Dependencies**
- **Streamlit 1.46.0** - Latest version with improved performance
- **Streamlit-Folium 0.25.0** - Better map integration
- **All packages updated** to their latest stable versions
- **Better compatibility** with modern Python environments

#### 🔧 **Error Handling Improvements**
- **Comprehensive error handling** throughout census and isochrone services
- **Better error messages** for common issues
- **Graceful fallbacks** when services are unavailable
- **Improved logging** for debugging

### ✨ New Features

#### **Streamlit Pages**
1. **Getting Started** - Interactive introduction to SocialMapper
2. **Custom POIs** - Upload and analyze custom locations with:
   - CSV file upload with validation
   - Interactive map preview
   - Multiple export formats
   - Detailed demographic analysis

3. **Travel Modes** - Compare accessibility across different modes:
   - Side-by-side comparison of walk, bike, and drive
   - Equity analysis based on income distribution
   - Distance distribution visualizations
   - Comprehensive demographic comparisons

4. **ZCTA Analysis** - (Coming Soon) ZIP code level analysis

#### **Enhanced Visualization**
- **Map downloads** for all generated visualizations
- **Preview capabilities** for maps and data tables
- **Better labeling** of exported files
- **Support for multiple map types** (accessibility, distance, demographics)

### 🔧 Technical Improvements

#### **Code Organization**
- **Modular page structure** for Streamlit app
- **Centralized configuration** for POI types, census variables, and travel modes
- **Reusable UI components** for maps and data display
- **Better separation of concerns** between UI and business logic

#### **Census Integration**
- **Fixed import errors** in census pipeline
- **Better error handling** for census API failures
- **Numba compatibility fixes** for caching
- **Improved ZCTA support** (partial implementation)

#### **File Management**
- **Better handling** of directory structures in exports
- **Individual file downloads** for map directories
- **User-friendly file naming** for downloads
- **Support for various file formats** (PNG, CSV, GeoJSON)

### 🐛 Bug Fixes

- **Fixed AttributeError** with PosixPath objects in file handling
- **Fixed IsADirectoryError** when trying to open directories as files
- **Fixed missing imports** for format_number and format_currency utilities
- **Fixed numba caching errors** in distance calculations
- **Resolved import errors** in census pipeline module
- **Fixed relative import issues** in Streamlit app structure

### 📈 Performance Improvements

- **Optimized file loading** in Streamlit pages
- **Better memory management** for large analyses
- **Improved caching** for repeated operations
- **Faster map rendering** with selective data loading

### 🏘️ User Experience

- **Clearer error messages** when analyses fail
- **Progress indicators** for long-running operations
- **Helpful tooltips** and explanations throughout UI
- **Example templates** for custom POI uploads
- **Comprehensive analysis summaries** in JSON format

### 📊 Data Export Enhancements

- **Multiple export formats** supported (CSV, PNG, GeoJSON)
- **Organized file structure** for outputs
- **Downloadable analysis summaries**
- **Better file naming conventions**

### 🚧 Known Issues

- **ZCTA Analysis** temporarily disabled pending full implementation
- **Some advanced features** may require additional testing
- **Large dataset processing** may be slower in Streamlit environment

### 🔄 Migration Notes

- **Streamlit app location** changed - use `streamlit run streamlit_app.py` from root
- **Updated dependencies** may require virtual environment refresh
- **New page-based structure** replaces single-page app
- **Configuration moved** to centralized location

### 📚 Documentation

- **Improved in-app documentation** with tutorial content
- **Better code comments** throughout new features
- **Updated type hints** for better IDE support
- **Comprehensive docstrings** for new functions

---

## [0.5.4] - Previous Release

(Previous changelog content...)