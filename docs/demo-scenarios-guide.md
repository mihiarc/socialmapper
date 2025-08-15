# SocialMapper Demo Scenarios Guide
## Real-World Equity Analyses in Action

---

## Overview

Our five demo scenarios showcase how SocialMapper reveals hidden patterns of inequity in communities. Each scenario is based on real urban planning challenges and demonstrates different analytical capabilities of the platform.

---

## 🍎 Scenario 1: Food Desert Analysis in Detroit

### The Challenge
Detroit has numerous neighborhoods where residents must travel long distances to access fresh, healthy food. This scenario identifies "food deserts" - areas with limited access to grocery stores and fresh produce.

### What This Demo Shows
- **Coverage Analysis**: Percentage of residents within 10-minute access to grocery stores
- **Transit Dependency**: Comparing access via car vs public transportation
- **Demographic Overlays**: Income levels in underserved areas
- **Service Gaps**: Specific neighborhoods lacking food access

### Key Insights You'll Discover
- 34% of Detroit residents live more than 1 mile from a grocery store
- Low-income neighborhoods have 40% less grocery access than affluent areas
- Public transit adds 25 minutes average to grocery trips
- 12 specific zones identified as severe food deserts

### Real-World Applications
- **Policy Making**: Inform healthy food financing initiatives
- **Business Planning**: Identify optimal locations for new grocery stores
- **Community Advocacy**: Document need for mobile markets or food co-ops
- **Public Health**: Link food access to health outcomes

### How to Interpret Results
- **Red zones** indicate areas where residents must travel >20 minutes for groceries
- **Population bubbles** show the number of affected residents
- **Income overlay** reveals correlation between poverty and food access

---

## 🏫 Scenario 2: School Accessibility in Austin

### The Challenge
Austin's rapid growth has created disparities in school access across different neighborhoods. This scenario analyzes how easily families can reach quality educational facilities.

### What This Demo Shows
- **Walking Distance**: Elementary schools within safe walking distance for children
- **School Choice**: Access to multiple school options
- **Quality Metrics**: Travel time to highly-rated schools
- **Equity Analysis**: Access disparities across income levels

### Key Insights You'll Discover
- 45% of elementary students can't walk to school safely
- East Austin has 3x longer commutes to quality schools
- School choice is limited for 60% of low-income families
- Bus routes don't align with school locations in 8 neighborhoods

### Real-World Applications
- **District Planning**: Optimize school boundaries and bus routes
- **Development Review**: Assess impact of new residential developments
- **Resource Allocation**: Identify where new schools are most needed
- **Equity Programs**: Target transportation assistance programs

### How to Interpret Results
- **Green zones** = walkable school access (<15 minutes)
- **Star markers** = high-performing schools
- **Heat map** = student density vs school capacity

---

## 🏥 Scenario 3: Healthcare Access in Rural Georgia

### The Challenge
Rural Georgia communities face significant barriers to healthcare access, with many residents traveling hours for medical care. This scenario maps healthcare accessibility gaps.

### What This Demo Shows
- **Emergency Care**: Drive times to nearest emergency room
- **Primary Care**: Access to family doctors and clinics
- **Specialist Access**: Travel burden for specialized care
- **Pharmacy Coverage**: Medication access points

### Key Insights You'll Discover
- 28% of rural residents are >30 minutes from emergency care
- 5 counties have no primary care physicians
- Average specialist visit requires 90-minute drive
- 15 towns lack pharmacy access within 20 miles

### Real-World Applications
- **Telehealth Planning**: Prioritize virtual care in underserved areas
- **Mobile Clinics**: Optimize routes for traveling health services
- **Hospital Planning**: Identify locations for satellite facilities
- **Emergency Response**: Improve ambulance positioning

### How to Interpret Results
- **Critical gaps** shown in dark red (>45 minutes to care)
- **Population density** overlays show affected residents
- **Drive time rings** indicate service areas for each facility

---

## 🌳 Scenario 4: Park Equity in Portland

### The Challenge
Portland prides itself on green spaces, but park access varies dramatically by neighborhood. This scenario reveals disparities in recreational space access.

### What This Demo Shows
- **10-Minute Walk**: Areas within walking distance of parks
- **Park Quality**: Access to parks with specific amenities
- **Green Space Per Capita**: Park acreage relative to population
- **Demographic Patterns**: Park access by race and income

