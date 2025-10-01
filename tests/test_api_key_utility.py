"""Tests for the simplified API key management utility."""

import os
import pytest
from unittest.mock import patch, MagicMock

from socialmapper.utils.api_key import get_api_key, set_api_key, KEYRING_AVAILABLE


class TestGetApiKey:
    """Test get_api_key function with various scenarios."""

    def test_get_api_key_from_environment_census_api(self):
        """Test retrieving Census API key from environment variable."""
        with patch.dict(os.environ, {"CENSUS_API_KEY": "test_census_key_123"}, clear=False):
            result = get_api_key("census_api")
            assert result == "test_census_key_123"

    def test_get_api_key_from_environment_mapbox(self):
        """Test retrieving Mapbox token from environment variable."""
        with patch.dict(os.environ, {"MAPBOX_TOKEN": "test_mapbox_token_456"}, clear=False):
            result = get_api_key("mapbox")
            assert result == "test_mapbox_token_456"

    def test_get_api_key_environment_takes_priority(self):
        """Test that environment variable takes priority over keyring."""
        with patch.dict(os.environ, {"CENSUS_API_KEY": "env_key"}, clear=False):
            with patch("socialmapper.utils.api_key.keyring") as mock_keyring:
                mock_keyring.get_password.return_value = "keyring_key"

                result = get_api_key("census_api")
                assert result == "env_key"

                # Keyring should not be called when env var exists
                mock_keyring.get_password.assert_not_called()

    def test_get_api_key_fallback_to_keyring(self):
        """Test fallback to keyring when environment variable is missing."""
        # Clear the environment variable
        with patch.dict(os.environ, {}, clear=True):
            with patch("socialmapper.utils.api_key.keyring") as mock_keyring:
                mock_keyring.get_password.return_value = "keyring_api_key"

                result = get_api_key("census_api")
                assert result == "keyring_api_key"

                mock_keyring.get_password.assert_called_once_with("socialmapper", "census_api")

    def test_get_api_key_keyring_not_available(self):
        """Test behavior when keyring is not available."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("socialmapper.utils.api_key.KEYRING_AVAILABLE", False):
                result = get_api_key("census_api")
                assert result is None

    def test_get_api_key_keyring_exception(self):
        """Test handling of keyring exceptions."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("socialmapper.utils.api_key.keyring") as mock_keyring:
                mock_keyring.get_password.side_effect = Exception("Keyring error")

                result = get_api_key("census_api")
                assert result is None

    def test_get_api_key_keyring_returns_none(self):
        """Test when keyring returns None (key not found)."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("socialmapper.utils.api_key.keyring") as mock_keyring:
                mock_keyring.get_password.return_value = None

                result = get_api_key("census_api")
                assert result is None

    def test_get_api_key_custom_key_name(self):
        """Test with custom key name that maps to uppercase env var."""
        with patch.dict(os.environ, {"CUSTOM_API": "custom_value"}, clear=False):
            result = get_api_key("custom_api")
            assert result == "custom_value"

    def test_get_api_key_default_parameter(self):
        """Test default parameter value for key_name."""
        with patch.dict(os.environ, {"CENSUS_API_KEY": "default_test"}, clear=False):
            result = get_api_key()  # Should default to "census_api"
            assert result == "default_test"

    def test_get_api_key_empty_environment_value(self):
        """Test behavior when environment variable is empty string."""
        with patch.dict(os.environ, {"CENSUS_API_KEY": ""}, clear=False):
            with patch("socialmapper.utils.api_key.keyring") as mock_keyring:
                mock_keyring.get_password.return_value = "keyring_fallback"

                result = get_api_key("census_api")
                # Empty string should fallback to keyring
                assert result == "keyring_fallback"


class TestSetApiKey:
    """Test set_api_key function with various scenarios."""

    def test_set_api_key_with_keyring_success(self):
        """Test successful storage in keyring."""
        with patch("socialmapper.utils.api_key.keyring") as mock_keyring:
            mock_keyring.set_password.return_value = None  # Success

            result = set_api_key("census_api", "test_key_value")

            assert result is True
            mock_keyring.set_password.assert_called_once_with(
                "socialmapper", "census_api", "test_key_value"
            )

    def test_set_api_key_keyring_disabled(self):
        """Test when keyring usage is disabled."""
        result = set_api_key("census_api", "test_key", use_keyring=False)
        assert result is False

    def test_set_api_key_keyring_not_available(self):
        """Test when keyring is not available."""
        with patch("socialmapper.utils.api_key.KEYRING_AVAILABLE", False):
            result = set_api_key("census_api", "test_key")
            assert result is False

    def test_set_api_key_keyring_exception(self):
        """Test handling of keyring exceptions during storage."""
        with patch("socialmapper.utils.api_key.keyring") as mock_keyring:
            mock_keyring.set_password.side_effect = Exception("Storage failed")

            result = set_api_key("census_api", "test_key")
            assert result is False

    def test_set_api_key_mapbox_token(self):
        """Test storing Mapbox token."""
        with patch("socialmapper.utils.api_key.keyring") as mock_keyring:
            result = set_api_key("mapbox", "pk.test_token")

            assert result is True
            mock_keyring.set_password.assert_called_once_with(
                "socialmapper", "mapbox", "pk.test_token"
            )

    def test_set_api_key_logs_success(self, caplog):
        """Test that successful storage is logged."""
        import logging
        caplog.set_level(logging.INFO)
        with patch("socialmapper.utils.api_key.keyring") as mock_keyring:
            set_api_key("census_api", "test_key")

            assert "Stored census_api in system keyring" in caplog.text

    def test_set_api_key_logs_failure(self, caplog):
        """Test that storage failure is logged."""
        import logging
        caplog.set_level(logging.WARNING)
        with patch("socialmapper.utils.api_key.keyring") as mock_keyring:
            mock_keyring.set_password.side_effect = Exception("Test error")

            set_api_key("census_api", "test_key")

            assert "Could not store in keyring: Test error" in caplog.text

    def test_set_api_key_logs_environment_fallback(self, caplog):
        """Test that environment variable instruction is logged on fallback."""
        import logging
        caplog.set_level(logging.INFO)
        with patch("socialmapper.utils.api_key.KEYRING_AVAILABLE", False):
            set_api_key("census_api", "test_key_123")

            assert "Please set environment variable CENSUS_API_KEY=test_key_123" in caplog.text


class TestApiKeyIntegration:
    """Integration tests for API key management workflow."""

    def test_set_then_get_api_key_workflow(self):
        """Test complete workflow of setting and getting API key."""
        # Clear environment first
        with patch.dict(os.environ, {}, clear=True):
            with patch("socialmapper.utils.api_key.keyring") as mock_keyring:
                # Setup keyring mock
                stored_keys = {}
                def mock_set(service, username, password):
                    stored_keys[f"{service}:{username}"] = password
                def mock_get(service, username):
                    return stored_keys.get(f"{service}:{username}")

                mock_keyring.set_password.side_effect = mock_set
                mock_keyring.get_password.side_effect = mock_get

                # Set the key
                result = set_api_key("census_api", "workflow_test_key")
                assert result is True

                # Get the key back
                retrieved_key = get_api_key("census_api")
                assert retrieved_key == "workflow_test_key"

    def test_multiple_key_types_independence(self):
        """Test that different key types are stored and retrieved independently."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("socialmapper.utils.api_key.keyring") as mock_keyring:
                stored_keys = {}
                def mock_set(service, username, password):
                    stored_keys[f"{service}:{username}"] = password
                def mock_get(service, username):
                    return stored_keys.get(f"{service}:{username}")

                mock_keyring.set_password.side_effect = mock_set
                mock_keyring.get_password.side_effect = mock_get

                # Store different keys
                set_api_key("census_api", "census_key_123")
                set_api_key("mapbox", "mapbox_token_456")

                # Verify they're retrieved independently
                assert get_api_key("census_api") == "census_key_123"
                assert get_api_key("mapbox") == "mapbox_token_456"

    def test_environment_overrides_stored_keyring(self):
        """Test that environment variables always override keyring values."""
        with patch("socialmapper.utils.api_key.keyring") as mock_keyring:
            # Setup keyring with a stored value
            mock_keyring.get_password.return_value = "old_keyring_value"

            # But environment has a different value
            with patch.dict(os.environ, {"CENSUS_API_KEY": "new_env_value"}, clear=False):
                result = get_api_key("census_api")
                assert result == "new_env_value"

                # Keyring should not be called
                mock_keyring.get_password.assert_not_called()


