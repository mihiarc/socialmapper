# SocialMapper Examples

This directory contains demonstrations, case studies, and example datasets for SocialMapper.

## 📁 Directory Structure

```
examples/
├── README.md                      # This file
├── demos/                         # Interactive demonstrations
│   ├── rich_ui_demo.py           # Rich terminal UI features
│   ├── plotly_integration_demo.py # Plotly/Mapbox mapping demo
│   ├── osmnx_features_demo.py     # OSMnx 2.0+ capabilities
│   └── fuquay_varina_case_study.py # Complete real-world case study
├── data/                          # Example datasets
│   ├── trail_heads.csv           # Trail locations dataset (2,661 POIs)
│   ├── custom_coordinates.csv    # Sample coordinate format
│   └── streamlit_example.csv     # Streamlit app example data
└── example_output/               # Sample output files
    └── maps/                     # Example generated maps
```

## 🚀 Getting Started

### Quick Demo Run
```bash
# Run the comprehensive case study
python examples/demos/fuquay_varina_case_study.py

# Try the Rich UI features
python examples/demos/rich_ui_demo.py

# Explore OSMnx 2.0+ capabilities  
python examples/demos/osmnx_features_demo.py
```

### Plotly Integration Demo (Streamlit)
```bash
# Run the interactive Plotly demo
streamlit run examples/demos/plotly_integration_demo.py
```

## 📋 Demo Descriptions

### 🏛️ Fuquay-Varina Case Study (`fuquay_varina_case_study.py`)
**Complete real-world demonstration** showing SocialMapper's full capabilities:

- **Location**: Fuquay-Varina Library, NC
- **Features**: Neighbor system optimization, geographic analysis, performance benchmarking
- **Use Case**: Community resource accessibility analysis
- **Duration**: ~2-3 minutes

**What you'll see**:
- Parquet-based neighbor system performance
- Geographic context analysis (counties and states)
- Real-world workflow demonstration
- Performance metrics and optimization benefits

### 🎨 Rich UI Demo (`rich_ui_demo.py`)
**Beautiful terminal interface showcase** featuring SocialMapper's enhanced UX:

- **Features**: Progress bars, tables, status indicators, formatted output
- **Interactive**: Real-time progress tracking simulation
- **Visual**: Color-coded panels and professional formatting
- **Duration**: ~1-2 minutes

**What you'll see**:
- Beautiful banners and branding
- Progress bars with performance metrics
- Formatted data tables (POIs, census variables)
- Status spinners and completion summaries

### 🗺️ Plotly Integration Demo (`plotly_integration_demo.py`)
**Interactive mapping demonstration** comparing Plotly vs Folium approaches:

- **Type**: Streamlit web application
- **Features**: Interactive maps, event handling, performance comparison
- **Data**: Sample census and POI data
- **Duration**: Interactive exploration

**What you'll see**:
- Modern Plotly Scattermap implementation
- Interactive click/hover events
- Performance benchmarks
- Real SocialMapper integration examples

### 🌐 OSMnx Features Demo (`osmnx_features_demo.py`)
**Advanced geospatial capabilities** showcasing OSMnx 2.0+ features:

- **Location**: Corvallis, Oregon
- **Features**: Network analysis, geometry handling, routing algorithms
- **Technical**: Performance benchmarks, centrality calculations
- **Duration**: ~3-5 minutes

**What you'll see**:
- Faster graph creation and processing
- Building footprints and POI downloads
- Network analysis (betweenness, closeness centrality)
- Advanced routing and spatial analysis

## 📊 Example Datasets

### `trail_heads.csv` (156KB, 2,661 records)
**Large-scale POI dataset** for performance testing and real-world scenarios:
- **Content**: Trail locations across multiple states
- **Use**: Performance benchmarking, batch processing demos
- **Format**: Standard CSV with lat/lon coordinates

### `custom_coordinates.csv` (83B, 2 records)  
**Minimal example** showing custom coordinate input format:
- **Content**: Sample POI locations for testing
- **Use**: Quick testing and format demonstration
- **Format**: Simple CSV with name, lat, lon

### `streamlit_example.csv` (275B, 6 records)
**Streamlit demo data** for web application examples:
- **Content**: Small dataset for web interface testing
- **Use**: Streamlit app demonstrations
- **Format**: CSV optimized for web display

## 🎯 Usage Patterns

### Basic SocialMapper Workflow
```python
from socialmapper import run_socialmapper

# Using example data
results = run_socialmapper(
    custom_coords_path="examples/data/trail_heads.csv",
    travel_time=15,
    census_variables=['total_population', 'median_income'],
    export_maps=True
)
```

### Interactive Demo Exploration
```python
# Run all demos sequentially
import subprocess

demos = [
    "examples/demos/fuquay_varina_case_study.py",
    "examples/demos/rich_ui_demo.py", 
    "examples/demos/osmnx_features_demo.py"
]

for demo in demos:
    print(f"Running {demo}...")
    subprocess.run(["python", demo])
```

### Performance Testing with Examples
```python
# Use example data for performance testing
from tests.performance.benchmark_quick import run_performance_test

# Test with trail_heads dataset
run_performance_test("examples/data/trail_heads.csv")
```

## 🧪 Integration with Tests

The examples work seamlessly with the testing infrastructure:

```bash
# Run performance tests using example data
python tests/performance/benchmark_comprehensive.py
python tests/performance/benchmark_quick.py

# Both tests can use examples/data/trail_heads.csv
```

## 🔧 Customizing Examples

### Adding Your Own Data
1. **Format**: Follow the CSV structure in `custom_coordinates.csv`
2. **Required columns**: name, latitude, longitude
3. **Optional columns**: state, type, address

### Running Custom Analysis
```python
# Create your own demo based on the examples
from socialmapper import run_socialmapper

results = run_socialmapper(
    custom_coords_path="your_data.csv",
    travel_time=20,  # Adjust as needed
    census_variables=['total_population'],
    export_csv=True,
    export_maps=True
)
```

## 📚 Learning Path

**Recommended order for exploring SocialMapper**:

1. **Start**: `fuquay_varina_case_study.py` - Complete overview
2. **UI**: `rich_ui_demo.py` - Beautiful terminal experience  
3. **Mapping**: `plotly_integration_demo.py` - Interactive visualization
4. **Advanced**: `osmnx_features_demo.py` - Technical capabilities
5. **Testing**: `tests/performance/` - Performance validation

## 🆘 Troubleshooting

### Common Issues
- **Import errors**: Ensure SocialMapper is installed (`pip install socialmapper`)
- **Missing data**: Check that CSV files exist in `examples/data/`
- **Streamlit issues**: Install streamlit (`pip install streamlit`)
- **Performance**: Use smaller datasets for initial testing

### Getting Help
- **Documentation**: Check `docs/` directory
- **Issues**: Create GitHub issues for bugs
- **Examples**: All demos include error handling and help text

---

**Happy mapping!** 🗺️✨

Explore these examples to understand SocialMapper's capabilities and find patterns for your own community analysis projects. 