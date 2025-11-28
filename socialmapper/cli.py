"""SocialMapper CLI - Launch the web interface.

Usage:
    socialmapper          # Launch web UI
    socialmapper --help   # Show help
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Launch the SocialMapper Streamlit application."""
    # Get the path to the app module
    app_path = Path(__file__).parent / "app.py"

    # Check if --help flag is passed
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        print("SocialMapper - Community Accessibility Analysis")
        print()
        print("Commands:")
        print("  socialmapper        Launch the web interface")
        print()
        print("The web interface provides:")
        print("  - Isochrone analysis (travel-time polygons)")
        print("  - POI discovery (find nearby places)")
        print("  - Census demographics (population data)")
        print()
        print("For programmatic access, use the Python API:")
        print("  from socialmapper import create_isochrone, get_poi, get_census_data")
        return

    # Launch Streamlit
    print("Starting SocialMapper...")
    print("Opening web interface at http://localhost:8501")
    print("Press Ctrl+C to stop")
    print()

    try:
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", str(app_path)],
            check=True,
        )
    except KeyboardInterrupt:
        print("\nSocialMapper stopped.")
    except subprocess.CalledProcessError as e:
        print(f"Error starting SocialMapper: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
