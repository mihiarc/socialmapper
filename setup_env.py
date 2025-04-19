#!/usr/bin/env python3
"""
Centralized environment setup for the Community Mapper project.
This script handles creation of virtual environments and package installation.
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path
import json

# Define project root directory (where this script lives)
PROJECT_ROOT = Path(__file__).parent.absolute()

# Define virtual environment path
VENV_PATH = PROJECT_ROOT / ".venv"

# Define required directories
REQUIRED_DIRS = [
    "isochrones",
    "results",
    "cache"
]

def create_directories():
    """Create required directories if they don't exist."""
    for dir_name in REQUIRED_DIRS:
        directory = PROJECT_ROOT / dir_name
        directory.mkdir(exist_ok=True)
        print(f"Ensured directory exists: {directory}")

def setup_virtual_env(upgrade=False, force=False):
    """
    Set up a virtual environment with uv package manager.
    
    Args:
        upgrade: Whether to upgrade packages if venv exists
        force: Force recreation of the virtual environment
    """
    if force and VENV_PATH.exists():
        import shutil
        print(f"Removing existing virtual environment at {VENV_PATH}")
        shutil.rmtree(VENV_PATH)
    
    if not VENV_PATH.exists():
        print("Setting up virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", str(VENV_PATH)])
        
        # Install uv in the virtual environment
        if sys.platform == "win32":
            pip_path = VENV_PATH / "Scripts" / "pip"
        else:
            pip_path = VENV_PATH / "bin" / "pip"
        
        subprocess.run([str(pip_path), "install", "uv"])
        
        # Install required packages using uv
        install_packages()
        
        print("Virtual environment created and packages installed.")
    elif upgrade:
        print("Upgrading packages in existing virtual environment...")
        install_packages(upgrade=True)
    else:
        print(f"Virtual environment already exists at {VENV_PATH}")
        print("Use --upgrade to upgrade packages or --force to recreate")

def install_packages(upgrade=False):
    """
    Install required packages using uv.
    
    Args:
        upgrade: Whether to upgrade existing packages
    """
    # Determine uv path based on platform
    if sys.platform == "win32":
        uv_path = VENV_PATH / "Scripts" / "uv"
    else:
        uv_path = VENV_PATH / "bin" / "uv"
    
    # Basic required packages
    base_packages = [
        "geopandas",
        "requests",
        "pandas",
        "python-dotenv",
        "pyyaml",
        "networkx",
        "osmnx",
        "matplotlib",
        "scipy"
    ]
    
    # Install packages using uv
    cmd = [str(uv_path), "pip", "install"]
    if upgrade:
        cmd.append("--upgrade")
    
    subprocess.run(cmd + base_packages)
    
    # Check for and install requirements.txt if it exists
    reqs_file = PROJECT_ROOT / "poi_query" / "requirements.txt"
    if reqs_file.exists():
        print(f"Installing requirements from {reqs_file}")
        subprocess.run([str(uv_path), "pip", "install", "-r", str(reqs_file)])

def activate_venv():
    """
    Rerun the current script with the virtual environment's Python.
    This function is called when a script wants to ensure it's running in the venv.
    """
    if not os.environ.get("VIRTUAL_ENV"):
        print("Activating virtual environment...")
        
        # Determine python path based on platform
        if sys.platform == "win32":
            python_path = VENV_PATH / "Scripts" / "python.exe"
        else:
            python_path = VENV_PATH / "bin" / "python"
        
        # Re-run the current script with all arguments
        cmd = [str(python_path)] + sys.argv
        os.execv(str(python_path), cmd)

def ensure_env_file():
    """Ensure .env file exists with required variables."""
    env_file = PROJECT_ROOT / ".env"
    
    if not env_file.exists():
        print("Creating .env file template...")
        with open(env_file, "w") as f:
            f.write("# Environment variables for Community Mapper\n\n")
            f.write("# Census API key (get one at https://api.census.gov/data/key_signup.html)\n")
            f.write("CENSUS_API_KEY=your_api_key_here\n")
        
        print(f"Created .env template at {env_file}")
        print("Please edit this file to add your actual API keys")
    else:
        print(f".env file already exists at {env_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set up environment for Community Mapper")
    parser.add_argument("--upgrade", action="store_true", help="Upgrade packages in existing environment")
    parser.add_argument("--force", action="store_true", help="Force recreation of virtual environment")
    parser.add_argument("--dirs", action="store_true", help="Create required directories")
    parser.add_argument("--env", action="store_true", help="Create .env file if it doesn't exist")
    parser.add_argument("--all", action="store_true", help="Perform all setup steps")
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if not any(vars(args).values()):
        parser.print_help()
        sys.exit(0)
    
    # Perform requested actions
    if args.all or args.dirs:
        create_directories()
    
    if args.all or args.env:
        ensure_env_file()
    
    if args.all or args.upgrade or args.force:
        setup_virtual_env(upgrade=args.upgrade, force=args.force) 