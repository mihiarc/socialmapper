# SocialMapper Security Guide

## Overview

SocialMapper now includes secure API key management to protect your credentials. This guide covers how to securely store and use API keys with SocialMapper.

## Quick Start

### 1. Install Security Dependencies

```bash
# Install with security features
pip install socialmapper[security]

# Or install individual dependencies
pip install keyring cryptography
```

### 2. Store Your API Keys Securely

```bash
# Store Census API key (recommended method)
python -m socialmapper.security.cli set census_api YOUR_API_KEY

# Verify key is stored
python -m socialmapper.security.cli get census_api

# List all stored keys
python -m socialmapper.security.cli list
```

### 3. Use Keys in Your Code

```python
from socialmapper import SocialMapper

# Keys are automatically loaded from secure storage
mapper = SocialMapper()  # No need to pass API key

# Or explicitly get a key
from socialmapper.security.utils import get_api_key
api_key = get_api_key("census_api")
```

## Storage Backends

SocialMapper supports multiple secure storage backends, automatically selecting the most secure available option:

### 1. System Keyring (Recommended)
- **Windows**: Windows Credential Vault
- **macOS**: Keychain
- **Linux**: Secret Service API (GNOME Keyring, KWallet)

```python
from socialmapper.security import SecureKeyManager, KeyStorage

manager = SecureKeyManager()
manager.set_key("census_api", "your_key", KeyStorage.KEYRING)
```

### 2. Encrypted File Storage
Keys are encrypted using Fernet symmetric encryption and stored in `~/.socialmapper/keys.enc`

```python
manager.set_key("census_api", "your_key", KeyStorage.ENCRYPTED_FILE)
```

### 3. Environment Variables (Fallback)
For backward compatibility, environment variables are still supported as a fallback:

```bash
export CENSUS_API_KEY="your_api_key"
```

## Migration from Environment Variables

If you have existing API keys in environment variables, migrate them to secure storage:

```bash
# Automatic migration
python -m socialmapper.security.cli migrate

# Manual migration
python -c "from socialmapper.security.utils import migrate_from_env; migrate_from_env()"
```

## Python API

### Basic Usage

```python
from socialmapper.security import SecureKeyManager

# Create key manager
manager = SecureKeyManager()

# Store a key
manager.set_key("census_api", "your_api_key")

# Retrieve a key
api_key = manager.get_key("census_api")

# Delete a key
manager.delete_key("census_api")

# Validate key format
is_valid = manager.validate_key("census_api", "test_key")
```

### Advanced Usage

```python
# Use temporary keys
with manager.temporary_key("census_api", "temporary_key"):
    # Temporary key is active here
    api_key = manager.get_key("census_api")
# Original key is restored

# List all keys
keys = manager.list_keys()
# {'keyring': ['census_api'], 'environment': ['MAPBOX_TOKEN']}

# Custom storage configuration
manager = SecureKeyManager(
    app_name="my_app",
    config_path="~/my_app/keys.enc",
    storage_preference=[KeyStorage.ENCRYPTED_FILE, KeyStorage.ENVIRONMENT]
)
```

## Command-Line Interface

```bash
# Store a key
python -m socialmapper.security.cli set census_api YOUR_KEY

# Store with specific backend
python -m socialmapper.security.cli set census_api YOUR_KEY --storage keyring

# Get a key (masked by default)
python -m socialmapper.security.cli get census_api

# Show full key value
python -m socialmapper.security.cli get census_api --show

# Delete a key
python -m socialmapper.security.cli delete census_api

# Delete from all backends
python -m socialmapper.security.cli delete census_api --all

# Validate a key
python -m socialmapper.security.cli validate census_api

# List all keys
python -m socialmapper.security.cli list

# Migrate from environment
python -m socialmapper.security.cli migrate
```

## Security Best Practices

### 1. Never Commit Keys
Add to `.gitignore`:
```
.env
*.key
*.enc
~/.socialmapper/
```

### 2. Use Different Keys for Different Environments
```python
# Development
manager.set_key("census_api_dev", dev_key)

# Production
manager.set_key("census_api_prod", prod_key)
```

### 3. Rotate Keys Regularly
```python
# Store new key
manager.set_key("census_api", new_key)

# Validate new key works
if validate_api_key("census_api", new_key):
    # Remove old key
    manager.delete_key("census_api_old")
```

### 4. Restrict File Permissions
Encrypted key files are automatically created with restricted permissions (600), but verify:
```bash
ls -la ~/.socialmapper/
# Should show: -rw------- for .master.key and keys.enc
```

### 5. Use Context Managers for Temporary Access
```python
# Keys are only available within context
with manager.temporary_key("api_key", sensitive_value):
    perform_api_call()
# Key is automatically cleaned up
```

## Troubleshooting

### Keyring Not Available
If keyring is not available on your system:
```bash
# Linux: Install system keyring
sudo apt-get install gnome-keyring  # Debian/Ubuntu
sudo yum install gnome-keyring      # RHEL/CentOS

# Or use encrypted file storage instead
python -m socialmapper.security.cli set census_api YOUR_KEY --storage encrypted
```

### Permission Denied Errors
```bash
# Fix permissions on key files
chmod 600 ~/.socialmapper/.master.key
chmod 600 ~/.socialmapper/keys.enc
```

### Lost Master Key
If you lose the master key for encrypted storage:
```bash
# Remove encrypted files
rm -rf ~/.socialmapper/

# Re-initialize and re-add keys
python -m socialmapper.security.cli set census_api YOUR_KEY
```

## Environment Variable Compatibility

For backward compatibility, the following environment variables are still checked as fallbacks:
- `CENSUS_API_KEY` - US Census Bureau API key
- `MAPBOX_TOKEN` - Mapbox access token
- `GOOGLE_MAPS_API_KEY` - Google Maps API key

However, we strongly recommend migrating to secure storage.

## Security Considerations

1. **Keyring Security**: System keyrings are generally secure but depend on OS implementation
2. **Encrypted Files**: Use Fernet (AES-128) encryption with PBKDF2 key derivation
3. **Master Key**: Stored separately from encrypted data with restricted permissions
4. **Memory Safety**: Keys are not logged or included in error messages
5. **Process Safety**: Keys in environment variables can be visible in process listings

## Support

For security issues or questions:
- Open an issue: https://github.com/mihiarc/socialmapper/issues
- Security vulnerabilities: Contact maintainers directly

Remember: **Never share your API keys publicly or commit them to version control!**