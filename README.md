# Crypto-Market-Trend-Liquidity-Ingestion-Engine

┌───────────────────────┐
               │    CoinGecko API      │
               │ (Public REST Endpoint)│
               └───────────┬───────────┘
                           │ HTTP Request (Backoff + Rate Limit Handling)
                           ▼
               ┌───────────────────────┐
               │ Python Extraction Layer│ (Pydantic Validation & Raw JSON Payload)
               └───────────┬───────────┘
                           │ Cleaned Dicts / DataFrames
                           ▼
               ┌───────────────────────┐
               │ Data Quality Engine   │ (Null checks, Price range assertions)
               └───────────┬───────────┘
                           │ Validated Data
                           ▼
               ┌───────────────────────┐
               │ Local DuckDB Storage  │ (Staging table -> Upsert into Production)
               └───────────────────────┘

