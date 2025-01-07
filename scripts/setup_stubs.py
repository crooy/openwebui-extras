#!/usr/bin/env python3
"""Script to fetch and set up type stubs for OpenWebUI models."""
import json
import os
import urllib.request
from typing import List


def ensure_dir(path: str) -> None:
    """Create directory if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)


def download_file(url: str, target: str) -> None:
    """Download a file from URL to target path."""
    print(f"Downloading {url} to {target}")
    urllib.request.urlretrieve(url, target)


def get_model_files(repo_url: str) -> List[str]:
    """Get list of all Python files in the models directory."""
    api_url = repo_url.replace(
        "github.com", "api.github.com/repos"
    ) + "/contents/backend/open_webui/models"

    try:
        with urllib.request.urlopen(api_url) as response:
            files = json.loads(response.read())
            return [
                f["name"]
                for f in files
                if f["name"].endswith(".py")
            ]
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
    ensure_dir(stub_dir)

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
    for file in os.listdir(stub_dir):
        if file.endswith(".py"):
            src = f"{stub_dir}/{file}"
            dst = f"{stub_dir}/{file}i"
            print(f"Converting {src} to {dst}")
            os.rename(src, dst)


if __name__ == "__main__":
    main()
