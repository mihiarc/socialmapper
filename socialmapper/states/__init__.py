#!/usr/bin/env python3
"""
Centralized state identifier management for the SocialMapper project.

This module provides tools for working with US states in different formats:
- Full state names (e.g., "California")
- Two-letter state abbreviations (e.g., "CA")
- FIPS codes (e.g., "06")

It also includes functions for state validation, neighboring states, and other state-related utilities.
"""
from typing import List, Optional, Union
from enum import Enum

class StateFormat(Enum):
    """Enumeration of different state formats."""
    NAME = "name"           # Full state name (e.g., "California")
    ABBREVIATION = "abbr"   # Two-letter abbreviation (e.g., "CA")
    FIPS = "fips"           # FIPS code (e.g., "06")

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

# Generate inverse mappings
STATE_ABBR_TO_NAME = {abbr: name for name, abbr in STATE_NAMES_TO_ABBR.items()}
STATE_FIPS_TO_ABBR = {fips: abbr for abbr, fips in STATE_ABBR_TO_FIPS.items()}
STATE_FIPS_TO_NAME = {fips: STATE_ABBR_TO_NAME[abbr] for fips, abbr in STATE_FIPS_TO_ABBR.items()}

# Map of state adjacencies for the United States
STATE_NEIGHBORS = {
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

def is_fips_code(code: Union[str, int]) -> bool:
    """
    Check if a string or number is a valid state FIPS code.
    
    Args:
        code: Potential FIPS code to check
        
    Returns:
        True if it is a valid state FIPS code, False otherwise
    """
    if isinstance(code, int):
        code = str(code).zfill(2)
    elif isinstance(code, str):
        # Ensure we have a 2-digit string
        code = code.zfill(2)
    else:
        return False
    
    # Check if it's in our FIPS mapping
    return code in STATE_FIPS_TO_ABBR

def detect_state_format(state: str) -> Optional[StateFormat]:
    """
    Detect the format of a state identifier.
    
    Args:
        state: State identifier (name, abbreviation, or FIPS code)
        
    Returns:
        StateFormat enum or None if format can't be determined
    """
    if not state:
        return None
        
    # Handle string
    if isinstance(state, str):
        # Check if it's a 2-letter abbreviation
        if len(state) == 2 and state.upper() in STATE_ABBR_TO_FIPS:
            return StateFormat.ABBREVIATION
            
        # Check if it's a FIPS code
        if (len(state) == 1 or len(state) == 2) and state.isdigit() and state.zfill(2) in STATE_FIPS_TO_ABBR:
            return StateFormat.FIPS
            
        # Check if it's a state name
        if state.title() in STATE_NAMES_TO_ABBR or state.upper() in STATE_NAMES_TO_ABBR:
            return StateFormat.NAME
    
    # Handle numeric (possibly a FIPS code)
    if isinstance(state, (int, float)):
        state_str = str(int(state)).zfill(2)
        if state_str in STATE_FIPS_TO_ABBR:
            return StateFormat.FIPS
    
    return None

def normalize_state(state: Union[str, int], to_format: StateFormat = StateFormat.ABBREVIATION) -> Optional[str]:
    """
    Convert a state identifier to the requested format.
    
    Args:
        state: State identifier (name, abbreviation, or FIPS code)
        to_format: Desired output format
        
    Returns:
        Normalized state identifier in the requested format or None if invalid
    """
    if state is None:
        return None
        
    # Detect input format
    state_format = detect_state_format(state)
    if state_format is None:
        return None
    
    # Convert to string and standardize
    state_str = str(state)
    
    # If already in desired format, just standardize and return
    if state_format == to_format:
        if state_format == StateFormat.ABBREVIATION:
            return state_str.upper()
        elif state_format == StateFormat.FIPS:
            return state_str.zfill(2)
        elif state_format == StateFormat.NAME:
            # Handle case variations by converting to title case
            for name in STATE_NAMES_TO_ABBR:
                if name.lower() == state_str.lower():
                    return name
            return state_str
    
    # Convert from source format to abbreviation (intermediate step)
    abbr = None
    if state_format == StateFormat.NAME:
        # Find case-insensitive match
        for name, code in STATE_NAMES_TO_ABBR.items():
            if name.lower() == state_str.lower():
                abbr = code
                break
        if not abbr:
            return None
    elif state_format == StateFormat.FIPS:
        abbr = STATE_FIPS_TO_ABBR.get(state_str.zfill(2))
    else:  # ABBREVIATION
        abbr = state_str.upper()
    
    # Convert from abbreviation to target format
    if to_format == StateFormat.ABBREVIATION:
        return abbr
    elif to_format == StateFormat.FIPS:
        return STATE_ABBR_TO_FIPS.get(abbr)
    elif to_format == StateFormat.NAME:
        return STATE_ABBR_TO_NAME.get(abbr)

def state_name_to_abbreviation(state_name: str) -> Optional[str]:
    """
    Convert a full state name to its two-letter abbreviation.
    
    Args:
        state_name: Full name of the state (e.g., "Kansas")
        
    Returns:
        Two-letter state abbreviation or None if not found
    """
    return normalize_state(state_name, to_format=StateFormat.ABBREVIATION)

def state_abbreviation_to_name(state_abbr: str) -> Optional[str]:
    """
    Convert a state abbreviation to its full name.
    
    Args:
        state_abbr: Two-letter state abbreviation (e.g., "KS")
        
    Returns:
        Full state name or None if not found
    """
    return normalize_state(state_abbr, to_format=StateFormat.NAME)

def state_abbreviation_to_fips(state_abbr: str) -> Optional[str]:
    """
    Convert a state abbreviation to its FIPS code.
    
    Args:
        state_abbr: Two-letter state abbreviation (e.g., "KS")
        
    Returns:
        FIPS code or None if not found
    """
    return normalize_state(state_abbr, to_format=StateFormat.FIPS)

def state_fips_to_abbreviation(fips: Union[str, int]) -> Optional[str]:
    """
    Convert a state FIPS code to its abbreviation.
    
    Args:
        fips: State FIPS code (e.g., "20" or 20)
        
    Returns:
        Two-letter state abbreviation or None if not found
    """
    return normalize_state(fips, to_format=StateFormat.ABBREVIATION)

def state_fips_to_name(fips: Union[str, int]) -> Optional[str]:
    """
    Convert a state FIPS code to its full name.
    
    Args:
        fips: State FIPS code (e.g., "20" or 20)
        
    Returns:
        Full state name or None if not found
    """
    return normalize_state(fips, to_format=StateFormat.NAME)

def state_name_to_fips(state_name: str) -> Optional[str]:
    """
    Convert a state name to its FIPS code.
    
    Args:
        state_name: Full state name (e.g., "Kansas")
        
    Returns:
        FIPS code or None if not found
    """
    return normalize_state(state_name, to_format=StateFormat.FIPS)

def get_neighboring_states(state: str, output_format: StateFormat = StateFormat.ABBREVIATION) -> List[str]:
    """
    Get all neighboring states for a given state.
    
    Args:
        state: State identifier (name, abbreviation, or FIPS code)
        output_format: Format for the returned state list
        
    Returns:
        List of neighboring state identifiers in the requested format
    """
    # Convert to abbreviation first (for lookup in neighbors map)
    state_abbr = normalize_state(state, to_format=StateFormat.ABBREVIATION)
    if not state_abbr:
        return []
    
    neighbors = STATE_NEIGHBORS.get(state_abbr, [])
    
    # If the output format is already abbreviation, just return
    if output_format == StateFormat.ABBREVIATION:
        return neighbors
    
    # Otherwise convert to requested format
    return [normalize_state(abbr, to_format=output_format) for abbr in neighbors]

def is_valid_state(state: Union[str, int]) -> bool:
    """
    Check if a string is a valid state identifier in any format.
    
    Args:
        state: State identifier to validate
        
    Returns:
        True if valid state identifier, False otherwise
    """
    return detect_state_format(state) is not None

def normalize_state_list(states: List[Union[str, int]], to_format: StateFormat = StateFormat.ABBREVIATION) -> List[str]:
    """
    Normalize a list of state identifiers to a consistent format.
    
    Args:
        states: List of state identifiers (can be mixed formats)
        to_format: Desired output format
        
    Returns:
        List of normalized state identifiers in the requested format (invalid entries removed)
    """
    normalized = []
    for state in states:
        norm_state = normalize_state(state, to_format=to_format)
        if norm_state and norm_state not in normalized:
            normalized.append(norm_state)
    return normalized

def get_all_states(format: StateFormat = StateFormat.ABBREVIATION) -> List[str]:
    """
    Get a list of all US states in the requested format.
    
    Args:
        format: Format for the returned state list
        
    Returns:
        List of all state identifiers in the requested format
    """
    if format == StateFormat.ABBREVIATION:
        return sorted(STATE_ABBR_TO_FIPS.keys())
    elif format == StateFormat.FIPS:
        return sorted(STATE_FIPS_TO_ABBR.keys())
    elif format == StateFormat.NAME:
        return sorted(STATE_NAMES_TO_ABBR.keys()) 