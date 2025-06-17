"""Path security utilities for safe file operations."""

from pathlib import Path


class PathSecurityError(Exception):
    """Raised when a path operation is deemed unsafe."""


def sanitize_path(
    user_path: str | Path,
    base_dir: str | Path | None = None,
    allow_absolute: bool = False,
    follow_symlinks: bool = False,
) -> Path:
    """Sanitize and validate a user-provided path to prevent directory traversal attacks.

    Args:
        user_path: The path provided by the user
        base_dir: The base directory to resolve relative paths against.
                 If None, uses current working directory.
        allow_absolute: Whether to allow absolute paths. Default False.
        follow_symlinks: Whether to follow symbolic links. Default False.

    Returns:
        A sanitized Path object that is safe to use

    Raises:
        PathSecurityError: If the path is deemed unsafe

    Examples:
        >>> sanitize_path("../../../etc/passwd", "/app/data")
        Raises PathSecurityError

        >>> sanitize_path("subdir/file.txt", "/app/data")
        Path('/app/data/subdir/file.txt')
    """
    # Convert to Path objects
    user_path = Path(user_path)
    base_dir = Path(base_dir) if base_dir else Path.cwd()

    # Ensure base directory is absolute
    base_dir = base_dir.resolve()

    # Check for null bytes (common in path injection attacks)
    if "\x00" in str(user_path):
        raise PathSecurityError("Path contains null bytes")

    # Check for suspicious patterns
    suspicious_patterns = [
        "..",  # Parent directory traversal
        "~",  # Home directory expansion
        "$",  # Environment variable expansion
        "\\",  # Windows path separator on Unix
    ]

    path_str = str(user_path)
    for pattern in suspicious_patterns:
        if pattern in path_str:
            # Allow .. only if it doesn't escape base directory
            if pattern == ".." and not _escapes_base_dir(user_path, base_dir):
                continue
            raise PathSecurityError(f"Path contains suspicious pattern: {pattern}")

    # Handle absolute paths
    if user_path.is_absolute():
        if not allow_absolute:
            raise PathSecurityError("Absolute paths are not allowed")
        resolved_path = user_path
    else:
        # Resolve relative to base directory
        resolved_path = base_dir / user_path

    # Resolve the path (follows symlinks by default)
    try:
        if follow_symlinks:
            final_path = resolved_path.resolve()
        else:
            final_path = resolved_path.resolve(strict=False)
            # Check if any part of the path is a symlink
            if _contains_symlink(final_path):
                raise PathSecurityError("Path contains symbolic links")
    except (OSError, RuntimeError) as e:
        raise PathSecurityError(f"Path resolution failed: {e}") from e

    # Ensure the final path is within the base directory
    if not allow_absolute:
        try:
            final_path.relative_to(base_dir)
        except ValueError:
            raise PathSecurityError(f"Path '{final_path}' is outside base directory '{base_dir}'") from None

    return final_path


def _escapes_base_dir(path: Path, base_dir: Path) -> bool:
    """Check if a path would escape the base directory."""
    try:
        # Try to resolve the path relative to base_dir
        resolved = (base_dir / path).resolve()
        resolved.relative_to(base_dir)
        return False
    except (ValueError, OSError):
        return True


def _contains_symlink(path: Path) -> bool:
    """Check if any component of the path is a symbolic link."""
    # Check each parent directory
    for parent in path.parents:
        if parent.exists() and parent.is_symlink():
            return True
    # Check the path itself
    return bool(path.exists() and path.is_symlink())


def safe_join_path(base: str | Path, *parts: str | Path) -> Path:
    """Safely join path components, ensuring the result stays within base directory.

    Args:
        base: The base directory
        *parts: Path components to join

    Returns:
        A safe joined path

    Raises:
        PathSecurityError: If the resulting path would escape base directory
    """
    base = Path(base).resolve()

    # Join all parts
    joined = base
    for part in parts:
        # Sanitize each part
        if str(part).startswith("/"):
            raise PathSecurityError("Path components cannot be absolute")
        joined = joined / part

    # Sanitize the final result
    return sanitize_path(joined, base_dir=base)


def validate_filename(filename: str, allow_hidden: bool = False) -> str:
    """Validate a filename to ensure it's safe to use.

    Args:
        filename: The filename to validate
        allow_hidden: Whether to allow hidden files (starting with .)

    Returns:
        The validated filename

    Raises:
        PathSecurityError: If the filename is invalid
    """
    # Check for empty filename
    if not filename or filename.isspace():
        raise PathSecurityError("Filename cannot be empty")

    # Check for path separators
    if "/" in filename or "\\" in filename:
        raise PathSecurityError("Filename cannot contain path separators")

    # Check for special filenames
    invalid_names = {
        ".",
        "..",
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }

    if filename.upper() in invalid_names:
        raise PathSecurityError(f"Invalid filename: {filename}")

    # Check for hidden files
    if filename.startswith(".") and not allow_hidden:
        raise PathSecurityError("Hidden files are not allowed")

    # Check for invalid characters
    invalid_chars = '<>:"|?*\x00'
    for char in invalid_chars:
        if char in filename:
            raise PathSecurityError(f"Filename contains invalid character: {char}")

    # Check length (255 is typical filesystem limit)
    if len(filename) > 255:
        raise PathSecurityError("Filename is too long (max 255 characters)")

    return filename


# Convenience function for the most common use case
def get_safe_cache_path(filename: str, cache_dir: str | Path) -> Path:
    """Get a safe path for a cache file.

    Args:
        filename: The cache filename
        cache_dir: The cache directory

    Returns:
        A safe path for the cache file
    """
    # Validate the filename
    safe_filename = validate_filename(filename)

    # Create safe path
    return safe_join_path(cache_dir, safe_filename)
