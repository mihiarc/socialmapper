#!/usr/bin/env python3
"""Launcher script for SocialMapper Streamlit app."""

import streamlit.web.cli as stcli
import sys
import os

if __name__ == "__main__":
    # Get the directory containing this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Build the path to the streamlit app
    streamlit_app_path = os.path.join(current_dir, "socialmapper", "streamlit_app.py")
    
    # Make sure socialmapper package is in the Python path
    sys.path.insert(0, current_dir)
    
    # Launch the Streamlit app
    sys.argv = ["streamlit", "run", streamlit_app_path]
    sys.exit(stcli.main()) 