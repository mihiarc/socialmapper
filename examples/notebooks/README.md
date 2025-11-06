# SocialMapper Interactive Notebooks 📓

Welcome to the SocialMapper interactive notebook collection! These Jupyter notebooks provide hands-on tutorials, workshop materials, and research templates for accessibility analysis and demographic mapping.

## 🚀 Quick Start

### Running in the Cloud (No Installation Required!)

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mihiarc/socialmapper/blob/main/examples/notebooks/01_getting_started.ipynb)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/mihiarc/socialmapper/main?labpath=examples%2Fnotebooks)

Click the badges above to run notebooks directly in your browser!

### Local Installation

```bash
# Install SocialMapper and Jupyter
pip install socialmapper jupyter

# Navigate to notebooks directory
cd examples/notebooks

# Start Jupyter
jupyter notebook
```

## 📚 Notebook Collection

### Core Tutorials (Completed) ✅

| Notebook | Description | Time | Level | Status |
|----------|-------------|------|-------|--------|
| [01_getting_started.ipynb](01_getting_started.ipynb) | Create your first isochrone, find POIs, analyze demographics | 30 min | Beginner | ✅ Complete |
| [02_travel_modes.ipynb](02_travel_modes.ipynb) | Compare walking, biking, and driving accessibility | 25 min | Beginner | ✅ Complete |
| [workshop_quickstart.ipynb](workshop_quickstart.ipynb) | 30-minute condensed workshop version | 30 min | All | ✅ Complete |
| [research_template.ipynb](research_template.ipynb) | Complete research workflow template | 60 min | Advanced | ✅ Complete |

### Additional Tutorials (In Development) 🚧

| Notebook | Description | Time | Level | Status |
|----------|-------------|------|-------|--------|
| 03_census_demographics.ipynb | Deep dive into US Census data | 30 min | Intermediate | 🚧 Coming Soon |
| 04_custom_pois.ipynb | Working with custom POI categories | 25 min | Intermediate | 🚧 Coming Soon |
| 05_combining_analysis.ipynb | Multi-factor accessibility analysis | 35 min | Intermediate | 🚧 Coming Soon |
| 06_multi_location.ipynb | Comparing multiple locations | 30 min | Intermediate | 🚧 Coming Soon |
| 07_zipcode_analysis.ipynb | ZIP code-based demographic analysis | 25 min | Intermediate | 🚧 Coming Soon |
| 08_address_geocoding.ipynb | Working with street addresses | 20 min | Beginner | 🚧 Coming Soon |

### Advanced Tutorials (Planned) 📋

| Notebook | Description | Time | Level | Status |
|----------|-------------|------|-------|--------|
| 09_equity_analysis.ipynb | Transportation equity assessment | 40 min | Advanced | 📋 Planned |
| 10_network_analysis.ipynb | Advanced network accessibility | 45 min | Advanced | 📋 Planned |
| 11_temporal_patterns.ipynb | Time-of-day accessibility changes | 35 min | Advanced | 📋 Planned |
| 12_custom_metrics.ipynb | Creating custom accessibility metrics | 40 min | Advanced | 📋 Planned |
| 13_report_generation.ipynb | Automated report generation | 30 min | Advanced | 📋 Planned |

## 🎯 Learning Paths

### Path 1: Beginner Track (2 hours)
1. **Start Here** → `01_getting_started.ipynb` (30 min)
2. **Explore Modes** → `02_travel_modes.ipynb` (25 min)
3. **Quick Practice** → `workshop_quickstart.ipynb` (30 min)
4. **Next Steps** → Try different locations and parameters (30 min)

### Path 2: Research Track (3 hours)
1. **Fundamentals** → `01_getting_started.ipynb` (30 min)
2. **Mode Analysis** → `02_travel_modes.ipynb` (25 min)
3. **Demographics** → `03_census_demographics.ipynb` (30 min)
4. **Research** → `research_template.ipynb` (60 min)
5. **Your Analysis** → Customize template for your research (45 min)

### Path 3: Workshop Leader (1.5 hours)
1. **Review** → `workshop_quickstart.ipynb` (15 min)
2. **Practice** → Run through with test data (30 min)
3. **Customize** → Adapt for your audience (30 min)
4. **Deliver** → 30-minute live workshop

