# SocialMapper ZCTA Test Demos

🧪 **Comprehensive test demonstrations for ZIP Code Tabulation Area (ZCTA) functionality**

These demos provide detailed testing and validation of SocialMapper's ZCTA capabilities. For a simple user example, see `examples/zcta_analysis.py`.

## 🎯 Demo Purpose

These demos serve as:
- **Functionality Tests**: Validate ZCTA API integrations
- **Performance Benchmarks**: Test processing speeds and efficiency  
- **API Validation**: Ensure proper Census Bureau API usage
- **Feature Demonstrations**: Showcase advanced capabilities
- **Development Tools**: Help developers understand implementation details

## 🧪 Available Demos

### Demo 1: ZCTA Fundamentals Test
**File:** `zcta_fundamentals_demo.py`
**Purpose:** Core ZCTA functionality validation

**Tests:**
- 📮 ZCTA concept validation and data fetching
- 🔧 Basic ZCTA operations with the census system
- 📊 Census data retrieval and processing
- ⚡ Multi-state batch processing
- 🔍 ZCTA vs Block Group performance comparison

### Demo 2: POI Integration Test
**File:** `zcta_poi_integration_demo.py`
**Purpose:** SocialMapperBuilder ZCTA integration testing

**Tests:**
- 🏗️ SocialMapperBuilder with ZCTA geographic level
- 🗺️ Side-by-side ZCTA vs Block Group analysis
- 📈 Business intelligence workflow validation
- 🔧 Modern library integration testing

### Demo 3: Modern Census API Test
**File:** `modern_zcta_api_demo.py`
**Purpose:** Census Data API format validation

**Tests:**
- 🚀 Proper Census Bureau API format usage
- ⚡ Efficient batch processing methods
- 📊 API response format handling
- 🔧 Performance optimization validation
- 🛡️ Error recovery and data validation

### Demo 4: TIGER REST API Test
**File:** `tiger_api_boundaries_demo.py`
**Purpose:** TIGER boundary API integration testing

**Tests:**
- 🐅 Official TIGER REST API endpoint validation
- 🗺️ ZCTA boundary fetching with rich field data
- 🔧 Multi-state batch processing
- 🔗 Boundary + census data integration
- 📊 API field mapping and standardization

## 🚀 Quick User Example

For everyday ZCTA analysis, use the simple example:

```bash
# Run the main user example
python examples/zcta_analysis.py
```

This provides a clean, focused demonstration of:
- Fetching ZCTA boundaries
- Getting census demographics  
- Combining and analyzing data
- Basic reporting and output

## 🧪 Running Test Demos

### Individual Demo Testing
```bash
# Test ZCTA fundamentals
python examples/demos/zcta_fundamentals_demo.py

# Test POI integration
python examples/demos/zcta_poi_integration_demo.py

# Test modern Census API
python examples/demos/modern_zcta_api_demo.py

# Test TIGER boundary API
python examples/demos/tiger_api_boundaries_demo.py
```

### Batch Demo Testing
```bash
# Run all ZCTA demos for comprehensive testing
for demo in examples/demos/*_demo.py; do
    echo "Running $demo..."
    python "$demo"
    echo "---"
done
```

## 🔧 Demo vs Example Usage

| Purpose | Use | File Location |
|---------|-----|---------------|
| **Quick Analysis** | User example | `examples/zcta_analysis.py` |
| **Feature Testing** | Test demos | `examples/demos/*_demo.py` |
| **API Validation** | Test demos | `examples/demos/*_demo.py` |
| **Performance Testing** | Test demos | `examples/demos/*_demo.py` |
| **Development** | Test demos | `examples/demos/*_demo.py` |

## 📈 API Integration Status

| Component | Status | Demo File |
|-----------|--------|-----------|
| **Census Data API** | ✅ Validated | `modern_zcta_api_demo.py` |
| **TIGER Boundary API** | ✅ Validated | `tiger_api_boundaries_demo.py` |
| **SocialMapperBuilder** | ✅ Validated | `zcta_poi_integration_demo.py` |
| **Batch Processing** | ✅ Validated | `zcta_fundamentals_demo.py` |
| **Error Handling** | ✅ Validated | All demos |

## 🎓 Prerequisites for Demos

- **SocialMapper**: `uv add socialmapper`
- **Census API Key**: Set `CENSUS_API_KEY` (recommended for demos)
- **Python 3.9+**: Modern Python features
- **GeoPandas**: `uv add geopandas`
- **Additional**: `uv add folium plotly tqdm`

## 🛠️ Development Notes

These demos are designed for:
- **API Testing**: Validate external API integrations
- **Regression Testing**: Ensure functionality doesn't break
- **Performance Monitoring**: Track processing speeds
- **Feature Validation**: Test new capabilities
- **Documentation**: Show implementation details

## 🤝 Contributing

When adding new ZCTA functionality:
1. Add comprehensive tests to appropriate demo files
2. Update this README with new test coverage
3. Ensure demos validate both success and error cases
4. Include performance benchmarks where relevant

---

*For simple ZCTA analysis, use `examples/zcta_analysis.py`. For comprehensive testing and validation, use these demos! 🧪* 