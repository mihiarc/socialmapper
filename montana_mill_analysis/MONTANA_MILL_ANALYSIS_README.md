# Montana Timber Mill Site Analysis

This directory contains specialized analysis scripts for evaluating a potential timber mill location in Montana using the SocialMapper toolkit.

## Location Details

The proposed timber mill site is located at:
- **Coordinates**: 47.167012, -113.466881
- **Nearest Town**: Philipsburg, Montana
- **County**: Granite County

## Analysis Scripts

### Important Note on 2-Hour Analysis Performance

The 2-hour (120-minute) analysis covers a very large area in rural Montana. To improve performance:
- Map generation is automatically disabled for 120-minute analysis
- Use `visualize_montana_results.py` to create visualizations after analysis completes
- The analysis still generates all demographic data and isochrone boundaries

## Analysis Scripts

### 1. `montana_mill_quick_demo.py`
A simple demonstration of basic workforce accessibility analysis.

```bash
./montana_mill_quick_demo.py
```

**Features:**
- 30-minute drive-time analysis
- Basic demographic summary
- Quick results overview

### 2. `montana_timber_mill_analysis.py`
Comprehensive workforce analysis with multiple commute radii.

```bash
./montana_timber_mill_analysis.py
```

**Features:**
- Multi-radius analysis (15, 30, 45, 60, and 120 minutes)
- Detailed demographic profiling including 2-hour maximum range
- Workforce characteristics assessment
- Comprehensive markdown report generation
- Maps and data exports for each radius
- Analysis of regional workforce up to major population centers

### 3. `montana_timber_mill_enhanced.py`
Advanced analysis including competitive assessment and infrastructure evaluation.

```bash
./montana_timber_mill_enhanced.py
```

**Features:**
- Comparison with nearby towns (Philipsburg, Anaconda, Deer Lodge, Drummond)
- Transportation infrastructure analysis
- Existing industrial facility search
- Seasonal workforce considerations
- Competitive workforce analysis report

### 4. `montana_mill_2hour_analysis.py`
Focused analysis on the maximum 2-hour commute radius.

```bash
./montana_mill_2hour_analysis.py
```

**Features:**
- Specific focus on 120-minute maximum travel time
- Analysis of major population centers (Missoula, Butte, Helena)
- Workforce estimates and recruitment zones
- Realistic commuting pattern assessment
- Regional workforce potential evaluation

### 5. `visualize_montana_results.py`
Visualize already-generated analysis results without re-running the pipeline.

```bash
./visualize_montana_results.py
```

**Features:**
- Fast visualization of existing analysis data
- No basemap downloads (much faster for large areas)
- Multiple visualization options:
  - Simple matplotlib plots
  - Comparison plots for different travel times
  - Interactive Folium maps
  - Batch export of all visualizations
- Ideal for 2-hour analysis visualization

## Key Metrics Analyzed

### Workforce Demographics
- **Total Population**: Potential workforce pool
- **Median Income**: Economic profile of workers
- **Median Age**: Workforce age distribution
- **Education Level**: Bachelor's degree or higher for skilled positions
- **Households**: Residential density

### Accessibility Factors
- **Commute Distance**: Drive-time isochrones at multiple intervals
- **Vehicle Access**: Percentage of households without vehicles
- **Transportation Infrastructure**: Proximity to highways and rail

### Economic Indicators
- **Poverty Rate**: Economic challenges in the workforce
- **Housing Units**: Available housing for workers
- **Income Distribution**: Economic sustainability

## Output Files

The analysis generates:

1. **CSV Files**: Detailed demographic data for each travel radius
2. **Isochrone Maps**: Visual representation of accessible areas
3. **Demographic Maps**: Choropleth maps showing population density, income levels
4. **Analysis Reports**: Markdown reports with findings and recommendations

## Prerequisites

1. **Census API Key**: Required for demographic data
   ```bash
   export CENSUS_API_KEY="your-key-here"
   ```
   Get a free key at: https://api.census.gov/data/key_signup.html

2. **Dependencies**: Install SocialMapper
   ```bash
   uv pip install -e ".[dev]"
   ```

## Interpreting Results

### Workforce Availability
- **15-minute radius**: Core workforce, likely daily commuters
- **30-minute radius**: Standard commute distance for rural areas
- **45-minute radius**: Extended workforce, may require incentives
- **60-minute radius**: Regional workforce, common for specialized positions
- **120-minute radius**: Maximum analysis range, captures major cities:
  - Missoula: University town with skilled workforce
  - Butte: Mining heritage and Montana Tech engineering programs
  - Helena: State capital with government workers

### Key Considerations
1. **Rural Context**: Montana's low population density means larger commute radii
2. **2-Hour Analysis**: The maximum 120-minute range helps identify:
   - Total regional workforce potential
   - Specialized skill availability in larger cities
   - Relocation candidates for key positions
3. **Seasonal Variation**: Timber operations peak May-October
4. **Competition**: Limited industrial employers reduce workforce competition
5. **Infrastructure**: Access to I-90 corridor crucial for logistics

## Recommendations

Based on the analysis framework, consider:

1. **Workforce Development**
   - Partner with Montana Tech for skilled worker training
   - Develop apprenticeship programs with local high schools

2. **Transportation**
   - Consider employee shuttle services from larger towns
   - Evaluate road improvement needs for truck traffic

3. **Housing**
   - Assess seasonal worker housing needs
   - Consider workforce housing development partnerships

4. **Community Integration**
   - Engage with Philipsburg and surrounding communities
   - Develop local hiring preferences

## Next Steps

1. Run the basic demo to verify setup
2. Execute comprehensive analysis for detailed workforce data
3. Use enhanced analysis for competitive assessment
4. Review generated reports and maps
5. Share findings with stakeholders

## Support

For questions about:
- **SocialMapper**: See main project documentation
- **Analysis Scripts**: Review code comments and docstrings
- **Census Data**: Consult docs/reference/census-variables.md