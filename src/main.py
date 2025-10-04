import os
import sys

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.installation import ensure_chromium_installed


def main():
    """
    Main function that ensures Chromium is installed and then performs crawling operations.
    """
    print("Starting web crawler...")

    # Ensure Chromium is installed
    if not ensure_chromium_installed():
        print("Failed to install Chromium. Exiting...")
        sys.exit(1)

    print("Chromium driver is ready.")


if __name__ == "__main__":
    main()
