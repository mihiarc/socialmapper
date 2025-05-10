#!/usr/bin/env python3
"""
Utility functions for mapping functions in the SocialMapper application.
"""
import sys
import os

# Add the parent directory to sys.path to ensure imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from socialmapper.util import CENSUS_VARIABLE_MAPPING

def get_variable_label(variable: str) -> str:
    """
    Get a human-readable label for a census variable.
    
    Args:
        variable: Census variable code or human-readable name
        
    Returns:
        Human-readable label for the variable
    """
    # Check if the variable is already a human-readable name
    if variable.lower() in CENSUS_VARIABLE_MAPPING:
        # Convert snake_case to Title Case
        return variable.replace('_', ' ').title()
    
    # Map common Census API codes to human-readable labels
    labels = {
        'B01003_001E': 'Total Population',
        'B19013_001E': 'Median Household Income',
        'B25077_001E': 'Median Home Value',
        'B25064_001E': 'Median Gross Rent',
        'B15003_022E': "Bachelor's Degree",
        'B15003_023E': "Master's Degree", 
        'B15003_024E': 'Professional Degree',
        'B15003_025E': 'Doctorate Degree',
        'B02001_002E': 'White Population',
        'B02001_003E': 'Black or African American Population',
        'B02001_004E': 'American Indian and Alaska Native Population',
        'B02001_005E': 'Asian Population',
        'B03002_012E': 'Hispanic or Latino Population',
        'B23025_004E': 'Unemployment Rate',
        'B25002_003E': 'Vacant Housing Units',
        'B08301_010E': 'Public Transportation Commuters',
        'B08301_001E': 'Total Commuters',
        'B11001_001E': 'Total Households',
        'B25002_001E': 'Total Housing Units',
        'B25002_002E': 'Occupied Housing Units',
        'B25003_002E': 'Owner-Occupied Housing Units',
        'B25003_003E': 'Renter-Occupied Housing Units',
        'B08303_001E': 'Travel Time to Work',
        'B08303_013E': 'Commute >60min',
        'B19001_001E': 'Household Income Distribution',
        'B19001H_001E': 'White Household Income Distribution',
        'B19001I_001E': 'Hispanic Household Income Distribution',
        'B19001B_001E': 'Black Household Income Distribution',
        'B19083_001E': 'Gini Index',
        'B19013H_001E': 'White Median Household Income',
        'B19013B_001E': 'Black Median Household Income',
        'B19013I_001E': 'Hispanic Median Household Income',
        'B17001_002E': 'Population Below Poverty Level',
        'B25014_007E': 'Overcrowded Housing Units',
        'B25040_001E': 'Home Heating Fuel',
        'B25040_010E': 'Solar Energy Homes',
        'B08126_001E': 'Means of Transportation to Work',
        'B08126_004E': 'Public Transit Commuters',
        'B01002_001E': 'Median Age',
        'B27010_033E': 'Health Insurance Coverage',
        'B05012_003E': 'Foreign-Born Population',
        'B05012_002E': 'Native-Born Population',
        'B25058_001E': 'Median Contract Rent',
        'B25071_001E': 'Median Gross Rent as Percentage of Income',
        'B25106_001E': 'Housing Costs as Percentage of Income',
        'B25106_024E': 'Housing Costs >30% of Income', 
        'B20017_001E': 'Median Earnings for Population',
        'B20017_002E': 'Median Earnings for Males',
        'B20017_003E': 'Median Earnings for Females',
        'B15001_001E': 'Educational Attainment',
        'B16002_001E': 'Language Spoken at Home',
        'B07201_001E': 'Geographical Mobility',
        'B24011_001E': 'Occupations',
        'B25035_001E': 'Median Year Structure Built',
        'B25024_001E': 'Housing Units by Units in Structure',
        'B25040_001E': 'House Heating Fuel',
        'B11011_001E': 'Household Type',
        'B14001_001E': 'School Enrollment',
        'B18101_001E': 'Disability Status',
        'B19053_001E': 'Self-Employment Income',
        'B19055_001E': 'Social Security Income',
        'B19056_001E': 'Supplemental Security Income (SSI)',
        'B19057_001E': 'Public Assistance Income',
        'B19059_001E': 'Retirement Income',
        'B09001_001E': 'Population Under 18 Years',
        'B10063_001E': 'Multigenerational Households',
        'B11006_001E': 'Unmarried Partner Households',
        'B11008_001E': 'Married Households',
        'B12007_001E': 'Median Age at First Marriage',
        'B15001_050E': 'Female Educational Attainment',
        'B15001_009E': 'Male Educational Attainment',
        'B25081_001E': 'Mortgage Status',
        'B25087_001E': 'Mortgage Costs',
        'B25091_001E': 'Mortgage Status by Monthly Housing Costs',
        'B25094_001E': 'Selected Monthly Owner Costs',
        'B29001_001E': 'Citizen Voting Age Population',
        'B13016_001E': 'Fertility',
        'B12002_001E': 'Marital Status',
        'B22010_001E': 'Food Stamps/SNAP',
        'B28002_001E': 'Internet Access',
        'B28011_001E': 'Internet Subscription Type',
        'B25043_001E': 'Vehicles Available',
        'B25016_001E': 'Housing Units by Occupants per Room'
    }
    
    # Check for exact match
    if variable in labels:
        return labels[variable]
    
    # Check for derived variables or common aliases
    derivations = {
        'bachelors_or_higher': "Population with Bachelor's Degree or Higher",
        'poverty_rate': 'Poverty Rate',
        'homeownership_rate': 'Homeownership Rate',
        'vacant_rate': 'Vacancy Rate',
        'public_transit_rate': 'Public Transit Usage Rate',
        'education_rate': 'College Education Rate',
        'population_density': 'Population Density',
        'housing_density': 'Housing Density',
        'median_income': 'Median Household Income',
        'median_home_value': 'Median Home Value',
        'median_rent': 'Median Gross Rent',
        'unemployment': 'Unemployment Rate',
        'income_inequality': 'Income Inequality (Gini Index)',
        'poverty': 'Poverty Rate',
        'commute_time': 'Average Commute Time',
        'rent_burden': 'Rent Burden (% of Income)',
        'education_level': 'Educational Attainment',
        'diversity_index': 'Diversity Index',
        'housing_affordability': 'Housing Affordability',
        'health_insurance': 'Health Insurance Coverage',
        'broadband_access': 'Broadband Internet Access'
    }
    
    # Check if we have a derived variable mapping
    if variable.lower() in derivations:
        return derivations[variable.lower()]
    
    # Fallback: clean up the variable name if no mapping found
    clean_var = variable.replace('_', ' ').replace('-', ' ')
    words = clean_var.split()
    # Convert to title case but keep common abbreviations uppercase
    for i, word in enumerate(words):
        if word.lower() in ['id', 'api', 'url', 'fips', 'acs', 'geoid', 'usa', 'us', 'cdc', 'epa']:
            words[i] = word.upper()
        elif word.lower() == 'e' and i > 0:
            # Keep Census API format pattern (e.g., B01003_001E)
            words[i] = word.upper()
        else:
            words[i] = word.capitalize()
    
    return ' '.join(words)

