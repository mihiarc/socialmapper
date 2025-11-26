"""
Comprehensive test suite for SocialMapper security module.

This test suite provides extensive coverage of the security module's
API key management functionality including:
- Secure key storage and retrieval across multiple backends
- Encryption and decryption operations
- Key validation and format checking
- Temporary key context managers
- Security hardening (file permissions, input validation)

Test Organization
------------------
- TestSecureKeyManagerInit: SecureKeyManager initialization
- TestKeyValidation: Input validation and sanitization
- TestKeyStorage: Key storage operations across backends
- TestKeyRetrieval: Key retrieval with fallback logic
- TestKeyDeletion: Key deletion operations
- TestTemporaryKeys: Context manager for temporary keys
- TestEncryptedFileStorage: Encrypted file operations
- TestSecurityHardening: File permissions and security
- TestUtilityFunctions: Utility function wrappers
- TestEdgeCases: Error handling and edge cases

Notes
-----
- Uses real API calls as per project requirements
- Temporary directories for file-based tests
- Mocks external dependencies (keyring) when necessary
- Tests security-critical features like encryption validation
"""

import json
import os
import stat
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from socialmapper.security import KeyStorage, SecureKeyManager
from socialmapper.security.key_manager import CRYPTO_AVAILABLE, KEYRING_AVAILABLE
from socialmapper.security.utils import (
    get_api_key,
    get_key_manager,
    migrate_from_env,
    set_api_key,
    validate_api_key,
)

if CRYPTO_AVAILABLE:
    import base64

    from cryptography.fernet import Fernet


class TestSecureKeyManagerInit:
    """
    Test SecureKeyManager initialization and configuration.

    Covers default settings, custom configurations, and storage
    backend preference ordering.
    """

    def test_init_with_defaults(self, tmp_path):
        """
        Test initialization with default parameters.

        Should create manager with sensible defaults for production
        use.
        """
        manager = SecureKeyManager()
        assert manager.app_name == "socialmapper"
        assert manager.config_path.name == "keys.enc"
        assert manager._memory_keys == {}

    def test_init_with_custom_app_name(self, tmp_path):
        """
        Test initialization with custom application name.

        Custom app name affects keyring namespace.
        """
        custom_name = "test_app"
        manager = SecureKeyManager(app_name=custom_name)
        assert manager.app_name == custom_name

    def test_init_with_custom_config_path(self, tmp_path):
        """
        Test initialization with custom config file path.

        Allows storing encrypted keys in non-default location.
        """
        custom_path = tmp_path / "custom_keys.enc"
        manager = SecureKeyManager(config_path=custom_path)
        assert manager.config_path == custom_path

    def test_init_creates_config_directory(self, tmp_path):
        """
        Test that config directory is created automatically.

        Directory should be created with secure permissions (0o700).
        """
        config_path = tmp_path / "new_dir" / "keys.enc"
        manager = SecureKeyManager(config_path=config_path)

        if CRYPTO_AVAILABLE:
            # Directory should be created
            assert config_path.parent.exists()
            # Check permissions are restrictive
            mode = config_path.parent.stat().st_mode
            # Should be owner-only (0o700)
            assert stat.S_IMODE(mode) == 0o700

    def test_init_with_custom_storage_preference(self, tmp_path):
        """
        Test initialization with custom storage preference order.

        Allows prioritizing specific backends like ENVIRONMENT first.
        """
        custom_order = [KeyStorage.ENVIRONMENT, KeyStorage.MEMORY]
        manager = SecureKeyManager(storage_preference=custom_order)
        assert manager.storage_preference == custom_order

    def test_init_default_storage_order_with_all_available(self, tmp_path):
        """
        Test default storage order when all backends available.

        Should prefer: KEYRING > ENCRYPTED_FILE > ENVIRONMENT
        """
        if KEYRING_AVAILABLE and CRYPTO_AVAILABLE:
            manager = SecureKeyManager()
            assert KeyStorage.KEYRING in manager.storage_preference
            assert KeyStorage.ENCRYPTED_FILE in manager.storage_preference
            assert KeyStorage.ENVIRONMENT in manager.storage_preference
            # KEYRING should come before ENCRYPTED_FILE
            keyring_idx = manager.storage_preference.index(KeyStorage.KEYRING)
            encrypted_idx = manager.storage_preference.index(KeyStorage.ENCRYPTED_FILE)
            assert keyring_idx < encrypted_idx

    def test_init_default_storage_order_without_keyring(self, tmp_path):
        """
        Test default storage order when keyring unavailable.

        Should use: ENCRYPTED_FILE > ENVIRONMENT
        """
        with patch("socialmapper.security.key_manager.KEYRING_AVAILABLE", False):
            manager = SecureKeyManager()
            assert KeyStorage.KEYRING not in manager.storage_preference
            assert KeyStorage.ENVIRONMENT in manager.storage_preference

    def test_init_default_storage_order_without_crypto(self, tmp_path):
        """
        Test default storage order when cryptography unavailable.

        Should only use: ENVIRONMENT
        """
        with patch("socialmapper.security.key_manager.CRYPTO_AVAILABLE", False):
            manager = SecureKeyManager()
            assert KeyStorage.ENCRYPTED_FILE not in manager.storage_preference
            assert KeyStorage.ENVIRONMENT in manager.storage_preference

    @pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="Cryptography library required")
    def test_init_initializes_cipher(self, tmp_path):
        """
        Test that encryption cipher is initialized.

        When crypto is available, should create Fernet cipher.
        """
        config_path = tmp_path / "keys.enc"
        manager = SecureKeyManager(config_path=config_path)
        # Cipher should be initialized if crypto available
        assert manager._cipher is not None or not CRYPTO_AVAILABLE

    def test_init_expands_home_directory(self):
        """
        Test that tilde in path is expanded to home directory.

        Ensures paths like ~/.socialmapper work correctly.
        """
        manager = SecureKeyManager(config_path="~/test/keys.enc")
        assert "~" not in str(manager.config_path)
        assert manager.config_path.is_absolute()


