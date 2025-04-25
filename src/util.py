#!/usr/bin/env python3
"""
Utility functions for the community mapper project.
"""
from typing import Optional, Dict

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