def calculate_optimal_bins(data_values, max_bins=10, min_bins=5):
    """
    Calculate optimal number of bins for choropleth maps based on data distribution.
    
    Args:
        data_values: List of data values
        max_bins: Maximum number of bins to use
        min_bins: Minimum number of bins to use
        
    Returns:
        Optimal number of bins
    """
    import numpy as np
    from scipy import stats
    
    # Remove NaN values
    data_values = [x for x in data_values if x == x]  # Simple NaN check
    
    if not data_values:
        return min_bins
    
    # Check if all values are the same
    if len(set(data_values)) <= 1:
        return min_bins
    
    # Different methods to estimate bins
    n = len(data_values)
    
    # Sturges' formula
    sturges = int(np.ceil(np.log2(n)) + 1)
    
    # Freedman-Diaconis rule
    q75, q25 = np.percentile(data_values, [75, 25])
    iqr = q75 - q25
    if iqr > 0:
        h = 2 * iqr / (n ** (1/3))
        if h > 0:
            data_range = max(data_values) - min(data_values)
            fd = int(np.ceil(data_range / h))
        else:
            fd = min_bins
    else:
        fd = min_bins
    
    # Rice rule
    rice = int(np.ceil(2 * (n ** (1/3))))
    
    # Scott's normal reference rule
    if len(data_values) > 1:
        h = 3.5 * np.std(data_values) / (n ** (1/3))
        if h > 0:
            data_range = max(data_values) - min(data_values)
            scott = int(np.ceil(data_range / h))
        else:
            scott = min_bins
    else:
        scott = min_bins
    
    # Take the median of the methods
    bin_estimates = [sturges, fd, rice, scott]
    bin_estimates = [b for b in bin_estimates if b >= min_bins and b <= max_bins]
    
    if bin_estimates:
        return int(np.median(bin_estimates))
    else:
        return min(max(min_bins, sturges), max_bins)

