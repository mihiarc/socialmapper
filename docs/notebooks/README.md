# SocialMapper Jupyter Notebooks

Interactive tutorials for Google Colab and Jupyter environments.

## Quick Start

Click any badge below to open the notebook in Google Colab:

| Notebook | Description | Open in Colab |
|----------|-------------|---------------|
| **01-Getting Started** | Installation, first analysis, demo mode | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mihiarc/socialmapper/blob/main/docs/notebooks/01-getting-started.ipynb) |
| **02-Isochrone Analysis** | Travel-time areas, routing backends | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mihiarc/socialmapper/blob/main/docs/notebooks/02-isochrone-analysis.ipynb) |
| **03-Points of Interest** | POI queries, categories, filters | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mihiarc/socialmapper/blob/main/docs/notebooks/03-points-of-interest.ipynb) |
| **04-Census Data** | Block groups, demographics, aggregation | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mihiarc/socialmapper/blob/main/docs/notebooks/04-census-data.ipynb) |
| **05-Mapping & Visualization** | Choropleth maps, export formats | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mihiarc/socialmapper/blob/main/docs/notebooks/05-mapping-visualization.ipynb) |
| **06-Complete Workflow** | Library access equity study | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mihiarc/socialmapper/blob/main/docs/notebooks/06-complete-workflow.ipynb) |
| **07-Food Desert Case Study** | Real-world food access analysis | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mihiarc/socialmapper/blob/main/docs/notebooks/07-food-desert-case-study.ipynb) |

## Learning Path

### Beginner
Start with notebooks 01-02 to learn core concepts.

### Intermediate
Notebooks 03-05 cover specific features in depth.

### Advanced
Notebooks 06-07 demonstrate complete real-world analyses.

## Running Locally

To run these notebooks locally:

```bash
# Install Jupyter and SocialMapper
pip install jupyter socialmapper[routing]

# Start Jupyter
jupyter notebook
```

## Demo Mode

All notebooks use demo mode by default, which doesn't require API keys:

```python
import os
os.environ["SOCIALMAPPER_DEMO_MODE"] = "true"
```

For production use with real data, set your API keys:

```python
os.environ["CENSUS_API_KEY"] = "your-key"
os.environ["ORS_API_KEY"] = "your-key"  # Optional
```

## Requirements

- Python 3.10+
- SocialMapper with routing extras
- Folium (for interactive maps)

All dependencies are installed automatically in the first cell of each notebook.
