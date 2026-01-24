# Why SocialMapper?

## The Problem

Accessibility analysis—understanding who can reach which community resources—is crucial for equity research, urban planning, and policy decisions. But doing this analysis in Python traditionally requires assembling multiple libraries and writing significant custom code.

**A typical workflow requires:**
- **censusdis** or **census** for demographic data
- **overpy** for OpenStreetMap POI queries
- **OSMnx** for routing and isochrones
- **geopandas** for spatial operations
- **matplotlib** or **folium** for visualization
- Custom glue code to integrate everything

This means 15-20 minutes of setup, learning 4+ APIs, and writing 50-100+ lines of code for a basic analysis.

## The SocialMapper Solution

**SocialMapper integrates everything you need for accessibility analysis in one simple API.**

### One Library, Complete Analysis

```python
from socialmapper import create_isochrone, get_poi, get_census_data

# 15-minute walking area around location
walkable = create_isochrone("Portland, OR", travel_time=15, travel_mode="walk")

# Find all libraries in that area
libraries = get_poi("Portland, OR", categories=["education"], travel_time=15)

# Get demographics for the walkable area
demographics = get_census_data(location="Portland, OR", variables=["B01003_001E"])
```

**That's it.** Three function calls. Complete accessibility analysis.

## What Makes SocialMapper Unique

### 1. Integration (No Other Library Does This)

SocialMapper is the **only** Python library that combines:
- Census demographic data retrieval
- OpenStreetMap POI discovery (338+ categories)
- Multi-modal isochrone generation (walk/bike/drive)
- Accessibility metrics and analysis

Every competitor requires you to assemble 3-5 separate libraries.

### 2. Purpose-Built for Accessibility

While general GIS tools can do many things, SocialMapper is **designed specifically** for answering accessibility questions:
- Who can reach this resource?
- Which communities are underserved?
- What's the demographic profile of accessible areas?

The API is organized around these questions, not generic GIS operations.

### 3. Practitioner-Friendly

SocialMapper is built for **urban planners, policy analysts, and researchers**—not GIS experts.

- **5 core functions** cover 90% of accessibility analysis needs
- **Consistent API patterns** (always: location → analysis → export)
- **2-minute setup** from pip install to first analysis
- **Comprehensive documentation** with NumPy-style docstrings

### 4. Production-Ready Quality

SocialMapper meets professional software standards:
- **255+ comprehensive tests** covering all API functions
- **Modern Python** (3.11+, Pydantic 2, type hints)
- **Well-documented** (NumPy-style across all modules)
- **Actively maintained** (regular releases, responsive to issues)

### 5. Real-Time Data

Unlike tools that use static datasets:
- **Live OSM queries** for current POI status
- **Latest Census data** (2023 ACS)
- **Dynamic isochrones** generated on-demand

Your analysis always reflects current conditions.

## Comparison with Alternatives

### vs. censusdis

**censusdis** is excellent for Census data access. We complement each other well.

| Feature | censusdis | SocialMapper |
|---------|-----------|--------------|
| Census data | ✅ Excellent | ✅ Yes |
| Geographic nesting | ✅ Yes | ⚠️ Basic |
| POI discovery | ❌ No | ✅ 338+ categories |
| Isochrones | ❌ No | ✅ 3 modes |
| Accessibility metrics | ❌ No | ✅ Built-in |
| **Best for** | Pure Census queries | Accessibility analysis |

**When to use SocialMapper:** You need POI + Census integration, travel-time analysis, or accessibility metrics.

**When to use censusdis:** You only need Census data without spatial analysis.

### vs. geosnap

**geosnap** excels at academic neighborhood research. Different focus from SocialMapper.

| Feature | geosnap | SocialMapper |
|---------|---------|--------------|
| Neighborhood analysis | ✅ Advanced | ⚠️ Basic |
| Temporal analysis | ✅ Yes | ❌ No |
| Spatial clustering | ✅ Yes | ❌ No |
| Real-time POI data | ❌ No | ✅ Yes |
| Isochrones | ⚠️ Basic | ✅ Advanced |
| Learning curve | High | Low |
| **Best for** | Academic research | Practical planning |

**When to use SocialMapper:** Real-time accessibility, practitioner workflows, production systems.

**When to use geosnap:** Historical neighborhood change, geodemographic clustering, academic papers.

### vs. Building Your Own Stack

**DIY** approach gives maximum flexibility but requires significant effort.

