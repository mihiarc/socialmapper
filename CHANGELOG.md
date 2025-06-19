# SocialMapper Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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