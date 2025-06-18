"""Utility functions for cleaning census data values."""

from typing import Optional, Union


# Census placeholder values that indicate missing or suppressed data
CENSUS_PLACEHOLDER_VALUES = {
    -999999999,  # Most common placeholder
    -888888888,  # Data suppressed
    -666666666,  # Not applicable
    -555555555,  # Data quality issue
    -222222222,  # Sample too small
    -111111111,  # Other error
}

# Census variable prefixes that represent monetary values
MONETARY_VARIABLE_PREFIXES = {
    'B19',  # Income variables
    'B25',  # Housing variables (including home values, rent)
    'B22',  # Food stamp/SNAP benefits
    'B27',  # Health insurance (premiums)
    'B28',  # Computer and internet (costs)
}

# Reasonable bounds for different types of monetary values
MONETARY_BOUNDS = {
    'B19': (0, 500000),      # Income: $0 to $500k
    'B25077': (0, 5000000),  # Home value: $0 to $5M
    'B25': (0, 10000),       # Rent/other housing costs: $0 to $10k/month
    'B22': (0, 50000),       # SNAP benefits: $0 to $50k/year
    'B27': (0, 50000),       # Health insurance: $0 to $50k/year
    'B28': (0, 5000),        # Internet costs: $0 to $5k/month
}


def is_valid_census_value(
    value: Optional[Union[int, float]], 
    variable_code: Optional[str] = None
) -> bool:
    """
    Check if a census value is valid (not a placeholder).
    
    Args:
        value: The census data value
        variable_code: Optional census variable code (e.g., 'B19013_001E')
        
    Returns:
        True if the value is valid, False if it's a placeholder or invalid
    """
    if value is None:
        return False
        
    # Check for known placeholder values
    if value in CENSUS_PLACEHOLDER_VALUES:
        return False
        
    # Check for any large negative value
    if value < -100000:
        return False
        
    # If we have a variable code, apply variable-specific rules
    if variable_code:
        # Check if it's a monetary variable
        prefix = variable_code[:3] if len(variable_code) >= 3 else None
        
        if prefix in MONETARY_VARIABLE_PREFIXES:
            # For monetary variables, any negative is invalid
            if value < 0:
                return False
                
            # Check reasonable bounds
            if variable_code.startswith('B25077'):  # Home value specifically
                min_val, max_val = MONETARY_BOUNDS['B25077']
            elif prefix in MONETARY_BOUNDS:
                min_val, max_val = MONETARY_BOUNDS[prefix]
            else:
                min_val, max_val = 0, 10000000  # Default max $10M
                
            return min_val <= value <= max_val
    
    return True


def clean_census_value(
    value: Optional[Union[int, float]], 
    variable_code: Optional[str] = None,
    default: Optional[Union[int, float]] = None
) -> Optional[Union[int, float]]:
    """
    Clean a census value by replacing invalid values with None or a default.
    
    Args:
        value: The census data value
        variable_code: Optional census variable code
        default: Default value to use for invalid data
        
    Returns:
        Cleaned value or default/None if invalid
    """
    if is_valid_census_value(value, variable_code):
        return value
    return default


def clean_monetary_value(
    value: Optional[Union[int, float]], 
    variable_code: Optional[str] = None
) -> Optional[float]:
    """
    Clean a monetary census value (income, home value, etc.).
    
    Args:
        value: The monetary value
        variable_code: Optional census variable code
        
    Returns:
        Cleaned monetary value or None if invalid
    """
    cleaned = clean_census_value(value, variable_code)
    
    # Ensure it's a float for consistency
    if cleaned is not None:
        return float(cleaned)
    return None


def format_monetary_value(
    value: Optional[Union[int, float]], 
    variable_code: Optional[str] = None,
    prefix: str = "$",
    suffix: str = "",
    decimal_places: int = 0,
    not_available_text: str = "N/A"
) -> str:
    """
    Format a monetary value for display, handling invalid values gracefully.
    
    Args:
        value: The monetary value
        variable_code: Optional census variable code
        prefix: Prefix for the formatted value (default "$")
        suffix: Suffix for the formatted value (default "")
        decimal_places: Number of decimal places to show
        not_available_text: Text to show for invalid/missing values
        
    Returns:
        Formatted string
    """
    cleaned = clean_monetary_value(value, variable_code)
    
    if cleaned is None:
        return not_available_text
        
    if decimal_places == 0:
        formatted = f"{int(cleaned):,}"
    else:
        formatted = f"{cleaned:,.{decimal_places}f}"
        
    return f"{prefix}{formatted}{suffix}"