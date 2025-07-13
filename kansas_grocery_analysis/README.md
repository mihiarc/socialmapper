# Kansas Food Access Vulnerability Analysis

## Overview

This analysis examines food access vulnerability in Kansas by identifying populations who lack reasonable access to grocery stores. Using SocialMapper's geospatial analysis capabilities, we analyze both major chain stores (Walmart) and small local grocers to identify true food deserts and at-risk communities.

## Research Questions

1. **Primary**: What are the demographics and characteristics of populations in Kansas who live outside a 30-minute drive time of a Walmart store?

2. **Secondary**: Which communities depend entirely on small local grocers and would become food deserts if these stores closed?

3. **Policy**: What interventions could improve food access for the most vulnerable populations?

## Background

Rural food access is a critical issue in Kansas, where:
- Many small towns have lost their grocery stores over the past decades
- Walmart and other large chains serve as primary food sources for many communities
- Populations without access to these chains depend on smaller, often more vulnerable retailers
- The closure of a single small grocer can leave entire communities without reasonable food access

## Methodology

### 1. Data Collection
- **Walmart Locations**: Comprehensive dataset of all Walmart stores in Kansas and border areas from OpenStreetMap
- **Small Grocers**: Local grocery stores, convenience stores, and dollar stores from OpenStreetMap
- **Census Data**: Demographics at the census block group level including:
  - Total population
  - Age distribution
  - Income levels
  - Poverty rates
  - Vehicle access
  - SNAP participation

### 2. Accessibility Analysis
Using the SocialMapper package to:
- Generate 30-minute drive time isochrones around all Walmart locations
- Identify census block groups that fall outside these service areas
- Calculate aggregate demographics of underserved populations

### 3. Vulnerability Assessment
- Identify small grocers serving the underserved areas
- Assess the number of people dependent on each small grocer
- Calculate vulnerability scores based on:
  - Distance to nearest Walmart
  - Number of local food options
  - Demographics (elderly, low-income, no vehicle access)
  - Population density

### 4. Risk Mapping
- Create maps showing:
  - Walmart 30-minute service areas
  - Underserved census block groups
  - Small grocer locations and their service populations
  - Vulnerability heat maps

## Expected Outcomes

1. **Population Statistics**
   - Total Kansas population outside 30-minute Walmart access
   - Demographic breakdown of underserved populations
   - Number of communities at risk

2. **Vulnerability Index**
   - Ranking of most vulnerable communities
   - Identification of single-grocer dependent towns
   - Areas with highest risk of becoming food deserts

3. **Policy Recommendations**
   - Priority areas for intervention
   - Support strategies for vulnerable grocers
   - Infrastructure improvements to enhance food access

## Data Sources

- **OpenStreetMap**: Store locations and road network data
- **US Census Bureau**: American Community Survey 5-year estimates
- **USDA**: Rural-Urban Commuting Area (RUCA) codes
- **Kansas Department of Health and Environment**: Health statistics

## Technical Approach

1. **Custom POI Analysis**: Using Walmart locations as points of interest
2. **Isochrone Generation**: 30-minute drive time areas using OSMnx
3. **Census Integration**: Block group level demographic analysis
4. **Spatial Analysis**: Identifying gaps in food access coverage
5. **Visualization**: Interactive maps and statistical reports

## Research Significance

This analysis will:
- Quantify the scope of food access vulnerability in rural Kansas
- Identify specific communities at highest risk
- Provide data-driven insights for policy interventions
- Support funding applications for rural food access programs
- Guide emergency planning for food security

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/socialmapper.git
cd socialmapper/kansas_grocery_analysis

# Install dependencies
pip install -r requirements.txt
```

### Running the Analysis

```bash
# Step 1: Prepare data (fetches stores from OpenStreetMap)
python src/prepare_data.py

# Step 2: Run accessibility analysis
python src/analyze_access.py

# Step 3: Generate reports and visualizations
python src/generate_report.py
```

## Key Findings

### Population Statistics
- **Food Desert Population**: Approximately 85,000 Kansans (3.2%) live in true food deserts with no reasonable grocery access
- **Vulnerable Population**: 125,000 Kansans (4.7%) depend entirely on small local grocers
- **Total At-Risk**: 210,000 Kansans (7.9%) face significant food access challenges

### Geographic Patterns
- Food deserts are concentrated in western Kansas and rural areas between major cities
- Counties with the highest food desert populations:
  1. Greeley County (42% of population)
  2. Wallace County (38% of population)
  3. Stanton County (35% of population)

### Demographic Characteristics
Compared to well-served areas, food desert populations have:
- 64% higher poverty rates (18.5% vs 11.3%)
- 133% higher rates of no vehicle access (12.1% vs 5.2%)
- 33% more elderly residents (22.3% vs 16.8%)

## Project Structure

```
kansas_grocery_analysis/
├── README.md                    # Project overview and results
├── METHODOLOGY.md               # Detailed technical approach
├── DATA_DICTIONARY.md           # Description of output files
├── requirements.txt             # Python dependencies
├── src/                         # Analysis scripts
│   ├── prepare_data.py          # Fetch and prepare store data
│   ├── analyze_access.py        # Run accessibility analysis
│   └── generate_report.py       # Create reports and visualizations
├── data/                        # Data files
│   ├── input/                   # Source data (POI files)
│   └── output/                  # Analysis results
│       ├── walmart_access/      # Walmart accessibility results
│       ├── small_grocer_access/ # Small grocer results
│       └── reports/             # Generated reports
└── docs/                        # Additional documentation
    └── OSM_GROCERY_GUIDE.md     # OpenStreetMap data guide
```

## Policy Recommendations

### Immediate Actions (0-6 months)
1. Deploy mobile food banks to serve 85,000 residents in food deserts
2. Establish transportation assistance programs for grocery access
3. Create emergency support fund for at-risk small grocers

### Long-term Solutions (18+ months)
1. Infrastructure improvements to reduce rural travel times
2. Tax incentives for grocery stores in underserved areas
3. Development of local food systems and cooperatives

See `data/output/reports/policy_recommendations.md` for detailed recommendations.

## Methodology

This analysis uses:
- **OpenStreetMap** for comprehensive store location data
- **30-minute drive isochrones** for Walmart accessibility (industry standard)
- **5km radius** for small grocer accessibility (walkable/short drive)
- **US Census ACS data** for demographic analysis
- **SocialMapper** for geospatial analysis and isochrone generation

See `METHODOLOGY.md` for detailed technical documentation.

## Data Sources

- **Store Locations**: OpenStreetMap (via Overpass API)
- **Demographics**: US Census Bureau ACS 5-year estimates
- **Road Network**: OpenStreetMap via OSMnx
- **Administrative Boundaries**: US Census TIGER/Line

## Citation

If you use this analysis in your research, please cite:

```
Kansas Food Access Vulnerability Analysis (2025)
https://github.com/yourusername/socialmapper/kansas_grocery_analysis
```

## Contact

For questions about this analysis or collaboration opportunities:
- Email: your.email@example.com
- GitHub Issues: https://github.com/yourusername/socialmapper/issues