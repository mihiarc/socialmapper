# SocialMapper - Claude Integration Guide

SocialMapper is a comprehensive platform for community accessibility analysis and demographic mapping.

## Table of Contents

- [Quick Start](#quick-start)
- [Docker Setup](#docker-setup)
- [Documentation Standards](#documentation-standards)

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Census API key (free from https://api.census.gov/data/key_signup.html)
- Docker and Docker Compose (for containerized setup)

### Installation

```bash
# Clone the repository
git clone https://github.com/mihiarc/socialmapper.git
cd socialmapper

# Create virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e .

# Copy and configure environment
cp .env.example .env
# Edit .env with your Census API key
```

### Basic Usage

Run the SocialMapper application:

```bash
uv run python -m socialmapper
```

## Docker Setup

### Development Environment

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Production Environment

```bash
# Use production configuration
docker-compose -f docker-compose.prod.yml up -d
```

## Documentation Standards

### NumPy Style Docstrings

All API functions MUST use NumPy-style docstrings for consistency and clarity. This format is preferred for scientific Python libraries and provides excellent structure for detailed documentation.

#### Required Sections

1. **Short summary** (mandatory) - One-line description
2. **Extended description** (if needed) - More detailed explanation
3. **Parameters** - All function parameters with types and descriptions
4. **Returns** - Return value types and descriptions
5. **Examples** - Doctests showing usage

#### Format Guidelines

- Line length: Maximum 75 characters for readability in terminals
- Use triple quotes `"""` for all docstrings
- Section headers should be underlined with hyphens
- Parameter types should follow NumPy conventions (e.g., `array_like`, `int`, `str`, `optional`)
- Examples should be in doctest format and be executable

#### Example Template

```python
def function_name(param1, param2, param3=None):
    """
    Short one-line summary that fits in 75 chars.

    Extended description providing more details about the function,
    its behavior, and any important notes for users.

    Parameters
    ----------
    param1 : type
        Description of param1.
    param2 : type
        Description of param2.
    param3 : type, optional
        Description of param3, by default None.

    Returns
    -------
    return_type
        Description of return value.

    Examples
    --------
    >>> function_name("example", 42)
    'Expected output'

    >>> function_name("test", 100, param3="optional")
    'Another example'
    """
```

#### Special Sections (use when applicable)

- **Raises** - Exceptions that may be raised
- **See Also** - Related functions or classes
- **Notes** - Algorithm details or mathematical formulas
- **References** - Citations to papers or external docs
- **Yields** - For generator functions instead of Returns

