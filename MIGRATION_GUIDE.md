# SocialMapper v0.7.0 Migration Guide

This guide helps you migrate from SocialMapper v0.6.x to v0.7.0, which introduces a major architectural change separating the frontend and backend components.

## Overview of Changes

### Architecture Separation
- **Backend**: Core SocialMapper functionality is now available as a standalone package without UI dependencies
- **Frontend**: UI components (Streamlit) are now optional and will eventually be replaced by a modern React application
- **API**: New FastAPI-based REST API enables programmatic access to all functionality

### Installation Changes
```bash
# Old (v0.6.x) - Installed everything including UI
pip install socialmapper

# New (v0.7.0) - Choose what you need
pip install socialmapper          # Backend only (CLI, Python API)
pip install socialmapper[ui]      # Backend + Streamlit UI (deprecated)
```

## Migration Paths

### 1. Command Line Users

**No changes required!** The CLI interface remains fully compatible:

```bash
# These commands work exactly the same in v0.7.0
socialmapper --poi --geocode-area "Boston" --poi-type "amenity" --poi-name "school"
socialmapper --custom-coords 40.7128 -74.0060 --travel-time 20
socialmapper --addresses "addresses.csv" --poi-type "shop" --poi-name "grocery"
```

### 2. Python API Users

The Python API remains fully compatible with enhanced features:

```python
# Existing code continues to work
from socialmapper import SocialMapperClient

with SocialMapperClient() as client:
    result = client.analyze(
        location="Seattle, WA",
        poi_type="amenity",
        poi_name="hospital",
        travel_time=15
    )
```

### 3. Streamlit Dashboard Users

The Streamlit UI is deprecated but still available during the transition period.

#### Option A: Continue Using Streamlit (Temporary)

```bash
# Install with UI support
pip install socialmapper[ui]

# Run as before
streamlit run streamlit_app.py
```

**Note**: You'll see deprecation warnings. The Streamlit UI will be removed in v0.8.0.

#### Option B: Switch to the Modern React UI (Recommended)

1. **Start the API Server**:
   ```bash
   cd socialmapper-api
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

2. **Start the React Frontend**:
   ```bash
   # Clone the frontend repository
   git clone https://github.com/mihiarc/socialmapper-ui.git
   cd socialmapper-ui
   
   # Install and run
   npm install
   npm run dev
   ```

3. **Access the UI** at http://localhost:3000

Benefits of the new UI:
- Modern, responsive design
- Real-time updates
- Better performance
- Enhanced visualizations
- Mobile-friendly

#### Option C: Use the REST API Directly

The new REST API provides full access to SocialMapper functionality:

```python
import httpx
import asyncio

async def analyze_location():
    async with httpx.AsyncClient() as client:
        # Start analysis
        response = await client.post(
            "http://localhost:8000/api/v1/analysis/location",
            json={
                "name": "Library Analysis",
                "latitude": 42.3601,
                "longitude": -71.0589,
                "travel_time_minutes": 15,
                "travel_mode": "walking",
                "poi_types": ["library"]
            }
        )
        job_id = response.json()["job_id"]
        
        # Check status
        status = await client.get(
            f"http://localhost:8000/api/v1/analysis/{job_id}/status"
        )
        print(status.json())

asyncio.run(analyze_location())
```

### 4. Package Developers

If you're importing SocialMapper in your own package:

#### Import Changes

```python
# ❌ Old imports (will show deprecation warnings)
from socialmapper.ui import StreamlitApp
from socialmapper.ui.console import print_info

# ✅ New imports
from socialmapper.console import print_info, get_logger
# Streamlit components should not be imported directly
```

#### Dependency Updates

Update your `requirements.txt` or `pyproject.toml`:

```toml
# Old
dependencies = ["socialmapper>=0.6.0"]

# New - Choose based on your needs
dependencies = ["socialmapper>=0.7.0"]           # Backend only
# or
dependencies = ["socialmapper[ui]>=0.7.0"]       # With UI (temporary)
```

## Breaking Changes

### 1. Module Reorganization

- `socialmapper.ui.console` → `socialmapper.console`
- UI components in `socialmapper.ui.streamlit` will be removed in v0.8.0

### 2. Environment Variables

New environment variables for API configuration:
```bash
# API Server Settings
SOCIALMAPPER_API_HOST=0.0.0.0
SOCIALMAPPER_API_PORT=8000

# CORS (for frontend integration)
SOCIALMAPPER_API_CORS_ORIGINS=["http://localhost:3000"]

# Optional Authentication
SOCIALMAPPER_API_KEY_ENABLED=false
SOCIALMAPPER_API_KEYS=["your-secret-key"]
```

### 3. Feature Flags

Control the transition with feature flags:
```bash
# Use monolithic mode (old behavior)
SOCIALMAPPER_UI_MODE=monolithic

# Use separated mode (new architecture)
SOCIALMAPPER_UI_MODE=separated

# Show migration notices
SOCIALMAPPER_SHOW_MIGRATION_NOTICE=true
```

## Deprecation Timeline

- **v0.7.0** (Current): Streamlit UI optional, deprecation warnings added
- **v0.8.0** (Q2 2025): Streamlit UI removed, React UI becomes primary
- **v1.0.0** (Q3 2025): Legacy compatibility removed, API-first architecture

## Common Migration Scenarios

### Scenario 1: Research Scripts

If you have research scripts using SocialMapper:

```python
# Your existing scripts continue to work unchanged
import socialmapper as sm

# This still works
result = sm.analyze_location(
    location="Denver, CO",
    poi_type="leisure",
    poi_name="park"
)
```

### Scenario 2: Automated Pipelines

For automated data pipelines:

```python
# Consider switching to async API for better performance
import asyncio
from socialmapper import SocialMapperClient

async def batch_analysis(locations):
    async with SocialMapperClient() as client:
        tasks = []
        for loc in locations:
            task = client.analyze_async(
                location=loc,
                poi_type="amenity",
                poi_name="school"
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return results
```

### Scenario 3: Web Applications

If you're building a web app with SocialMapper:

1. **Use the REST API** for maximum flexibility
2. **Consider the React UI** as a starting point
3. **Implement your own frontend** using the API

## Troubleshooting

### Import Errors

```python
# If you see: ImportError: cannot import name 'StreamlitApp'
# Solution: Install with UI support
pip install socialmapper[ui]
```

### Deprecation Warnings

```python
# To suppress deprecation warnings temporarily
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Better: Update your code to use new imports
```

### API Connection Issues

```bash
# If the API isn't responding
# Check if the server is running
curl http://localhost:8000/api/v1/health

# Start the server if needed
cd socialmapper-api && uvicorn main:app
```

## Getting Help

- **Documentation**: [Full Documentation](https://socialmapper.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/mihiarc/socialmapper/issues)
- **Examples**: [Migration Examples](examples/migration/)

## Best Practices

1. **Test in a virtual environment** before upgrading production systems
2. **Review deprecation warnings** and update code accordingly
3. **Consider the REST API** for new projects
4. **Plan for Streamlit removal** if you're using the UI

## FAQ

**Q: Will my existing scripts break?**
A: No, the CLI and Python API remain backward compatible.

**Q: When will Streamlit be removed?**
A: Streamlit will be removed in v0.8.0 (planned for Q2 2025).

**Q: Can I use both UIs during migration?**
A: Yes, you can run both the Streamlit and React UIs simultaneously.

**Q: Is the REST API stable?**
A: Yes, the REST API follows semantic versioning and is production-ready.

**Q: How do I report migration issues?**
A: Please open an issue on [GitHub](https://github.com/mihiarc/socialmapper/issues) with the "migration" label.