#!/usr/bin/env python3
"""Streamlit app entry point for SocialMapper."""

import sys
from socialmapper.ui import run_app
from socialmapper.core import set_quiet_logging

if __name__ == "__main__":
    # Set quiet logging by default for the Streamlit app to reduce console clutter
    set_quiet_logging()
    
    # Run the Streamlit app
    run_app()
    sys.exit(0) 