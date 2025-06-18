"""Input validation utilities for SocialMapper.

This module provides functions for validating user inputs, API responses,
and data integrity throughout the SocialMapper system.
"""

import html
import re
from typing import Any
from urllib.parse import quote, urlparse

from ..constants import (
    MAX_LATITUDE,
    MAX_LONGITUDE,
    MAX_VARIABLE_NAME_LENGTH,
    MIN_ADDRESS_LENGTH,
    MIN_ASCII_PRINTABLE,
    MIN_LATITUDE,
    MIN_LONGITUDE,
)


class InputValidationError(Exception):
    """Exception raised when input validation fails."""


def sanitize_string_input(input_str: str, max_length: int = 1000) -> str:
    """Sanitize string input to prevent injection attacks and clean data.

    Args:
        input_str: The input string to sanitize
        max_length: Maximum allowed length for the string

    Returns:
        Sanitized string

    Raises:
        InputValidationError: If input is invalid
    """
    if not isinstance(input_str, str):
        raise InputValidationError("Input must be a string")

    if len(input_str) > max_length:
        raise InputValidationError(f"Input too long (max {max_length} characters)")

    # Remove control characters (except newline and tab)
    input_str = "".join(char for char in input_str if ord(char) >= MIN_ASCII_PRINTABLE or char in "\n\t")

    # HTML escape to prevent injection
    return html.escape(input_str.strip())


def validate_address(address: str) -> str:
    """Validate and sanitize an address string.

    Args:
        address: The address string to validate

    Returns:
        Validated and sanitized address

    Raises:
        InputValidationError: If address is invalid
    """
    if not isinstance(address, str):
        raise InputValidationError("Address must be a string")

    address = address.strip()

    if not address:
        raise InputValidationError("Address cannot be empty")

    # Check for minimum length
    if len(address) < MIN_ADDRESS_LENGTH:
        raise InputValidationError("Address too short")

    # Basic suspicious pattern checks
    suspicious_patterns = [
        r"<script",
        r"javascript:",
        r"data:",
        r"vbscript:",
        r"\x00",  # null bytes
        r"[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]",  # control characters
    ]

    for pattern in suspicious_patterns:
        if re.search(pattern, address, re.IGNORECASE):
            raise InputValidationError("Address contains invalid characters")

    return sanitize_string_input(address)


def validate_coordinates(lat: str | int | float, lon: str | int | float) -> tuple[float, float]:
    """Validate coordinate values.

    Args:
        lat: Latitude value
        lon: Longitude value

    Returns:
        Tuple of validated (latitude, longitude) as floats

    Raises:
        InputValidationError: If coordinates are invalid
    """
    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError) as e:
        raise InputValidationError(f"Coordinates must be numeric: {e}") from None

    # Validate ranges
    if not MIN_LATITUDE <= lat <= MAX_LATITUDE:
        raise InputValidationError(f"Invalid latitude: {lat}. Must be between -90 and 90")

    if not MIN_LONGITUDE <= lon <= MAX_LONGITUDE:
        raise InputValidationError(f"Invalid longitude: {lon}. Must be between -180 and 180")

    return lat, lon


def validate_census_variable(variable: str) -> str:
    """Validate a Census variable code.

    Args:
        variable: Census variable code to validate

    Returns:
        Validated variable code

    Raises:
        InputValidationError: If variable code is invalid
    """
    if not isinstance(variable, str):
        raise InputValidationError("Census variable must be a string")

    variable = variable.strip()

    if not variable:
        raise InputValidationError("Census variable cannot be empty")

    # Standard Census variable pattern (e.g., B01003_001E)
    pattern = r"^[A-Z]\d{5}_\d{3}[A-Z]$"

    if not re.match(pattern, variable):
        # Check if it might be a human-readable name instead
        if re.match(r"^[a-z_]+$", variable.lower()) and len(variable) < MAX_VARIABLE_NAME_LENGTH:
            return variable  # Allow human-readable names
        raise InputValidationError(
            f"Invalid Census variable format: {variable}. "
            "Expected format like 'B01003_001E' or human-readable name"
        )

    return variable


def validate_poi_type(poi_type: str) -> str:
    """Validate POI type string.

    Args:
        poi_type: POI type to validate

    Returns:
        Validated POI type

    Raises:
        InputValidationError: If POI type is invalid
    """
    if not isinstance(poi_type, str):
        raise InputValidationError("POI type must be a string")

    poi_type = poi_type.strip().lower()

    if not poi_type:
        raise InputValidationError("POI type cannot be empty")

    # Allow alphanumeric, underscore, hyphen, and space
    if not re.match(r"^[a-z0-9_\-\s]+$", poi_type):
        raise InputValidationError("POI type contains invalid characters")

    return poi_type


