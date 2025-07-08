# Library Access Equity Analysis Report
## Chapel Hill, NC - 15-Minute Travel Time Analysis

### Executive Summary

This analysis examines equitable access to libraries in Chapel Hill, NC by comparing three travel modes (walking, biking, and driving) within a 15-minute travel time radius. The findings reveal significant disparities in access based on transportation mode, with important implications for community equity.

### Key Findings

#### 1. Population Coverage

| Travel Mode | Population Served | Census Block Groups | Coverage Increase |
|-------------|-------------------|---------------------|-------------------|
| Walk        | 27,884           | 17                  | Baseline          |
| Bike        | 77,057           | 59                  | +176.3%           |
| Drive       | 85,137           | 66                  | +205.3%           |

**Finding**: Only 32.8% of the population served by libraries has walkable access (within 15 minutes). The remaining 67.2% (57,253 people) require a vehicle or bicycle to reach a library within 15 minutes.

#### 2. Income Disparities

| Travel Mode | Median Household Income | Average Household Income |
|-------------|-------------------------|--------------------------|
| Walk        | $52,969                | $70,493                  |
| Bike        | $82,115                | $103,019                 |
| Drive       | $97,917                | $106,564                 |

**Finding**: Areas accessible only by driving have 1.8x higher median household income compared to walk-accessible areas. This suggests that:
- Current library locations provide better walkable access to lower-income communities
- Higher-income areas are predominantly car-dependent for library access
- The income gap between walk-accessible ($52,969) and drive-only accessible areas ($117,221) is substantial

#### 3. Travel Distance Analysis

| Travel Mode | Average Distance | Median Distance | Maximum Distance |
|-------------|------------------|-----------------|------------------|
| Walk        | 1.05 km         | 1.04 km         | 2.05 km          |
| Bike        | 2.35 km         | 2.33 km         | 4.61 km          |
| Drive       | 2.50 km         | 2.42 km         | 5.79 km          |

**Finding**: Walking distances are naturally limited, while driving enables access from nearly 3x the distance, expanding the service area significantly.

### Equity Implications

#### Transportation Equity Concerns
1. **Transit Dependency**: 67.2% of library users need vehicles or bikes, creating barriers for:
   - Households without vehicles
   - Elderly residents
   - Disabled individuals
   - Low-income families

2. **Geographic Gaps**: 
   - 49 census block groups (57,253 people) are only accessible by car
   - 7 census block groups (8,080 people) cannot even access libraries by bike within 15 minutes

#### Socioeconomic Considerations
1. **Income-Based Access**: While lower-income areas have better walkable access, the overall limited walkable coverage means many low-income residents in other areas face transportation barriers

2. **Service Distribution**: Current library placement appears to prioritize walkable access for lower-income neighborhoods, but coverage remains limited

### Recommendations

1. **Expand Walkable Access**
   - Evaluate potential new library locations to increase the walkable service area
   - Target areas with high populations but limited current access

2. **Improve Transit Connections**
   - Enhance public transit routes to existing libraries
   - Consider library shuttle services during peak hours

3. **Alternative Service Models**
   - Implement mobile library services for underserved areas
   - Develop community partnership locations (schools, community centers)
   - Expand digital library services for remote access

4. **Equity-Focused Planning**
   - Prioritize new services in areas with:
     - Low vehicle ownership rates
     - High elderly/disabled populations
     - Limited current access options
   - Ensure future library locations balance both income-level coverage and transportation mode accessibility

### Data Sources and Methodology

- **Data**: US Census American Community Survey (ACS) 5-year estimates
- **Key Variables**: 
  - B01003_001E: Total population
  - B19013_001E: Median household income
  - B25077_001E: Median home value
- **Travel Time**: 15-minute isochrones calculated using OSMnx
- **Travel Speeds**: Based on OpenStreetMap road network data and realistic travel speeds for each mode

### Conclusion

This analysis reveals that while Chapel Hill's libraries currently provide good walkable access to lower-income communities, the overall walkable coverage is limited to just 32.8% of the served population. The majority of residents require vehicles or bicycles for library access, creating significant equity concerns. Addressing these gaps through strategic expansion of services, improved transit connections, and alternative service models will be essential for ensuring equitable library access for all community members.