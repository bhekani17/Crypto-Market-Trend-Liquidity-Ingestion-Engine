import os

# Free keyless API has strict per-minute rate limits
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
MARKETS_ENDPOINT = f"{COINGECKO_BASE_URL}/coins/markets"

# Target cryptocurrencies to track
TARGET_COINS = ["bitcoin", "ethereum", "solana", "cardano", "ripple"]
VS_CURRENCY = "usd"

DB_FILEPATH = os.path.join("data", "crypto_warehouse.db")