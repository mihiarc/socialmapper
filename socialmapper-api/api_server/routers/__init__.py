"""
API routers for different endpoint groups.
"""

from . import health
from . import analysis
from . import results
from . import metadata

__all__ = ["health", "analysis", "results", "metadata"]