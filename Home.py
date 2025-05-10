#!/usr/bin/env python3
"""
SocialMapper Streamlit App Compatibility Wrapper.

This file provides backward compatibility for the original Home.py entry point.
"""

import sys
from socialmapper.ui import run_app

if __name__ == "__main__":
    run_app()
    sys.exit(0) 