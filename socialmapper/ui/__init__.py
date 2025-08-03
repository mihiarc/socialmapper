"""UI module for SocialMapper.

DEPRECATION WARNING: The UI module is being separated from the backend package.
Streamlit UI functionality will be removed in a future version.
Please use the new separated React UI available at https://github.com/mihiarc/socialmapper-ui
"""

import warnings

# Issue deprecation warning when this module is imported
warnings.warn(
    "The socialmapper.ui module is deprecated and will be removed in a future version. "
    "Streamlit UI functionality is now available as a separate React application. "
    "Visit https://github.com/mihiarc/socialmapper-ui for the new UI. "
    "The console UI components will be moved to socialmapper.console.",
    DeprecationWarning,
    stacklevel=2
)

# This module contains CLI, Rich terminal UI, and Streamlit web UI components

from .compatibility import (
    check_ui_availability,
    show_migration_notice_if_needed,
    get_streamlit_app_factory,
    UICompatibilityWarning
)

# Show migration notice when UI module is imported
show_migration_notice_if_needed()

__all__ = [
    "check_ui_availability",
    "show_migration_notice_if_needed", 
    "get_streamlit_app_factory",
    "UICompatibilityWarning"
]
