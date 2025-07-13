# Methodology - Kansas Food Access Vulnerability Analysis

## Overview

This document provides detailed technical documentation of the methodology used to analyze food access vulnerability in Kansas. The analysis combines geospatial analysis, demographic data, and accessibility modeling to identify food deserts and at-risk populations.

## Data Collection

### 1. Store Location Data

#### Walmart Stores
- **Source**: OpenStreetMap via Overpass API
- **Query Strategy**: 
  - Primary: Wikidata identifier (Q483551 for Walmart, Q1972120 for Sam's Club)
  - Secondary: Name-based matching for stores without Wikidata tags
- **Geographic Scope**: Kansas + 50km buffer to capture border stores
- **Data Fields**: Name, coordinates, address, store type (supercenter, neighborhood market, etc.)
- **Quality Control**: Deduplication based on name and coordinates

#### Small Grocery Stores
- **Source**: OpenStreetMap via Overpass API
- **Store Types Included**:
  - Traditional grocery stores (`shop=grocery`)
  - Convenience stores (`shop=convenience`)
  - Dollar stores (`shop=variety_store` or name matching)
  - Specialty food stores (butchers, produce stands, etc.)
  - General stores (`shop=general`)
- **Geographic Scope**: Kansas state boundaries only
- **Exclusions**: Walmart-owned stores, pharmacies without food

### 2. Demographic Data

- **Source**: US Census Bureau American Community Survey (ACS) 5-year estimates
- **Geographic Unit**: Census Block Groups
- **Variables Collected**:
  - Total population (B01003_001E)
  - Median household income (B19013_001E)
  - Poverty status (B17001_002E)
  - Vehicle availability (B08201_002E)
  - Age distribution (B01001 series for elderly populations)
  - SNAP participation (when available)

### 3. Geographic Data

- **Road Network**: OpenStreetMap via OSMnx
- **Administrative Boundaries**: US Census TIGER/Line shapefiles
- **Coordinate System**: WGS84 (EPSG:4326) for storage, Web Mercator (EPSG:3857) for analysis

## Accessibility Analysis

### 1. Travel Time Thresholds

#### Walmart Accessibility
- **Threshold**: 30-minute drive time
- **Rationale**: 
  - Industry standard for rural grocery access
  - Accounts for highway travel in rural areas
  - Represents reasonable weekly shopping trip

#### Small Grocer Accessibility
- **Threshold**: 5 kilometers (approximately 8-minute drive)
- **Rationale**:
  - Represents daily/frequent shopping distance
  - Walkable for some, short drive for others
  - Critical for populations without vehicles

### 2. Isochrone Generation

Using SocialMapper's isochrone generation capabilities:

```python
# Walmart analysis
walmart_isochrones = SocialMapperBuilder()
    .custom_pois("walmart_locations.csv")
    .travel_time(30)
    .travel_mode("drive")
    .enable_isochrone_export()
    .build()
```

**Technical Details**:
- **Routing Engine**: OSMnx with realistic turn penalties
- **Speed Assignment**:
  1. OSM maxspeed tags when available
  2. Highway-type specific speeds (e.g., rural highway: 110 km/h)
  3. Statistical imputation for unmapped segments
- **Network Simplification**: Preserves intersection nodes while removing degree-2 nodes

### 3. Census Integration

For each isochrone:
1. Identify intersecting census block groups using spatial join
2. Calculate area-weighted population for partial overlaps
3. Aggregate demographic variables
4. Apply margin of error calculations for ACS estimates

## Food Desert Classification

### Classification Categories

1. **Food Deserts**
   - Definition: No access to Walmart (>30 min) AND no small grocer (<5 km)
   - Represents true lack of food access
   - Highest priority for intervention

2. **Vulnerable Areas**
   - Definition: Small grocer access only (no Walmart within 30 min)
   - At risk if small grocer closes
   - Requires support for existing stores

3. **Well-Served Areas**
   - Definition: Walmart access within 30 minutes
   - May also have small grocer access
   - Adequate food access options

### Validation Methods

1. **Ground Truth Sampling**: Verify subset of stores exist via:
   - Google Street View
   - State business registries
   - Local knowledge

2. **Sensitivity Analysis**: Test impact of:
   - Travel time variations (±5 minutes)
   - Speed assumptions (±10%)
   - Store inclusion criteria

## Limitations and Assumptions

### Data Limitations

1. **OpenStreetMap Coverage**
   - May miss recently closed stores
   - Rural areas may have incomplete tagging
   - Relies on volunteer contributions

2. **Census Data**
   - 5-year estimates have larger margins of error in rural areas
   - Block group boundaries may not align with communities
   - Some demographic data suppressed for privacy

3. **Travel Time Assumptions**
   - Assumes car ownership for drive times
   - Does not account for traffic or weather
   - Single mode per analysis (no mixed-mode trips)

### Methodological Assumptions

1. **Store Equivalence**: All Walmart Supercenters assumed to have full grocery
2. **Travel Patterns**: Assumes shortest path routing
3. **Population Distribution**: Assumes uniform distribution within block groups
4. **Store Capacity**: Does not consider store size or inventory

## Quality Assurance

### Data Validation Steps

1. **Coordinate Validation**
   - Ensure all stores within reasonable Kansas bounds
   - Flag suspicious locations for manual review

2. **Duplicate Detection**
   - Match stores by name and proximity
   - Consolidate chain store locations

3. **Classification Verification**
   - Sample manual verification of store types
   - Cross-reference with chain store lists

### Analysis Validation

1. **Edge Case Testing**
   - State border areas
   - Urban/rural transitions
   - Islands of inaccessibility

2. **Result Reasonableness**
   - Compare to USDA Food Access Research Atlas
   - Validate against known food deserts
   - Check demographic patterns match literature

## Reproducibility

All analysis code is available in the `src/` directory. To reproduce:

1. **Environment Setup**
   ```bash
   pip install -r requirements.txt
   ```

2. **Data Collection**
   ```bash
   python src/prepare_data.py
   ```

3. **Analysis Execution**
   ```bash
   python src/analyze_access.py
   ```

4. **Report Generation**
   ```bash
   python src/generate_report.py
   ```

Results may vary slightly due to:
- OpenStreetMap data updates
- Census data releases
- Random sampling in visualization

## Computational Requirements

- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Storage**: ~2GB for caching road networks
- **Processing Time**: 
  - Data preparation: 10-15 minutes
  - Analysis: 30-45 minutes for full state
  - Report generation: 5-10 minutes

## Future Improvements

1. **Multi-modal Analysis**: Include walking and transit options
2. **Temporal Analysis**: Account for store hours and seasonal variations
3. **Economic Factors**: Include food prices and affordability
4. **Health Outcomes**: Correlate with diet-related health data
5. **Real-time Updates**: Automated monitoring of store closures/openings