class TestApiKeyEdgeCases:
    """Test edge cases and error conditions."""

    def test_get_api_key_with_special_characters(self):
        """Test API keys with special characters."""
        special_key = "sk-1234567890abcdef!@#$%^&*()_+"
        with patch.dict(os.environ, {"CENSUS_API_KEY": special_key}, clear=False):
            result = get_api_key("census_api")
            assert result == special_key

    def test_get_api_key_very_long_key(self):
        """Test with very long API key."""
        long_key = "x" * 1000  # 1000 character key
        with patch.dict(os.environ, {"CENSUS_API_KEY": long_key}, clear=False):
            result = get_api_key("census_api")
            assert result == long_key
            assert len(result) == 1000

    def test_set_api_key_empty_value(self):
        """Test setting empty API key value."""
        with patch("socialmapper.utils.api_key.keyring") as mock_keyring:
            result = set_api_key("census_api", "")

            assert result is True
            mock_keyring.set_password.assert_called_once_with(
                "socialmapper", "census_api", ""
            )

    def test_get_api_key_case_sensitivity(self):
        """Test that key name matching is case sensitive."""
        with patch.dict(os.environ, {"CENSUS_API_KEY": "test_key"}, clear=False):
            # Correct case should work
            assert get_api_key("census_api") == "test_key"

            # Different case should not match and fallback to None
            with patch("socialmapper.utils.api_key.keyring") as mock_keyring:
                mock_keyring.get_password.return_value = None
                assert get_api_key("Census_Api") is None

    def test_concurrent_access_safety(self):
        """Test that concurrent access doesn't cause issues."""
        import threading
        import time

        results = []

        def worker():
            with patch.dict(os.environ, {"CENSUS_API_KEY": "concurrent_test"}, clear=False):
                result = get_api_key("census_api")
                results.append(result)

        # Start multiple threads
        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All should have gotten the same result
        assert len(results) == 10
        assert all(r == "concurrent_test" for r in results)


class TestApiKeyModuleImport:
    """Test module-level behavior and imports."""

    def test_keyring_availability_detection(self):
        """Test that keyring availability is correctly detected."""
        # This tests the actual import logic at module level
        assert isinstance(KEYRING_AVAILABLE, bool)

    @patch("socialmapper.utils.api_key.keyring", None)
    def test_module_works_without_keyring(self):
        """Test that module functions work even if keyring import fails."""
        with patch("socialmapper.utils.api_key.KEYRING_AVAILABLE", False):
            # Should not raise an exception
            result = get_api_key("test_key")
            assert result is None

            # Should return False but not crash
            result = set_api_key("test_key", "test_value")
            assert result is False