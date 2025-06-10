# SocialMapper: Explore Community Connections

[![PyPI version](https://badge.fury.io/py/socialmapper.svg)](https://badge.fury.io/py/socialmapper)
[![Python Versions](https://img.shields.io/pypi/pyversions/socialmapper.svg)](https://pypi.org/project/socialmapper/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/socialmapper)](https://pepy.tech/project/socialmapper)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://socialmapper.streamlit.app)

SocialMapper is an open-source Python toolkit that helps you understand how people connect with the important places in their community. Imagine taking a key spot like your local shopping center or school and seeing exactly what areas are within a certain travel time – whether it's a quick walk or a longer drive. SocialMapper does just that.

But it doesn't stop at travel time. SocialMapper also shows you the characteristics of the people who live within these accessible areas, like how many people live there and what the average income is. This helps you see who can easily reach vital community resources and identify any gaps in access.

Whether you're looking at bustling city neighborhoods or more spread-out rural areas, SocialMapper provides clear insights for making communities better, planning services, and ensuring everyone has good access to the places that matter.

## 🚀 Quick Start

**[Try the Interactive Web App](https://socialmapper.streamlit.app)** - Explore community connections with our Streamlit app - no coding required!

**Install with pip:**
```bash
pip install socialmapper
```

**Basic usage:**
```python
from socialmapper import run_socialmapper

# Analyze library accessibility in your city
results = run_socialmapper(
    geocode_area="Chicago",
    state="IL",
    poi_type="amenity",
    poi_name="library",
    travel_time=15,
    census_variables=["total_population", "median_household_income"]
)
```

## 🎯 Key Features

### 🗺️ **Advanced Mapping & Visualization**
- **[Address Geocoding System](ADDRESS_GEOCODING.md)** - Production-ready address lookup with multiple providers
- **[Plotly Integration](PLOTLY_INTEGRATION.md)** - Interactive maps with modern visualization
- **[AI Community Detection](features/ai-community-detection.md)** - Discover organic community boundaries

### 🏘️ **Community Analysis**
- **Travel Time Analysis** - Generate isochrones showing reachable areas
- **Demographic Integration** - Census data analysis for community characteristics  
- **Point of Interest Discovery** - Find libraries, schools, healthcare facilities
- **[Satellite Imagery Integration](examples/satellite_imagery_integration.md)** - Computer vision for land use analysis

### 🛠️ **Developer Tools**
- **Python API** - Full programmatic access
- **Command Line Interface** - Easy scripting and automation
- **Streamlit App** - Interactive web interface
- **[OSMnx Integration](OSMNX_FEATURES.md)** - Advanced network analysis

## 📚 Documentation Sections

### 🚀 Getting Started
- **[Installation Guide](getting-started/installation.md)** - Set up SocialMapper
- **[Quick Start Tutorial](getting-started/quick-start.md)** - Your first analysis
- **[Demo Instructions](DEMO_INSTRUCTIONS.md)** - Interactive demonstrations

### 📖 User Guide  
- **[Configuration](user-guide/configuration.md)** - Customize your analysis
- **[Data Sources](user-guide/data-sources.md)** - Understanding input data
- **[Architecture Overview](ARCHITECTURE.md)** - System design and components

### 🎯 Features in Detail
- **[Address Geocoding](ADDRESS_GEOCODING.md)** - Modern address lookup system
- **[AI Community Detection](features/ai-community-detection.md)** - Machine learning for boundaries
- **[Plotly Visualization](PLOTLY_INTEGRATION.md)** - Interactive mapping

### 🔧 Development
- **[Contributing Guide](development/contributing.md)** - Join the project
- **[Architecture Details](development/architecture.md)** - Technical design
- **[API Reference](api/index.md)** - Complete function documentation

## 🌟 What's New

### Latest Release Features
- **🛰️ Satellite Imagery Integration** - Real imagery analysis with geoai
- **🤖 AI Community Detection** - Machine learning boundary discovery  
- **📍 Enhanced Geocoding** - Production-ready address system
- **⚡ Performance Improvements** - 17x faster processing
- **🎨 Modern UI** - Rich terminal output and better visualization

See the **[Changelog](CHANGELOG.md)** for complete release history.

## 🎯 Use Cases

### Urban Planning
- **Service Accessibility** - Analyze access to public facilities
- **Transportation Planning** - Understand travel patterns
- **Community Impact Assessment** - Measure development effects

### Public Health & Policy
- **Healthcare Access** - Map medical facility coverage
- **Food Security** - Analyze grocery store accessibility  
- **Educational Equity** - Study school access patterns

### Research & Analysis
- **Demographic Studies** - Population characteristics analysis
- **Community Mapping** - Discover organic neighborhoods
- **Social Equity** - Identify service gaps and opportunities

## 🚀 Try It Now

=== "Web App (No Installation)"

    **[Launch SocialMapper Web App](https://socialmapper.streamlit.app)**
    
    - Interactive interface
    - No coding required  
    - Instant results
    - Export capabilities

=== "Command Line"

    ```bash
    # Install SocialMapper
    pip install socialmapper
    
    # Run analysis
    socialmapper --poi --geocode-area "Seattle" --state "WA" \
      --poi-type "amenity" --poi-name "library" --travel-time 15
    ```

=== "Python API"

    ```python
    from socialmapper import run_socialmapper
    
    # Analyze community access
    results = run_socialmapper(
        geocode_area="Portland",
        state="OR", 
        poi_type="amenity",
        poi_name="school",
        travel_time=20
    )
    ```

## 🤝 Community & Support

- **[GitHub Repository](https://github.com/mihiarc/socialmapper)** - Source code and issues
- **[PyPI Package](https://pypi.org/project/socialmapper/)** - Package downloads
- **[Documentation](https://mihiarc.github.io/socialmapper)** - This site
- **[Live Demo](https://socialmapper.streamlit.app)** - Try it online

## 🔮 Future Vision

SocialMapper is evolving toward comprehensive community analysis with plans for:

- **🌍 Environmental Integration** - Natural area accessibility
- **🚊 Multi-modal Transportation** - Transit, walking, cycling analysis  
- **📊 Real-time Data** - Dynamic community monitoring
- **🌐 Global Expansion** - International data sources

---

**Ready to explore your community?** Start with our **[Getting Started Guide](getting-started/installation.md)** or jump right in with the **[Interactive Web App](https://socialmapper.streamlit.app)**! 