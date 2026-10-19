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








crypto-ingestion-engine/
├── data/
│   └── crypto_warehouse.db       # Generated DuckDB database
├── src/
│   ├── __init__.py
│   ├── config.py                 # API endpoints & constants
│   ├── db.py                     # Database connection & DDL execution
│   ├── extract.py                # CoinGecko REST client with retry logic
│   └── pipeline.py               # Main Orchestrator (Extract -> Validate -> Upsert)
├── tests/
│   ├── __init__.py
│   └── test_pipeline.py          # Pytest unit & integration tests
├── requirements.txt
└── README.md