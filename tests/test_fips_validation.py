"""Test FIPS code validation to ensure SQL injection prevention."""

import pytest
from socialmapper._census import validate_fips_code


class TestFIPSValidation:
    """Test suite for FIPS code validation."""

    def test_valid_state_fips(self):
        """Test valid state FIPS codes are accepted."""
        assert validate_fips_code("06", 2, "State") == "06"
        assert validate_fips_code("01", 2, "State") == "01"
        assert validate_fips_code("72", 2, "State") == "72"  # Puerto Rico

    def test_valid_county_fips(self):
        """Test valid county FIPS codes are accepted."""
        assert validate_fips_code("037", 3, "County") == "037"
        assert validate_fips_code("001", 3, "County") == "001"
        assert validate_fips_code("999", 3, "County") == "999"

    def test_whitespace_handling(self):
        """Test that whitespace is properly stripped."""
        assert validate_fips_code("  06  ", 2, "State") == "06"
        assert validate_fips_code("\t037\n", 3, "County") == "037"

    def test_empty_value_rejection(self):
        """Test empty values are rejected."""
        with pytest.raises(ValueError, match="empty value"):
            validate_fips_code("", 2, "State")

        with pytest.raises(ValueError, match="empty value"):
            validate_fips_code("   ", 2, "State")

    def test_wrong_length_rejection(self):
        """Test incorrect length FIPS codes are rejected."""
        with pytest.raises(ValueError, match="expected 2 digits, got 3"):
            validate_fips_code("037", 2, "State")

        with pytest.raises(ValueError, match="expected 3 digits, got 2"):
            validate_fips_code("06", 3, "County")

        with pytest.raises(ValueError, match="expected 2 digits, got 1"):
            validate_fips_code("6", 2, "State")

    def test_sql_injection_attempts(self):
        """Test SQL injection attempts are blocked."""
        injection_attempts = [
            "'; DROP TABLE--",
            "' OR '1'='1",
            "06' OR '1'='1'--",
            "037'; DELETE FROM census--",
            "06 UNION SELECT * FROM users--",
            "037' AND 1=1--",
            "06'; EXEC sp_MSForEachTable 'DROP TABLE ?'--"
        ]

        for attempt in injection_attempts:
            with pytest.raises(ValueError, match="contains non-digit characters"):
                validate_fips_code(attempt, 2, "State")

            with pytest.raises(ValueError, match="contains non-digit characters"):
                validate_fips_code(attempt, 3, "County")

    def test_special_characters_rejection(self):
        """Test special characters are rejected."""
        special_chars = [
            "0-6",
            "03.7",
            "06!",
            "03@7",
            "0#6",
            "03$7",
            "06%",
            "03^7",
            "06&",
            "03*7",
            "06(",
            "03)7",
            "06[",
            "03]7",
            "06{",
            "03}7",
            "06\\",
            "03/7",
            "06|",
            "03`7",
            "06~",
            "03=7"
        ]

        for char_test in special_chars:
            with pytest.raises(ValueError, match="contains non-digit characters"):
                validate_fips_code(char_test, len(char_test), "Test")

    def test_alphanumeric_rejection(self):
        """Test alphanumeric values are rejected."""
        alphanumeric_tests = [
            "0A",
            "A37",
            "06B",
            "C37",
            "O6",  # Letter O, not zero
            "l37", # Letter l, not one
        ]

        for test_val in alphanumeric_tests:
            with pytest.raises(ValueError, match="contains non-digit characters"):
                validate_fips_code(test_val, len(test_val), "Test")

    def test_unicode_rejection(self):
        """Test unicode characters are rejected."""
        unicode_tests = [
            "0６",  # Full-width digit
            "０37", # Another full-width digit
            "06♦",
            "03☺7",
            "06😀"
        ]

        for test_val in unicode_tests:
            with pytest.raises(ValueError, match="contains non-digit characters"):
                validate_fips_code(test_val, 3, "Test")