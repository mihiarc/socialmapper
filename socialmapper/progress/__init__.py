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
        A progress bar function (stqdm if in Streamlit context, tqdm otherwise)
    """
    # Use the environment detection done at import time
    progress_bar = stqdm if _IN_STREAMLIT else tqdm
    
    return progress_bar(iterable, **kwargs) if iterable is not None else progress_bar 