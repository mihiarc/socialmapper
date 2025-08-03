"""Compatibility layer for UI imports during frontend-backend separation."""

import warnings
from typing import Optional, Any
from ..config.feature_flags import (
    get_feature_flags,
    is_monolithic_mode,
    is_separated_mode,
    should_show_migration_notice,
    get_ui_base_url
)


class UICompatibilityWarning(UserWarning):
    """Warning for UI compatibility issues."""
    pass


def check_ui_availability() -> bool:
    """Check if UI components are available in current mode."""
    flags = get_feature_flags()
    
    if is_monolithic_mode():
        return True
    elif is_separated_mode():
        if flags.allow_legacy_imports:
            if flags.deprecation_warnings:
                warnings.warn(
                    "Direct UI imports are deprecated. "
                    f"Please use the separated UI at {get_ui_base_url()} "
                    "or set SOCIALMAPPER_UI_MODE=monolithic to continue using embedded UI.",
                    UICompatibilityWarning,
                    stacklevel=3
                )
            return True
        else:
            return False
    
    return True


def show_migration_notice_if_needed():
    """Show migration notice if configured to do so."""
    if should_show_migration_notice():
        print("\n" + "="*60)
        print("🚀 SocialMapper UI Architecture Update")
        print("="*60)
        print("The UI is now available in separated mode!")
        print(f"• Frontend UI: {get_ui_base_url()}")
        print(f"• Backend API: {get_feature_flags().api_server_host}:{get_feature_flags().api_server_port}")
        print("\nTo use the new architecture:")
        print("1. Start the backend: cd socialmapper-api && ./setup-dev.sh")
        print("2. Start the frontend: cd socialmapper-ui && ./setup-dev.sh")
        print("\nTo disable this notice: set SOCIALMAPPER_SHOW_MIGRATION_NOTICE=false")
        print("="*60 + "\n")


def get_streamlit_app_factory():
    """Get the appropriate Streamlit app factory based on current mode."""
    if not check_ui_availability():
        raise ImportError(
            "UI components are not available in separated mode. "
            f"Please use the separated UI at {get_ui_base_url()}"
        )
    
    # Import the original streamlit app
    try:
        from .streamlit.app import main as streamlit_main
        return streamlit_main
    except ImportError as e:
        if is_separated_mode():
            raise ImportError(
                "Streamlit UI is not available in separated mode. "
                f"Please use the separated UI at {get_ui_base_url()}"
            ) from e
        raise


def create_compatibility_wrapper(module_name: str, original_import_path: str):
    """Create a compatibility wrapper for UI module imports."""
    def wrapper():
        if not check_ui_availability():
            raise ImportError(
                f"Module '{module_name}' is not available in separated mode. "
                f"Please use the separated UI at {get_ui_base_url()}"
            )
        
        # Dynamic import of the original module
        import importlib
        try:
            return importlib.import_module(original_import_path)
        except ImportError as e:
            if is_separated_mode():
                raise ImportError(
                    f"Module '{module_name}' is not available in separated mode. "
                    f"Please use the separated UI at {get_ui_base_url()}"
                ) from e
            raise
    
    return wrapper