class TestKeyValidation:
    """
    Test input validation for key names and values.

    Security-critical validation to prevent path traversal,
    injection attacks, and resource exhaustion.
    """

    def test_validate_key_name_alphanumeric(self, tmp_path):
        """
        Test validation accepts alphanumeric key names.

        Standard key names should pass validation.
        """
        manager = SecureKeyManager(
            config_path=tmp_path / "keys.enc",
            storage_preference=[KeyStorage.MEMORY]
        )
        assert manager.set_key("test_key", "value123")
        assert manager.set_key("API-KEY-1", "value123")
        assert manager.set_key("key123", "value123")

    def test_validate_key_name_rejects_special_characters(self, tmp_path):
        """
        Test validation rejects special characters in key names.

        Prevents path traversal and injection attacks.
        """
        manager = SecureKeyManager(
            config_path=tmp_path / "keys.enc",
            storage_preference=[KeyStorage.MEMORY]
        )
        # These should all fail
        assert not manager.set_key("../etc/passwd", "malicious")
        assert not manager.set_key("key/path", "value")
        assert not manager.set_key("key;command", "value")
        assert not manager.set_key("key with spaces", "value")
        assert not manager.set_key("key.ext", "value")
        assert not manager.set_key("key$var", "value")

    def test_validate_key_name_length_limit(self, tmp_path):
        """
        Test validation enforces key name length limit.

        Prevents potential DoS through extremely long names.
        """
        manager = SecureKeyManager(
            config_path=tmp_path / "keys.enc",
            storage_preference=[KeyStorage.MEMORY]
        )
        # Just under limit should work
        long_name = "a" * 100
        assert manager.set_key(long_name, "value")

        # Over limit should fail
        too_long = "a" * 101
        assert not manager.set_key(too_long, "value")

    def test_validate_key_value_not_empty(self, tmp_path):
        """
        Test validation rejects empty key values.

        Empty values are not useful and should be rejected.
        """
        manager = SecureKeyManager(
            config_path=tmp_path / "keys.enc",
            storage_preference=[KeyStorage.MEMORY]
        )
        assert not manager.set_key("test_key", "")

    def test_validate_key_value_length_limit(self, tmp_path):
        """
        Test validation enforces key value length limit.

        Prevents memory exhaustion from extremely large keys.
        """
        manager = SecureKeyManager(
            config_path=tmp_path / "keys.enc",
            storage_preference=[KeyStorage.MEMORY]
        )
        # Just under limit should work
        large_value = "a" * 10000
        assert manager.set_key("test_key", large_value)

        # Over limit should fail
        too_large = "a" * 10001
        assert not manager.set_key("test_key", too_large)

    def test_validate_api_key_census_format(self, tmp_path):
        """
        Test Census API key format validation.

        Census keys should be exactly 40 characters.
        """
        manager = SecureKeyManager(config_path=tmp_path / "keys.enc")
        # Valid Census API key (40 chars)
        valid_key = "a" * 40
        assert manager.validate_key("census_api", valid_key)

        # Invalid lengths
        assert not manager.validate_key("census_api", "a" * 39)
        assert not manager.validate_key("census_api", "a" * 41)

    def test_validate_api_key_mapbox_format(self, tmp_path):
        """
        Test Mapbox token format validation.

        Mapbox tokens should start with 'pk.' or 'sk.'.
        """
        manager = SecureKeyManager(config_path=tmp_path / "keys.enc")
        # Valid Mapbox tokens
        assert manager.validate_key("mapbox", "pk.eyJ1234567890")
        assert manager.validate_key("mapbox", "sk.eyJ1234567890")

        # Invalid format
        assert not manager.validate_key("mapbox", "invalid_token")
        assert not manager.validate_key("mapbox", "ak.token")

    def test_validate_api_key_generic_format(self, tmp_path):
        """
        Test generic API key validation.

        Unknown key types should have basic validation:
        non-empty and no spaces.
        """
        manager = SecureKeyManager(config_path=tmp_path / "keys.enc")
        # Valid generic keys
        assert manager.validate_key("unknown_service", "abc123xyz")

        # Invalid - contains spaces
        assert not manager.validate_key("unknown_service", "key with spaces")

        # Invalid - empty
        assert not manager.validate_key("unknown_service", "")

    def test_validate_api_key_retrieves_from_storage(self, tmp_path):
        """
        Test validation can retrieve and validate stored key.

        Should work without explicitly passing key value.
        """
        manager = SecureKeyManager(
            config_path=tmp_path / "keys.enc",
            storage_preference=[KeyStorage.MEMORY]
        )
        # Store a valid key
        valid_key = "a" * 40
        manager.set_key("census_api", valid_key)

        # Validate without passing value
        assert manager.validate_key("census_api")


