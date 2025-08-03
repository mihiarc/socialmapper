"""Tests for the Result types (Ok/Err pattern)."""

import pytest

from socialmapper.api.result_types import Err, Error, ErrorType, Ok, Result


class TestResultTypes:
    """Test the Result type implementation."""

    def test_ok_creation(self):
        """Test creating an Ok result."""
        result = Ok(42)
        assert result.is_ok() is True
        assert result.is_err() is False
        assert result.unwrap() == 42

    def test_err_creation(self):
        """Test creating an Err result."""
        error = Error(ErrorType.VALIDATION, "Something went wrong")
        result = Err(error)
        assert result.is_ok() is False
        assert result.is_err() is True
        assert result._value.message == "Something went wrong"

    def test_ok_unwrap(self):
        """Test unwrapping an Ok result."""
        result = Ok("success")
        assert result.unwrap() == "success"

    def test_err_unwrap_raises(self):
        """Test that unwrapping an Err raises exception."""
        error = Error(ErrorType.VALIDATION, "error message")
        result = Err(error)
        with pytest.raises(RuntimeError, match="Called unwrap on an Err value"):
            result.unwrap()

    def test_ok_unwrap_or(self):
        """Test unwrap_or on Ok result."""
        result = Ok(100)
        assert result.unwrap_or(50) == 100

    def test_err_unwrap_or(self):
        """Test unwrap_or on Err result."""
        error = Error(ErrorType.VALIDATION, "error")
        result = Err(error)
        assert result.unwrap_or(50) == 50

    def test_ok_unwrap_or_else(self):
        """Test unwrap_or_else on Ok result."""
        result = Ok(100)
        assert result.unwrap_or_else(lambda: 50) == 100

    def test_err_unwrap_or_else(self):
        """Test unwrap_or_else on Err result."""
        error = Error(ErrorType.VALIDATION, "error")
        result = Err(error)
        # unwrap_or_else passes the error value to the function
        assert result.unwrap_or_else(lambda e: 50) == 50

    def test_ok_map(self):
        """Test map on Ok result."""
        result = Ok(10)
        mapped = result.map(lambda x: x * 2)
        assert mapped.is_ok()
        assert mapped.unwrap() == 20

    def test_err_map(self):
        """Test map on Err result."""
        error = Error(ErrorType.VALIDATION, "error")
        result = Err(error)
        mapped = result.map(lambda x: x * 2)
        assert mapped.is_err()
        assert mapped._value.message == "error"

    def test_ok_map_err(self):
        """Test map_err on Ok result."""
        result = Ok(10)
        mapped = result.map_err(lambda e: f"Error: {e}")
        assert mapped.is_ok()
        assert mapped.unwrap() == 10

    def test_err_map_err(self):
        """Test map_err on Err result."""
        error = Error(ErrorType.VALIDATION, "fail")
        result = Err(error)
        mapped = result.map_err(lambda e: Error(ErrorType.PROCESSING, f"Error: {e.message}"))
        assert mapped.is_err()
        assert mapped._value.message == "Error: fail"

    def test_ok_and_then(self):
        """Test and_then on Ok result."""
        result = Ok(10)
        chained = result.and_then(lambda x: Ok(x * 2))
        assert chained.is_ok()
        assert chained.unwrap() == 20

    def test_err_and_then(self):
        """Test and_then on Err result."""
        error = Error(ErrorType.VALIDATION, "error")
        result = Err(error)
        chained = result.and_then(lambda x: Ok(x * 2))
        assert chained.is_err()
        assert chained._value.message == "error"

    def test_ok_or_else(self):
        """Test or_else on Ok result."""
        result = Ok(10)
        chained = result.or_else(lambda e: Ok(0))
        assert chained.is_ok()
        assert chained.unwrap() == 10

    def test_err_or_else(self):
        """Test or_else on Err result."""
        error = Error(ErrorType.VALIDATION, "error")
        result = Err(error)
        chained = result.or_else(lambda e: Ok(0))
        assert chained.is_ok()
        assert chained.unwrap() == 0

    def test_result_type_hint(self):
        """Test that Result works as a type hint."""
        def divide(a: int, b: int) -> Result[float, Error]:
            if b == 0:
                return Err(Error(ErrorType.VALIDATION, "Division by zero"))
            return Ok(a / b)

        result1 = divide(10, 2)
        assert result1.is_ok()
        assert result1.unwrap() == 5.0

        result2 = divide(10, 0)
        assert result2.is_err()
        assert result2._value.message == "Division by zero"

    def test_result_chaining(self):
        """Test chaining multiple operations."""
        result = (
            Ok(5)
            .map(lambda x: x * 2)
            .and_then(lambda x: Ok(x + 1) if x > 5 else Err("Too small"))
            .map(lambda x: x ** 2)
        )
        assert result.is_ok()
        assert result.unwrap() == 121  # ((5 * 2) + 1) ** 2
