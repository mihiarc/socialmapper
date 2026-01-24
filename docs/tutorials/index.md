# SocialMapper Tutorials

Welcome to the SocialMapper tutorial series. These tutorials will guide you from basic concepts to advanced real-world applications.

## Learning Path

### Beginner

| Tutorial | Description | Time |
|----------|-------------|------|
| [Getting Started](01-getting-started.md) | Installation, first analysis, demo mode | 15 min |
| [Isochrone Analysis](02-isochrone-analysis.md) | Travel-time areas and routing backends | 20 min |

### Intermediate

| Tutorial | Description | Time |
|----------|-------------|------|
| [Points of Interest](03-points-of-interest.md) | Finding and analyzing POIs | 20 min |
| [Census Data](04-census-data.md) | Demographics and population data | 25 min |
| [Mapping & Visualization](05-mapping-visualization.md) | Creating choropleth maps | 20 min |

### Advanced

| Tutorial | Description | Time |
|----------|-------------|------|
| [Complete Workflow](06-complete-workflow.md) | End-to-end library access study | 30 min |
| [Food Desert Case Study](07-food-desert-case-study.md) | Real-world equity analysis | 35 min |

## Quick Reference

### Core Functions

```python
from socialmapper import (
    create_isochrone,    # Travel-time polygons
    get_poi,             # Points of interest
    get_census_blocks,   # Census geography
    get_census_data,     # Demographics
    create_map           # Visualization
)
```

### Common Workflows

**Accessibility Analysis**
```python
# What's reachable in 15 minutes?
isochrone = create_isochrone("Seattle, WA", travel_time=15)
pois = get_poi("Seattle, WA", categories=["healthcare"], travel_time=15)
```

**Demographic Analysis**
```python
# Who lives in this area?
blocks = get_census_blocks(polygon=isochrone)
census = get_census_data([b['geoid'] for b in blocks], variables=["population"])
```

**Visualization**
```python
# Create a map
result = create_map(data=blocks, column="population", save_path="map.png")
```

## Prerequisites

Before starting, ensure you have:

1. **Python 3.10+** installed
2. **SocialMapper** installed:
   ```bash
   pip install socialmapper
   ```
3. **API Keys** (for production use):
   - Census API key: https://api.census.gov/data/key_signup.html
   - ORS API key (optional): https://openrouteservice.org/dev/

## Tutorial Features

Each tutorial includes:

- **Concept explanations** - Understand what you're doing and why
- **Runnable code examples** - Copy and paste directly
- **Practical applications** - Real-world use cases
- **Best practices** - Tips for production use
- **Next steps** - Links to related tutorials

## Demo Mode

All tutorials work in demo mode without API keys:

```python
import os
os.environ["SOCIALMAPPER_DEMO_MODE"] = "true"

from socialmapper import create_isochrone
iso = create_isochrone("Demo City", travel_time=15)  # Works instantly!
```

## Getting Help

- **API Reference**: See the [API Documentation](../api-reference.md)
- **GitHub Issues**: Report bugs or request features
- **Examples**: Check the [examples directory](../../examples/)

## Start Learning

Ready to begin? Start with [Getting Started](01-getting-started.md) to set up your environment and run your first analysis.