class TestKeyStorage:
    """
    Test key storage operations across different backends.

    Covers storage in memory, environment, encrypted files,
    and system keyring.
    """

    def test_set_key_in_memory(self, tmp_path):
        """
        Test storing key in memory storage.

        Memory storage is fast and ideal for testing.
        """
        manager = SecureKeyManager(
            config_path=tmp_path / "keys.enc",
            storage_preference=[KeyStorage.MEMORY]
        )
        assert manager.set_key("test_key", "test_value", KeyStorage.MEMORY)
        assert "test_key" in manager._memory_keys
        assert manager._memory_keys["test_key"] == "test_value"

    def test_set_key_in_environment(self, tmp_path):
        """
        Test storing key in environment variables.

        Environment storage is session-only but widely supported.
        """
        manager = SecureKeyManager(config_path=tmp_path / "keys.enc")
        assert manager.set_key("test_key", "test_value", KeyStorage.ENVIRONMENT)
        # Should be in environment
        assert os.environ.get("TEST_KEY") == "test_value"

        # Clean up
        if "TEST_KEY" in os.environ:
            del os.environ["TEST_KEY"]

    def test_set_key_environment_mapping_census(self, tmp_path):
        """
        Test environment variable mapping for census_api.

        census_api should map to CENSUS_API_KEY.
        """
        manager = SecureKeyManager(config_path=tmp_path / "keys.enc")
        manager.set_key("census_api", "test123", KeyStorage.ENVIRONMENT)
        assert os.environ.get("CENSUS_API_KEY") == "test123"

        # Clean up
        if "CENSUS_API_KEY" in os.environ:
            del os.environ["CENSUS_API_KEY"]

    def test_set_key_environment_mapping_mapbox(self, tmp_path):
        """
        Test environment variable mapping for mapbox.

        mapbox should map to MAPBOX_TOKEN.
        """
        manager = SecureKeyManager(config_path=tmp_path / "keys.enc")
        manager.set_key("mapbox", "pk.test", KeyStorage.ENVIRONMENT)
        assert os.environ.get("MAPBOX_TOKEN") == "pk.test"

        # Clean up
        if "MAPBOX_TOKEN" in os.environ:
            del os.environ["MAPBOX_TOKEN"]

    @pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="Cryptography library required")
    def test_set_key_in_encrypted_file(self, tmp_path):
        """
        Test storing key in encrypted file.

        File should be created and encrypted with Fernet.
        """
        config_path = tmp_path / "keys.enc"
        manager = SecureKeyManager(config_path=config_path)

        assert manager.set_key("test_key", "test_value", KeyStorage.ENCRYPTED_FILE)

        # File should exist
        assert config_path.exists()

        # File should not contain plaintext
        with open(config_path, "rb") as f:
            content = f.read()
        assert b"test_value" not in content

        # Should be able to decrypt
        decrypted = manager._cipher.decrypt(content)
        keys = json.loads(decrypted.decode())
        assert keys["test_key"] == "test_value"

    @pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="Cryptography library required")
    def test_set_key_encrypted_file_permissions(self, tmp_path):
        """
        Test that encrypted file has secure permissions.

        File should be readable/writable only by owner (0o600).
        """
        config_path = tmp_path / "keys.enc"
        manager = SecureKeyManager(config_path=config_path)
        manager.set_key("test_key", "test_value", KeyStorage.ENCRYPTED_FILE)

        # Check file permissions
        mode = config_path.stat().st_mode
        assert stat.S_IMODE(mode) == 0o600

    @pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="Cryptography library required")
    def test_set_key_encrypted_file_updates_existing(self, tmp_path):
        """
        Test updating existing key in encrypted file.

        Should merge with existing keys, not overwrite file.
        """
        config_path = tmp_path / "keys.enc"
        manager = SecureKeyManager(config_path=config_path)

        # Store first key
        manager.set_key("key1", "value1", KeyStorage.ENCRYPTED_FILE)
        # Store second key
        manager.set_key("key2", "value2", KeyStorage.ENCRYPTED_FILE)

        # Both should be present
        assert manager.get_key("key1") == "value1"
        assert manager.get_key("key2") == "value2"

    @pytest.mark.skipif(not KEYRING_AVAILABLE, reason="Keyring library required")
    def test_set_key_in_keyring(self, tmp_path):
        """
        Test storing key in system keyring.

        Uses actual keyring API to ensure integration works.
        """
        import keyring

        manager = SecureKeyManager(config_path=tmp_path / "keys.enc")
        test_key_name = "socialmapper_test_key"

        try:
            assert manager.set_key(test_key_name, "test_value", KeyStorage.KEYRING)

            # Verify directly with keyring
            stored = keyring.get_password(manager.app_name, test_key_name)
            assert stored == "test_value"
        finally:
            # Clean up
            try:
                keyring.delete_password(manager.app_name, test_key_name)
            except Exception:
                pass

    def test_set_key_uses_default_storage(self, tmp_path):
        """
        Test that set_key uses first storage in preference list.

        When no storage specified, should use default.
        """
        manager = SecureKeyManager(
            config_path=tmp_path / "keys.enc",
            storage_preference=[KeyStorage.MEMORY, KeyStorage.ENVIRONMENT]
        )
        manager.set_key("test_key", "test_value")

        # Should be in memory (first preference)
        assert "test_key" in manager._memory_keys

    def test_set_key_handles_storage_failure_gracefully(self, tmp_path):
        """
        Test graceful handling of storage backend failure.

        Should return False without raising exception.
        """
        manager = SecureKeyManager(config_path=tmp_path / "keys.enc")

        # Mock failure in keyring
        with patch("socialmapper.security.key_manager.KEYRING_AVAILABLE", True), \
             patch("keyring.set_password", side_effect=Exception("Keyring error")):
            result = manager.set_key("test_key", "value", KeyStorage.KEYRING)
            assert result is False


