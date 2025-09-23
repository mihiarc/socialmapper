"""Simple API key management utility."""

import os
import logging

logger = logging.getLogger(__name__)

# Try to import keyring, but don't fail if it's not available
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False


def get_api_key(key_name: str = "census_api") -> str:
    """
    Get API key from environment or keyring.

    First checks environment variables, then optionally checks
    system keyring if available.

    Parameters
    ----------
    key_name : str
        Name of the API key to retrieve.

    Returns
    -------
    str or None
        The API key if found, None otherwise.
    """
    # Map key names to environment variables
    env_map = {
        "census_api": "CENSUS_API_KEY",
        "mapbox": "MAPBOX_TOKEN",
    }

    env_var = env_map.get(key_name, key_name.upper())

    # Check environment first
    api_key = os.getenv(env_var)
    if api_key:
        return api_key

    # Try keyring if available
    if KEYRING_AVAILABLE:
        try:
            api_key = keyring.get_password("socialmapper", key_name)
            if api_key:
                return api_key
        except Exception:
            # Keyring might not be configured, that's ok
            pass

    return None


def set_api_key(key_name: str, key_value: str, use_keyring: bool = True) -> bool:
    """
    Store API key in keyring if available.

    Parameters
    ----------
    key_name : str
        Name of the API key.
    key_value : str
        The API key value.
    use_keyring : bool
        Whether to try storing in keyring.

    Returns
    -------
    bool
        True if successfully stored.
    """
    if use_keyring and KEYRING_AVAILABLE:
        try:
            keyring.set_password("socialmapper", key_name, key_value)
            logger.info(f"Stored {key_name} in system keyring")
            return True
        except Exception as e:
            logger.warning(f"Could not store in keyring: {e}")

    # Fallback: just tell user to set environment variable
    env_map = {
        "census_api": "CENSUS_API_KEY",
        "mapbox": "MAPBOX_TOKEN",
    }
    env_var = env_map.get(key_name, key_name.upper())

    logger.info(f"Please set environment variable {env_var}={key_value}")
    return False