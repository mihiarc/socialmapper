"""Data formatting utilities for the Streamlit application."""

from typing import Union


def format_census_variable(var_code: str, value: Union[float, int]) -> str:
    """Format census variables with human-readable names.
    
    Args:
        var_code: Census variable code (e.g., "B01003_001E")
        value: The numeric value to format
        
    Returns:
        Formatted string with human-readable name and value
    """
    from socialmapper.census.utils import clean_census_value, format_monetary_value
    
    variable_names = {
        "B01003_001E": "Total Population",
        "B19013_001E": "Median Household Income",
        "B25077_001E": "Median Home Value",
        "B15003_022E": "Bachelor's Degree Holders",
        "B08301_021E": "Public Transit Users",
        "B17001_002E": "Population in Poverty"
    }
    
    # Get human-readable name or use code as fallback
    name = variable_names.get(var_code, var_code)
    
    # Clean the value first
    cleaned_value = clean_census_value(value, var_code)
    if cleaned_value is None:
        return f"{name}: N/A"
    
    # Format based on variable type
    name_lower = name.lower()
    
    if "income" in name_lower or "value" in name_lower:
        # Use the monetary formatter which handles all edge cases
        formatted_value = format_monetary_value(value, var_code)
        return f"{name}: {formatted_value}"
    elif "population" in name_lower or "holders" in name_lower or "users" in name_lower:
        return f"{name}: {cleaned_value:,.0f}"
    else:
        return f"{name}: {cleaned_value}"


def format_distance(meters: float) -> str:
    """Format distance in meters to human-readable string.
    
    Args:
        meters: Distance in meters
        
    Returns:
        Formatted distance string
    """
    if meters < 1000:
        return f"{meters:.0f} m"
    else:
        return f"{meters/1000:.1f} km"


def format_time(minutes: int) -> str:
    """Format time in minutes to human-readable string.
    
    Args:
        minutes: Time in minutes
        
    Returns:
        Formatted time string
    """
    if minutes < 60:
        return f"{minutes} min"
    else:
        hours = minutes // 60
        mins = minutes % 60
        if mins == 0:
            return f"{hours} hr"
        else:
            return f"{hours} hr {mins} min"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format a decimal value as percentage.
    
    Args:
        value: Decimal value (0.0 - 1.0)
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    return f"{value * 100:.{decimals}f}%"