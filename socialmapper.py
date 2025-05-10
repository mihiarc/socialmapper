#!/usr/bin/env python3
"""
Compatibility wrapper for SocialMapper.

This file provides backward compatibility for scripts that imported from socialmapper.py.
It simply imports and re-exports the functions from the proper package.
"""

import sys
from socialmapper.core import run_socialmapper, setup_directories
from socialmapper.cli import main

if __name__ == "__main__":
    sys.exit(main()) 