"""
Utilities for progress bars that work in both CLI and Streamlit contexts
"""

# Import tqdm as a fallback
from tqdm import tqdm

def get_progress_bar(iterable=None, **kwargs):
    """
    Return the appropriate progress bar based on the execution context
    
    Args:
        iterable: The iterable to wrap with a progress bar
        **kwargs: Additional arguments to pass to the progress bar
        
    Returns:
        A progress bar function (stqdm if in Streamlit context, tqdm otherwise)
    """
    # Defer checking for Streamlit context until the function is actually called
    # This prevents warnings at import time
    try:
        # Try to import Streamlit-related modules only when needed
        from stqdm import stqdm
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        
        # Check if we're in a Streamlit context
        if get_script_run_ctx() is not None:
            # We're in Streamlit environment
            progress_bar = stqdm
        else:
            # Not in Streamlit environment, use regular tqdm
            progress_bar = tqdm
    except (ImportError, ModuleNotFoundError):
        # Streamlit/stqdm is not available, use regular tqdm
        progress_bar = tqdm
    
    return progress_bar(iterable, **kwargs) if iterable is not None else progress_bar 