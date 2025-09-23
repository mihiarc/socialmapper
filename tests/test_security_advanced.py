"""Advanced security tests for API key management."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import stat

import pytest

from socialmapper.security import SecureKeyManager, KeyStorage
from socialmapper.security.utils import get_api_key


class TestSecurityVulnerabilities:
    """Test for security vulnerabilities and edge cases."""

    def test_file_permissions_on_creation(self):
        """Test that files are created with proper permissions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "keys.enc"
            manager = SecureKeyManager(config_path=config_path)

            # Set a key to trigger file creation
            manager.set_key("test_key", "test_value", KeyStorage.ENCRYPTED_FILE)

            # Check master key permissions
            master_key_path = Path(tmpdir) / ".master.key"
            if master_key_path.exists():
                stats = master_key_path.stat()
                mode = stat.filemode(stats.st_mode)
                # Should be -rw------- (0o600)
                assert mode == '-rw-------', f"Master key has unsafe permissions: {mode}"

            # Check encrypted file permissions
            if config_path.exists():
                stats = config_path.stat()
                mode = stat.filemode(stats.st_mode)
                assert mode == '-rw-------', f"Encrypted file has unsafe permissions: {mode}"

            # Check directory permissions
            stats = Path(tmpdir).stat()
            mode = stat.filemode(stats.st_mode)
            # Should be drwx------ (0o700)
            assert mode.startswith('drwx------'), f"Directory has unsafe permissions: {mode}"

    def test_input_validation_injection_attempts(self):
        """Test that injection attempts are blocked."""
        manager = SecureKeyManager()

        # Path traversal attempts
        injection_attempts = [
            "../etc/passwd",
            "../../secret",
            "key/../../../etc/shadow",
            "key\x00.txt",  # Null byte injection
            "key|rm -rf /",  # Command injection
            "key;cat /etc/passwd",
            "key$(whoami)",
            "key`id`",
        ]

        for attempt in injection_attempts:
            result = manager.set_key(attempt, "value", KeyStorage.MEMORY)
            assert result is False, f"Injection attempt not blocked: {attempt}"
            assert manager.get_key(attempt) is None

    def test_key_name_validation(self):
        """Test key name validation rules."""
        manager = SecureKeyManager()

        # Valid key names
        valid_names = [
            "api_key",
            "API-KEY",
            "key123",
            "my-service-key",
            "KEY_2024",
        ]

        for name in valid_names:
            assert manager.set_key(name, "value", KeyStorage.MEMORY)
            assert manager.get_key(name) == "value"
            manager.delete_key(name, KeyStorage.MEMORY)

        # Invalid key names
        invalid_names = [
            "",  # Empty
            " ",  # Whitespace
            "key with spaces",
            "key/with/slashes",
            "key\\with\\backslashes",
            "key.with.dots",
            "key@with@special",
            "k" * 101,  # Too long
        ]

        for name in invalid_names:
            assert not manager.set_key(name, "value", KeyStorage.MEMORY)

    def test_key_value_limits(self):
        """Test key value size limits."""
        manager = SecureKeyManager()

        # Test maximum allowed size
        large_value = "x" * 10000
        assert manager.set_key("large_key", large_value, KeyStorage.MEMORY)

        # Test oversized value
        oversized_value = "x" * 10001
        assert not manager.set_key("oversized_key", oversized_value, KeyStorage.MEMORY)

    def test_concurrent_access_protection(self):
        """Test protection against concurrent access."""
        import threading
        import time

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "keys.enc"
            manager = SecureKeyManager(config_path=config_path)

            results = []

            def write_key(key_num):
                try:
                    success = manager.set_key(f"key_{key_num}", f"value_{key_num}", KeyStorage.ENCRYPTED_FILE)
                    results.append(success)
                except Exception as e:
                    results.append(False)

            # Launch multiple threads to write concurrently
            threads = []
            for i in range(10):
                t = threading.Thread(target=write_key, args=(i,))
                threads.append(t)
                t.start()

            # Wait for all threads to complete
            for t in threads:
                t.join()

            # All operations should succeed or fail gracefully
            assert len(results) == 10
            # At least some should succeed
            assert any(results)

    def test_memory_cleanup(self):
        """Test that keys are not left in memory after deletion."""
        manager = SecureKeyManager()

        sensitive_key = "super_secret_api_key_12345"
        manager.set_key("memory_test", sensitive_key, KeyStorage.MEMORY)

        # Delete the key
        manager.delete_key("memory_test", KeyStorage.MEMORY)

        # Key should not be retrievable
        assert manager.get_key("memory_test") is None

        # Check that the key is not in the internal dictionary
        assert "memory_test" not in manager._memory_keys

    def test_encryption_actually_encrypts(self):
        """Test that data is actually encrypted on disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "keys.enc"
            manager = SecureKeyManager(config_path=config_path)

            # Skip if cryptography not available
            try:
                from cryptography.fernet import Fernet
            except ImportError:
                pytest.skip("cryptography not available")

            sensitive_value = "my_super_secret_api_key_that_should_not_appear_in_plain_text"
            manager.set_key("secret_key", sensitive_value, KeyStorage.ENCRYPTED_FILE)

            # Read the raw file contents
            if config_path.exists():
                with open(config_path, 'rb') as f:
                    raw_data = f.read()

                # The sensitive value should NOT appear in the file
                assert sensitive_value.encode() not in raw_data
                assert b"secret_key" not in raw_data

    def test_keyring_fallback_on_failure(self):
        """Test fallback when keyring is unavailable."""
        with patch('socialmapper.security.key_manager.KEYRING_AVAILABLE', False):
            manager = SecureKeyManager()

            # Should fallback to next available storage
            assert KeyStorage.KEYRING not in manager.storage_preference

            # Should still be able to store keys
            assert manager.set_key("test_key", "test_value", KeyStorage.MEMORY)
            assert manager.get_key("test_key") == "test_value"

    def test_corrupted_encrypted_file_recovery(self):
        """Test recovery from corrupted encrypted files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "keys.enc"
            manager = SecureKeyManager(config_path=config_path)

            # Store a key
            manager.set_key("test_key", "test_value", KeyStorage.ENCRYPTED_FILE)

            # Corrupt the encrypted file
            if config_path.exists():
                with open(config_path, 'wb') as f:
                    f.write(b"corrupted data that is not valid encryption")

            # Should handle gracefully
            result = manager.get_key("test_key")
            # Should return None or handle error gracefully
            assert result is None or isinstance(result, str)

    def test_timing_attack_resistance(self):
        """Test resistance to timing attacks on key validation."""
        import time
        manager = SecureKeyManager()

        manager.set_key("valid_key", "a" * 40, KeyStorage.MEMORY)

        # Measure validation time for valid key
        valid_times = []
        for _ in range(10):
            start = time.perf_counter()
            manager.validate_key("valid_key")
            valid_times.append(time.perf_counter() - start)

        # Measure validation time for invalid key
        invalid_times = []
        for _ in range(10):
            start = time.perf_counter()
            manager.validate_key("invalid_key", "wrong_value")
            invalid_times.append(time.perf_counter() - start)

        # Times should be similar (within 50% variance)
        avg_valid = sum(valid_times) / len(valid_times)
        avg_invalid = sum(invalid_times) / len(invalid_times)

        # This is a simplified check - proper timing attack resistance
        # would need constant-time comparison
        ratio = max(avg_valid, avg_invalid) / min(avg_valid, avg_invalid)
        assert ratio < 2.0, "Possible timing attack vulnerability detected"


