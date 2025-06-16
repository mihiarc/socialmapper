"""Environment variable loading utilities.

Provides consistent dotenv loading across the SocialMapper codebase.
"""

import os
from pathlib import Path


def load_environment_variables(env_file: str | None = None, verbose: bool = False) -> bool:
    """Load environment variables from .env file.

    Args:
        env_file: Path to specific .env file (optional)
        verbose: Whether to print loading information

    Returns:
        True if dotenv was loaded successfully, False otherwise
    """
    try:
        from dotenv import load_dotenv

        # Determine which .env file to load
        if env_file:
            env_path = Path(env_file)
        else:
            # Look for .env in current directory and parent directories
            current_dir = Path.cwd()
            env_path = None

            # Check current directory and up to 3 parent directories
            for path in [current_dir] + list(current_dir.parents)[:3]:
                potential_env = path / ".env"
                if potential_env.exists():
                    env_path = potential_env
                    break

        # Load the .env file
        if env_path and env_path.exists():
            load_dotenv(env_path)
            if verbose:
                print(f"Loaded environment variables from: {env_path}")
            return True
        else:
            # Try loading from default location
            load_dotenv()
            if verbose:
                print("Attempted to load .env from default locations")
            return True

    except ImportError:
        if verbose:
            print("python-dotenv not available - continuing without .env file loading")
        return False
    except Exception as e:
        if verbose:
            print(f"Error loading .env file: {e}")
        return False


def ensure_environment_loaded(verbose: bool = False) -> None:
    """Ensure environment variables are loaded.

    This is a convenience function that can be called from any module
    to ensure .env files are loaded.

    Args:
        verbose: Whether to print loading information
    """
    load_environment_variables(verbose=verbose)


def get_env_var(key: str, default: str | None = None, required: bool = False) -> str | None:
    """Get an environment variable with optional default and validation.

    Args:
        key: Environment variable name
        default: Default value if not found
        required: Whether the variable is required

    Returns:
        Environment variable value or default

    Raises:
        ValueError: If required variable is not found
    """
    value = os.getenv(key, default)

    if required and value is None:
        raise ValueError(f"Required environment variable '{key}' not found")

    return value


# Convenience function for Census API key
def get_census_api_key(required: bool = False) -> str | None:
    """Get the Census API key from environment variables.

    Args:
        required: Whether the API key is required

    Returns:
        Census API key or None

    Raises:
        ValueError: If required and not found
    """
    return get_env_var("CENSUS_API_KEY", required=required)


# Auto-load environment variables when this module is imported
ensure_environment_loaded()