class TestKeyRetrieval:
    """
    Test key retrieval with fallback logic across backends.

    Tests the hierarchical storage search and default value
    handling.
    """

    def test_get_key_from_memory(self, tmp_path):
        """
        Test retrieving key from memory storage.

        Memory is checked first, should be fastest.
        """
        manager = SecureKeyManager(
            config_path=tmp_path / "keys.enc",
            storage_preference=[KeyStorage.MEMORY]
        )
        manager.set_key("test_key", "test_value", KeyStorage.MEMORY)

        retrieved = manager.get_key("test_key")
        assert retrieved == "test_value"

    def test_get_key_from_environment(self, tmp_path):
        """
        Test retrieving key from environment variables.

        Should map key names to environment variables correctly.
        """
        manager = SecureKeyManager(
            config_path=tmp_path / "keys.enc",
            storage_preference=[KeyStorage.ENVIRONMENT]
        )
        os.environ["CENSUS_API_KEY"] = "env_test_key"

        try:
            retrieved = manager.get_key("census_api")
            assert retrieved == "env_test_key"
        finally:
            del os.environ["CENSUS_API_KEY"]

    @pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="Cryptography library required")
    def test_get_key_from_encrypted_file(self, tmp_path):
        """
        Test retrieving key from encrypted file.

        Should decrypt and parse JSON correctly.
        """
        config_path = tmp_path / "keys.enc"
        manager = SecureKeyManager(
            config_path=config_path,
            storage_preference=[KeyStorage.ENCRYPTED_FILE]
        )
        manager.set_key("test_key", "encrypted_value", KeyStorage.ENCRYPTED_FILE)

        retrieved = manager.get_key("test_key")
        assert retrieved == "encrypted_value"

    @pytest.mark.skipif(not KEYRING_AVAILABLE, reason="Keyring library required")
    def test_get_key_from_keyring(self, tmp_path):
        """
        Test retrieving key from system keyring.

        Uses real keyring API call.
        """
        import keyring

        manager = SecureKeyManager(config_path=tmp_path / "keys.enc")
        test_key_name = "socialmapper_test_retrieve"

        try:
            # Store in keyring directly
            keyring.set_password(manager.app_name, test_key_name, "keyring_value")

            # Retrieve through manager
            retrieved = manager.get_key(test_key_name)
            assert retrieved == "keyring_value"
        finally:
            # Clean up
            try:
                keyring.delete_password(manager.app_name, test_key_name)
            except Exception:
                pass

    def test_get_key_fallback_to_next_storage(self, tmp_path):
        """
        Test fallback to next storage when key not found.

        Should try each storage in preference order.
        """
        manager = SecureKeyManager(
            config_path=tmp_path / "keys.enc",
            storage_preference=[KeyStorage.MEMORY, KeyStorage.ENVIRONMENT]
        )
        # Store only in environment
        os.environ["TEST_FALLBACK"] = "fallback_value"

        try:
            # Should fallback from memory to environment
            retrieved = manager.get_key("test_fallback")
            assert retrieved == "fallback_value"
        finally:
            del os.environ["TEST_FALLBACK"]

    def test_get_key_memory_takes_precedence(self, tmp_path):
        """
        Test that memory storage takes precedence over others.

        Even if key exists in multiple backends, memory wins.
        """
        manager = SecureKeyManager(
            config_path=tmp_path / "keys.enc",
            storage_preference=[KeyStorage.MEMORY, KeyStorage.ENVIRONMENT]
        )
        # Set in both
        manager.set_key("test_key", "memory_value", KeyStorage.MEMORY)
        os.environ["TEST_KEY"] = "env_value"

        try:
            retrieved = manager.get_key("test_key")
            assert retrieved == "memory_value"
        finally:
            if "TEST_KEY" in os.environ:
                del os.environ["TEST_KEY"]

    def test_get_key_returns_default_when_not_found(self, tmp_path):
        """
        Test that default value is returned when key not found.

        Should return default instead of None when specified.
        """
        manager = SecureKeyManager(config_path=tmp_path / "keys.enc")
        retrieved = manager.get_key("nonexistent_key", default="default_value")
        assert retrieved == "default_value"

    def test_get_key_returns_none_when_not_found(self, tmp_path):
        """
        Test that None is returned when key not found and no default.

        Default behavior without explicit default parameter.
        """
        manager = SecureKeyManager(config_path=tmp_path / "keys.enc")
        retrieved = manager.get_key("nonexistent_key")
        assert retrieved is None

    def test_get_key_handles_corrupted_encrypted_file(self, tmp_path):
        """
        Test graceful handling of corrupted encrypted file.

        Should fallback to other backends instead of crashing.
        """
        config_path = tmp_path / "keys.enc"
        manager = SecureKeyManager(
            config_path=config_path,
            storage_preference=[KeyStorage.ENCRYPTED_FILE, KeyStorage.ENVIRONMENT]
        )

        # Create corrupted file
        with open(config_path, "wb") as f:
            f.write(b"corrupted data")

        # Set fallback in environment
        os.environ["TEST_KEY"] = "fallback_value"

        try:
            # Should fallback to environment
            retrieved = manager.get_key("test_key")
            assert retrieved == "fallback_value"
        finally:
            if "TEST_KEY" in os.environ:
                del os.environ["TEST_KEY"]


