#!/bin/bash
# Ruff utility script for SocialMapper
# This script provides convenient commands for linting and formatting

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[RUFF]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Default target directory
TARGET=${1:-"socialmapper/"}

case "${2:-check}" in
    "check")
        print_status "Running Ruff linter on $TARGET..."
        uv run ruff check "$TARGET"
        ;;
    "fix")
        print_status "Running Ruff linter with auto-fixes on $TARGET..."
        uv run ruff check --fix "$TARGET"
        print_success "Auto-fixes applied!"
        ;;
    "format")
        print_status "Running Ruff formatter on $TARGET..."
        uv run ruff format "$TARGET"
        print_success "Formatting complete!"
        ;;
    "all")
        print_status "Running complete Ruff check and format on $TARGET..."
        echo "Step 1: Linting with auto-fixes..."
        uv run ruff check --fix "$TARGET"
        echo "Step 2: Formatting code..."
        uv run ruff format "$TARGET"
        print_success "All Ruff operations complete!"
        ;;
    "diff")
        print_status "Showing Ruff format diff for $TARGET..."
        uv run ruff format --diff "$TARGET"
        ;;
    "unsafe")
        print_warning "Running Ruff with unsafe fixes on $TARGET..."
        uv run ruff check --fix --unsafe-fixes "$TARGET"
        ;;
    *)
        echo "Usage: $0 [target_directory] [command]"
        echo ""
        echo "Commands:"
        echo "  check   - Run linter (default)"
        echo "  fix     - Run linter with auto-fixes"
        echo "  format  - Run formatter"
        echo "  all     - Run both linter and formatter"
        echo "  diff    - Show format diff without applying"
        echo "  unsafe  - Run with unsafe fixes enabled"
        echo ""
        echo "Examples:"
        echo "  $0                           # Check entire project"
        echo "  $0 socialmapper/ fix         # Fix issues in socialmapper/"
        echo "  $0 tests/ format             # Format test files"
        echo "  $0 . all                     # Run all checks on entire project"
        exit 1
        ;;
esac 