#!/usr/bin/env python3
"""Standalone cache management script for SocialMapper."""

import sys
from pathlib import Path

# Add parent directory to path to import socialmapper
sys.path.insert(0, str(Path(__file__).parent.parent))

from socialmapper.cli.cache import app

if __name__ == "__main__":
    app()