## 🌟 Features

### Interactive Elements
- 🗺️ **Interactive Maps**: Folium-based maps you can zoom and explore
- 📊 **Live Visualizations**: Matplotlib and Seaborn charts that update with your data
- 🎮 **Hands-On Exercises**: Code cells for you to modify and experiment
- 💡 **Solutions Included**: Hidden solutions you can reveal when stuck

### Educational Design
- **Progressive Complexity**: Start simple, build up gradually
- **Real-World Examples**: Actual city data and practical scenarios
- **Checkpoint Questions**: Test your understanding as you go
- **Visual Learning**: Maps, charts, and diagrams throughout

### Research Features
- **Reproducible Workflows**: All parameters documented
- **Statistical Analysis**: Built-in statistical tests
- **Export Options**: Save results in multiple formats
- **Citation Support**: Proper attribution and references

## 💻 Requirements

### Minimum Requirements
- Python 3.11+
- SocialMapper installed
- Jupyter Notebook or JupyterLab

### Recommended Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install socialmapper[notebooks]

# Install additional visualization libraries
pip install folium matplotlib seaborn plotly
```

### API Keys (Optional but Recommended)
- **Census API Key**: Free from [census.gov](https://api.census.gov/data/key_signup.html)
- Add to `.env` file:
  ```
  CENSUS_API_KEY=your_key_here
  ```

## 🚀 Tips for Success

### For Learners
1. **Run cells in order** - Each cell builds on previous ones
2. **Experiment freely** - You can't break anything!
3. **Read the markdown** - Context and explanations are important
4. **Try the exercises** - Practice solidifies learning
5. **Use your own data** - Try your city/neighborhood

### For Instructors
1. **Test beforehand** - Run through the notebook before class
2. **Have backup data** - In case APIs are slow
3. **Encourage questions** - Pause for discussion
4. **Share screens** - Show both code and output
5. **Provide support** - Help with debugging

### For Researchers
1. **Document everything** - Parameters, versions, dates
2. **Set random seeds** - For reproducibility
3. **Save intermediates** - Don't rely on memory
4. **Version control** - Track your modifications
5. **Cite properly** - Credit data sources and tools

## 🐛 Troubleshooting

### Common Issues

**Import Errors**
```python
# If socialmapper isn't found:
!pip install socialmapper  # Run in notebook
```

**API Timeouts**
```python
# Reduce the area or number of requests
travel_time = 10  # Smaller area
limit = 20  # Fewer POIs
```

**Memory Issues**
```python
# Sample the data
sample_size = min(50, len(blocks))  # Limit census blocks
```

**Visualization Problems**
```python
# Ensure all required libraries
!pip install folium matplotlib seaborn
```

## 📊 Example Outputs

### What You'll Create

1. **Interactive Maps**
   - Multi-layer isochrones
   - POI markers
   - Choropleth demographics

2. **Statistical Analysis**
   - Coverage comparisons
   - Equity scores
   - Correlation analysis

3. **Publication Graphics**
   - High-resolution charts
   - Formatted tables
   - Export-ready figures

## 🤝 Contributing

We welcome contributions! To add a notebook:

1. Follow the existing format and style
2. Include clear learning objectives
3. Add exercises with solutions
4. Test with fresh kernel
5. Submit PR with description

## 📄 License

These notebooks are part of SocialMapper and covered under the same license. Feel free to use, modify, and share for educational purposes.

## 🙋 Getting Help

- **Issues**: [GitHub Issues](https://github.com/mihiarc/socialmapper/issues)
- **Discussions**: [GitHub Discussions](https://github.com/mihiarc/socialmapper/discussions)
- **Documentation**: [Main README](../../README.md)

## 📈 Progress Tracking

Track your learning progress:

- [ ] Completed Tutorial 01
- [ ] Completed Tutorial 02
- [ ] Ran workshop notebook
- [ ] Customized research template
- [ ] Analyzed my own city
- [ ] Created custom visualizations
- [ ] Shared results

---

**Happy Learning!** 🎓

*Last updated: November 2024*