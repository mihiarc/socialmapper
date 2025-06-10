"""Input validation utilities for secure API interactions."""

import re
import html
from typing import Union, List, Optional, Dict, Any
from urllib.parse import quote, unquote
import ipaddress


class InputValidationError(Exception):
    """Raised when input validation fails."""
    pass


def sanitize_for_api(input_str: str, max_length: int = 1000) -> str:
    """
    Sanitize user input for safe use in API calls.
    
    Args:
        input_str: The input string to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string safe for API use
        
    Raises:
        InputValidationError: If input is invalid
    """
    if not isinstance(input_str, str):
        raise InputValidationError("Input must be a string")
    
    # Remove null bytes
    input_str = input_str.replace('\x00', '')
    
    # Trim whitespace
    input_str = input_str.strip()
    
    # Check length
    if len(input_str) > max_length:
        raise InputValidationError(f"Input exceeds maximum length of {max_length}")
    
    # Remove control characters (except newline and tab)
    input_str = ''.join(char for char in input_str if ord(char) >= 32 or char in '\n\t')
    
    # HTML escape to prevent injection
    input_str = html.escape(input_str, quote=False)
    
    return input_str


def validate_address(address: str) -> str:
    """
    Validate and sanitize an address string for geocoding.
    
    Args:
        address: The address to validate
        
    Returns:
        Sanitized address string
        
    Raises:
        InputValidationError: If address is invalid
    """
    # Basic sanitization
    address = sanitize_for_api(address, max_length=500)
    
    # Check for minimum length
    if len(address) < 3:
        raise InputValidationError("Address too short")
    
    # Check for suspicious patterns that might indicate injection attempts
    suspicious_patterns = [
        r'<script',
        r'javascript:',
        r'data:text/html',
        r'vbscript:',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*=',
        r'%3Cscript',
        r'%00',
        r'\bexec\b',
        r'\beval\b',
        r'__import__',
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, address, re.IGNORECASE):
            raise InputValidationError(f"Address contains suspicious pattern")
    
    return address


def validate_coordinates(lat: Union[str, float], lon: Union[str, float]) -> tuple[float, float]:
    """
    Validate geographic coordinates.
    
    Args:
        lat: Latitude value
        lon: Longitude value
        
    Returns:
        Tuple of (latitude, longitude) as floats
        
    Raises:
        InputValidationError: If coordinates are invalid
    """
    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError):
        raise InputValidationError("Coordinates must be numeric")
    
    # Validate ranges
    if not -90 <= lat <= 90:
        raise InputValidationError(f"Invalid latitude: {lat}. Must be between -90 and 90")
    
    if not -180 <= lon <= 180:
        raise InputValidationError(f"Invalid longitude: {lon}. Must be between -180 and 180")
    
    return lat, lon


def validate_census_variable(variable: str) -> str:
    """
    Validate a census variable code.
    
    Args:
        variable: Census variable code
        
    Returns:
        Validated variable code
        
    Raises:
        InputValidationError: If variable code is invalid
    """
    # Census variable pattern: Letter followed by digits, underscore, digits, and letter
    # Example: B01003_001E
    pattern = r'^[A-Z]\d{5}_\d{3}[A-Z]$'
    
    if not re.match(pattern, variable):
        # Check if it might be a human-readable name instead
        if re.match(r'^[a-z_]+$', variable.lower()) and len(variable) < 50:
            return variable  # Allow human-readable names
        raise InputValidationError(
            f"Invalid census variable format: {variable}. "
            "Expected format like 'B01003_001E' or a descriptive name"
        )
    
    return variable


def validate_state_name(state: str) -> str:
    """
    Validate a US state name or abbreviation.
    
    Args:
        state: State name or abbreviation
        
    Returns:
        Validated state string
        
    Raises:
        InputValidationError: If state is invalid
    """
    state = sanitize_for_api(state, max_length=50)
    
    # List of valid state names and abbreviations
    valid_states = {
        'alabama', 'al', 'alaska', 'ak', 'arizona', 'az', 'arkansas', 'ar',
        'california', 'ca', 'colorado', 'co', 'connecticut', 'ct', 'delaware', 'de',
        'florida', 'fl', 'georgia', 'ga', 'hawaii', 'hi', 'idaho', 'id',
        'illinois', 'il', 'indiana', 'in', 'iowa', 'ia', 'kansas', 'ks',
        'kentucky', 'ky', 'louisiana', 'la', 'maine', 'me', 'maryland', 'md',
        'massachusetts', 'ma', 'michigan', 'mi', 'minnesota', 'mn', 'mississippi', 'ms',
        'missouri', 'mo', 'montana', 'mt', 'nebraska', 'ne', 'nevada', 'nv',
        'new hampshire', 'nh', 'new jersey', 'nj', 'new mexico', 'nm', 'new york', 'ny',
        'north carolina', 'nc', 'north dakota', 'nd', 'ohio', 'oh', 'oklahoma', 'ok',
        'oregon', 'or', 'pennsylvania', 'pa', 'rhode island', 'ri', 'south carolina', 'sc',
        'south dakota', 'sd', 'tennessee', 'tn', 'texas', 'tx', 'utah', 'ut',
        'vermont', 'vt', 'virginia', 'va', 'washington', 'wa', 'west virginia', 'wv',
        'wisconsin', 'wi', 'wyoming', 'wy', 'district of columbia', 'dc', 'puerto rico', 'pr'
    }
    
    if state.lower() not in valid_states:
        raise InputValidationError(f"Invalid state: {state}")
    
    return state


