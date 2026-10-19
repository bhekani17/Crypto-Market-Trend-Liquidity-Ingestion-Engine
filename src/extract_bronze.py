import os
import json
import requests
from datetime import datetime

BRONZE_DIR = os.path.join("data", "bronze")
os.makedirs(BRONZE_DIR, exist_ok=True)

def fetch_repo_issues(owner: str, repo: str):
    """Fetches public issues from a GitHub repository handling pagination."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    params = {"state": "all", "per_page": 100, "page": 1}
    headers = {"Accept": "application/vnd.github+json"}
    
    all_issues = []
    
    while True:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        # Check remaining rate limits
        remaining = response.headers.get("X-RateLimit-Remaining")
        print(f"GitHub API Rate Limit Remaining: {remaining}")
        
        page_data = response.json()
        if not page_data:
            break
            
        all_issues.extend(page_data)
        params["page"] += 1
        
        # Safety break for public unauthenticated limit demo
        if params["page"] > 5 or len(page_data) < 100:
            break

    # Save raw snapshot to Bronze Layer
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(BRONZE_DIR, f"issues_{repo}_{timestamp}.json")
    
    with open(filepath, "w") as f:
        json.dump(all_issues, f, indent=2)
        
    print(f"Bronze layer ingestion complete: Saved {len(all_issues)} raw records to {filepath}")
    return filepath