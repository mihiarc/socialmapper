"""
SocialMapper: Explore Community Connections.

An open-source Python toolkit that helps understand 
community connections through mapping demographics and access to points of interest.
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("socialmapper")
except PackageNotFoundError:
    # Package is not installed
    try:
        from . import _version
        __version__ = _version.__version__
    except (ImportError, AttributeError):
        __version__ = "0.3.0-alpha"  # fallback

# Import main functionality
from .core import run_socialmapper, setup_directory

__all__ = [
    "run_socialmapper",
    "setup_directory",
] 