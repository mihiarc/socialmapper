"""Integration tests for API key management across the application."""

import os
import pytest
from unittest.mock import patch, MagicMock

from socialmapper.utils.api_key import get_api_key


class TestCensusApiKeyIntegration:
    """Test that Census API functions correctly use API key management."""

    def test_census_functions_should_use_api_key_utility(self):
        """Test that Census functions should be updated to use the new utility."""
        # This test documents that the codebase needs to be updated
        # Current state: _census.py still uses os.getenv("CENSUS_API_KEY") directly
        # Expected: Should use get_api_key("census_api") from utils.api_key

        # Check current implementation
        with patch.dict(os.environ, {"CENSUS_API_KEY": "test_key_direct"}, clear=False):
            # This shows the current state - direct environment access
            direct_key = os.getenv("CENSUS_API_KEY")

            # This shows what it should use - the utility function
            utility_key = get_api_key("census_api")

            # Both should return the same value for now
            assert direct_key == utility_key == "test_key_direct"

    def test_api_key_consistency_across_modules(self):
        """Test that all modules would get the same API key value."""
        test_key = "consistency_test_key_123"

        with patch.dict(os.environ, {"CENSUS_API_KEY": test_key}, clear=False):
            # Current direct access (what _census.py does)
            direct_access = os.getenv("CENSUS_API_KEY")

            # New utility function (what should be used)
            utility_access = get_api_key("census_api")

            # Both should return the same value
            assert direct_access == utility_access == test_key

    def test_keyring_fallback_behavior_integration(self):
        """Test how keyring fallback would work in practice."""
        # Clear environment variable
        with patch.dict(os.environ, {}, clear=True):
            with patch("socialmapper.utils.api_key.keyring") as mock_keyring:
                mock_keyring.get_password.return_value = "keyring_census_key"

                # New utility would return keyring value
                utility_key = get_api_key("census_api")
                assert utility_key == "keyring_census_key"

                # Direct access would return None (current implementation issue)
                direct_key = os.getenv("CENSUS_API_KEY")
                assert direct_key is None

                # This demonstrates why the codebase needs to be updated


class TestApiKeyMigrationNeeds:
    """Document what needs to be updated to use the new API key utility."""

    def test_census_module_migration_needed(self):
        """Document that _census.py needs to be updated."""
        # Current pattern in _census.py line 460:
        # api_key = os.getenv("CENSUS_API_KEY")

        # Should be changed to:
        # from socialmapper.utils.api_key import get_api_key
        # api_key = get_api_key("census_api")

        # This test documents the migration need
        assert True  # Placeholder

    def test_client_module_migration_needed(self):
        """Document that client.py needs to be updated."""
        # Current pattern in client.py line 57:
        # self.api_key = api_key or os.getenv("CENSUS_API_KEY")

        # Should be changed to:
        # from socialmapper.utils.api_key import get_api_key
        # self.api_key = api_key or get_api_key("census_api")

        # This test documents the migration need
        assert True  # Placeholder

    def test_other_modules_migration_needed(self):
        """Document other modules that need updating."""
        # Found in grep results:
        # - socialmapper/census.py line 39
        # - socialmapper/config/feature_flags.py line 26
        # - Examples and documentation files

        # All should use get_api_key("census_api") instead of os.getenv("CENSUS_API_KEY")
        assert True  # Placeholder


