"""
Utilities for progress bars that work in both CLI and Streamlit contexts
"""

# Import tqdm as the default
from tqdm import tqdm

# Determine environment once at import time
_IN_STREAMLIT = False
try:
    # Use a safer way to detect Streamlit environment
    import streamlit as st
    from streamlit import runtime
    if runtime.exists():
        _IN_STREAMLIT = True
        # Only import stqdm if we're actually in Streamlit
        from stqdm import stqdm
except (ImportError, ModuleNotFoundError):
    pass

def get_progress_bar(iterable=None, **kwargs):
    """
    Return the appropriate progress bar based on the execution context
    
    Args:
        iterable: The iterable to wrap with a progress bar
        **kwargs: Additional arguments to pass to the progress bar
        
    Returns:
        A progress bar instance that can be used as a context manager
    """
    # Use the environment detection done at import time
    progress_bar_class = stqdm if _IN_STREAMLIT else tqdm
    
    # Always return an instance, not a class
    if iterable is not None:
        return progress_bar_class(iterable, **kwargs)
    else:
        # Create an instance with the provided kwargs
        return progress_bar_class(**kwargs) 