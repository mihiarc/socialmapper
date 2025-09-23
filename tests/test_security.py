"""Tests for secure API key management."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from socialmapper.security import SecureKeyManager, KeyStorage
from socialmapper.security.utils import (
    get_api_key,
    set_api_key,
    validate_api_key,
    migrate_from_env,
)


class TestSecureKeyManager:
    """Test SecureKeyManager class."""

    def test_initialization(self):
        """Test key manager initialization."""
        manager = SecureKeyManager()

        assert manager.app_name == "socialmapper"
        assert manager.config_path.name == "keys.enc"
        assert isinstance(manager.storage_preference, list)

    def test_memory_storage(self):
        """Test in-memory key storage."""
        manager = SecureKeyManager()

        # Set key in memory
        assert manager.set_key("test_key", "test_value", KeyStorage.MEMORY)

        # Retrieve key from memory
        assert manager.get_key("test_key") == "test_value"

        # Delete key from memory
        assert manager.delete_key("test_key", KeyStorage.MEMORY)
        assert manager.get_key("test_key") is None

    def test_environment_storage(self):
        """Test environment variable storage."""
        manager = SecureKeyManager()

        # Set key in environment
        assert manager.set_key("census_api", "test_api_key", KeyStorage.ENVIRONMENT)
        assert os.getenv("CENSUS_API_KEY") == "test_api_key"

        # Retrieve key from environment
        assert manager.get_key("census_api") == "test_api_key"

        # Delete key from environment
        assert manager.delete_key("census_api", KeyStorage.ENVIRONMENT)
        assert os.getenv("CENSUS_API_KEY") is None

    def test_encrypted_file_storage(self):
        """Test encrypted file storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "keys.enc"
            manager = SecureKeyManager(config_path=config_path)

            # Skip if cryptography not available
            try:
                from cryptography.fernet import Fernet
            except ImportError:
                pytest.skip("cryptography not available")

            # Set key in encrypted file
            assert manager.set_key("test_key", "test_value", KeyStorage.ENCRYPTED_FILE)

            # Retrieve key from encrypted file
            assert manager.get_key("test_key") == "test_value"

            # Verify file is encrypted
            assert config_path.exists()
            with open(config_path, 'rb') as f:
                data = f.read()
                # Should not contain plain text
                assert b"test_value" not in data

            # Delete key from encrypted file
            assert manager.delete_key("test_key", KeyStorage.ENCRYPTED_FILE)
            assert manager.get_key("test_key") is None

    def test_temporary_key_context_manager(self):
        """Test temporary key context manager."""
        manager = SecureKeyManager()

        # Set a permanent key
        manager.set_key("test_key", "permanent_value", KeyStorage.MEMORY)

        # Use temporary key
        with manager.temporary_key("test_key", "temporary_value"):
            assert manager.get_key("test_key") == "temporary_value"

        # Should revert to permanent key
        assert manager.get_key("test_key") == "permanent_value"

        # Test with new key
        with manager.temporary_key("new_key", "temp_value"):
            assert manager.get_key("new_key") == "temp_value"

        # Should be removed after context
        assert manager.get_key("new_key") is None

    def test_key_validation(self):
        """Test API key validation."""
        manager = SecureKeyManager()

        # Test Census API key validation
        valid_census_key = "a" * 40
        invalid_census_key = "a" * 39

        assert manager.validate_key("census_api", valid_census_key)
        assert not manager.validate_key("census_api", invalid_census_key)

        # Test Mapbox token validation
        valid_mapbox = "pk.test_token_here"
        invalid_mapbox = "invalid_token"

        assert manager.validate_key("mapbox", valid_mapbox)
        assert not manager.validate_key("mapbox", invalid_mapbox)

        # Test generic validation
        assert manager.validate_key("custom_key", "valid_key")
        assert not manager.validate_key("custom_key", "")
        assert not manager.validate_key("custom_key", "key with spaces")

    def test_list_keys(self):
        """Test listing keys from all backends."""
        manager = SecureKeyManager()

        # Add keys to different backends
        manager.set_key("memory_key", "value1", KeyStorage.MEMORY)
        manager.set_key("env_key", "value2", KeyStorage.ENVIRONMENT)

        keys = manager.list_keys()

        assert "memory" in keys
        assert "memory_key" in keys["memory"]

        # Clean up
        manager.delete_key("memory_key", KeyStorage.MEMORY)
        manager.delete_key("env_key", KeyStorage.ENVIRONMENT)


class TestSecurityUtils:
    """Test security utility functions."""

    def test_get_api_key(self):
        """Test get_api_key utility function."""
        # Test with environment variable
        with patch.dict(os.environ, {"CENSUS_API_KEY": "test_key"}):
            key = get_api_key("census_api", "CENSUS_API_KEY")
            assert key == "test_key"

        # Test with missing key
        key = get_api_key("nonexistent_key")
        assert key is None

    def test_set_api_key(self):
        """Test set_api_key utility function."""
        # Set key
        assert set_api_key("test_key", "test_value", KeyStorage.MEMORY)

        # Verify key was set
        from socialmapper.security.utils import get_key_manager
        manager = get_key_manager()
        assert manager.get_key("test_key") == "test_value"

        # Clean up
        manager.delete_key("test_key", KeyStorage.MEMORY)

    def test_validate_api_key(self):
        """Test validate_api_key utility function."""
        # Test with valid key
        valid_census_key = "a" * 40
        assert validate_api_key("census_api", valid_census_key)

        # Test with invalid key
        invalid_key = "short"
        assert not validate_api_key("census_api", invalid_key)

    def test_migrate_from_env(self):
        """Test migrating keys from environment variables."""
        # Set up environment variables
        with patch.dict(os.environ, {
            "CENSUS_API_KEY": "test_census_key",
            "MAPBOX_TOKEN": "pk.test_mapbox_token"
        }):
            # Mock the key manager
            with patch("socialmapper.security.utils.get_key_manager") as mock_get_manager:
                mock_manager = MagicMock()
                mock_manager.set_key.return_value = True
                mock_get_manager.return_value = mock_manager

                # Run migration
                results = migrate_from_env()

                # Check results
                assert results["census_api"] is True
                assert results["mapbox"] is True

                # Verify set_key was called
                assert mock_manager.set_key.call_count >= 2


class TestKeyStorage:
    """Test KeyStorage enum."""

    def test_storage_enum(self):
        """Test KeyStorage enum values."""
        assert KeyStorage.ENVIRONMENT.value == "environment"
        assert KeyStorage.KEYRING.value == "keyring"
        assert KeyStorage.ENCRYPTED_FILE.value == "encrypted_file"
        assert KeyStorage.MEMORY.value == "memory"