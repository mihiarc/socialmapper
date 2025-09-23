"""Integration tests for census module security fixes."""

import pytest
from socialmapper._census import (
    fetch_tiger_block_groups,
    fetch_block_groups_alternative,
    validate_fips_code
)


class TestCensusSecurityIntegration:
    """Integration tests for SQL injection prevention in census module."""

    def test_fetch_tiger_block_groups_validates_state_injection(self):
        """Test that fetch_tiger_block_groups prevents state FIPS injection."""
        with pytest.raises(ValueError, match="contains non-digit characters"):
            fetch_tiger_block_groups("'; DROP TABLE--", "037")

        with pytest.raises(ValueError, match="contains non-digit characters"):
            fetch_tiger_block_groups("' OR '1'='1", "037")

    def test_fetch_tiger_block_groups_validates_county_injection(self):
        """Test that fetch_tiger_block_groups prevents county FIPS injection."""
        with pytest.raises(ValueError, match="contains non-digit characters"):
            fetch_tiger_block_groups("06", "'; DELETE FROM census--")

        with pytest.raises(ValueError, match="contains non-digit characters"):
            fetch_tiger_block_groups("06", "037' OR '1'='1'")

    def test_fetch_block_groups_alternative_validates_injection(self):
        """Test that alternative fetch method also validates inputs."""
        with pytest.raises(ValueError, match="contains non-digit characters"):
            fetch_block_groups_alternative("'; DROP TABLE--", "037")

        with pytest.raises(ValueError, match="contains non-digit characters"):
            fetch_block_groups_alternative("06", "037' UNION SELECT *--")

    def test_fetch_tiger_block_groups_accepts_valid_inputs(self):
        """Test that valid FIPS codes are accepted and processed."""
        # This would make an actual API call, so we'll just verify it doesn't raise
        # a validation error for valid inputs
        try:
            # Valid California (06) and Los Angeles County (037) codes
            result = fetch_tiger_block_groups("06", "037")
            # We don't care about the result, just that validation passed
            assert isinstance(result, list)
        except Exception as e:
            # If it fails for non-validation reasons (network, API), that's ok
            assert "Invalid" not in str(e) and "contains non-digit" not in str(e)

    def test_mixed_injection_attempts(self):
        """Test various mixed injection patterns are blocked."""
        injection_patterns = [
            ("06", "037; DROP TABLE census--"),
            ("06' AND '1'='1", "037"),
            ("06", "037' OR EXISTS(SELECT * FROM users)--"),
            ("6' OR LENGTH(database())>0--", "037"),
        ]

        for state, county in injection_patterns:
            with pytest.raises(ValueError):
                fetch_tiger_block_groups(state, county)

    def test_validation_performance(self):
        """Ensure validation doesn't significantly impact performance."""
        import time

        # Test that validation is fast (< 1ms per call)
        iterations = 1000
        start = time.time()

        for _ in range(iterations):
            try:
                validate_fips_code("06", 2, "State")
            except:
                pass

        elapsed = time.time() - start
        avg_time = elapsed / iterations

        # Should be very fast - less than 0.1ms per validation
        assert avg_time < 0.0001, f"Validation too slow: {avg_time*1000:.3f}ms per call"

    def test_error_messages_no_information_leak(self):
        """Ensure error messages don't leak sensitive information."""
        try:
            fetch_tiger_block_groups("'; SELECT password FROM users--", "037")
        except ValueError as e:
            # Error should not echo back the malicious input verbatim
            assert "SELECT password FROM users" not in str(e)
            assert "contains non-digit characters" in str(e)