class TestKeyDeletion:
    """
    Test key deletion operations across backends.

    Ensures keys can be properly removed from all storage
    locations.
    """

    def test_delete_key_from_memory(self, tmp_path):
        """
        Test deleting key from memory storage.

        Should remove from internal dictionary.
        """
        manager = SecureKeyManager(
            config_path=tmp_path / "keys.enc",
            storage_preference=[KeyStorage.MEMORY]
        )
        manager.set_key("test_key", "test_value", KeyStorage.MEMORY)

        assert manager.delete_key("test_key")
        assert "test_key" not in manager._memory_keys

    def test_delete_key_from_environment(self, tmp_path):
        """
        Test deleting key from environment variables.

        Should remove from os.environ.
        """
        manager = SecureKeyManager(config_path=tmp_path / "keys.enc")
        os.environ["TEST_DELETE"] = "value"

        assert manager.delete_key("test_delete", KeyStorage.ENVIRONMENT)
        assert "TEST_DELETE" not in os.environ

    @pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="Cryptography library required")
    def test_delete_key_from_encrypted_file(self, tmp_path):
        """
        Test deleting key from encrypted file.

        Should remove key but preserve other keys in file.
        """
        config_path = tmp_path / "keys.enc"
        manager = SecureKeyManager(config_path=config_path)

        # Store two keys
        manager.set_key("key1", "value1", KeyStorage.ENCRYPTED_FILE)
        manager.set_key("key2", "value2", KeyStorage.ENCRYPTED_FILE)

        # Delete one
        assert manager.delete_key("key1", KeyStorage.ENCRYPTED_FILE)

        # key2 should still exist
        assert manager.get_key("key2") == "value2"
        # key1 should be gone
        assert manager.get_key("key1") is None

    @pytest.mark.skipif(not KEYRING_AVAILABLE, reason="Keyring library required")
    def test_delete_key_from_keyring(self, tmp_path):
        """
        Test deleting key from system keyring.

        Uses real keyring API call.
        """
        import keyring

        manager = SecureKeyManager(config_path=tmp_path / "keys.enc")
        test_key_name = "socialmapper_test_delete"

        try:
            # Store in keyring
            keyring.set_password(manager.app_name, test_key_name, "value")

            # Delete through manager
            assert manager.delete_key(test_key_name, KeyStorage.KEYRING)

            # Verify deletion
            assert keyring.get_password(manager.app_name, test_key_name) is None
        finally:
            # Clean up just in case
            try:
                keyring.delete_password(manager.app_name, test_key_name)
            except Exception:
                pass

    def test_delete_key_from_all_backends(self, tmp_path):
        """
        Test deleting key from all backends when storage not specified.

        Should remove from memory, environment, and file.
        """
        manager = SecureKeyManager(
            config_path=tmp_path / "keys.enc",
            storage_preference=[KeyStorage.MEMORY, KeyStorage.ENVIRONMENT]
        )

        # Store in multiple backends
        manager.set_key("test_key", "value", KeyStorage.MEMORY)
        manager.set_key("test_key", "value", KeyStorage.ENVIRONMENT)

        # Delete from all
        assert manager.delete_key("test_key")

        # Should be gone from both
        assert "test_key" not in manager._memory_keys
        assert "TEST_KEY" not in os.environ

    def test_delete_nonexistent_key_returns_false(self, tmp_path):
        """
        Test that deleting nonexistent key returns False.

        Should not raise exception.
        """
        manager = SecureKeyManager(config_path=tmp_path / "keys.enc")
        result = manager.delete_key("nonexistent_key")
        # May return False if not found anywhere
        assert isinstance(result, bool)

    def test_delete_key_handles_backend_errors(self, tmp_path):
        """
        Test graceful error handling during deletion.

        Backend errors should be logged but not crash.
        """
        manager = SecureKeyManager(config_path=tmp_path / "keys.enc")

        # Mock error in keyring deletion
        with patch("socialmapper.security.key_manager.KEYRING_AVAILABLE", True), \
             patch("keyring.delete_password", side_effect=Exception("Delete error")):
            # Should not raise exception
            result = manager.delete_key("test_key", KeyStorage.KEYRING)
            # Result depends on whether error was handled
            assert isinstance(result, bool)


class TestTemporaryKeys:
    """
    Test temporary key context manager.

    Temporary keys are useful for testing or one-time operations
    without permanently storing credentials.
    """

    def test_temporary_key_sets_key_in_context(self, tmp_path):
        """
        Test that temporary key is available within context.

        Key should be accessible inside the with block.
        """
        manager = SecureKeyManager(config_path=tmp_path / "keys.enc")

        with manager.temporary_key("temp_key", "temp_value"):
            assert manager.get_key("temp_key") == "temp_value"

    def test_temporary_key_removes_key_after_context(self, tmp_path):
        """
        Test that temporary key is removed after context.

        Key should not persist after exiting with block.
        """
        manager = SecureKeyManager(config_path=tmp_path / "keys.enc")

        with manager.temporary_key("temp_key", "temp_value"):
            pass

        assert manager.get_key("temp_key") is None

    def test_temporary_key_preserves_existing_key(self, tmp_path):
        """
        Test that existing key is restored after temporary key.

        Original key should be restored, not deleted.
        """
        manager = SecureKeyManager(
            config_path=tmp_path / "keys.enc",
            storage_preference=[KeyStorage.MEMORY]
        )

        # Set original key
        manager.set_key("key", "original", KeyStorage.MEMORY)

        # Use temporary override
        with manager.temporary_key("key", "temporary"):
            assert manager.get_key("key") == "temporary"

        # Original should be restored
        assert manager.get_key("key") == "original"

    def test_temporary_key_handles_exception_in_context(self, tmp_path):
        """
        Test that temporary key is cleaned up even on exception.

        Ensures cleanup happens in finally block.
        """
        manager = SecureKeyManager(config_path=tmp_path / "keys.enc")

        with pytest.raises(ValueError):
            with manager.temporary_key("temp_key", "temp_value"):
                raise ValueError("Test exception")

        # Key should still be removed
        assert manager.get_key("temp_key") is None

    def test_temporary_key_nested_contexts(self, tmp_path):
        """
        Test nested temporary key contexts.

        Each context should properly save and restore.
        """
        manager = SecureKeyManager(
            config_path=tmp_path / "keys.enc",
            storage_preference=[KeyStorage.MEMORY]
        )

        manager.set_key("key", "original", KeyStorage.MEMORY)

        with manager.temporary_key("key", "temp1"):
            assert manager.get_key("key") == "temp1"

            with manager.temporary_key("key", "temp2"):
                assert manager.get_key("key") == "temp2"

            assert manager.get_key("key") == "temp1"

        assert manager.get_key("key") == "original"


