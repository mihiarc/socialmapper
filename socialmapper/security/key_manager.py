"""Secure API key management for SocialMapper."""

import json
import logging
import os
import platform
import re
import subprocess
import tempfile
import uuid
from contextlib import contextmanager
from enum import Enum
from pathlib import Path

try:
    import keyring

    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

try:
    import base64

    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

logger = logging.getLogger(__name__)

# Constants for key management
MASTER_KEY_KEYRING_SERVICE = "socialmapper_master_key"
MASTER_KEY_KEYRING_USERNAME = "encryption_key"
MACHINE_KEY_SALT = b"socialmapper_machine_key_v1"
PBKDF2_ITERATIONS = 100_000


def _get_machine_identifier() -> bytes:
    """
    Get a stable machine-specific identifier.

    Combines multiple sources for stability across reboots while
    maintaining uniqueness per machine. Falls back gracefully if
    certain identifiers are unavailable.

    Returns
    -------
    bytes
        A stable machine identifier.
    """
    identifiers = []

    # Try to get machine UUID (most reliable)
    try:
        system = platform.system()
        if system == "Darwin":  # macOS
            result = subprocess.run(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in result.stdout.split("\n"):
                if "IOPlatformUUID" in line:
                    machine_uuid = line.split('"')[-2]
                    identifiers.append(machine_uuid)
                    break
        elif system == "Linux":
            # Try /etc/machine-id first (most reliable on Linux)
            machine_id_path = Path("/etc/machine-id")
            if machine_id_path.exists():
                identifiers.append(machine_id_path.read_text().strip())
            else:
                # Fallback to /var/lib/dbus/machine-id
                dbus_path = Path("/var/lib/dbus/machine-id")
                if dbus_path.exists():
                    identifiers.append(dbus_path.read_text().strip())
        elif system == "Windows":
            result = subprocess.run(
                ["wmic", "csproduct", "get", "UUID"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            lines = result.stdout.strip().split("\n")
            if len(lines) > 1:
                identifiers.append(lines[1].strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    # Add MAC address as secondary identifier
    try:
        mac = uuid.getnode()
        if mac != uuid.getnode():  # Check it's not random
            identifiers.append(str(mac))
    except Exception:
        pass

    # Add hostname as tertiary identifier
    try:
        identifiers.append(platform.node())
    except Exception:
        pass

    # Combine all identifiers
    if not identifiers:
        # Last resort: use a fixed identifier (less secure but functional)
        logger.warning(
            "Could not determine machine identifier. "
            "Using fallback - encrypted keys may not be portable."
        )
        identifiers.append("socialmapper_fallback_id")

    combined = ":".join(identifiers)
    return combined.encode("utf-8")


def _derive_machine_key() -> bytes:
    """
    Derive an encryption key from machine-specific identifiers.

    This key is used to encrypt the master key when system keyring
    is not available. The key is deterministic for the same machine
    but different across machines.

    Returns
    -------
    bytes
        A 32-byte Fernet-compatible key.
    """
    if not CRYPTO_AVAILABLE:
        raise RuntimeError("Cryptography library required for key derivation")

    machine_id = _get_machine_identifier()

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=MACHINE_KEY_SALT,
        iterations=PBKDF2_ITERATIONS,
    )

    key_material = kdf.derive(machine_id)
    return base64.urlsafe_b64encode(key_material)


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
        config_path: Path | None = None,
        storage_preference: list | None = None,
    ):
        """Initialize secure key manager."""
        self.app_name = app_name
        self.config_path = Path(config_path or "~/.socialmapper/keys.enc").expanduser()
        self.master_key_path = self.config_path.parent / ".master.key"

        # In-memory storage for temporary keys
        self._memory_keys: dict[str, str] = {}

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
        """
        Initialize encryption for encrypted file storage.

        Uses a tiered security approach:
        1. System keyring (most secure) - stores master key in OS credential store
        2. Machine-encrypted file - encrypts master key with machine-derived key
        3. Falls back gracefully with appropriate warnings
        """
        if not CRYPTO_AVAILABLE:
            return

        # Create config directory with restricted permissions
        self.config_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)

        # Try to get master key from keyring first (most secure)
        key = self._get_master_key_from_keyring()

        if key is None:
            # Try to load from encrypted file
            key = self._load_master_key_from_file()

        if key is None:
            # Generate new master key
            key = self._generate_and_store_master_key()

        if key is not None:
            try:
                self._cipher = Fernet(key)
            except Exception as e:
                logger.error(f"Failed to initialize encryption cipher: {e}")
                self._cipher = None

    def _get_master_key_from_keyring(self) -> bytes | None:
        """
        Retrieve master encryption key from system keyring.

        Returns
        -------
        bytes or None
            The master key if found in keyring, None otherwise.
        """
        if not KEYRING_AVAILABLE:
            return None

        try:
            key_str = keyring.get_password(
                MASTER_KEY_KEYRING_SERVICE, MASTER_KEY_KEYRING_USERNAME
            )
            if key_str:
                logger.debug("Retrieved master key from system keyring")
                return key_str.encode("utf-8")
        except Exception as e:
            logger.debug(f"Could not retrieve master key from keyring: {e}")

        return None

    def _store_master_key_in_keyring(self, key: bytes) -> bool:
        """
        Store master encryption key in system keyring.

        Parameters
        ----------
        key : bytes
            The master key to store.

        Returns
        -------
        bool
            True if successfully stored.
        """
        if not KEYRING_AVAILABLE:
            return False

        try:
            keyring.set_password(
                MASTER_KEY_KEYRING_SERVICE,
                MASTER_KEY_KEYRING_USERNAME,
                key.decode("utf-8"),
            )
            logger.info("Stored master key in system keyring (most secure)")
            return True
        except Exception as e:
            logger.debug(f"Could not store master key in keyring: {e}")
            return False

    def _load_master_key_from_file(self) -> bytes | None:
        """
        Load and decrypt master key from encrypted file.

        The master key file is encrypted using a machine-derived key,
        ensuring it cannot be used on a different machine.

        Returns
        -------
        bytes or None
            The decrypted master key if successful, None otherwise.
        """
        if not self.master_key_path.exists():
            return None

        try:
            with open(self.master_key_path, "rb") as f:
                encrypted_data = f.read()

            # Decrypt using machine-derived key
            machine_key = _derive_machine_key()
            machine_cipher = Fernet(machine_key)

            decrypted_key = machine_cipher.decrypt(encrypted_data)
            logger.debug("Loaded master key from encrypted file")
            return decrypted_key

        except InvalidToken:
            logger.warning(
                "Could not decrypt master key file. This may happen if: "
                "1) The file was created on a different machine, "
                "2) Hardware identifiers have changed, or "
                "3) The file is corrupted. "
                "A new master key will be generated."
            )
            # Remove corrupted/incompatible key file
            try:
                self.master_key_path.unlink()
            except OSError:
                pass
            return None
        except Exception as e:
            logger.debug(f"Could not load master key from file: {e}")
            return None

    def _save_master_key_to_file(self, key: bytes) -> bool:
        """
        Encrypt and save master key to file.

        The master key is encrypted using a machine-derived key before
        being written to disk, providing protection at rest.

        Parameters
        ----------
        key : bytes
            The master key to save.

        Returns
        -------
        bool
            True if successfully saved.
        """
        try:
            # Encrypt using machine-derived key
            machine_key = _derive_machine_key()
            machine_cipher = Fernet(machine_key)
            encrypted_key = machine_cipher.encrypt(key)

            # Write atomically with restricted permissions
            fd, temp_path = tempfile.mkstemp(dir=self.config_path.parent)
            try:
                os.chmod(temp_path, 0o600)
                with os.fdopen(fd, "wb") as f:
                    f.write(encrypted_key)
                os.replace(temp_path, self.master_key_path)
            except Exception:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
                raise

            logger.info(
                "Stored master key in machine-encrypted file. "
                "Note: This key is tied to this machine and cannot be transferred."
            )
            return True

        except Exception as e:
            logger.error(f"Failed to save master key to file: {e}")
            return False

    def _generate_and_store_master_key(self) -> bytes | None:
        """
        Generate a new master encryption key and store it securely.

        Attempts to store in system keyring first (most secure),
        then falls back to machine-encrypted file.

        Returns
        -------
        bytes or None
            The generated master key, or None if storage failed.
        """
        # Generate new master key using OS random source
        salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=PBKDF2_ITERATIONS,
        )

        # Generate random password for key derivation
        password = os.urandom(32)
        key_material = kdf.derive(password)
        key = base64.urlsafe_b64encode(key_material)

        # Try to store in keyring first (most secure)
        if self._store_master_key_in_keyring(key):
            return key

        # Fall back to machine-encrypted file
        if self._save_master_key_to_file(key):
            return key

        logger.error(
            "Failed to store master key. Encrypted file storage will not be available. "
            "Consider using system keyring or environment variables for API keys."
        )
        return None

    def get_key(self, key_name: str, default: str | None = None) -> str | None:
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
        self, key_name: str, key_value: str, storage: KeyStorage | None = None
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
        if not re.match(r"^[a-zA-Z0-9_-]+$", key_name):
            logger.error(
                f"Invalid key name: {key_name}. "
                "Use only alphanumeric, underscore, and hyphen."
            )
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
            storage = (
                self.storage_preference[0]
                if self.storage_preference
                else KeyStorage.ENVIRONMENT
            )

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

    def delete_key(self, key_name: str, storage: KeyStorage | None = None) -> bool:
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
    def _get_from_keyring(self, key_name: str) -> str | None:
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
    def _get_from_encrypted_file(self, key_name: str) -> str | None:
        """Get key from encrypted file."""
        if not CRYPTO_AVAILABLE or not self._cipher:
            return None

        if not self.config_path.exists():
            return None

        try:
            with open(self.config_path, "rb") as f:
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
                with open(self.config_path, "rb") as f:
                    encrypted_data = f.read()
                decrypted_data = self._cipher.decrypt(encrypted_data)
                keys = json.loads(decrypted_data.decode())
            else:
                keys = {}

            # Update key
            keys[key_name] = key_value

            # Encrypt and save
            encrypted_data = self._cipher.encrypt(json.dumps(keys).encode())
            with open(self.config_path, "wb") as f:
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
            with open(self.config_path, "rb") as f:
                encrypted_data = f.read()
            decrypted_data = self._cipher.decrypt(encrypted_data)
            keys = json.loads(decrypted_data.decode())

            # Remove key if exists
            if key_name in keys:
                del keys[key_name]

                # Re-encrypt and save
                encrypted_data = self._cipher.encrypt(json.dumps(keys).encode())
                with open(self.config_path, "wb") as f:
                    f.write(encrypted_data)

                return True

            return False

        except Exception:
            return False

    # Environment variable storage methods
    def _get_from_environment(self, key_name: str) -> str | None:
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

    def validate_key(self, key_name: str, key_value: str | None = None) -> bool:
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
            return key_value.startswith(("pk.", "sk."))
        else:
            # Generic validation - not empty, no spaces
            return bool(key_value) and " " not in key_value

    def list_keys(self) -> dict[str, list]:
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
                with open(self.config_path, "rb") as f:
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
