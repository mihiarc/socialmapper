"""Helper utilities for tutorials with enhanced error handling.

This module provides utilities to make tutorials more robust and user-friendly.
"""

import sys
from contextlib import contextmanager
from typing import Any

from .exceptions import (
    APIError,
    ValidationError,
    DataError,
    SocialMapperError,
)

# Map old exception names to new simple ones
CensusAPIError = APIError
GeocodingError = APIError
OSMAPIError = APIError
ConfigurationError = ValidationError
InvalidLocationError = ValidationError
MissingAPIKeyError = ValidationError
NoDataFoundError = DataError


def format_error_for_user(error: Exception) -> str:
    """Format any error for user display."""
    if isinstance(error, SocialMapperError):
        return str(error)
    return f"An unexpected error occurred: {type(error).__name__}: {error}"


@contextmanager
def tutorial_error_handler(tutorial_name: str = "Tutorial"):
    """Context manager for handling errors in tutorials.

    Provides user-friendly error messages and helpful suggestions.

    Example:
        ```python
        with tutorial_error_handler("Getting Started Tutorial"):
            # Tutorial code here
            run_analysis()
        ```
    """
    try:
        yield
    except KeyboardInterrupt:
        print("\n\n⚠️  Tutorial interrupted by user")
        print("You can restart the tutorial at any time.")
        sys.exit(0)
    except MissingAPIKeyError as e:
        print(f"\n❌ {tutorial_name} Error: {e}")
        print("\n📝 To get a Census API key:")
        print("1. Visit: https://api.census.gov/data/key_signup.html")
        print("2. Fill out the form (it's free!)")
        print("3. Check your email for the API key")
        print("4. Set it as an environment variable:")
        print("   export CENSUS_API_KEY='your-key-here'")
        print("\nNote: The Census API key is optional but recommended for demographic analysis.")
        sys.exit(1)
    except InvalidLocationError as e:
        print(f"\n❌ {tutorial_name} Error: {e}")
        print("\n📍 Location Format Examples:")
        print("• City and state: 'San Francisco, CA'")
        print("• County: 'Wake County, North Carolina'")
        print("• Full state name: 'Austin, Texas'")
        sys.exit(1)
    except NoDataFoundError as e:
        print(f"\n❌ {tutorial_name} Error: {e}")
        print("\n💡 Common causes:")
        print("• The POI type might not exist in this area")
        print("• The location name might be misspelled")
        print("• The area might be too small")
        print("\n🔍 Try these alternatives:")
        print("• Different POI types: 'school', 'hospital', 'park'")
        print("• Larger areas: use county instead of city")
        print("• Different locations: try a major city")
        sys.exit(1)
    except OSMAPIError as e:
        print(f"\n❌ {tutorial_name} Error: {e}")
        print("\n🌐 OpenStreetMap Connection Issues:")
        print("• Check your internet connection")
        print("• The Overpass API might be temporarily down")
        print("• Try again in a few minutes")
        print("\n💡 Alternative: Use custom coordinates from a CSV/JSON file")
        sys.exit(1)
    except CensusAPIError as e:
        print(f"\n❌ {tutorial_name} Error: {e}")
        print("\n🏛️  Census API Issues:")
        if "401" in str(e):
            print("• Your API key might be invalid")
            print("• Double-check the key is correctly set")
        elif "429" in str(e):
            print("• You've hit the rate limit")
            print("• Wait a few minutes before trying again")
        else:
            print("• The Census API might be temporarily unavailable")
            print("• Check your internet connection")
        sys.exit(1)
    except GeocodingError as e:
        print(f"\n❌ {tutorial_name} Error: {e}")
        print("\n📍 Geocoding Failed:")
        print("• Verify the location name is spelled correctly")
        print("• Try being more specific (add state/country)")
        print("• Use a well-known location for testing")
        sys.exit(1)
    except SocialMapperError as e:
        # Generic SocialMapper error with suggestions
        print(f"\n❌ {tutorial_name} Error: {format_error_for_user(e)}")
        if e.context.suggestions:
            print("\n💡 Suggestions:")
            for suggestion in e.context.suggestions:
                print(f"• {suggestion}")
        sys.exit(1)
    except Exception as e:
        # Unexpected error - show more details
        print(f"\n❌ Unexpected error in {tutorial_name}: {type(e).__name__}: {e}")
        print("\n🐛 This might be a bug. Please report it with:")
        print("• The full error message above")
        print("• The tutorial you were running")
        print("• Your Python version and OS")
        print("\nFor more details, run with --debug flag")
        sys.exit(1)


def safe_import(module_name: str, package: str | None = None) -> Any:
    """Safely import a module with helpful error messages.

    Args:
        module_name: Name of module to import
        package: Package name for installation instructions

    Returns
    -------
        Imported module or None if import failed
    """
    try:
        if module_name.startswith("."):
            # Relative import
            from importlib import import_module

            return import_module(module_name, package="socialmapper")
        else:
            # Absolute import
            return __import__(module_name)
    except ImportError:
        print(f"\n⚠️  Missing dependency: {module_name}")
        if package:
            print(f"Install it with: pip install {package}")
        else:
            print(f"Install it with: pip install {module_name}")
        print("\nOr install all tutorial dependencies:")
        print("pip install socialmapper[tutorials]")
        return None


def check_dependencies() -> bool:
    """Check if all backend tutorial dependencies are available.

    Returns
    -------
        True if all dependencies are available
    """
    required = [
        ("pandas", "pandas"),
        ("geopandas", "geopandas"),
        ("matplotlib", "matplotlib"),
    ]

    missing = []
    for module, package in required:
        if safe_import(module, package) is None:
            missing.append(package)

    if missing:
        print("\n📦 Missing dependencies for backend tutorials:")
        print(f"pip install {' '.join(missing)}")
        return False

    return True


def validate_tutorial_config(config: dict[str, Any]) -> None:
    """Validate tutorial configuration with helpful error messages.

    Args:
        config: Configuration dictionary to validate

    Raises
    ------
        ConfigurationError: If configuration is invalid
    """
    required_fields = ["location", "poi_type", "poi_name"]
    missing = [field for field in required_fields if not config.get(field)]

    if missing:
        raise ConfigurationError(
            f"Missing required configuration: {', '.join(missing)}",
            config=config,
            missing_fields=missing,
        ).add_suggestion("Check that all required parameters are provided")

    # Validate location format
    location = config["location"]
    if "," not in location:
        raise InvalidLocationError(location)

    # Validate travel time if provided
    if "travel_time" in config:
        travel_time = config["travel_time"]
        if not isinstance(travel_time, int) or travel_time < 1 or travel_time > 60:
            raise ConfigurationError(
                "Invalid travel time",
                field="travel_time",
                value=travel_time,
                reason="Must be an integer between 1 and 60 minutes",
            )


def print_tutorial_header(title: str, description: str) -> None:
    """Print a formatted tutorial header.

    Args:
        title: Tutorial title
        description: Tutorial description
    """
    print("=" * 60)
    print(f"🗺️  {title}")
    print("=" * 60)
    print(f"\n{description}\n")


def print_tutorial_section(title: str) -> None:
    """Print a formatted section header.

    Args:
        title: Section title
    """
    print(f"\n{'─' * 40}")
    print(f"📍 {title}")
    print(f"{'─' * 40}\n")