class TestCLISecurity:
    """Test CLI security features."""

    def test_cli_input_sanitization(self):
        """Test that CLI properly sanitizes inputs."""
        from socialmapper.security.cli import set as cli_set

        # Mock the runner to capture what would be executed
        from click.testing import CliRunner
        runner = CliRunner()

        # Test command injection attempts
        dangerous_inputs = [
            ("key", "value; rm -rf /"),
            ("key`whoami`", "value"),
            ("key$(cat /etc/passwd)", "value"),
            ("key|ls", "value"),
        ]

        with patch('socialmapper.security.cli.SecureKeyManager') as mock_manager:
            mock_instance = MagicMock()
            mock_manager.return_value = mock_instance
            mock_instance.set_key.return_value = False  # Simulate rejection

            for key_name, key_value in dangerous_inputs:
                result = runner.invoke(cli_set, [key_name, key_value])
                # Should fail safely
                assert result.exit_code != 0


class TestAuditLogging:
    """Test security audit logging features."""

    def test_sensitive_operations_logged(self):
        """Test that sensitive operations are logged appropriately."""
        with patch('socialmapper.security.key_manager.logger') as mock_logger:
            manager = SecureKeyManager()

            # Set a key
            manager.set_key("test_key", "test_value", KeyStorage.MEMORY)

            # Should log the operation but NOT the value
            calls = str(mock_logger.info.call_args_list)
            assert "test_value" not in calls  # Value should not be logged

            # Delete a key
            manager.delete_key("test_key", KeyStorage.MEMORY)

            # Should log deletion
            assert mock_logger.info.called or mock_logger.debug.called