"""Secure API key management for SocialMapper."""

import os
import re
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum
from contextlib import contextmanager

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import base64
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

logger = logging.getLogger(__name__)


class KeyStorage(Enum):
    """Storage backend options for API keys."""

    ENVIRONMENT = "environment"
    KEYRING = "keyring"
    ENCRYPTED_FILE = "encrypted_file"
    MEMORY = "memory"


class SecureKeyManager:
    """
    Secure API key management with multiple storage backends.

    Provides secure storage and retrieval of API keys using:
    - System keyring (Windows Credential Vault, macOS Keychain, Linux Secret Service)
    - Encrypted configuration files
    - Environment variables (fallback)
    - In-memory storage (testing)

    Parameters
    ----------
    app_name : str, optional
        Application name for keyring storage, by default "socialmapper".
    config_path : Path or str, optional
        Path to encrypted config file, by default "~/.socialmapper/keys.enc".
    storage_preference : list of KeyStorage, optional
        Ordered list of storage backends to try.

    Examples
    --------
    >>> key_manager = SecureKeyManager()
    >>> key_manager.set_key("census_api", "your_api_key")
    >>> api_key = key_manager.get_key("census_api")

    >>> # Use context manager for temporary keys
    >>> with key_manager.temporary_key("census_api", "temp_key"):
    ...     # Key is available here
    ...     api_key = key_manager.get_key("census_api")
    """

    def __init__(
        self,
        app_name: str = "socialmapper",
        config_path: Optional[Path] = None,
        storage_preference: Optional[list] = None
    ):
        """Initialize secure key manager."""
        self.app_name = app_name
        self.config_path = Path(config_path or "~/.socialmapper/keys.enc").expanduser()
        self.master_key_path = self.config_path.parent / ".master.key"

        # In-memory storage for temporary keys
        self._memory_keys: Dict[str, str] = {}

        # Set storage preference order
        if storage_preference:
            self.storage_preference = storage_preference
        else:
            self.storage_preference = self._get_default_storage_order()

        # Initialize encryption if available
        self._cipher = None
        if CRYPTO_AVAILABLE:
            self._initialize_encryption()

    def _get_default_storage_order(self) -> list:
        """Get default storage backend preference order."""
        order = []

        # Prefer keyring if available
        if KEYRING_AVAILABLE:
            order.append(KeyStorage.KEYRING)

        # Then encrypted file if cryptography is available
        if CRYPTO_AVAILABLE:
            order.append(KeyStorage.ENCRYPTED_FILE)

        # Always include environment as fallback
        order.append(KeyStorage.ENVIRONMENT)

        return order

    def _initialize_encryption(self):
        """Initialize encryption for encrypted file storage."""
        if not CRYPTO_AVAILABLE:
            return

        # Create config directory with restricted permissions
        self.config_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)

        # Load or generate master key
        if self.master_key_path.exists():
            with open(self.master_key_path, 'rb') as f:
                encrypted_key = f.read()

            # For now, use the key directly (should be encrypted with user passphrase in production)
            key = encrypted_key
        else:
            # Generate new master key using OS random source
            salt = os.urandom(16)

            # Derive key from random bytes using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100_000,
            )

            # Generate random password for key derivation
            password = os.urandom(32)
            key_material = kdf.derive(password)
            key = base64.urlsafe_b64encode(key_material)

            # Store salt and encrypted key (in production, encrypt with user passphrase)
            key_data = salt + key

            # Create file with restricted permissions atomically
            import tempfile
            fd, temp_path = tempfile.mkstemp(dir=self.config_path.parent)
            try:
                os.chmod(temp_path, 0o600)
                with os.fdopen(fd, 'wb') as f:
                    f.write(key_data)
                os.replace(temp_path, self.master_key_path)
            except:
                os.unlink(temp_path)
                raise

            logger.info(f"Generated new master key at {self.master_key_path}")

            # Extract key for use
            key = key_data[16:]  # Skip salt

        self._cipher = Fernet(key)

    def get_key(self, key_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieve an API key using configured storage backends.

        Parameters
        ----------
        key_name : str
            Name of the key to retrieve (e.g., "census_api").
        default : str, optional
            Default value if key not found.

        Returns
        -------
        str or None
            The API key or default value.
        """
        # Check memory storage first
        if key_name in self._memory_keys:
            return self._memory_keys[key_name]

        # Try each storage backend in order
        for storage in self.storage_preference:
            try:
                if storage == KeyStorage.KEYRING:
                    key = self._get_from_keyring(key_name)
                elif storage == KeyStorage.ENCRYPTED_FILE:
                    key = self._get_from_encrypted_file(key_name)
                elif storage == KeyStorage.ENVIRONMENT:
                    key = self._get_from_environment(key_name)
                else:
                    continue

                if key:
                    logger.debug(f"Retrieved key '{key_name}' from {storage.value}")
                    return key

            except Exception as e:
                logger.warning(f"Failed to get key from {storage.value}: {e}")
                continue

        if default:
            logger.debug(f"Using default value for key '{key_name}'")
        else:
            logger.warning(f"Key '{key_name}' not found in any storage backend")

        return default

    def set_key(
        self,
        key_name: str,
        key_value: str,
        storage: Optional[KeyStorage] = None
    ) -> bool:
        """
        Store an API key in specified storage backend.

        Parameters
        ----------
        key_name : str
            Name of the key to store.
        key_value : str
            The API key value.
        storage : KeyStorage, optional
            Storage backend to use, defaults to first available.

        Returns
        -------
        bool
            True if successfully stored.
        """
        # Validate inputs
        if not key_value:
            logger.error("Cannot store empty key value")
            return False

        # Validate key name (prevent path traversal and special characters)
        if not re.match(r'^[a-zA-Z0-9_-]+$', key_name):
            logger.error(f"Invalid key name: {key_name}. Use only alphanumeric, underscore, and hyphen.")
            return False

        # Limit key name length
        if len(key_name) > 100:
            logger.error("Key name too long (max 100 characters)")
            return False

        # Limit key value length (prevent memory issues)
        if len(key_value) > 10000:
            logger.error("Key value too long (max 10000 characters)")
            return False

        # Use specified storage or first available
        if storage is None:
            storage = self.storage_preference[0] if self.storage_preference else KeyStorage.ENVIRONMENT

        try:
            if storage == KeyStorage.KEYRING:
                return self._set_in_keyring(key_name, key_value)
            elif storage == KeyStorage.ENCRYPTED_FILE:
                return self._set_in_encrypted_file(key_name, key_value)
            elif storage == KeyStorage.ENVIRONMENT:
                return self._set_in_environment(key_name, key_value)
            elif storage == KeyStorage.MEMORY:
                self._memory_keys[key_name] = key_value
                return True
            else:
                logger.error(f"Unsupported storage type: {storage}")
                return False

        except Exception as e:
            logger.error(f"Failed to store key in {storage.value}: {e}")
            return False

    def delete_key(self, key_name: str, storage: Optional[KeyStorage] = None) -> bool:
        """
        Delete an API key from storage.

        Parameters
        ----------
        key_name : str
            Name of the key to delete.
        storage : KeyStorage, optional
            Storage backend to delete from, defaults to all.

        Returns
        -------
        bool
            True if successfully deleted.
        """
        success = False

        # Delete from memory
        if key_name in self._memory_keys:
            del self._memory_keys[key_name]
            success = True

        if storage:
            backends = [storage]
        else:
            backends = self.storage_preference

        for backend in backends:
            try:
                if backend == KeyStorage.KEYRING:
                    if self._delete_from_keyring(key_name):
                        success = True
                elif backend == KeyStorage.ENCRYPTED_FILE:
                    if self._delete_from_encrypted_file(key_name):
                        success = True
                elif backend == KeyStorage.ENVIRONMENT:
                    if self._delete_from_environment(key_name):
                        success = True
            except Exception as e:
                logger.warning(f"Failed to delete key from {backend.value}: {e}")

        return success

    @contextmanager
    def temporary_key(self, key_name: str, key_value: str):
        """
        Context manager for temporary API key.

        Parameters
        ----------
        key_name : str
            Name of the temporary key.
        key_value : str
            Temporary key value.

        Examples
        --------
        >>> with key_manager.temporary_key("census_api", "temp_key"):
        ...     # Use temporary key here
        ...     api_key = key_manager.get_key("census_api")
        """
        # Save existing key if any
        existing = self._memory_keys.get(key_name)

        try:
            # Set temporary key in memory
            self._memory_keys[key_name] = key_value
            yield
        finally:
            # Restore original key
            if existing:
                self._memory_keys[key_name] = existing
            elif key_name in self._memory_keys:
                del self._memory_keys[key_name]

    # Keyring storage methods
    def _get_from_keyring(self, key_name: str) -> Optional[str]:
        """Get key from system keyring."""
        if not KEYRING_AVAILABLE:
            return None

        try:
            return keyring.get_password(self.app_name, key_name)
        except Exception as e:
            logger.debug(f"Keyring get failed: {e}")
            return None

    def _set_in_keyring(self, key_name: str, key_value: str) -> bool:
        """Store key in system keyring."""
        if not KEYRING_AVAILABLE:
            logger.error("Keyring not available")
            return False

        try:
            keyring.set_password(self.app_name, key_name, key_value)
            logger.info(f"Stored key '{key_name}' in keyring")
            return True
        except Exception as e:
            logger.error(f"Failed to store in keyring: {e}")
            return False

    def _delete_from_keyring(self, key_name: str) -> bool:
        """Delete key from system keyring."""
        if not KEYRING_AVAILABLE:
            return False

        try:
            keyring.delete_password(self.app_name, key_name)
            return True
        except Exception:
            return False

    # Encrypted file storage methods
    def _get_from_encrypted_file(self, key_name: str) -> Optional[str]:
        """Get key from encrypted file."""
        if not CRYPTO_AVAILABLE or not self._cipher:
            return None

        if not self.config_path.exists():
            return None

        try:
            with open(self.config_path, 'rb') as f:
                encrypted_data = f.read()

            decrypted_data = self._cipher.decrypt(encrypted_data)
            keys = json.loads(decrypted_data.decode())

            return keys.get(key_name)
        except Exception as e:
            logger.debug(f"Failed to read encrypted file: {e}")
            return None

    def _set_in_encrypted_file(self, key_name: str, key_value: str) -> bool:
        """Store key in encrypted file."""
        if not CRYPTO_AVAILABLE or not self._cipher:
            logger.error("Encryption not available")
            return False

        try:
            # Load existing keys
            if self.config_path.exists():
                with open(self.config_path, 'rb') as f:
                    encrypted_data = f.read()
                decrypted_data = self._cipher.decrypt(encrypted_data)
                keys = json.loads(decrypted_data.decode())
            else:
                keys = {}

            # Update key
            keys[key_name] = key_value

            # Encrypt and save
            encrypted_data = self._cipher.encrypt(json.dumps(keys).encode())
            with open(self.config_path, 'wb') as f:
                f.write(encrypted_data)

            # Set file permissions
            self.config_path.chmod(0o600)

            logger.info(f"Stored key '{key_name}' in encrypted file")
            return True

        except Exception as e:
            logger.error(f"Failed to store in encrypted file: {e}")
            return False

    def _delete_from_encrypted_file(self, key_name: str) -> bool:
        """Delete key from encrypted file."""
        if not CRYPTO_AVAILABLE or not self._cipher:
            return False

        if not self.config_path.exists():
            return False

        try:
            # Load existing keys
            with open(self.config_path, 'rb') as f:
                encrypted_data = f.read()
            decrypted_data = self._cipher.decrypt(encrypted_data)
            keys = json.loads(decrypted_data.decode())

            # Remove key if exists
            if key_name in keys:
                del keys[key_name]

                # Re-encrypt and save
                encrypted_data = self._cipher.encrypt(json.dumps(keys).encode())
                with open(self.config_path, 'wb') as f:
                    f.write(encrypted_data)

                return True

            return False

        except Exception:
            return False

    # Environment variable storage methods
    def _get_from_environment(self, key_name: str) -> Optional[str]:
        """Get key from environment variable."""
        # Map key names to environment variable names
        env_mapping = {
            "census_api": "CENSUS_API_KEY",
            "mapbox": "MAPBOX_TOKEN",
            "google_maps": "GOOGLE_MAPS_API_KEY",
        }

        env_var = env_mapping.get(key_name, key_name.upper())
        return os.getenv(env_var)

    def _set_in_environment(self, key_name: str, key_value: str) -> bool:
        """Store key in environment variable (session only)."""
        env_mapping = {
            "census_api": "CENSUS_API_KEY",
            "mapbox": "MAPBOX_TOKEN",
            "google_maps": "GOOGLE_MAPS_API_KEY",
        }

        env_var = env_mapping.get(key_name, key_name.upper())
        os.environ[env_var] = key_value
        logger.info(f"Set environment variable {env_var}")
        return True

    def _delete_from_environment(self, key_name: str) -> bool:
        """Delete key from environment variable."""
        env_mapping = {
            "census_api": "CENSUS_API_KEY",
            "mapbox": "MAPBOX_TOKEN",
            "google_maps": "GOOGLE_MAPS_API_KEY",
        }

        env_var = env_mapping.get(key_name, key_name.upper())
        if env_var in os.environ:
            del os.environ[env_var]
            return True
        return False

    def validate_key(self, key_name: str, key_value: Optional[str] = None) -> bool:
        """
        Validate API key format.

        Parameters
        ----------
        key_name : str
            Name of the key type.
        key_value : str, optional
            Key to validate, or retrieves from storage.

        Returns
        -------
        bool
            True if key appears valid.
        """
        if key_value is None:
            key_value = self.get_key(key_name)

        if not key_value:
            return False

        # Basic validation rules
        if key_name == "census_api":
            # Census API keys are 40 characters
            return len(key_value) == 40
        elif key_name == "mapbox":
            # Mapbox tokens start with 'pk.' or 'sk.'
            return key_value.startswith(('pk.', 'sk.'))
        else:
            # Generic validation - not empty, no spaces
            return bool(key_value) and ' ' not in key_value

    def list_keys(self) -> Dict[str, list]:
        """
        List all available keys by storage backend.

        Returns
        -------
        dict
            Keys organized by storage backend.
        """
        result = {}

        # Check memory keys
        if self._memory_keys:
            result["memory"] = list(self._memory_keys.keys())

        # Check encrypted file
        if CRYPTO_AVAILABLE and self._cipher and self.config_path.exists():
            try:
                with open(self.config_path, 'rb') as f:
                    encrypted_data = f.read()
                decrypted_data = self._cipher.decrypt(encrypted_data)
                keys = json.loads(decrypted_data.decode())
                result["encrypted_file"] = list(keys.keys())
            except Exception:
                pass

        # Check environment
        env_keys = []
        for key in ["CENSUS_API_KEY", "MAPBOX_TOKEN", "GOOGLE_MAPS_API_KEY"]:
            if os.getenv(key):
                env_keys.append(key)
        if env_keys:
            result["environment"] = env_keys

        return result