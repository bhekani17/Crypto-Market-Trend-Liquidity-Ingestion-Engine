from pathlib import Path
import duckdb
from src.config import DATA_DIR


def load_silver_to_gold(silver_filepath: str | None = None, db_filepath: str | None = None) -> str:
    """Computes aggregate developer metrics from Silver Parquet and loads into Gold DuckDB mart."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if silver_filepath is None:
        silver_filepath = str(DATA_DIR / "silver" / "cleaned_issues.parquet")
    if db_filepath is None:
        db_filepath = str(DATA_DIR / "gold_warehouse.db")

    if not Path(silver_filepath).exists():
        raise FileNotFoundError(f"Silver layer file not found: {silver_filepath}")

    conn = duckdb.connect(db_filepath)
    try:
        conn.execute("""
            CREATE OR REPLACE TABLE gold_author_metrics AS
            SELECT
                author,
                COUNT(*) AS total_issues,
                COUNT(*) FILTER (WHERE state = 'open') AS open_issues,
                COUNT(*) FILTER (WHERE state = 'closed') AS closed_issues,
                COALESCE(SUM(comments_count), 0) AS total_comments,
                AVG(
                    CASE
                        WHEN closed_at IS NOT NULL AND created_at IS NOT NULL
                        THEN EPOCH(closed_at - created_at) / 3600.0
                    END
                ) AS avg_resolution_hours
            FROM read_parquet(?)
            GROUP BY author
            ORDER BY total_issues DESC, author ASC;
        """, [silver_filepath])
    finally:
        conn.close()

    print(f"Gold layer aggregation complete: Saved to {db_filepath}")
    return db_filepath


if __name__ == "__main__":
    load_silver_to_gold()
