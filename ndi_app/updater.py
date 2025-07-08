import requests
from .config import CURRENT_VERSION

GITHUB_REPO = "newproject8/returnfeed_pd_software"
API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

def check_for_updates():
    """
    Checks for a new release on GitHub.

    Returns:
        dict: A dictionary with new version info if an update is available, otherwise None.
              e.g., {'version': '1.0.1', 'notes': 'Release notes here', 'url': '...'}
    """
    try:
        response = requests.get(API_URL, timeout=5)
        response.raise_for_status()  # Raise an exception for bad status codes
        latest_release = response.json()
        latest_version = latest_release.get("tag_name", "").lstrip('v')
        
        # A simple version comparison
        if latest_version and latest_version > CURRENT_VERSION:
            return {
                "version": latest_version,
                "notes": latest_release.get("body", "No release notes."),
                "url": latest_release.get("html_url")
            }
    except requests.RequestException as e:
        print(f"Update check failed: {e}")
        return None
    
    return None