"""
Setup script for backward compatibility with older pip versions that don't fully support pyproject.toml.
This shouldn't be needed for modern installations, but is provided for convenience.
"""

from setuptools import setup

if __name__ == "__main__":
    setup() 