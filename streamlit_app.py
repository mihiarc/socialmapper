"""SocialMapper Interactive Tutorial Application

This is the main entry point for the SocialMapper Streamlit application.
The app provides interactive tutorials that mirror the documentation examples,
allowing users to learn SocialMapper through hands-on experience.

Run with: streamlit run streamlit_app.py
"""

from socialmapper.ui.streamlit.app import main

if __name__ == "__main__":
    main()