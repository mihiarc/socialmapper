# Installation Guide

This guide covers multiple ways to install SocialMapper depending on your needs and experience level.

## Quick Installation

=== "uv (Recommended)"

    ```bash
    uv pip install socialmapper
    ```

=== "pip (Alternative)"

    ```bash
    pip install socialmapper
    ```

=== "conda"

    ```bash
    # Add conda-forge channel if not already added
    conda config --add channels conda-forge
    
    # Install SocialMapper
    conda install socialmapper
    ```

## System Requirements

### Python Version
- **Python 3.11+** (minimum required)
- **Python 3.12** (recommended for best performance)
- **Python 3.13** (latest, fully supported)

### Operating Systems
- ✅ **Windows** 10/11
- ✅ **macOS** 10.15+ (Intel and Apple Silicon)
- ✅ **Linux** (Ubuntu 20.04+, CentOS 8+, and others)

### Hardware Recommendations
- **RAM**: 4GB minimum, 8GB+ recommended
- **Storage**: 1GB free space (for cache and outputs)
- **Internet**: Required for data downloads

## Installation Options

### Option 1: Standard Installation

For most users, the standard installation provides all core features:

```bash
uv pip install socialmapper
```

### Option 2: Development Installation with Enhanced Features

For development work and extended functionality:

```bash
uv pip install socialmapper[dev]
```

This includes additional dependencies for:
- 🔧 Development tools (testing, linting, formatting)
- 📊 Enhanced analysis capabilities
- 🎨 Rich terminal UI features

### Option 3: Development Installation

For contributors and developers:

```bash
# Clone the repository
git clone https://github.com/mihiarc/socialmapper.git
cd socialmapper

# Install in development mode with all dependencies
uv pip install -e .[dev]
```

### Option 4: Minimal Installation

Note: The `[minimal]` extra is not currently available. The standard installation already provides a lightweight experience.

## Dependency Management

### Using uv (Recommended)

According to a memory from a past conversation, you should use 'uv' as the package management tool for installing and managing Python dependencies in this project instead of pip.

```bash
# Install uv
pip install uv

# Create a new project with SocialMapper
uv init my-socialmapper-project
cd my-socialmapper-project
uv add socialmapper

# Or add to existing project
uv add socialmapper
```

### Using pip with virtual environments

```bash
# Create virtual environment
python -m venv socialmapper-env

# Activate (Windows)
socialmapper-env\Scripts\activate

# Activate (macOS/Linux)
source socialmapper-env/bin/activate

# Install SocialMapper
pip install socialmapper
```

## Verify Installation

Test your installation with these commands:

```bash
# Check version
uv run python -c "import socialmapper; print(socialmapper.__version__)"

# Quick test import
uv run python -c "from socialmapper import create_isochrone, get_census_data; print('✅ Installation successful!')"
```

## Optional: API Keys

While SocialMapper works without API keys, some features are enhanced with them:

### Census Bureau API Key (Recommended)
- **Benefit**: Faster census data downloads
- **Get key**: [Census API Registration](https://api.census.gov/data/key_signup.html)
- **Setup**: `export CENSUS_API_KEY="your_key_here"`

### Google Maps API Key (Optional)
- **Benefit**: Enhanced geocoding accuracy
- **Get key**: [Google Cloud Console](https://console.cloud.google.com/)
- **Setup**: `export GOOGLE_MAPS_API_KEY="your_key_here"`

## Common Installation Issues

### Issue: "No module named 'socialmapper'"

**Solution**:
```bash
# Ensure you're in the right environment
which python
pip list | grep socialmapper

# Reinstall if needed
pip uninstall socialmapper
pip install socialmapper
```

### Issue: Dependency conflicts

**Solution**: Use a fresh virtual environment:
```bash
python -m venv fresh-env
source fresh-env/bin/activate  # or fresh-env\Scripts\activate on Windows
pip install socialmapper
```

### Issue: Network/SSL errors

**Solution**: Update certificates and try again:
```bash
# macOS
/Applications/Python\ 3.x/Install\ Certificates.command

# Or use trusted hosts
pip install --trusted-host pypi.org --trusted-host pypi.python.org socialmapper
```

### Issue: Permission errors (Linux/macOS)

**Solution**: Use user installation:
```bash
pip install --user socialmapper
```

### Issue: Missing system dependencies (Linux)

**Solution**: Install system packages:
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-dev python3-pip build-essential

# CentOS/RHEL
sudo yum install python3-devel python3-pip gcc
```

## Platform-Specific Notes

### Windows
- Use **Command Prompt** or **PowerShell** (avoid Git Bash for installation)
- Consider **Windows Subsystem for Linux (WSL)** for a Linux-like experience
- **Visual Studio Build Tools** may be needed for some dependencies

### macOS
- **Xcode Command Line Tools** required: `xcode-select --install`
- **Homebrew** recommended for Python management: `brew install python`
- **Apple Silicon (M1/M2)**: All dependencies are compatible

### Linux
- Most distributions include Python, but you may need `python3-pip`
- **GDAL** and **spatial libraries** are included in the package
- **Build tools** (`gcc`, `make`) may be required

## Next Steps

After successful installation:

1. 📖 **Read** the [Quick Start Guide](quick-start.md)
2. 🎯 **Explore** the [Examples](https://github.com/mihiarc/socialmapper/tree/main/examples)
3. 💻 **Learn** about [Finding Places](../user-guide/finding-places.md)
4. 🔧 **Get** a [Census API key](https://census.gov/developers) (optional)

## Getting Help

If you encounter issues:

1. 📚 **Check** this documentation
2. 🔍 **Search** [GitHub Issues](https://github.com/mihiarc/socialmapper/issues)
3. 🐛 **Report** new issues with:
   - Your Python version (`python --version`)
   - Your OS and version
   - Complete error messages
   - Installation method used

---

**Ready to start?** Continue to the [Quick Start Guide](quick-start.md)! 