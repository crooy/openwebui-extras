#!/usr/bin/env python3
"""Script to fetch and set up type stubs for OpenWebUI models."""
import json
import os
import shutil
import urllib.request
from typing import List


def ensure_clean_dir(path: str) -> None:
    """Create or clean directory."""
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)


def download_file(url: str, target: str) -> None:
    """Download a file from URL to target path."""
    print(f"Downloading {url} to {target}")
    urllib.request.urlretrieve(url, target)


def get_model_files(repo_url: str) -> List[str]:
    """Get list of all Python files in the models directory."""
    api_url = repo_url.replace("github.com", "api.github.com/repos") + "/contents/backend/open_webui/models"

    try:
        with urllib.request.urlopen(api_url) as response:
            files = json.loads(response.read())
            return [f["name"] for f in files if f["name"].endswith(".py")]
    except Exception as e:
        print(f"Error fetching file list: {e}, falling back to default files")
        return [
            "memories.py",
            "users.py",
            "conversations.py",
            "settings.py",
            "__init__.py",
        ]


def main() -> None:
    """Main function to set up stubs."""
    # Setup paths
    stub_dir = "stubs/open_webui/models"
    ensure_clean_dir(stub_dir)

    # Get list of model files
    repo_url = "https://github.com/open-webui/open-webui"
    files = get_model_files(repo_url)
    print(f"Found model files: {files}")

    base_url = f"{repo_url}/raw/main/backend/open_webui/models"

    # Download files
    for file in files:
        url = f"{base_url}/{file}"
        target = f"{stub_dir}/{file}"
        download_file(url, target)

    # Convert to stubs
    import os.path

    script_dir = os.path.dirname(os.path.abspath(__file__))
    simplify_script = os.path.join(script_dir, "simplify_stubs.py")
    if os.path.exists(simplify_script):
        import runpy

        runpy.run_path(simplify_script)
    else:
        print("Warning: simplify_stubs.py not found")


if __name__ == "__main__":
    main()