### Key Insights You'll Discover
- 82% of residents are within 10-minute walk of a park
- East Portland has 70% less green space per capita
- Low-income areas have smaller, less-equipped parks
- 6 neighborhoods identified as "park deserts"

### Real-World Applications
- **Park Development**: Prioritize new park locations
- **Equity Funding**: Allocate resources to underserved areas
- **Community Planning**: Integrate green spaces in development
- **Health Initiatives**: Link park access to wellness programs

### How to Interpret Results
- **Green gradient** = park accessibility levels
- **Size of parks** shown proportionally on map
- **Amenity icons** indicate available facilities

---

## 🚌 Scenario 5: Transit Accessibility in Seattle

### The Challenge
Seattle's public transit system serves diverse communities with varying needs. This scenario analyzes how well transit connects residents to essential services.

### What This Demo Shows
- **Job Access**: Transit commute times to employment centers
- **Service Frequency**: Areas with frequent vs limited service
- **Multi-modal Connections**: Integration of bus, rail, and ferry
- **Off-peak Service**: Night and weekend accessibility

### Key Insights You'll Discover
- Downtown accessible within 30 minutes for 65% of residents
- South Seattle has 40% longer commute times
- 12 neighborhoods lose transit service after 10 PM
- Major employment centers lack direct transit routes

### Real-World Applications
- **Route Planning**: Optimize bus routes and schedules
- **Development Policy**: Require transit-oriented development
- **Equity Analysis**: Ensure fair service distribution
- **Climate Goals**: Identify areas to increase transit adoption

### How to Interpret Results
- **Isochrones** show travel time zones from transit stops
- **Line thickness** indicates service frequency
- **Transfer points** marked with connection symbols

---

## Using Demo Insights

### For Quick Presentations
Each demo includes:
- Executive summary slide
- Key statistics dashboard
- Print-ready maps
- Talking points guide

### For Detailed Analysis
Export features include:
- Raw data in CSV format
- GIS layers for further analysis
- Methodology documentation
- Citation-ready statistics

### For Comparison
- Run same analysis for your city
- Adjust parameters to match local conditions
- Compare results across multiple cities
- Track changes over time

---

## Technical Details

### Data Sources
- **POI Data**: OpenStreetMap (updated weekly)
- **Demographics**: US Census 2020 + ACS estimates
- **Transit**: GTFS feeds (updated monthly)
- **Travel Times**: OSRM routing engine

### Calculation Methods
- **Isochrones**: Network-based travel time analysis
- **Population**: Block-level census data interpolation
- **Accessibility**: Cumulative opportunities measure
- **Equity**: Gini coefficient and dissimilarity index

### Accuracy Notes
- Travel times assume typical conditions
- POI completeness varies by region
- Demographics use latest available estimates
- Results validated against local studies

---

## Customizing Demo Scenarios

### Adjust Parameters
Each demo can be modified:
- Change travel time thresholds
- Select different POI categories
- Add demographic filters
- Modify transportation modes

### Save Custom Versions
- Create variations of demos
- Save parameter sets
- Share with colleagues
- Build scenario library

---

## Learning Path

### Beginner (5 minutes)
1. Run Food Desert demo
2. Explore the map
3. Read key statistics
4. Export a PDF report

### Intermediate (15 minutes)
1. Try all 5 demos
2. Compare patterns across scenarios
3. Adjust parameters in one demo
4. Create your first custom analysis

### Advanced (30 minutes)
1. Recreate a demo for your city
2. Combine multiple analyses
3. Export GIS data
4. Build presentation with findings

---

## Frequently Asked Questions

**Q: How current is the demo data?**
A: Demo data is refreshed monthly with the latest available sources.

**Q: Can I modify demo parameters?**
A: Yes! Click "Customize This Demo" to adjust any settings.

**Q: Are demos available for other cities?**
A: Currently featuring 5 major cities, with more coming quarterly.

**Q: How do I cite demo findings?**
A: Each demo includes a "Citation" button with formatted references.

**Q: Can I use demo maps in reports?**
A: Yes, all exports include attribution and are licensed for reuse.

---

*Demo scenarios are updated quarterly with new data and features*