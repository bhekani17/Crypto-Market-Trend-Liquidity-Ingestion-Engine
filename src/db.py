import duckdb
from src.config import DATA_DIR, DB_FILEPATH

def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(DB_FILEPATH))

def initialize_database():
    """Sets up the target production table in DuckDB."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fact_crypto_market_ticks (
            coin_id VARCHAR,
            symbol VARCHAR,
            name VARCHAR,
            price_usd DOUBLE,
            market_cap_usd DOUBLE,
            total_volume_usd DOUBLE,
            price_change_24h DOUBLE,
            last_updated_at TIMESTAMP,
            ingested_at TIMESTAMP,
            PRIMARY KEY (coin_id, last_updated_at)
        );
    """)
    conn.close()