# Contributing to SocialMapper 🌍

Welcome! We're thrilled that you're interested in contributing to SocialMapper. Whether you're fixing a bug, adding a feature, improving documentation, or sharing ideas, your contribution matters and helps make spatial analysis more accessible to everyone.

SocialMapper is a community-driven project, and we believe the best software comes from diverse perspectives and collaborative development. This guide will help you get started contributing to our Python toolkit for spatial analysis and demographic mapping.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Ways to Contribute](#ways-to-contribute)
- [Getting Started](#getting-started)
- [Development Guidelines](#development-guidelines)
- [Making Your Contribution](#making-your-contribution)
- [Testing](#testing)
- [Documentation](#documentation)
- [Release Process](#release-process)
- [Getting Help](#getting-help)
- [Recognition](#recognition)

## Code of Conduct

We are committed to providing a welcoming and inspiring community for all. By participating in this project, you agree to abide by our Code of Conduct:

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Expected Behavior

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, discriminatory language, and personal attacks
- Publishing others' private information without permission
- Conduct which could reasonably be considered inappropriate in a professional setting

### Enforcement

Instances of unacceptable behavior may be reported by opening an issue or contacting the maintainer directly. All complaints will be reviewed and investigated promptly and fairly.

## Ways to Contribute

Every contribution is valuable! Here are some ways you can help:

### 🐛 Report Bugs
Found something that doesn't work? [Open an issue](https://github.com/mihiarc/socialmapper/issues/new) with:
- Clear title and description
- Steps to reproduce
- Expected vs actual behavior
- Your environment (Python version, OS)

### 💡 Suggest Features
Have an idea to improve SocialMapper? We'd love to hear it! [Open a feature request](https://github.com/mihiarc/socialmapper/issues/new) describing:
- The problem you're trying to solve
- Your proposed solution
- Example use cases

### 📖 Improve Documentation
- Fix typos or clarify explanations
- Add examples and tutorials
- Translate documentation
- Create educational content (blog posts, videos)

### 💻 Write Code
- Fix bugs (look for ["good first issue"](https://github.com/mihiarc/socialmapper/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) labels)
- Add new features
- Improve performance
- Add tests

### 🎨 Design & UX
- Improve visualizations
- Create better map styles
- Design intuitive APIs

### 🔬 Share Use Cases
- Write about how you use SocialMapper
- Share analysis results
- Contribute example notebooks

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git for version control
- A Census API key (free from [api.census.gov](https://api.census.gov/data/key_signup.html)) - only needed for census-related features

### Development Setup

1. **Fork the repository**

   Click the "Fork" button at the top right of the [SocialMapper repository](https://github.com/mihiarc/socialmapper).

2. **Clone your fork**

   ```bash
   git clone https://github.com/YOUR_USERNAME/socialmapper.git
   cd socialmapper
   ```

3. **Set up the development environment using uv**

   We use `uv` for fast, reliable Python package management:

   ```bash
   # Install uv if you haven't already
   pip install uv

   # Create virtual environment
   uv venv

   # Activate it
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

   # Install SocialMapper in development mode with all dependencies
   uv pip install -e ".[dev]"
   ```

4. **Set up pre-commit hooks (optional but recommended)**

   ```bash
   # Install pre-commit
   uv pip install pre-commit

   # Set up the git hooks
   pre-commit install
   ```

5. **Configure environment variables**

   ```bash
   # Copy the example environment file
   cp .env.example .env

   # Edit .env and add your Census API key (if you have one)
   ```

6. **Verify your setup**

   ```bash
   # Run the test suite
   uv run pytest tests/ -v

   # Run a quick example
   uv run python -c "from socialmapper import demo; print(demo.quick_start('Portland, OR'))"
   ```

   You're all set! 🎉

## Development Guidelines

### Code Standards

#### Python Style

We use modern Python 3.11+ features and follow these conventions:

- **Type hints** for all function parameters and returns
- **Pydantic v2** for data validation
- **Rich** for terminal output
- **Line length**: 100 characters (configured in `pyproject.toml`)
- **Import sorting**: Handled automatically by ruff

#### Code Quality Tools

We use `ruff` for linting and formatting:

```bash
# Check code quality
uv run ruff check socialmapper/

# Fix auto-fixable issues
uv run ruff check --fix socialmapper/

# Format code
uv run ruff format socialmapper/
```

#### Docstring Format

All public functions MUST use NumPy-style docstrings. Here's our standard template:

```python
def analyze_accessibility(
    location: str | tuple[float, float],
    poi_type: str,
    travel_time: int = 15
) -> pd.DataFrame:
    """
    Analyze accessibility to points of interest from a location.

    Calculates travel times and demographic characteristics for
    populations with access to specified points of interest.

    Parameters
    ----------
    location : str or tuple of float
        Either a "City, State" string for geocoding or a
        (latitude, longitude) tuple with coordinates.
    poi_type : str
        OpenStreetMap amenity type (e.g., "library", "hospital").
    travel_time : int, optional
        Maximum travel time in minutes, by default 15.
        Must be between 1 and 120.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns:
        - 'poi_name': Name of the point of interest
        - 'distance_km': Distance in kilometers
        - 'population': Population with access
        - 'demographics': Demographic breakdown

    Raises
    ------
    ValueError
        If location cannot be geocoded or poi_type is invalid.
    ConnectionError
        If OpenStreetMap or Census API is unavailable.

    Examples
    --------
    >>> df = analyze_accessibility("Portland, OR", "library")
    >>> df['population'].sum()
    125000

    >>> df = analyze_accessibility((45.5152, -122.6784), "hospital",
    ...                            travel_time=20)
    >>> len(df)
    5

    Notes
    -----
    This function combines multiple data sources:
    1. OpenStreetMap for POI locations
    2. Census API for demographic data
    3. OSMNX for travel-time calculations

    See Also
    --------
    get_poi : Retrieve points of interest
    create_isochrone : Generate travel-time polygons
    """
```

### Performance Considerations

SocialMapper prioritizes performance for large-scale analyses:

- **Use concurrent processing** where possible (we have 4-8x speedups)
- **Implement caching** for expensive operations (geocoding, API calls)
- **Profile before optimizing** - measure first, optimize second
- **Memory efficiency** - use generators for large datasets
- **Add benchmarks** for performance-critical code

Example of adding a performance test:

```python
@pytest.mark.benchmark
def test_isochrone_performance(benchmark):
    """Benchmark isochrone generation performance."""
    result = benchmark(create_isochrone, "Portland, OR", travel_time=15)
    assert result is not None
    # Performance assertions
    assert benchmark.stats['mean'] < 2.0  # Should complete in < 2 seconds
```

### Testing Requirements

We maintain high code quality with comprehensive testing:

- **Minimum coverage**: 80% for new code
- **Test types**: Unit, integration, and performance tests
- **Real API calls**: We test against real services (not mocks) where feasible
- **Test markers**: Use appropriate pytest markers

```python
@pytest.mark.unit
def test_validate_travel_time():
    """Test travel time validation logic."""
    assert validate_travel_time(15) == 15
    with pytest.raises(ValueError):
        validate_travel_time(150)  # Exceeds maximum

@pytest.mark.integration
@pytest.mark.external
def test_census_api_connection():
    """Test real Census API connectivity."""
    data = get_census_data("North Carolina")
    assert len(data) > 0
```

## Making Your Contribution

### Contribution Workflow

1. **Create an issue first** (if one doesn't exist)

   Before starting work, [open an issue](https://github.com/mihiarc/socialmapper/issues/new) or comment on an existing one. This helps:
   - Avoid duplicate work
   - Discuss the approach
   - Get early feedback

2. **Create a feature branch**

   ```bash
   # Update your main branch
   git checkout main
   git pull upstream main

   # Create a feature branch
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-number-description
   ```

3. **Make your changes**

   - Write clear, self-documenting code
   - Add tests for new functionality
   - Update documentation as needed
   - Follow our code standards

4. **Commit your changes**

   We follow conventional commit messages for clarity:

   ```bash
   # Format: <type>: <description>

   # Examples:
   git commit -m "feat: Add support for bicycle isochrones"
   git commit -m "fix: Correct census tract boundary calculation"
   git commit -m "docs: Update accessibility analysis tutorial"
   git commit -m "test: Add integration tests for POI search"
   git commit -m "perf: Optimize isochrone generation with caching"
   ```

   **Commit message types:**
   - `feat`: New feature
   - `fix`: Bug fix
   - `docs`: Documentation changes
   - `test`: Adding or updating tests
   - `perf`: Performance improvements
   - `refactor`: Code restructuring
   - `style`: Code formatting
   - `chore`: Maintenance tasks

   **Example of a good commit message:**

   ```
   feat: Add demographic filtering to POI analysis

   - Implement age and income filters for get_poi()
   - Add validation for demographic parameters
   - Include tests for edge cases
   - Update API documentation with examples

   Closes #67
   ```

5. **Run tests locally**

   ```bash
   # Run all tests
   uv run pytest

   # Run specific test file
   uv run pytest tests/test_api.py

   # Run with coverage
   uv run pytest --cov=socialmapper --cov-report=html

   # Run only fast tests
   uv run pytest -m "not slow"
   ```

6. **Push your branch**

   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**

   - Go to your fork on GitHub
   - Click "New Pull Request"
   - Select your feature branch
   - Fill out the PR template:

   ```markdown
   ## Description
   Brief description of what this PR does.

   ## Related Issue
   Fixes #(issue number)

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation update
   - [ ] Performance improvement

   ## Testing
   - [ ] Tests pass locally
   - [ ] Added new tests for changes
   - [ ] Updated documentation

   ## Screenshots (if applicable)
   Add any relevant screenshots here.

   ## Checklist
   - [ ] Code follows project style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated
   - [ ] Tests added/updated
   - [ ] All tests passing
   ```

### Code Review Process

After submitting your PR:

1. **Automated checks** run (tests, linting)
2. **Maintainer review** - usually within 48-72 hours
3. **Address feedback** - push additional commits as needed
4. **Approval and merge** - maintainers will merge when ready

**What we look for in reviews:**
- Code quality and style consistency
- Test coverage
- Documentation completeness
- Performance implications
- Security considerations

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test markers
uv run pytest -m unit           # Fast unit tests only
uv run pytest -m integration    # Integration tests
uv run pytest -m "not slow"     # Skip slow tests
uv run pytest -m performance    # Performance benchmarks

# Run tests for specific module
uv run pytest tests/test_api.py::TestCreateIsochrone

# Run with coverage report
uv run pytest --cov=socialmapper --cov-report=term-missing

# Run tests in parallel (faster)
uv run pytest -n auto
```

### Writing Tests

Place tests in the `tests/` directory following the pattern `test_*.py`:

```python
"""Test demographic analysis functions."""

import pytest
import pandas as pd
from socialmapper import analyze_demographics


class TestDemographicAnalysis:
    """Test suite for demographic analysis."""

    @pytest.fixture
    def sample_location(self):
        """Provide sample location for tests."""
        return "Durham, NC"

    @pytest.mark.unit
    def test_basic_analysis(self, sample_location):
        """Test basic demographic analysis returns expected structure."""
        result = analyze_demographics(sample_location)

        assert isinstance(result, pd.DataFrame)
        assert 'population' in result.columns
        assert len(result) > 0

    @pytest.mark.integration
    @pytest.mark.external
    def test_census_integration(self, sample_location):
        """Test integration with Census API."""
        result = analyze_demographics(
            sample_location,
            include_census=True
        )

        assert 'median_income' in result.columns
        assert result['median_income'].notna().any()
```

### Test Fixtures

Common fixtures are available in `tests/conftest.py`:

```python
@pytest.fixture
def mock_census_data():
    """Provide mock census data for testing."""
    return pd.DataFrame({
        'tract': ['001', '002'],
        'population': [5000, 3000],
        'median_income': [65000, 45000]
    })
```

## Documentation

### When to Update Documentation

Update documentation when you:
- Add new public functions or classes
- Change function signatures or behavior
- Add new examples or use cases
- Fix documentation errors
- Add new dependencies or requirements

### Building Documentation Locally

```bash
# Install documentation dependencies
uv pip install mkdocs mkdocs-material

# Build and serve documentation
uv run mkdocs serve

# View at http://localhost:8000
```

### Documentation Structure

```
docs/
├── index.md           # Home page
├── quick-start.md     # Getting started guide
├── tutorials/         # Step-by-step tutorials
├── api/              # API reference
├── examples/         # Code examples
└── contributing.md   # This file
```

### Adding Examples

Place example scripts in `examples/` and notebooks in `examples/notebooks/`:

```python
#!/usr/bin/env python
"""
Example: Analyzing Library Accessibility in Portland

This script demonstrates how to:
1. Find all libraries in a city
2. Calculate 15-minute walking areas
3. Analyze demographics of served populations
"""

from socialmapper import get_poi, create_isochrone, get_census_data

def main():
    # Find libraries in Portland
    libraries = get_poi("Portland, OR", "library")
    print(f"Found {len(libraries)} libraries")

    # Create walking isochrones
    for lib in libraries[:3]:  # First 3 for demo
        iso = create_isochrone(
            (lib['lat'], lib['lon']),
            travel_time=15,
            travel_mode="walk"
        )
        print(f"Library: {lib['name']}")
        print(f"Area covered: {iso['properties']['area_sq_km']:.2f} km²")

if __name__ == "__main__":
    main()
```

## Release Process

We follow [semantic versioning](https://semver.org/) (MAJOR.MINOR.PATCH):

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality, backwards compatible
- **PATCH**: Bug fixes, backwards compatible

### Release Checklist

1. **Update version** in `pyproject.toml`
2. **Update CHANGELOG.md** with release notes
3. **Run full test suite**: `uv run pytest`
4. **Build distribution**: `uv run python -m build`
5. **Create git tag**: `git tag -a v0.9.1 -m "Release version 0.9.1"`
6. **Push tag**: `git push upstream v0.9.1`

Releases are automatically deployed to PyPI when tags are pushed.

### Changelog Format

```markdown
## [0.9.1] - 2025-01-15

### Added
- Bicycle mode for isochrone generation
- Caching for geocoding requests

### Fixed
- Memory leak in large POI queries
- Incorrect census tract boundaries

### Changed
- Improved performance of demographic calculations by 40%

### Deprecated
- `analyze_area()` - use `analyze_region()` instead
```

## Getting Help

### Where to Ask Questions

- **🐛 Bug Reports**: [Open an issue](https://github.com/mihiarc/socialmapper/issues/new)
- **💬 Discussions**: [GitHub Discussions](https://github.com/mihiarc/socialmapper/discussions) for general questions
- **📧 Email**: Contact the maintainer for sensitive issues
- **📖 Documentation**: Check our [comprehensive docs](https://github.com/mihiarc/socialmapper/tree/main/docs)

### Response Times

- **Critical bugs**: Within 24 hours
- **Feature requests**: Within 72 hours
- **General questions**: Within 1 week
- **PR reviews**: Within 48-72 hours

### Tips for Getting Help

1. **Search first** - Check if your question has been answered
2. **Be specific** - Include error messages, code snippets, environment details
3. **Provide context** - Explain what you're trying to achieve
4. **Be patient** - Maintainers are volunteers

## Recognition

### Contributors

We value all contributions! Contributors are recognized in:

- **README.md**: Major contributors section
- **Release notes**: Credited for specific contributions
- **GitHub insights**: Automatic contribution tracking

### First-Time Contributors

Look for issues labeled ["good first issue"](https://github.com/mihiarc/socialmapper/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) - these are specifically chosen to be approachable for newcomers.

**Your first PR merged?** We'll add you to our contributors list! 🎉

### Types of Recognition

- **🌟 Core Contributors**: Regular contributors with merge rights
- **📖 Documentation Heroes**: Significant documentation improvements
- **🐛 Bug Hunters**: Finding and fixing critical bugs
- **🚀 Performance Champions**: Major performance improvements
- **💡 Feature Creators**: Implementing new capabilities

---

## Thank You! 💙

Thank you for contributing to SocialMapper! Your efforts help make spatial analysis more accessible and powerful for researchers, planners, and communities worldwide.

Together, we're building tools that help create more equitable, accessible communities.

**Ready to contribute?** Pick an [issue](https://github.com/mihiarc/socialmapper/issues), fork the repo, and let's build something amazing together!

---

*Last updated: January 2025 | Version: 1.0.0*