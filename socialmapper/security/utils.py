"""Security utility functions for backward compatibility."""

import logging
import os

from .key_manager import KeyStorage, SecureKeyManager

logger = logging.getLogger(__name__)

# Global key manager instance
_key_manager: SecureKeyManager | None = None


def get_key_manager() -> SecureKeyManager:
    """
    Get or create the global key manager instance.

    Returns
    -------
    SecureKeyManager
        The global key manager instance.
    """
    global _key_manager
    if _key_manager is None:
        _key_manager = SecureKeyManager()
    return _key_manager


def get_api_key(key_name: str = "census_api", fallback_env: str | None = None) -> str | None:
    """
    Get API key with backward compatibility.

    This function provides a simple interface that maintains backward
    compatibility with existing code that expects environment variables.

    Parameters
    ----------
    key_name : str, optional
        Name of the API key, by default "census_api".
    fallback_env : str, optional
        Environment variable to check as fallback.

    Returns
    -------
    str or None
        The API key or None if not found.

    Examples
    --------
    >>> # Get Census API key
    >>> api_key = get_api_key("census_api")

    >>> # Get with custom fallback
    >>> api_key = get_api_key("mapbox", "MAPBOX_ACCESS_TOKEN")
    """
    manager = get_key_manager()

    # Try secure storage first
    key = manager.get_key(key_name)

    # Fallback to specific environment variable if provided
    if not key and fallback_env:
        key = os.getenv(fallback_env)

    # Log warning if no key found
    if not key:
        logger.warning(
            f"No API key found for '{key_name}'. "
            f"Please set it using: socialmapper-keys set {key_name} <your-key>"
        )

    return key


def set_api_key(key_name: str, key_value: str, storage: KeyStorage | None = None) -> bool:
    """
    Set API key in secure storage.

    Parameters
    ----------
    key_name : str
        Name of the API key.
    key_value : str
        The API key value.
    storage : KeyStorage, optional
        Storage backend to use.

    Returns
    -------
    bool
        True if successfully stored.

    Examples
    --------
    >>> # Store in default storage (keyring if available)
    >>> set_api_key("census_api", "your_key_here")

    >>> # Store in specific backend
    >>> from socialmapper.security import KeyStorage
    >>> set_api_key("census_api", "your_key", KeyStorage.ENCRYPTED_FILE)
    """
    manager = get_key_manager()
    return manager.set_key(key_name, key_value, storage)


def validate_api_key(key_name: str, key_value: str | None = None) -> bool:
    """
    Validate API key format.

    Parameters
    ----------
    key_name : str
        Name of the API key type.
    key_value : str, optional
        Key to validate, or retrieves from storage.

    Returns
    -------
    bool
        True if key appears valid.

    Examples
    --------
    >>> # Validate stored key
    >>> is_valid = validate_api_key("census_api")

    >>> # Validate specific key
    >>> is_valid = validate_api_key("census_api", "test_key_value")
    """
    manager = get_key_manager()
    return manager.validate_key(key_name, key_value)


def migrate_from_env() -> dict:
    """
    Migrate API keys from environment variables to secure storage.

    Returns
    -------
    dict
        Migration results for each key.

    Examples
    --------
    >>> # Migrate all known API keys from environment
    >>> results = migrate_from_env()
    >>> print(f"Migrated {sum(results.values())} keys")
    """
    manager = get_key_manager()
    results = {}

    # Known environment variable mappings
    env_mappings = {
        "census_api": "CENSUS_API_KEY",
        "mapbox": "MAPBOX_TOKEN",
        "google_maps": "GOOGLE_MAPS_API_KEY",
    }

    for key_name, env_var in env_mappings.items():
        env_value = os.getenv(env_var)
        if env_value:
            # Try to store in most secure available backend
            success = manager.set_key(key_name, env_value)
            results[key_name] = success

            if success:
                logger.info(f"Migrated {env_var} to secure storage")
                # Optionally remove from environment
                # del os.environ[env_var]
            else:
                logger.warning(f"Failed to migrate {env_var}")
        else:
            results[key_name] = False

    return results
