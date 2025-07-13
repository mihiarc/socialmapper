# Census Variable Reference Guide

This document maps U.S. Census Bureau variable codes to their human-readable descriptions for the Kansas Grocery Access Analysis.

## Variables Used in Analysis

### Basic Demographics
- **B01003_001E**: Total Population
  - The total count of all people in the geographic area

### Economic Indicators
- **B19013_001E**: Median Household Income
  - The median income for all households in the past 12 months (in inflation-adjusted dollars)
  
- **B17001_002E**: Population Below Poverty Level
  - Total population for whom poverty status is determined as below poverty level

### Transportation Access
- **B08201_002E**: Households Without Vehicle Available
  - Number of households with no vehicle available for use

### Elderly Population (Age 65+)
Used to identify areas with high concentrations of elderly residents who may face mobility challenges:

#### Male Population by Age
- **B01001_020E**: Males Age 65-66 years
- **B01001_021E**: Males Age 67-69 years
- **B01001_022E**: Males Age 70-74 years
- **B01001_023E**: Males Age 75-79 years
- **B01001_024E**: Males Age 80-84 years
- **B01001_025E**: Males Age 85 years and over

#### Female Population by Age
- **B01001_044E**: Females Age 65-66 years
- **B01001_045E**: Females Age 67-69 years
- **B01001_046E**: Females Age 70-74 years
- **B01001_047E**: Females Age 75-79 years
- **B01001_048E**: Females Age 80-84 years
- **B01001_049E**: Females Age 85 years and over

## Why These Variables Matter

### Food Desert Analysis
- **Income** (B19013_001E, B17001_002E): Low-income areas are more vulnerable to food access issues
- **Vehicle Access** (B08201_002E): Households without vehicles depend on walkable/transit-accessible groceries
- **Elderly Population** (B01001_020E-025E, B01001_044E-049E): Elderly residents often have limited mobility and fixed incomes

### Kansas-Specific Considerations
In rural Kansas, elderly population concentration is often more predictive of food access vulnerability than income alone, as:
- Rural elderly may have limited driving ability
- Public transit is minimal in rural areas
- Small town grocery stores serve high percentages of elderly customers
- Store closures disproportionately impact elderly residents

## Data Source
All variables come from the American Community Survey (ACS) 5-Year Estimates, which provide the most reliable data for small geographic areas like census block groups.