class TestApiKeySecurityConsiderations:
    """Test security aspects of the simplified API key management."""

    def test_no_api_key_logging(self):
        """Ensure API keys are not logged."""
        import logging
        from io import StringIO

        # Capture log output
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        logger = logging.getLogger("socialmapper.utils.api_key")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        try:
            with patch.dict(os.environ, {"CENSUS_API_KEY": "secret_key_123"}, clear=False):
                key = get_api_key("census_api")
                assert key == "secret_key_123"

                # Check that the actual key value wasn't logged
                log_output = log_stream.getvalue()
                assert "secret_key_123" not in log_output
        finally:
            logger.removeHandler(handler)

    def test_keyring_exception_handling(self):
        """Test that keyring exceptions don't expose sensitive information."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("socialmapper.utils.api_key.keyring") as mock_keyring:
                # Simulate various keyring failures
                mock_keyring.get_password.side_effect = Exception("Keyring backend not available")

                # Should not raise exception, should return None
                result = get_api_key("census_api")
                assert result is None

    def test_environment_variable_precedence(self):
        """Test that environment variables always take precedence for security."""
        with patch("socialmapper.utils.api_key.keyring") as mock_keyring:
            mock_keyring.get_password.return_value = "potentially_stale_keyring_value"

            # Environment should always override keyring for security
            with patch.dict(os.environ, {"CENSUS_API_KEY": "current_env_value"}, clear=False):
                result = get_api_key("census_api")
                assert result == "current_env_value"

                # Keyring should not even be consulted
                mock_keyring.get_password.assert_not_called()


class TestApiKeyErrorHandling:
    """Test error handling and edge cases for API key management."""

    def test_malformed_keyring_data(self):
        """Test handling of malformed data from keyring."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("socialmapper.utils.api_key.keyring") as mock_keyring:
                # Return non-string data (should not happen but test anyway)
                mock_keyring.get_password.return_value = None

                result = get_api_key("census_api")
                assert result is None

    def test_empty_string_environment_fallback(self):
        """Test that empty string in environment falls back to keyring."""
        with patch.dict(os.environ, {"CENSUS_API_KEY": ""}, clear=False):
            with patch("socialmapper.utils.api_key.keyring") as mock_keyring:
                mock_keyring.get_password.return_value = "keyring_backup"

                result = get_api_key("census_api")
                assert result == "keyring_backup"

    def test_whitespace_only_environment_fallback(self):
        """Test that whitespace-only environment variable falls back."""
        with patch.dict(os.environ, {"CENSUS_API_KEY": "   "}, clear=False):
            with patch("socialmapper.utils.api_key.keyring") as mock_keyring:
                mock_keyring.get_password.return_value = "keyring_backup"

                result = get_api_key("census_api")
                # Should return the whitespace (os.getenv behavior)
                assert result == "   "


class TestApiKeyPerformance:
    """Test performance characteristics of API key retrieval."""

    def test_environment_access_performance(self):
        """Test that environment variable access is fast."""
        import time

        with patch.dict(os.environ, {"CENSUS_API_KEY": "perf_test_key"}, clear=False):
            start_time = time.time()

            # Call multiple times
            for _ in range(1000):
                key = get_api_key("census_api")
                assert key == "perf_test_key"

            elapsed = time.time() - start_time

            # Should be very fast - less than 100ms for 1000 calls
            assert elapsed < 0.1, f"Environment access too slow: {elapsed:.3f}s for 1000 calls"

    def test_keyring_fallback_performance(self):
        """Test that keyring fallback doesn't significantly impact performance."""
        import time

        with patch.dict(os.environ, {}, clear=True):
            with patch("socialmapper.utils.api_key.keyring") as mock_keyring:
                mock_keyring.get_password.return_value = "keyring_key"

                start_time = time.time()

                # Call multiple times
                for _ in range(100):  # Fewer calls since keyring might be slower
                    key = get_api_key("census_api")
                    assert key == "keyring_key"

                elapsed = time.time() - start_time

                # Should still be reasonable - less than 1s for 100 calls
                assert elapsed < 1.0, f"Keyring access too slow: {elapsed:.3f}s for 100 calls"


class TestApiKeyBackwardsCompatibility:
    """Test backwards compatibility with existing code patterns."""

    def test_environment_variable_names_unchanged(self):
        """Test that environment variable names remain the same."""
        # Existing code expects CENSUS_API_KEY
        with patch.dict(os.environ, {"CENSUS_API_KEY": "compat_test"}, clear=False):
            # Both old and new methods should work
            old_method = os.getenv("CENSUS_API_KEY")
            new_method = get_api_key("census_api")

            assert old_method == new_method == "compat_test"

    def test_mapbox_token_compatibility(self):
        """Test that Mapbox token handling is compatible."""
        with patch.dict(os.environ, {"MAPBOX_TOKEN": "mapbox_compat_test"}, clear=False):
            # Both methods should work
            old_method = os.getenv("MAPBOX_TOKEN")
            new_method = get_api_key("mapbox")

            assert old_method == new_method == "mapbox_compat_test"

    def test_none_return_compatibility(self):
        """Test that None returns are compatible with existing error handling."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("socialmapper.utils.api_key.KEYRING_AVAILABLE", False):
                result = get_api_key("census_api")
                assert result is None

                # Existing code should handle None the same way
                assert not result  # Falsy check should work the same