import os

from playwright.sync_api import sync_playwright


def ensure_chromium_installed():
    """
    Check if Chromium is installed with Playwright, and install it if not.
    Returns True if Chromium is available, False otherwise.
    """
    try:
        with sync_playwright() as p:
            # Try to get the Chromium browser path
            browser_path = p.chromium.executable_path
            if browser_path and os.path.exists(browser_path):
                print(f"Chromium already installed at: {browser_path}")
                return True
            else:
                print("Chromium not found, installing...")
                # Install Chromium
                p.chromium.install()
                print("Chromium installed successfully")
                return True
    except Exception as e:
        print(f"Error checking/installing Chromium: {e}")
        return False


if __name__ == "__main__":
    ensure_chromium_installed()
