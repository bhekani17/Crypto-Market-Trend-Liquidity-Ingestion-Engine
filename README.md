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




┌───────────────────────┐
               │      GitHub API       │
               │ (/repos/.../issues)   │
               └───────────┬───────────┘
                           │ HTTP Request (Pagination & Rate Limit Headers)
                           ▼
               ┌───────────────────────┐
               │    Bronze Layer       │ (Raw JSON dumps stored locally / partitioned)
               └───────────┬───────────┘
                           │ Parsing & Flattening (Pandas / Polars)
                           ▼
               ┌───────────────────────┐
               │    Silver Layer       │ (Cleaned Parquet tables with enforced schemas)
               └───────────┬───────────┘
                           │ Aggregations & Window Functions
                           ▼
               ┌───────────────────────┐
               │     Gold Layer        │ (Business-ready developer metrics & summary marts)
               └───────────────────────┘













               github-activity-pipeline/
├── data/
│   ├── bronze/                  # Raw JSON snapshots
│   ├── silver/                  # Cleaned Parquet files
│   └── gold_warehouse.db        # DuckDB / SQLite final analytics mart
├── src/
│   ├── __init__.py
│   ├── extract_bronze.py        # GitHub API client with pagination & rate-limit tracking
│   ├── transform_silver.py      # Flattens nested JSON payloads into structured Parquet
│   └── load_gold.py             # Computes aggregate metrics and loads into DuckDB
├── requirements.txt
└── README.md








┌───────────────────────┐         ┌───────────────────────┐
               │  REST Countries API   │         │    World Bank API     │
               │ (Geographic metadata) │         │ (Economic indicators) │
               └───────────┬───────────┘         └───────────┬───────────┘
                           │                                 │
                           └───────────────┬─────────────────┘
                                           ▼
                           ┌───────────────────────────────┐
                           │ Python Ingestion & Normalizer │ (Pandas / Polars merging)
                           └───────────────┬───────────────┘
                                           ▼
                           ┌───────────────────────────────┐
                           │ DuckDB / PostgreSQL Warehouse │ 
                           │ ├── dim_country               │
                           │ └── fact_economic_indicators  │
                           └───────────────────────────────┘


DONT REMOVE : WTC-Y9V2J6QA

                           
