"""SocialMapper Streamlit UI module."""

# Temporarily disable import to fix circular import issue
# from .app import main

def main():
    """Import and run the main function from app module"""
    from .app import main as app_main
    return app_main()

__all__ = ["main"]
