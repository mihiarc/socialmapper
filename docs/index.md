# SocialMapper: Explore Community Connections

[![PyPI version](https://badge.fury.io/py/socialmapper.svg)](https://badge.fury.io/py/socialmapper)
[![Python Versions](https://img.shields.io/pypi/pyversions/socialmapper.svg)](https://pypi.org/project/socialmapper/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/socialmapper)](https://pepy.tech/project/socialmapper)

SocialMapper is an open-source Python toolkit that helps you understand how people connect with the important places in their community. Imagine taking a key spot like your local shopping center or school and seeing exactly what areas are within a certain travel time – whether it's a quick walk or a longer drive. SocialMapper does just that.

But it doesn't stop at travel time. SocialMapper also shows you the characteristics of the people who live within these accessible areas, like how many people live there and what the average income is. This helps you see who can easily reach vital community resources and identify any gaps in access.

Whether you're looking at bustling city neighborhoods or more spread-out rural areas, SocialMapper provides clear insights for making communities better, planning services, and ensuring everyone has good access to the places that matter.

## 🚀 Quick Start


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

### 🗺️ **Core Analysis**
- **[Address Geocoding System](ADDRESS_GEOCODING.md)** - Production-ready address lookup with multiple providers
- **Travel Time Analysis** - Generate isochrones showing reachable areas
- **Demographic Integration** - Census data analysis for community characteristics  
- **Point of Interest Discovery** - Find libraries, schools, healthcare facilities
- **Static Map Generation** - Create publication-ready visualizations

### 🛠️ **Developer Tools**
- **Python API** - Full programmatic access
- **Command Line Interface** - Easy scripting and automation
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
- **[OSMnx Integration](OSMNX_FEATURES.md)** - Advanced network analysis capabilities

### 🔧 Development
- **[Contributing Guide](development/contributing.md)** - Join the project
- **[Architecture Details](development/architecture.md)** - Technical design
- **[API Reference](api/index.md)** - Complete function documentation

## 🌟 What's New

### Latest Release Features
- **🏗️ Streamlined Architecture** - Focused on core demographic analysis
- **📍 Enhanced Geocoding** - Production-ready address system
- **⚡ Performance Improvements** - 17x faster processing with optimized neighbor system
- **🎨 Modern UI** - Rich terminal output and better visualization
- **📊 Enhanced Data Export** - Improved CSV and GeoJSON output formats

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
- **Accessibility Analysis** - Measure access to community resources
- **Social Equity** - Identify service gaps and opportunities

## 🚀 Try It Now

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

=== "Data Export"

    ```bash
    # Export results to CSV and maps
    socialmapper --poi --geocode-area "Seattle" --state "WA" \
      --poi-type "amenity" --poi-name "library" --travel-time 15 \
      --export-csv --export-maps
    ```

## 🤝 Community & Support

- **[GitHub Repository](https://github.com/mihiarc/socialmapper)** - Source code and issues
- **[PyPI Package](https://pypi.org/project/socialmapper/)** - Package downloads
- **[Documentation](https://mihiarc.github.io/socialmapper)** - This site
- **[Examples](examples/)** - Sample workflows and use cases

## 🔮 Future Vision

SocialMapper is focused on becoming the premier tool for demographic accessibility analysis with plans for:

- **🌍 Environmental Integration** - Natural area accessibility
- **🚊 Multi-modal Transportation** - Enhanced transit, walking, cycling analysis  
- **📊 Enhanced Analytics** - More sophisticated demographic analysis
- **🌐 Global Expansion** - International data sources and census systems

---

**Ready to explore your community?** Start with our **[Getting Started Guide](getting-started/installation.md)** or try the **[Command Line Interface](https://github.com/mihiarc/socialmapper#using-the-command-line-interface)**! 