def validate_api_response(response_data: Any, expected_fields: list[str] | None = None) -> bool:
    """Validate API response structure.

    Args:
        response_data: The API response data to validate
        expected_fields: List of fields that must be present

    Returns:
        True if response is valid

    Raises:
        InputValidationError: If response is invalid
    """
    if response_data is None:
        raise InputValidationError("API response is None")

    if not isinstance(response_data, dict | list):
        raise InputValidationError("API response must be a dictionary or list")

    if expected_fields and isinstance(response_data, dict):
        missing_fields = [field for field in expected_fields if field not in response_data]
        if missing_fields:
            raise InputValidationError(f"API response missing required fields: {missing_fields}")

    return True


def validate_file_path(file_path: str, allowed_extensions: list[str] | None = None) -> str:
    """Validate file path for security and format.

    Args:
        file_path: Path to validate
        allowed_extensions: List of allowed file extensions (with dots)

    Returns:
        Validated file path

    Raises:
        InputValidationError: If file path is invalid
    """
    if not isinstance(file_path, str):
        raise InputValidationError("File path must be a string")

    file_path = file_path.strip()

    if not file_path:
        raise InputValidationError("File path cannot be empty")

    # Check for path traversal attempts
    dangerous_patterns = ["../", "..\\", "/etc/", "\\windows\\", "~"]
    for pattern in dangerous_patterns:
        if pattern in file_path.lower():
            raise InputValidationError(f"Potentially dangerous path pattern detected: {pattern}")

    # Check file extension if specified
    if allowed_extensions:
        file_extension = "." + file_path.split(".")[-1] if "." in file_path else ""
        if file_extension.lower() not in [ext.lower() for ext in allowed_extensions]:
            raise InputValidationError(
                f"Invalid file extension: {file_extension}. Allowed: {allowed_extensions}"
            )

    return file_path


def validate_numeric_range(value: str | int | float, min_val: float, max_val: float,
                         param_name: str = "value") -> float:
    """Validate that a numeric value is within specified range.

    Args:
        value: Value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        param_name: Name of parameter for error messages

    Returns:
        Validated numeric value as float

    Raises:
        InputValidationError: If value is invalid or out of range
    """
    try:
        num_value = float(value)
    except (ValueError, TypeError) as e:
        raise InputValidationError(f"{param_name} must be numeric: {e}") from None

    if not min_val <= num_value <= max_val:
        raise InputValidationError(
            f"{param_name} must be between {min_val} and {max_val}, got {num_value}"
        )

    return num_value


def validate_list_input(input_list: Any, min_length: int = 0, max_length: int | None = None,
                       item_type: type | None = None, item_name: str = "item") -> list[Any]:
    """Validate list input with optional constraints.

    Args:
        input_list: List to validate
        min_length: Minimum required length
        max_length: Maximum allowed length
        item_type: Required type for list items
        item_name: Name for items in error messages

    Returns:
        Validated list

    Raises:
        InputValidationError: If list is invalid
    """
    if not isinstance(input_list, list):
        raise InputValidationError("Input must be a list")

    if len(input_list) < min_length:
        raise InputValidationError(f"List must contain at least {min_length} {item_name}(s)")

    if max_length is not None and len(input_list) > max_length:
        raise InputValidationError(f"List cannot contain more than {max_length} {item_name}(s)")

    if item_type is not None:
        invalid_items = [i for i, item in enumerate(input_list) if not isinstance(item, item_type)]
        if invalid_items:
            raise InputValidationError(
                f"List contains invalid {item_name} types at positions: {invalid_items}"
            )

    return input_list


def validate_dict_input(input_dict: Any, required_keys: list[str] | None = None,
                       optional_keys: list[str] | None = None) -> dict[str, Any]:
    """Validate dictionary input structure.

    Args:
        input_dict: Dictionary to validate
        required_keys: Keys that must be present
        optional_keys: Keys that are allowed but not required

    Returns:
        Validated dictionary

    Raises:
        InputValidationError: If dictionary structure is invalid
    """
    if not isinstance(input_dict, dict):
        raise InputValidationError("Input must be a dictionary")

    if required_keys:
        missing_keys = [key for key in required_keys if key not in input_dict]
        if missing_keys:
            raise InputValidationError(f"Missing required keys: {missing_keys}")

    if optional_keys is not None:
        allowed_keys = set(required_keys or []) | set(optional_keys)
        extra_keys = set(input_dict.keys()) - allowed_keys
        if extra_keys:
            raise InputValidationError(f"Unexpected keys found: {extra_keys}")

    return input_dict


