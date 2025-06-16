#!/bin/bash
# Run the SocialMapper Streamlit dashboard with uv

# Set Streamlit theme configuration
export STREAMLIT_THEME_BASE="light"
export STREAMLIT_THEME_PRIMARY_COLOR="#1f77b4"
export STREAMLIT_THEME_BACKGROUND_COLOR="#ffffff"
export STREAMLIT_THEME_SECONDARY_BACKGROUND_COLOR="#f0f2f6"
export STREAMLIT_THEME_TEXT_COLOR="#262730"
export STREAMLIT_THEME_FONT="sans serif"

# Run the Streamlit app with uv
uv run streamlit run streamlit_app.py --server.port 8501 --server.address localhost