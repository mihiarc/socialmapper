#!/usr/bin/env python3
"""
Utility functions for the community mapper project.
"""
from typing import Optional, Dict, List

# State name to abbreviation mapping
STATE_NAMES_TO_ABBR = {
    'Alabama': 'AL',
    'Alaska': 'AK',
    'Arizona': 'AZ',
    'Arkansas': 'AR',
    'California': 'CA',
    'Colorado': 'CO',
    'Connecticut': 'CT',
    'Delaware': 'DE',
    'Florida': 'FL',
    'Georgia': 'GA',
    'Hawaii': 'HI',
    'Idaho': 'ID',
    'Illinois': 'IL',
    'Indiana': 'IN',
    'Iowa': 'IA',
    'Kansas': 'KS',
    'Kentucky': 'KY',
    'Louisiana': 'LA',
    'Maine': 'ME',
    'Maryland': 'MD',
    'Massachusetts': 'MA',
    'Michigan': 'MI',
    'Minnesota': 'MN',
    'Mississippi': 'MS',
    'Missouri': 'MO',
    'Montana': 'MT',
    'Nebraska': 'NE',
    'Nevada': 'NV',
    'New Hampshire': 'NH',
    'New Jersey': 'NJ',
    'New Mexico': 'NM',
    'New York': 'NY',
    'North Carolina': 'NC',
    'North Dakota': 'ND',
    'Ohio': 'OH',
    'Oklahoma': 'OK',
    'Oregon': 'OR',
    'Pennsylvania': 'PA',
    'Rhode Island': 'RI',
    'South Carolina': 'SC',
    'South Dakota': 'SD',
    'Tennessee': 'TN',
    'Texas': 'TX',
    'Utah': 'UT',
    'Vermont': 'VT',
    'Virginia': 'VA',
    'Washington': 'WA',
    'West Virginia': 'WV',
    'Wisconsin': 'WI',
    'Wyoming': 'WY',
    'District of Columbia': 'DC'
}

# State abbreviation to FIPS code mapping
STATE_ABBR_TO_FIPS = {
    'AL': '01', 'AK': '02', 'AZ': '04', 'AR': '05', 'CA': '06', 'CO': '08', 'CT': '09',
    'DE': '10', 'FL': '12', 'GA': '13', 'HI': '15', 'ID': '16', 'IL': '17', 'IN': '18',
    'IA': '19', 'KS': '20', 'KY': '21', 'LA': '22', 'ME': '23', 'MD': '24', 'MA': '25',
    'MI': '26', 'MN': '27', 'MS': '28', 'MO': '29', 'MT': '30', 'NE': '31', 'NV': '32',
    'NH': '33', 'NJ': '34', 'NM': '35', 'NY': '36', 'NC': '37', 'ND': '38', 'OH': '39',
    'OK': '40', 'OR': '41', 'PA': '42', 'RI': '44', 'SC': '45', 'SD': '46', 'TN': '47',
    'TX': '48', 'UT': '49', 'VT': '50', 'VA': '51', 'WA': '53', 'WV': '54', 'WI': '55',
    'WY': '56', 'DC': '11'
}

# FIPS code to state abbreviation mapping (inverse of STATE_ABBR_TO_FIPS)
STATE_FIPS_TO_ABBR = {fips: abbr for abbr, fips in STATE_ABBR_TO_FIPS.items()}

# Mapping of common names to Census API variable codes
CENSUS_VARIABLE_MAPPING = {
    'population': 'B01003_001E',
    'total_population': 'B01003_001E',
    'median_income': 'B19013_001E',
    'median_household_income': 'B19013_001E',
    'median_age': 'B01002_001E',
    'households': 'B11001_001E',
    'housing_units': 'B25001_001E',
    'median_home_value': 'B25077_001E',
    'white_population': 'B02001_002E',
    'black_population': 'B02001_003E',
    'hispanic_population': 'B03003_003E',
    'education_bachelors_plus': 'B15003_022E'
}

# Variable-specific color schemes
VARIABLE_COLORMAPS = {
    'B01003_001E': 'viridis',      # Population - blues/greens
    'B19013_001E': 'plasma',       # Income - yellows/purples
    'B25077_001E': 'inferno',      # Home value - oranges/reds
    'B01002_001E': 'cividis',      # Age - yellows/blues
    'B02001_002E': 'Blues',        # White population
    'B02001_003E': 'Purples',      # Black population
    'B03003_003E': 'Oranges',      # Hispanic population
    'B15003_022E': 'Greens'        # Education (Bachelor's or higher)
}

def state_name_to_abbreviation(state_name: str) -> Optional[str]:
    """
    Convert a full state name to its two-letter abbreviation.
    
    Args:
        state_name: Full name of the state (e.g., "Kansas")
        
    Returns:
        Two-letter state abbreviation or None if not found
    """
    # Check for exact matches first
    if state_name in STATE_NAMES_TO_ABBR:
        return STATE_NAMES_TO_ABBR[state_name]
    
    # Try case-insensitive matching
    state_name_lower = state_name.lower()
    for name, abbr in STATE_NAMES_TO_ABBR.items():
        if name.lower() == state_name_lower:
            return abbr
    
    # No match found
    return None

def state_abbreviation_to_fips(state_abbr: str) -> Optional[str]:
    """
    Convert a state abbreviation to its FIPS code.
    
    Args:
        state_abbr: Two-letter state abbreviation (e.g., "KS")
        
    Returns:
        FIPS code or None if not found
    """
    return STATE_ABBR_TO_FIPS.get(state_abbr.upper())

