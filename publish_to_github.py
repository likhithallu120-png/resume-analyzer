"""
Publish to GitHub Helper Script
Uses dulwich to push the local Git repository to GitHub.
"""

import sys
import os
import dulwich.porcelain
import dulwich.repo

def publish(repo_url: str, token: str = None, username: str = None):
    repo_path = os.path.dirname(os.path.abspath(__file__))
    repo = dulwich.repo.Repo(repo_path)
    
    # Configure remote
    if token:
        # Format URL with token for authenticated push
        # https://TOKEN@github.com/USER/REPO.git
        clean_url = repo_url.replace("https://", "").replace("http://", "")
        if "@" in clean_url:
            clean_url = clean_url.split("@")[-1]
        target_url = f"https://{token}@{clean_url}"
    else:
        target_url = repo_url

    print(f"Adding remote 'origin' -> {repo_url}...")
    try:
        dulwich.porcelain.remote_add(repo, "origin", target_url)
    except Exception:
        # If origin exists, set it
        pass

    print("Pushing to GitHub (main branch)...")
    try:
        dulwich.porcelain.push(repo, target_url, "refs/heads/main:refs/heads/main")
        print("Successfully published to GitHub!")
    except Exception as e:
        print(f"Push failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Ensure your GitHub Personal Access Token (PAT) has 'repo' permissions.")
        print("2. Ensure the remote repository has been created on GitHub.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python publish_to_github.py <github_repo_url> [github_token]")
        sys.exit(1)
    
    url = sys.argv[1]
    pat = sys.argv[2] if len(sys.argv) > 2 else None
    publish(url, pat)
