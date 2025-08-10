#!/usr/bin/env python3
"""Type checking integration for SocialMapper using ty.

This script provides convenient commands for running type checks
with ty, Astral's ultra-fast Python type checker.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_ty_check(
    paths: list[str] | None = None, strict: bool = False, verbose: bool = False
) -> int:
    """Run ty type checking on the specified paths.

    Args:
        paths: List of paths to check. If None, checks entire socialmapper package
        strict: Enable strict mode for comprehensive type checking
        verbose: Enable verbose output

    Returns:
        Exit code (0 for success, non-zero for failures)
    """
    cmd = ["uv", "run", "ty", "check"]

    # Add paths or default to socialmapper package
    if paths:
        cmd.extend(paths)
    else:
        cmd.append("socialmapper/")

    # Add flags
    if strict:
        cmd.append("--strict")
    if verbose:
        cmd.append("--verbose")

    print(f"🔍 Running ty type checker: {' '.join(cmd)}")
    print("=" * 60)

    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n❌ Type checking interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error running ty: {e}")
        return 1


def main():
    """Main CLI interface for ty type checking."""
    parser = argparse.ArgumentParser(
        description="Type checking for SocialMapper using ty",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check entire codebase
  python scripts/type_check.py

  # Check specific files/modules
  python scripts/type_check.py socialmapper/api/ socialmapper/census/

  # Run in strict mode
  python scripts/type_check.py --strict

  # Verbose output
  python scripts/type_check.py --verbose
        """,
    )

    parser.add_argument("paths", nargs="*", help="Paths to type check (default: socialmapper/)")

    parser.add_argument("--strict", action="store_true", help="Enable strict type checking mode")

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    # Ensure we're in the project root
    project_root = Path(__file__).parent.parent
    if not (project_root / "pyproject.toml").exists():
        print("❌ Error: Must be run from project root directory")
        sys.exit(1)

    # Run type checking
    exit_code = run_ty_check(
        paths=args.paths if args.paths else None, strict=args.strict, verbose=args.verbose
    )

    if exit_code == 0:
        print("\n✅ Type checking completed successfully!")
    else:
        print(f"\n❌ Type checking failed with {exit_code} issues found")
        print("💡 Tip: Use 'ty check --help' for more options")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