def state_fips_to_abbreviation(fips: str) -> Optional[str]:
    """
    Convert a state FIPS code to its abbreviation.
    
    Args:
        fips: State FIPS code (e.g., "20")
        
    Returns:
        Two-letter state abbreviation or None if not found
    """
    return STATE_FIPS_TO_ABBR.get(fips)

def get_neighboring_states(state_abbr: str) -> List[str]:
    """
    Get all neighboring states for a given state abbreviation.
    
    Args:
        state_abbr: Two-letter state abbreviation (e.g., 'NC')
        
    Returns:
        List of neighboring state abbreviations
    """
    # Map of state adjacencies for the United States
    adjacency_map = {
        'AL': ['FL', 'GA', 'MS', 'TN'],
        'AK': [],
        'AZ': ['CA', 'CO', 'NM', 'NV', 'UT'],
        'AR': ['LA', 'MO', 'MS', 'OK', 'TN', 'TX'],
        'CA': ['AZ', 'NV', 'OR'],
        'CO': ['AZ', 'KS', 'NE', 'NM', 'OK', 'UT', 'WY'],
        'CT': ['MA', 'NY', 'RI'],
        'DE': ['MD', 'NJ', 'PA'],
        'FL': ['AL', 'GA'],
        'GA': ['AL', 'FL', 'NC', 'SC', 'TN'],
        'HI': [],
        'ID': ['MT', 'NV', 'OR', 'UT', 'WA', 'WY'],
        'IL': ['IN', 'IA', 'KY', 'MO', 'WI'],
        'IN': ['IL', 'KY', 'MI', 'OH'],
        'IA': ['IL', 'MN', 'MO', 'NE', 'SD', 'WI'],
        'KS': ['CO', 'MO', 'NE', 'OK'],
        'KY': ['IL', 'IN', 'MO', 'OH', 'TN', 'VA', 'WV'],
        'LA': ['AR', 'MS', 'TX'],
        'ME': ['NH'],
        'MD': ['DE', 'PA', 'VA', 'WV', 'DC'],
        'MA': ['CT', 'NH', 'NY', 'RI', 'VT'],
        'MI': ['IN', 'OH', 'WI'],
        'MN': ['IA', 'ND', 'SD', 'WI'],
        'MS': ['AL', 'AR', 'LA', 'TN'],
        'MO': ['AR', 'IL', 'IA', 'KS', 'KY', 'NE', 'OK', 'TN'],
        'MT': ['ID', 'ND', 'SD', 'WY'],
        'NE': ['CO', 'IA', 'KS', 'MO', 'SD', 'WY'],
        'NV': ['AZ', 'CA', 'ID', 'OR', 'UT'],
        'NH': ['ME', 'MA', 'VT'],
        'NJ': ['DE', 'NY', 'PA'],
        'NM': ['AZ', 'CO', 'OK', 'TX', 'UT'],
        'NY': ['CT', 'MA', 'NJ', 'PA', 'VT'],
        'NC': ['GA', 'SC', 'TN', 'VA'],
        'ND': ['MN', 'MT', 'SD'],
        'OH': ['IN', 'KY', 'MI', 'PA', 'WV'],
        'OK': ['AR', 'CO', 'KS', 'MO', 'NM', 'TX'],
        'OR': ['CA', 'ID', 'NV', 'WA'],
        'PA': ['DE', 'MD', 'NJ', 'NY', 'OH', 'WV'],
        'RI': ['CT', 'MA'],
        'SC': ['GA', 'NC'],
        'SD': ['IA', 'MN', 'MT', 'NE', 'ND', 'WY'],
        'TN': ['AL', 'AR', 'GA', 'KY', 'MS', 'MO', 'NC', 'VA'],
        'TX': ['AR', 'LA', 'NM', 'OK'],
        'UT': ['AZ', 'CO', 'ID', 'NM', 'NV', 'WY'],
        'VT': ['MA', 'NH', 'NY'],
        'VA': ['KY', 'MD', 'NC', 'TN', 'WV', 'DC'],
        'WA': ['ID', 'OR'],
        'WV': ['KY', 'MD', 'OH', 'PA', 'VA'],
        'WI': ['IL', 'IA', 'MI', 'MN'],
        'WY': ['CO', 'ID', 'MT', 'NE', 'SD', 'UT'],
        'DC': ['MD', 'VA']
    }
    
    return adjacency_map.get(state_abbr.upper(), [])

def census_code_to_name(census_code: str) -> str:
    """
    Convert a census variable code to its human-readable name.
    
    Args:
        census_code: Census variable code (e.g., "B01003_001E")
        
    Returns:
        Human-readable name or the original code if not found
    """
    return CENSUS_VARIABLE_MAPPING.get(census_code, census_code)

def census_name_to_code(name: str) -> str:
    """
    Convert a human-readable name to its census variable code.
    
    Args:
        name: Human-readable name (e.g., "total_population")
        
    Returns:
        Census variable code or the original name if not found
    """
    return CENSUS_VARIABLE_MAPPING.get(name, name)

def normalize_census_variable(variable: str) -> str:
    """
    Normalize a census variable to its code form, whether it's provided as a code or name.
    
    Args:
        variable: Census variable code or name
        
    Returns:
        Census variable code
    """
    # If it's already a code with format like 'BXXXXX_XXXE', return as is
    if variable.startswith('B') and '_' in variable and variable.endswith('E'):
        return variable
    
    # Check if it's a known human-readable name
    code = census_name_to_code(variable)
    if code != variable:  # Found a match
        return code
    
    # If not recognized, return as is (could be a custom variable)
    return variable 