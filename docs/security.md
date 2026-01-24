# SocialMapper Security Guide

## Overview

SocialMapper uses API keys to access external data sources. This guide covers how to securely configure and use API keys.

## API Key Configuration

### Census API Key

The Census API key is required for live demographic data. Get a free key at: https://api.census.gov/data/key_signup.html

#### Option 1: Environment Variable (Recommended)

```bash
# Set in your shell
export CENSUS_API_KEY="your_api_key_here"

# Or add to your shell profile (~/.bashrc, ~/.zshrc)
echo 'export CENSUS_API_KEY="your_api_key_here"' >> ~/.zshrc
```

#### Option 2: .env File

Create a `.env` file in your project directory:

```bash
# .env
CENSUS_API_KEY=your_api_key_here
```

SocialMapper automatically loads `.env` files using python-dotenv.

#### Option 3: Set in Code (Not Recommended for Production)

```python
import os
os.environ['CENSUS_API_KEY'] = 'your_api_key_here'

from socialmapper import get_census_data
# Now census functions will work
```

## Demo Mode (No API Key Required)

You can explore SocialMapper without any API keys using demo mode:

```python
from socialmapper import demo

# List available demo cities
demo.list_available_demos()

# Run analysis with pre-cached data
result = demo.quick_start("Portland, OR")
```

## Security Best Practices

### 1. Never Commit Keys to Version Control

Add to your `.gitignore`:

```
.env
.env.local
.env.*.local
```

### 2. Use Environment Variables in Production

Environment variables are the most secure way to manage API keys:

```python
import os

# Check if key is configured
if not os.environ.get("CENSUS_API_KEY"):
    print("Warning: CENSUS_API_KEY not set")
```

### 3. Validate API Keys

Test your configuration before running analysis:

```python
from socialmapper import get_census_data

try:
    # Test with a simple query
    data = get_census_data(
        location=(35.7796, -78.6382),
        variables=["population"]
    )
    print("API key is working!")
except Exception as e:
    print(f"API key error: {e}")
```

### 4. Rate Limiting

SocialMapper respects API rate limits:

- **Census API**: 500 requests per day (free tier)
- **Nominatim**: 1 request per second
- **Overpass API**: Reasonable use policy

The library includes automatic caching to minimize API calls.

## Environment Variables Reference

| Variable | Description | Required |
|----------|-------------|----------|
| `CENSUS_API_KEY` | US Census Bureau API key | For live data |
| `SOCIALMAPPER_CACHE_DIR` | Custom cache directory | No |

## Getting Your Census API Key

1. Visit https://api.census.gov/data/key_signup.html
2. Fill out the form with your email
3. Check your email for the API key (instant)
4. Set the environment variable as shown above

## Support

For security issues or questions:
- Open an issue: https://github.com/mihiarc/socialmapper/issues
- Security vulnerabilities: Contact maintainers directly

**Remember: Never share your API keys publicly or commit them to version control!**
