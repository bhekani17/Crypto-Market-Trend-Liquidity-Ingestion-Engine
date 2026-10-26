from datetime import datetime, timezone
import pandas as pd
from pydantic import BaseModel, Field, PositiveFloat
from src.db import initialize_database, get_connection
from src.extract import fetch_market_data

# Pydantic Schema Enforcement
class CoinTick(BaseModel):
    id: str
    symbol: str
    name: str
    current_price: PositiveFloat
    market_cap: float
    total_volume: float
    price_change_24h: float | None = None
    last_updated: str

def validate_data(raw_records: list) -> list[dict]:
    """Validates incoming payloads using Pydantic."""
    validated = []
    for record in raw_records:
        validated_record = CoinTick(**record)
        validated.append(validated_record.model_dump())
    return validated

def run_pipeline():
    print("Initializing Database...")
    initialize_database()
    
    print("Fetching Market Data from CoinGecko...")
    raw_data = fetch_market_data()
    
    print("Validating Raw Payloads...")
    validated_records = validate_data(raw_data)
    
    # Convert validated payloads to DataFrame
    df = pd.DataFrame(validated_records)
    
    # Transform fields
    df = df.rename(columns={
        "id": "coin_id",
        "current_price": "price_usd",
        "market_cap": "market_cap_usd",
        "total_volume": "total_volume_usd",
        "last_updated": "last_updated_at"
    })
    
    df['last_updated_at'] = pd.to_datetime(df['last_updated_at'])
    df['ingested_at'] = datetime.now(timezone.utc).replace(tzinfo=None)
    
    # Filter specific target columns
    target_columns = [
        "coin_id", "symbol", "name", "price_usd", 
        "market_cap_usd", "total_volume_usd", "price_change_24h", 
        "last_updated_at", "ingested_at"
    ]
    df = df[target_columns]
    
    print(f"Loaded {len(df)} records into processing queue.")
    
    # Upsert Logic into DuckDB
    conn = get_connection()
    
    # Step 1: Write to temporary staging table
    conn.register("stg_crypto_ticks", df)
    
    # Step 2: Idempotent MERGE (Upsert) to prevent duplicates on rerun
    upsert_query = """
        MERGE INTO fact_crypto_market_ticks AS target
        USING stg_crypto_ticks AS source
        ON target.coin_id = source.coin_id 
       AND target.last_updated_at = source.last_updated_at
        WHEN MATCHED THEN
            UPDATE SET 
                symbol = source.symbol,
                name = source.name,
                price_usd = source.price_usd,
                market_cap_usd = source.market_cap_usd,
                total_volume_usd = source.total_volume_usd,
                price_change_24h = source.price_change_24h,
                ingested_at = source.ingested_at
        WHEN NOT MATCHED THEN
            INSERT VALUES (
                source.coin_id, source.symbol, source.name,
                source.price_usd, source.market_cap_usd, source.total_volume_usd,
                source.price_change_24h, source.last_updated_at, source.ingested_at
            );
    """
    
    conn.execute(upsert_query)
    conn.close()
    print("Pipeline Execution Completed Successfully!")

if __name__ == "__main__":
    run_pipeline()
    