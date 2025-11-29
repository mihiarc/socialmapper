# SocialMapper Notebooks

This directory is reserved for Jupyter notebooks demonstrating SocialMapper.

## Current Status

Interactive notebooks are planned for future releases. For now, use the Python examples in the parent directory:

```bash
# Run the demo (no API key needed)
uv run python examples/demo_quickstart.py

# Run the full example
uv run python examples/quick_start.py
```

## Quick Start with Python

```python
from socialmapper import demo

# No API key required!
result = demo.quick_start("Portland, OR")
print(f"Found {result['poi_count']} libraries")
```

## Resources

- [Quick Start Guide](../../docs/quick-start.md)
- [API Reference](../../docs/api-reference.md)
- [Example Scripts](../README.md)