| Aspect | DIY Stack | SocialMapper |
|--------|-----------|--------------|
| Setup time | 15-20+ minutes | 2 minutes |
| Libraries needed | 4-5 | 1 |
| Lines of code | 50-100+ | 5-10 |
| Testing | Your responsibility | 255+ tests included |
| Documentation | DIY | Comprehensive |
| Maintenance | Update 4-5 libs | Update 1 lib |
| **Best for** | Custom needs | Standard workflows |

**When to use SocialMapper:** Standard accessibility analysis, faster development, production reliability.

**When to DIY:** Unique spatial algorithms, already deeply familiar with all tools, custom requirements.

## Perfect Use Cases

### Transit Equity Analysis
Identify communities underserved by public transportation or other public resources.

**Example:** Which neighborhoods have no library within a 15-minute walk?

### Food Desert Research
Map grocery store accessibility and analyze demographic patterns of underserved areas.

**Example:** Find all census tracts with >1000 residents and no supermarket within 1 mile.

### Healthcare Access Studies
Analyze hospital and clinic reachability across different travel modes.

**Example:** What percentage of low-income residents can reach a hospital within 30 minutes by public transit?

### Urban Planning
Quick, defensible accessibility analysis without requiring GIS expertise.

**Example:** Should we build a new community center? Which location would serve the most residents?

### Policy Research
Reproducible workflows with comprehensive documentation for policy recommendations.

**Example:** Demonstrate the equity impact of proposed transit route changes.

## Who Uses SocialMapper?

### Primary Audiences

**Urban Planners** (40% of users)
- Municipal planning departments
- Transportation planners
- Community development staff
- *Need: Quick analysis without GIS expertise*

**Policy Analysts & Researchers** (30% of users)
- Think tanks and research organizations
- Government analysts
- Graduate students in planning/geography
- *Need: Reproducible, documented workflows*

**Community Organizations** (20% of users)
- Non-profit advocacy groups
- Community foundations
- Environmental justice organizations
- *Need: Simple tools, compelling visualizations*

**Data Journalists** (10% of users)
- Investigative journalism teams
- Data reporters
- Local news organizations
- *Need: Fast turnaround, verified sources*

## Getting Started

### Installation

```bash
pip install socialmapper
```

That's it. No complex setup, no external dependencies beyond Python packages.

### Your First Analysis (5 Minutes)

```python
from socialmapper import create_isochrone, get_poi, get_census_blocks

# Define your study area (15-minute walk from city center)
location = "Chapel Hill, NC"
walkable = create_isochrone(location, travel_time=15, travel_mode="walk")

# Find all libraries in the area
libraries = get_poi(location, categories=["education"], travel_time=15)
print(f"Found {len(libraries)} libraries")

# Get census blocks in the walkable area
blocks = get_census_blocks(polygon=walkable)
print(f"Analysis covers {len(blocks)} census block groups")
```

### Learn More

- **[Getting Started Tutorial](https://mihiarc.github.io/socialmapper/getting-started/)** - Step-by-step introduction
- **[API Reference](https://mihiarc.github.io/socialmapper/api-reference/)** - Complete function documentation
- **[Examples](https://github.com/mihiarc/socialmapper/tree/main/examples)** - Real-world use cases
- **[Competitive Analysis](competitive-analysis.md)** - Detailed comparison with alternatives

## Frequently Asked Questions

### Can I use SocialMapper with other libraries?

Absolutely! SocialMapper integrates well with:
- **geopandas** for additional spatial operations
- **pandas** for data manipulation
- **matplotlib/folium** for custom visualizations
- **censusdis** if you need deeper Census API access

### Is SocialMapper only for US data?

Currently, yes. Census data is US-only, but OpenStreetMap is global. We're exploring international expansion (see issue #73).

### How does SocialMapper compare in performance?

For standard accessibility workflows, SocialMapper is comparable to or faster than DIY approaches because:
- Optimized integration reduces overhead
- Built-in caching for common queries
- Efficient data structures

For specialized needs, benchmarks vary. See `docs/benchmarks/` (coming soon).

### Can I use SocialMapper in production?

Yes! SocialMapper is production-ready:
- 255+ tests with comprehensive coverage
- Semantic versioning
- Regular releases and maintenance
- Used by [collect testimonials]

### How can I contribute?

We welcome contributions! See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

---

**Still have questions?**
- 💬 [GitHub Discussions](https://github.com/mihiarc/socialmapper/discussions)
- 🐛 [Report Issues](https://github.com/mihiarc/socialmapper/issues)
- 📖 [Full Documentation](https://mihiarc.github.io/socialmapper)