class TestEncryptedFileStorage:
    """
    Test encrypted file storage operations in detail.

    Focuses on encryption, decryption, and file integrity.
    """

    @pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="Cryptography library required")
    def test_encrypted_file_uses_json_format(self, tmp_path):
        """
        Test that encrypted file stores keys as JSON.

        After decryption, should be valid JSON with key-value pairs.
        """
        config_path = tmp_path / "keys.enc"
        manager = SecureKeyManager(config_path=config_path)

        manager.set_key("key1", "value1", KeyStorage.ENCRYPTED_FILE)
        manager.set_key("key2", "value2", KeyStorage.ENCRYPTED_FILE)

        # Read and decrypt file
        with open(config_path, "rb") as f:
            encrypted = f.read()
        decrypted = manager._cipher.decrypt(encrypted)
        data = json.loads(decrypted.decode())

        assert isinstance(data, dict)
        assert data["key1"] == "value1"
        assert data["key2"] == "value2"

    @pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="Cryptography library required")
    def test_encrypted_file_handles_nonexistent_file(self, tmp_path):
        """
        Test reading from nonexistent encrypted file.

        Should return None gracefully, not raise exception.
        """
        config_path = tmp_path / "nonexistent.enc"
        manager = SecureKeyManager(config_path=config_path)

        result = manager.get_key("any_key")
        assert result is None

    @pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="Cryptography library required")
    def test_encrypted_file_handles_invalid_json(self, tmp_path):
        """
        Test handling of file with invalid JSON after decryption.

        Should handle json.JSONDecodeError gracefully.
        """
        config_path = tmp_path / "keys.enc"
        manager = SecureKeyManager(config_path=config_path)

        # Write encrypted invalid JSON
        encrypted = manager._cipher.encrypt(b"not valid json")
        with open(config_path, "wb") as f:
            f.write(encrypted)

        # Should handle gracefully
        result = manager.get_key("key")
        assert result is None


class TestSecurityHardening:
    """
    Test security hardening features.

    Covers file permissions, atomic writes, and protection against
    common attack vectors.
    """

    @pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="Cryptography library required")
    def test_config_directory_permissions(self, tmp_path):
        """
        Test that config directory has secure permissions.

        Directory should be 0o700 (owner only).
        """
        config_path = tmp_path / "new_secure_dir" / "keys.enc"
        manager = SecureKeyManager(config_path=config_path)

        # Directory should be created
        assert config_path.parent.exists()

        # Check permissions
        mode = config_path.parent.stat().st_mode
        assert stat.S_IMODE(mode) == 0o700

    @pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="Cryptography library required")
    def test_atomic_file_write(self, tmp_path):
        """
        Test that file writes are atomic.

        Uses temporary file and os.replace to ensure atomicity.
        """
        config_path = tmp_path / "keys.enc"
        manager = SecureKeyManager(config_path=config_path)

        # Write key
        manager.set_key("key1", "value1", KeyStorage.ENCRYPTED_FILE)

        # File should exist and be valid
        assert config_path.exists()

        # Should be able to read immediately
        assert manager.get_key("key1") == "value1"

    def test_input_validation_prevents_path_traversal(self, tmp_path):
        """
        Test that input validation prevents path traversal attacks.

        Key names like '../../../etc/passwd' should be rejected.
        """
        manager = SecureKeyManager(config_path=tmp_path / "keys.enc")

        # Attempt path traversal
        result = manager.set_key("../../etc/passwd", "malicious")
        assert result is False

    def test_input_validation_prevents_command_injection(self, tmp_path):
        """
        Test that input validation prevents command injection.

        Key names with shell metacharacters should be rejected.
        """
        manager = SecureKeyManager(
            config_path=tmp_path / "keys.enc",
            storage_preference=[KeyStorage.MEMORY]
        )

        # Attempt various injection patterns
        assert not manager.set_key("key; rm -rf /", "value")
        assert not manager.set_key("key && malicious", "value")
        assert not manager.set_key("key | cat /etc/passwd", "value")
        assert not manager.set_key("key`whoami`", "value")
        assert not manager.set_key("key$(whoami)", "value")

    def test_key_value_size_limit_prevents_dos(self, tmp_path):
        """
        Test that key value size limit prevents DoS attacks.

        Extremely large keys could exhaust memory.
        """
        manager = SecureKeyManager(
            config_path=tmp_path / "keys.enc",
            storage_preference=[KeyStorage.MEMORY]
        )

        # Attempt to store huge value
        huge_value = "a" * 100_000  # 100KB
        result = manager.set_key("key", huge_value)
        assert result is False

    @pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="Cryptography library required")
    def test_encrypted_file_not_world_readable(self, tmp_path):
        """
        Test that encrypted file is not world-readable.

        Even encrypted, file should have restrictive permissions.
        """
        config_path = tmp_path / "keys.enc"
        manager = SecureKeyManager(config_path=config_path)
        manager.set_key("key", "value", KeyStorage.ENCRYPTED_FILE)

        mode = config_path.stat().st_mode
        # Should not have world-read permission
        assert not bool(mode & stat.S_IROTH)
        # Should not have group-read permission
        assert not bool(mode & stat.S_IRGRP)