def validate_url(url: str) -> str:
    """Validate URL format and security.

    Args:
        url: URL to validate

    Returns:
        Validated URL

    Raises:
        InputValidationError: If URL is invalid
    """
    if not isinstance(url, str):
        raise InputValidationError("URL must be a string")

    url = url.strip()

    if not url:
        raise InputValidationError("URL cannot be empty")

    # Basic URL validation
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise InputValidationError("Invalid URL format")

        # Security checks
        if parsed.scheme.lower() not in ["http", "https"]:
            raise InputValidationError("Only HTTP and HTTPS URLs are allowed")

        # Check for suspicious patterns
        suspicious_patterns = [
            "javascript:",
            "data:",
            "file:",
            "ftp:",
            "chrome:",
            "chrome-extension:",
        ]

        for pattern in suspicious_patterns:
            if pattern in url.lower():
                raise InputValidationError(f"Suspicious URL pattern detected: {pattern}")
    except Exception:
        raise InputValidationError("Could not parse URL") from None

    return url


def encode_for_url(value: str) -> str:
    """Safely encode a string for use in URLs.

    Args:
        value: String to encode

    Returns:
        URL-encoded string
    """
    return quote(str(value), safe="")


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename for safe file operations.

    Args:
        filename: Filename to sanitize

    Returns:
        Sanitized filename

    Raises:
        InputValidationError: If filename is invalid
    """
    # Remove any path components
    filename = filename.replace("/", "").replace("\\", "")

    # Remove dangerous characters
    filename = re.sub(r'[<>:"|?*\x00-\x1f]', "", filename)

    # Remove leading/trailing dots and spaces
    filename = filename.strip(". ")

    # Ensure it's not empty
    if not filename:
        raise InputValidationError("Filename cannot be empty after sanitization")

    # Check for reserved names (Windows)
    reserved_names = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }

    name_without_ext = filename.split(".")[0].upper()
    if name_without_ext in reserved_names:
        raise InputValidationError(f"Reserved filename: {filename}")

    return filename


def sanitize_for_api(value: str) -> str:
    """Sanitize string value for safe use in API requests.
    
    Args:
        value: String value to sanitize
        
    Returns:
        Sanitized string safe for API use
    """
    if not isinstance(value, str):
        value = str(value)

    # Remove control characters and clean whitespace
    value = "".join(char for char in value if ord(char) >= MIN_ASCII_PRINTABLE or char in "\n\t ")
    value = value.strip()

    # Limit length for API use
    if len(value) > 255:
        value = value[:255]

    return value


def validate_state_name(state: str) -> str:
    """Validate a US state name or abbreviation.
    
    Args:
        state: State name or abbreviation to validate
        
    Returns:
        Validated state string
        
    Raises:
        InputValidationError: If state is invalid
    """
    if not isinstance(state, str):
        raise InputValidationError("State must be a string")

    state = state.strip()

    if not state:
        raise InputValidationError("State cannot be empty")

    # List of valid state abbreviations
    valid_abbrs = {
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL",
        "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME",
        "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH",
        "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "PR",
        "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV",
        "WI", "WY"
    }

    # Check if it's a valid abbreviation
    if state.upper() in valid_abbrs:
        return state.upper()

    # List of valid state names (lowercase for comparison)
    valid_names = {
        "alabama", "alaska", "arizona", "arkansas", "california",
        "colorado", "connecticut", "delaware", "district of columbia",
        "florida", "georgia", "hawaii", "idaho", "illinois", "indiana",
        "iowa", "kansas", "kentucky", "louisiana", "maine", "maryland",
        "massachusetts", "michigan", "minnesota", "mississippi", "missouri",
        "montana", "nebraska", "nevada", "new hampshire", "new jersey",
        "new mexico", "new york", "north carolina", "north dakota", "ohio",
        "oklahoma", "oregon", "pennsylvania", "puerto rico", "rhode island",
        "south carolina", "south dakota", "tennessee", "texas", "utah",
        "vermont", "virginia", "washington", "west virginia", "wisconsin",
        "wyoming"
    }

    # Check if it's a valid full name
    if state.lower() in valid_names:
        return state.title()

    raise InputValidationError(f"Invalid state: {state}")
