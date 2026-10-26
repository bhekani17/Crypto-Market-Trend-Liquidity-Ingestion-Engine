import os
import json
import duckdb
import pandas as pd
from src.config import DATA_DIR

def process_bronze_to_silver(bronze_filepath: str):
    """Cleans, normalizes, and converts raw JSON payload into Silver Parquet."""
    with open(bronze_filepath, "r") as f:
        raw_data = json.load(f)
        
    if not raw_data:
        print("No records found in bronze file.")
        return None
        
    parsed_records = []
    for issue in raw_data:
        # Skip pull requests which share the issues endpoint in GitHub API
        if "pull_request" in issue:
            continue
            
        parsed_records.append({
            "issue_id": issue.get("id"),
            "issue_number": issue.get("number"),
            "title": issue.get("title"),
            "state": issue.get("state"),
            "author": issue.get("user", {}).get("login"),
            "comments_count": issue.get("comments"),
            "created_at": issue.get("created_at"),
            "closed_at": issue.get("closed_at")
        })
        
    df = pd.DataFrame(parsed_records)
    if df.empty:
        print("No issue records found after filtering pull requests.")
        return None

    # Cast types
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['closed_at'] = pd.to_datetime(df['closed_at'])
    df['author'] = df['author'].fillna("unknown")
    
    # Save to Silver Layer as Parquet
    silver_dir = DATA_DIR / "silver"
    silver_dir.mkdir(parents=True, exist_ok=True)

    silver_filepath = str(silver_dir / "cleaned_issues.parquet")
    conn = duckdb.connect()
    conn.register("silver_issues", df)
    conn.execute("COPY (SELECT * FROM silver_issues) TO ? (FORMAT PARQUET)", [silver_filepath])
    conn.close()
    
    print(f"Silver layer transformation complete: Saved to {silver_filepath}")
    return silver_filepath