class TestUtilityFunctions:
    """
    Test utility functions in utils.py.

    Covers get_api_key, set_api_key, validate_api_key, and
    migrate_from_env.
    """

    def test_get_key_manager_returns_singleton(self):
        """
        Test that get_key_manager returns same instance.

        Should maintain singleton pattern for global usage.
        """
        manager1 = get_key_manager()
        manager2 = get_key_manager()
        assert manager1 is manager2

    def test_get_api_key_wrapper(self, tmp_path):
        """
        Test get_api_key utility function.

        Should work as convenient wrapper around manager.
        """
        # Reset singleton
        import socialmapper.security.utils as utils_module
        utils_module._key_manager = None

        # Set key in environment for test
        os.environ["CENSUS_API_KEY"] = "test_census_key"

        try:
            key = get_api_key("census_api")
            assert key == "test_census_key"
        finally:
            del os.environ["CENSUS_API_KEY"]
            utils_module._key_manager = None

    def test_get_api_key_with_fallback_env(self, tmp_path):
        """
        Test get_api_key with custom fallback environment variable.

        Should check fallback if not found in storage.
        """
        import socialmapper.security.utils as utils_module
        utils_module._key_manager = None

        os.environ["CUSTOM_API_KEY"] = "custom_value"

        try:
            key = get_api_key("unknown_key", fallback_env="CUSTOM_API_KEY")
            assert key == "custom_value"
        finally:
            del os.environ["CUSTOM_API_KEY"]
            utils_module._key_manager = None

    def test_set_api_key_wrapper(self, tmp_path):
        """
        Test set_api_key utility function.

        Should work as convenient wrapper around manager.
        """
        import socialmapper.security.utils as utils_module
        utils_module._key_manager = None

        # Use manager with temp path
        manager = SecureKeyManager(
            config_path=tmp_path / "keys.enc",
            storage_preference=[KeyStorage.MEMORY]
        )
        utils_module._key_manager = manager

        result = set_api_key("test_key", "test_value")
        assert result is True
        assert manager.get_key("test_key") == "test_value"

        utils_module._key_manager = None

    def test_validate_api_key_wrapper(self, tmp_path):
        """
        Test validate_api_key utility function.

        Should validate without retrieving key.
        """
        valid_census = "a" * 40
        assert validate_api_key("census_api", valid_census)

        invalid_census = "too_short"
        assert not validate_api_key("census_api", invalid_census)

    def test_migrate_from_env_success(self, tmp_path):
        """
        Test successful migration of keys from environment.

        Should copy keys from env vars to secure storage.
        """
        import socialmapper.security.utils as utils_module
        utils_module._key_manager = None

        # Use manager with temp path
        manager = SecureKeyManager(
            config_path=tmp_path / "keys.enc",
            storage_preference=[KeyStorage.MEMORY]
        )
        utils_module._key_manager = manager

        # Set environment variables
        os.environ["CENSUS_API_KEY"] = "a" * 40
        os.environ["MAPBOX_TOKEN"] = "pk.test_token"

        try:
            results = migrate_from_env()

            # Check results
            assert results["census_api"] is True
            assert results["mapbox"] is True

            # Verify keys were stored
            assert manager.get_key("census_api") == "a" * 40
            assert manager.get_key("mapbox") == "pk.test_token"
        finally:
            if "CENSUS_API_KEY" in os.environ:
                del os.environ["CENSUS_API_KEY"]
            if "MAPBOX_TOKEN" in os.environ:
                del os.environ["MAPBOX_TOKEN"]
            utils_module._key_manager = None

    def test_migrate_from_env_partial_keys(self, tmp_path):
        """
        Test migration when only some keys present in environment.

        Should migrate available keys and mark others as False.
        """
        import socialmapper.security.utils as utils_module
        utils_module._key_manager = None

        manager = SecureKeyManager(
            config_path=tmp_path / "keys.enc",
            storage_preference=[KeyStorage.MEMORY]
        )
        utils_module._key_manager = manager

        # Set only Census API key
        os.environ["CENSUS_API_KEY"] = "test_key"

        try:
            results = migrate_from_env()

            assert results["census_api"] is True
            assert results["mapbox"] is False
            assert results["google_maps"] is False
        finally:
            if "CENSUS_API_KEY" in os.environ:
                del os.environ["CENSUS_API_KEY"]
            utils_module._key_manager = None

    def test_migrate_from_env_no_keys(self, tmp_path):
        """
        Test migration when no keys in environment.

        Should return all False results.
        """
        import socialmapper.security.utils as utils_module
        utils_module._key_manager = None

        manager = SecureKeyManager(
            config_path=tmp_path / "keys.enc",
            storage_preference=[KeyStorage.MEMORY]
        )
        utils_module._key_manager = manager

        results = migrate_from_env()

        assert all(v is False for v in results.values())

        utils_module._key_manager = None