def validate_poi_type(poi_type: str, poi_name: str) -> tuple[str, str]:
    """
    Validate POI type and name for OpenStreetMap queries.
    
    Args:
        poi_type: POI type (e.g., 'amenity', 'shop')
        poi_name: POI name (e.g., 'library', 'hospital')
        
    Returns:
        Tuple of (validated_type, validated_name)
        
    Raises:
        InputValidationError: If POI parameters are invalid
    """
    # Allowed POI types in OpenStreetMap
    allowed_types = {
        'amenity', 'shop', 'tourism', 'leisure', 'healthcare',
        'education', 'public_transport', 'office', 'craft', 'emergency'
    }
    
    poi_type = poi_type.lower().strip()
    if poi_type not in allowed_types:
        raise InputValidationError(
            f"Invalid POI type: {poi_type}. "
            f"Allowed types: {', '.join(sorted(allowed_types))}"
        )
    
    # Validate POI name - alphanumeric with underscores
    if not re.match(r'^[a-z0-9_]+$', poi_name.lower()):
        raise InputValidationError(
            f"Invalid POI name: {poi_name}. "
            "Must contain only letters, numbers, and underscores"
        )
    
    return poi_type, poi_name


def validate_url(url: str) -> str:
    """
    Validate and sanitize a URL.
    
    Args:
        url: URL to validate
        
    Returns:
        Validated URL
        
    Raises:
        InputValidationError: If URL is invalid
    """
    # Basic URL pattern
    url_pattern = r'^https?://[^\s<>"{}|\\^`\[\]]+$'
    
    if not re.match(url_pattern, url):
        raise InputValidationError("Invalid URL format")
    
    # Check for localhost/private IPs
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        hostname = parsed.hostname
        
        if hostname:
            # Check for localhost
            if hostname.lower() in ['localhost', '127.0.0.1', '::1']:
                raise InputValidationError("URLs to localhost are not allowed")
            
            # Check for private IP ranges
            try:
                ip = ipaddress.ip_address(hostname)
                if ip.is_private:
                    raise InputValidationError("URLs to private IP addresses are not allowed")
            except ValueError:
                # Not an IP address, that's fine
                pass
    except Exception:
        raise InputValidationError("Could not parse URL")
    
    return url


def encode_for_url(value: str) -> str:
    """
    Safely encode a string for use in URLs.
    
    Args:
        value: String to encode
        
    Returns:
        URL-encoded string
    """
    return quote(str(value), safe='')


def validate_api_response(response_data: Any, expected_fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Validate API response data structure.
    
    Args:
        response_data: Response data from API
        expected_fields: List of expected field names
        
    Returns:
        Validated response data
        
    Raises:
        InputValidationError: If response is invalid
    """
    if not isinstance(response_data, dict):
        raise InputValidationError("API response must be a dictionary")
    
    if expected_fields:
        missing_fields = set(expected_fields) - set(response_data.keys())
        if missing_fields:
            raise InputValidationError(
                f"API response missing required fields: {', '.join(missing_fields)}"
            )
    
    return response_data


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename for safe file operations.
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Sanitized filename
        
    Raises:
        InputValidationError: If filename is invalid
    """
    # Remove any path components
    filename = filename.replace('/', '').replace('\\', '')
    
    # Remove dangerous characters
    filename = re.sub(r'[<>:"|?*\x00-\x1f]', '', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Ensure it's not empty
    if not filename:
        raise InputValidationError("Filename cannot be empty after sanitization")
    
    # Check for reserved names (Windows)
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
        'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3',
        'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    name_without_ext = filename.split('.')[0].upper()
    if name_without_ext in reserved_names:
        raise InputValidationError(f"Reserved filename: {filename}")
    
    return filename