def apply_quantile_classification(data_values, num_bins=5, scheme='quantile'):
    """
    Apply a classification scheme to data values.
    
    Args:
        data_values: List of data values
        num_bins: Number of bins to create
        scheme: Classification scheme ('quantile', 'equal_interval', 'natural_breaks', 'jenks')
        
    Returns:
        Tuple of (bins, labels) where bins are the bin edges and labels are the bin labels
    """
    import numpy as np
    from mapclassify import Quantiles, EqualInterval, NaturalBreaks
    
    # Remove NaN values
    clean_values = np.array([x for x in data_values if x == x])
    
    if len(clean_values) <= 1:
        return [min(clean_values), max(clean_values)], [f"{min(clean_values):.1f} - {max(clean_values):.1f}"]
    
    try:
        if scheme == 'equal_interval':
            classifier = EqualInterval(clean_values, k=num_bins)
        elif scheme == 'natural_breaks' or scheme == 'jenks':
            classifier = NaturalBreaks(clean_values, k=num_bins)
        else:  # Default to quantile
            classifier = Quantiles(clean_values, k=num_bins)
        
        # Get the bin edges
        bins = list(classifier.bins)
        bins.insert(0, min(clean_values))
        
        # Create labels
        labels = []
        for i in range(len(bins)-1):
            if abs(bins[i+1]) > 1000 or abs(bins[i]) > 1000:
                # Format with commas for large numbers
                labels.append(f"{int(bins[i]):,} - {int(bins[i+1]):,}")
            else:
                # Use decimal places for smaller numbers
                labels.append(f"{bins[i]:.1f} - {bins[i+1]:.1f}")
        
        return bins, labels
    except Exception as e:
        # Fallback to simple equal interval if classification fails
        print(f"Classification error: {e}. Using simple equal interval.")
        data_min = min(clean_values)
        data_max = max(clean_values)
        bins = np.linspace(data_min, data_max, num_bins + 1)
        
        labels = []
        for i in range(len(bins)-1):
            if abs(bins[i+1]) > 1000 or abs(bins[i]) > 1000:
                labels.append(f"{int(bins[i]):,} - {int(bins[i+1]):,}")
            else:
                labels.append(f"{bins[i]:.1f} - {bins[i+1]:.1f}")
        
        return bins, labels

def choose_appropriate_colormap(variable, default_colormap='GnBu'):
    """
    Choose an appropriate colormap based on the variable type.
    
    Args:
        variable: Census variable code or name
        default_colormap: Default colormap to use if no specific mapping is found
        
    Returns:
        Name of the matplotlib colormap to use
    """
    # Define mappings of variable types to appropriate colormaps
    income_vars = ['B19013', 'median_income', 'income', 'earnings', 'salary', 'wealth']
    housing_vars = ['B25077', 'home_value', 'housing', 'rent', 'B25064', 'mortgage']
    education_vars = ['B15003', 'education', 'bachelor', 'degree', 'school', 'college']
    population_vars = ['B01003', 'population', 'people', 'residents', 'persons']
    poverty_vars = ['poverty', 'B17001', 'assistance', 'snap', 'benefits']
    transportation_vars = ['B08301', 'commute', 'travel', 'transportation', 'transit']
    diversity_vars = ['B02001', 'race', 'ethnicity', 'hispanic', 'latino', 'diversity']
    age_vars = ['B01002', 'age', 'elderly', 'senior', 'youth', 'children']
    employment_vars = ['B23025', 'employment', 'unemployment', 'job', 'labor', 'workforce']
    
    # Convert variable to lowercase for matching
    var_lower = variable.lower()
    
    # Check for matches in each category
    if any(term in var_lower for term in income_vars):
        return 'Greens'
    elif any(term in var_lower for term in housing_vars):
        return 'Purples'
    elif any(term in var_lower for term in education_vars):
        return 'Blues'
    elif any(term in var_lower for term in population_vars):
        return 'YlOrRd'
    elif any(term in var_lower for term in poverty_vars):
        return 'OrRd'
    elif any(term in var_lower for term in transportation_vars):
        return 'YlGnBu'
    elif any(term in var_lower for term in diversity_vars):
        return 'viridis'
    elif any(term in var_lower for term in age_vars):
        return 'BuPu'
    elif any(term in var_lower for term in employment_vars):
        return 'RdYlGn'
    
    # Return default if no match found
    return default_colormap 