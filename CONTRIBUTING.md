# Contributing to SocialMapper

Thank you for your interest in contributing to SocialMapper!
This document provides guidelines and instructions for
contributing to the project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Project Structure](#project-structure)
- [Getting Help](#getting-help)

## Getting Started

SocialMapper is a Python toolkit for spatial analysis and
demographic mapping. We welcome contributions of all kinds:

- 🐛 Bug reports and fixes
- ✨ New features and enhancements
- 📝 Documentation improvements
- 🧪 Test coverage improvements
- 💡 Ideas and suggestions

## Development Setup

### Prerequisites

- **Python 3.11, 3.12, or 3.13** (3.11+ required)
- **Git** for version control
- **uv** (recommended) or pip for package management
- **Census API key** (free from
  https://api.census.gov/data/key_signup.html)

### Initial Setup

1. **Fork and Clone**

   ```bash
   # Fork the repository on GitHub first, then:
   git clone https://github.com/YOUR-USERNAME/socialmapper.git
   cd socialmapper
   ```

2. **Create Virtual Environment**

   Using uv (recommended):
   ```bash
   uv venv
   source .venv/bin/activate
   # On Windows: .venv\Scripts\activate
   ```

   Or using standard Python:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   # On Windows: .venv\Scripts\activate
   ```

3. **Install in Development Mode**

   ```bash
   # Install package with development dependencies
   uv pip install -e ".[dev]"

   # Or with standard pip:
   pip install -e ".[dev]"
   ```

4. **Configure Environment**

   ```bash
   # Copy environment template
   cp .env.example .env

   # Edit .env and add your Census API key
   CENSUS_API_KEY=your_key_here
   ```

5. **Verify Installation**

   ```bash
   # Run basic tests
   pytest tests/test_basic.py

   # Check code quality
   ruff check socialmapper/
   ```

## Code Standards

### Code Style

SocialMapper uses **Ruff** for linting and formatting
(replaces Black and Flake8):

```bash
# Format code
ruff format .

# Check and fix linting issues
ruff check --fix .

# Check without fixing
ruff check .
```

**Key Style Guidelines:**
- Line length: 100 characters
- Quote style: Double quotes
- Import sorting: Handled by ruff
- Type hints: Required for all public functions

### Docstring Convention

All functions, classes, and modules must use
**NumPy-style docstrings**:

```python
def example_function(param1, param2, optional_param=None):
    """
    Brief one-line description of the function.

    Extended description providing more context about
    the function's behavior and usage.

    Parameters
    ----------
    param1 : type
        Description of param1.
    param2 : type
        Description of param2.
    optional_param : type, optional
        Description of optional parameter. Default is
        None.

    Returns
    -------
    return_type
        Description of return value.

    Raises
    ------
    ValueError
        When invalid input is provided.

    Examples
    --------
    >>> result = example_function(1, 2)
    >>> print(result)
    3

    Notes
    -----
    Additional implementation notes or mathematical
    details.
    """
```

**Docstring Requirements:**
- Maximum 75 characters per line for readability
- Parameters section with types and descriptions
- Returns section with type and description
- Examples section with doctests when appropriate
- Raises section for exceptions
- Notes section for important details

### Type Hints

All public functions must include type hints:

```python
from typing import Optional, List, Dict, Any

def process_data(
    data: List[Dict[str, Any]],
    threshold: float = 0.5
) -> Optional[Dict[str, Any]]:
    """Process data with type hints."""
    ...
```

### Naming Conventions

- **Functions/Methods**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private members**: Prefix with underscore `_private_method`

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run tests with coverage
pytest --cov=socialmapper \
       --cov-report=html

# Run only unit tests
pytest -m unit

# Run integration tests
pytest -m integration
```

### Writing Tests

- Place tests in `tests/` directory
- Name test files as `test_*.py`
- Name test functions as `test_*`
- Use pytest fixtures from `conftest.py`
- Aim for >80% code coverage
- Test both success and failure cases

**Example Test:**

```python
def test_create_isochrone():
    """Test isochrone creation from coordinates."""
    result = create_isochrone(
        location=(45.5152, -122.6784),
        travel_time=15,
        travel_mode="walk"
    )

    assert result["type"] == "Feature"
    assert "geometry" in result
    assert result["properties"]["travel_time"] == 15
```

### Test Markers

Use pytest markers to categorize tests:

- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Tests with external
  dependencies
- `@pytest.mark.slow` - Long-running tests
- `@pytest.mark.external` - Requires network/APIs

## Documentation

### Building Documentation

```bash
# Install documentation dependencies (included in dev)
pip install -e ".[dev]"

# Serve documentation locally
mkdocs serve

# Build static documentation
mkdocs build
```

### Documentation Structure

- **User Guides**: `docs/user-guide/` - How to use
  features
- **Tutorials**: `docs/tutorials/` - Step-by-step
  examples
- **API Reference**: `docs/api-reference.md` - Function
  reference
- **Developer Docs**: `docs/` - Architecture and design
  docs

### Adding Documentation

When adding new features:
1. Update relevant user guide in `docs/user-guide/`
2. Add examples to `examples/` directory
3. Update API reference if adding public functions
4. Add docstrings to all new code

## Pull Request Process

### Before Submitting

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clear, focused commits
   - Follow code standards
   - Add tests for new functionality
   - Update documentation

3. **Run quality checks**
   ```bash
   # Format code
   ruff format .

   # Check linting
   ruff check .

   # Run tests
   pytest

   # Check test coverage
   pytest --cov=socialmapper
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add: Brief description of changes"
   git push origin feature/your-feature-name
   ```

### Commit Message Convention

Use clear, descriptive commit messages:

```
Add: New feature or functionality
Fix: Bug fix
Update: Modify existing feature
Docs: Documentation changes
Test: Add or modify tests
Refactor: Code restructuring
Style: Formatting changes
```

### Creating the Pull Request

1. Go to GitHub and create a pull request
2. Fill out the PR template with:
   - **Description**: What does this PR do?
   - **Motivation**: Why is this change needed?
   - **Testing**: How was this tested?
   - **Screenshots**: If applicable
   - **Related Issues**: Link to issues

3. Wait for review and address feedback

### Review Process

- Maintainers will review your PR
- Address any requested changes
- Once approved, your PR will be merged
- Your contribution will be credited in the
  changelog

## Project Structure

```
socialmapper/
├── socialmapper/           # Main package
│   ├── api.py             # Public API functions
│   ├── census.py          # Census data integration
│   ├── geocoding/         # Address geocoding
│   ├── isochrone/         # Travel time polygons
│   ├── export/            # Data export functionality
│   ├── visualization/     # Map creation
│   └── neighbors.py       # Geographic neighbor queries
├── tests/                 # Test suite
├── examples/              # Usage examples
├── docs/                  # Documentation
└── pyproject.toml        # Project configuration
```

### Key Modules

- **`api.py`**: Main API with 5 core functions
- **`isochrone/`**: Isochrone generation with
  optimization
- **`geocoding/`**: Multi-provider address geocoding
- **`census.py`**: US Census data integration
- **`export/`**: Data export in multiple formats
- **`visualization/`**: Choropleth map creation

## Getting Help

### Resources

- **Documentation**:
  https://mihiarc.github.io/socialmapper
- **Issue Tracker**:
  https://github.com/mihiarc/socialmapper/issues
- **Discussions**:
  https://github.com/mihiarc/socialmapper/discussions

### Asking Questions

- Search existing issues first
- Use GitHub Discussions for general questions
- Create issues for bug reports or feature requests
- Include code examples and error messages

### Reporting Bugs

When reporting bugs, include:

1. **Description**: Clear description of the issue
2. **Steps to Reproduce**: Minimal code to reproduce
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**: Python version, OS, package
   versions
6. **Error Messages**: Complete error traceback

## Code of Conduct

- Be respectful and professional
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Assume good intentions

## License

By contributing to SocialMapper, you agree that your
contributions will be licensed under the MIT License.

---

Thank you for contributing to SocialMapper! 🎉
