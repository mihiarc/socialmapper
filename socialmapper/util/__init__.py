#!/usr/bin/env python3
"""
Utility functions for the socialmapper project.
"""

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

# Add north arrow utility function
def add_north_arrow(ax, position='upper right', scale=0.1):
    """
    Add a north arrow to a map.
    
    Args:
        ax: Matplotlib axis to add arrow to
        position: Position on the plot ('upper right', 'upper left', 'lower right', 'lower left')
        scale: Size of the arrow relative to the axis
        
    Returns:
        The arrow annotation object
    """
    # Get axis limits
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    
    # Calculate position
    if position == 'upper right':
        x = xlim[1] - (xlim[1] - xlim[0]) * 0.05
        y = ylim[1] - (ylim[1] - ylim[0]) * 0.05
    elif position == 'upper left':
        x = xlim[0] + (xlim[1] - xlim[0]) * 0.05
        y = ylim[1] - (ylim[1] - ylim[0]) * 0.05
    elif position == 'lower right':
        x = xlim[1] - (xlim[1] - xlim[0]) * 0.05
        y = ylim[0] + (ylim[1] - ylim[0]) * 0.05
    else:  # lower left
        x = xlim[0] + (xlim[1] - xlim[0]) * 0.05
        y = ylim[0] + (ylim[1] - ylim[0]) * 0.05
    
    # Scale the offset based on the scale parameter
    arrow_height = (ylim[1] - ylim[0]) * scale
    
    # Add the arrow
    arrow = ax.annotate('N', xy=(x, y), 
                       xytext=(x, y - arrow_height),
                       arrowprops=dict(facecolor='black', width=3, headwidth=10),
                       ha='center', va='center', fontsize=10, fontweight='bold')
    
    return arrow 