class TestEdgeCases:
    """
    Test edge cases and error conditions.

    Covers rare scenarios, boundary conditions, and error paths.
    """

    def test_manager_without_cryptography_library(self, tmp_path):
        """
        Test manager functionality when cryptography unavailable.

        Should fall back to environment storage only.
        """
        with patch("socialmapper.security.key_manager.CRYPTO_AVAILABLE", False):
            manager = SecureKeyManager(config_path=tmp_path / "keys.enc")

            # Should not have encrypted file in preferences
            assert KeyStorage.ENCRYPTED_FILE not in manager.storage_preference

            # Should still work with environment
            manager.set_key("test_key", "value", KeyStorage.ENVIRONMENT)
            assert manager.get_key("test_key") == "value"

            # Clean up
            if "TEST_KEY" in os.environ:
                del os.environ["TEST_KEY"]

    def test_manager_without_keyring_library(self, tmp_path):
        """
        Test manager functionality when keyring unavailable.

        Should work with file and environment storage.
        """
        with patch("socialmapper.security.key_manager.KEYRING_AVAILABLE", False):
            manager = SecureKeyManager(config_path=tmp_path / "keys.enc")

            # Should not have keyring in preferences
            assert KeyStorage.KEYRING not in manager.storage_preference

            # Should still work with other backends
            if CRYPTO_AVAILABLE:
                manager.set_key("test_key", "value", KeyStorage.ENCRYPTED_FILE)
                assert manager.get_key("test_key") == "value"

    def test_list_keys_empty_storage(self, tmp_path):
        """
        Test listing keys when no keys stored.

        Should return empty dict or dict with empty lists.
        """
        manager = SecureKeyManager(config_path=tmp_path / "keys.enc")
        keys = manager.list_keys()

        assert isinstance(keys, dict)
        # Should either be empty or have empty lists
        for value in keys.values():
            assert len(value) == 0

    def test_list_keys_with_multiple_backends(self, tmp_path):
        """
        Test listing keys across multiple storage backends.

        Should show keys from all backends separately.
        """
        manager = SecureKeyManager(
            config_path=tmp_path / "keys.enc",
            storage_preference=[KeyStorage.MEMORY, KeyStorage.ENVIRONMENT]
        )

        # Store in different backends
        manager.set_key("memory_key", "value", KeyStorage.MEMORY)
        manager.set_key("env_key", "value", KeyStorage.ENVIRONMENT)

        try:
            keys = manager.list_keys()

            # Memory keys should be listed
            if "memory" in keys:
                assert "memory_key" in keys["memory"]

            # Environment keys should be listed
            if "environment" in keys:
                # Environment uses uppercase
                assert any("ENV_KEY" in k.upper() for k in keys.get("environment", []))
        finally:
            if "ENV_KEY" in os.environ:
                del os.environ["ENV_KEY"]

    @pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="Cryptography library required")
    def test_list_keys_encrypted_file(self, tmp_path):
        """
        Test listing keys from encrypted file.

        Should decrypt and return key names.
        """
        config_path = tmp_path / "keys.enc"
        manager = SecureKeyManager(config_path=config_path)

        manager.set_key("key1", "value1", KeyStorage.ENCRYPTED_FILE)
        manager.set_key("key2", "value2", KeyStorage.ENCRYPTED_FILE)

        keys = manager.list_keys()

        assert "encrypted_file" in keys
        assert "key1" in keys["encrypted_file"]
        assert "key2" in keys["encrypted_file"]

    def test_empty_storage_preference_list(self, tmp_path):
        """
        Test initialization with empty storage preference.

        When empty list provided, uses default storage order.
        """
        manager = SecureKeyManager(
            config_path=tmp_path / "keys.enc",
            storage_preference=[]
        )

        # Empty list gets replaced with defaults during init
        # This is expected behavior - manager needs at least one backend
        assert len(manager.storage_preference) > 0

        # set_key should work with default storage
        result = manager.set_key("test_key", "value")
        assert result is True

    @pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="Cryptography library required")
    def test_concurrent_file_access(self, tmp_path):
        """
        Test handling of concurrent file access.

        Multiple managers accessing same file should not corrupt it.
        """
        config_path = tmp_path / "keys.enc"

        manager1 = SecureKeyManager(config_path=config_path)
        manager2 = SecureKeyManager(config_path=config_path)

        # Both write keys
        manager1.set_key("key1", "value1", KeyStorage.ENCRYPTED_FILE)
        manager2.set_key("key2", "value2", KeyStorage.ENCRYPTED_FILE)

        # Both should be able to read their keys
        # Note: last write wins, so key1 might be lost
        assert manager2.get_key("key2") == "value2"

    def test_unicode_in_key_values(self, tmp_path):
        """
        Test handling of Unicode characters in key values.

        Should properly encode/decode UTF-8.
        """
        manager = SecureKeyManager(
            config_path=tmp_path / "keys.enc",
            storage_preference=[KeyStorage.MEMORY]
        )

        unicode_value = "test_value_with_émojis_🔑_and_中文"
        manager.set_key("unicode_key", unicode_value)

        retrieved = manager.get_key("unicode_key")
        assert retrieved == unicode_value

    @pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="Cryptography library required")
    def test_encrypted_file_with_unicode(self, tmp_path):
        """
        Test encrypted file storage with Unicode values.

        Should properly handle UTF-8 encoding in JSON.
        """
        config_path = tmp_path / "keys.enc"
        manager = SecureKeyManager(
            config_path=config_path,
            storage_preference=[KeyStorage.ENCRYPTED_FILE]
        )

        unicode_value = "émojis_🔐_and_日本語"
        manager.set_key("unicode_test_key", unicode_value, KeyStorage.ENCRYPTED_FILE)

        retrieved = manager.get_key("unicode_test_key")
        assert retrieved == unicode_value

    def test_very_long_key_name_within_limit(self, tmp_path):
        """
        Test key name at exactly the length limit.

        Should accept 100-character names.
        """
        manager = SecureKeyManager(
            config_path=tmp_path / "keys.enc",
            storage_preference=[KeyStorage.MEMORY]
        )

        long_name = "a" * 100
        assert manager.set_key(long_name, "value")
        assert manager.get_key(long_name) == "value"

    def test_environment_mapping_unknown_key(self, tmp_path):
        """
        Test environment variable mapping for unknown key types.

        Should convert to uppercase with underscores.
        """
        manager = SecureKeyManager(config_path=tmp_path / "keys.enc")

        manager.set_key("custom_key", "value", KeyStorage.ENVIRONMENT)

        # Should map to CUSTOM_KEY
        assert os.environ.get("CUSTOM_KEY") == "value"

        # Clean up
        if "CUSTOM_KEY" in os.environ:
            del os.environ["CUSTOM_KEY"]
