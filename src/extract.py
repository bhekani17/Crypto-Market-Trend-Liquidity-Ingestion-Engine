import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.config import MARKETS_ENDPOINT, TARGET_COINS, VS_CURRENCY

class APIError(Exception):
    """Custom exception for non-200 responses."""
    pass

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception_type((APIError, requests.RequestException)),
    reraise=True
)
def fetch_market_data() -> list:
    """Fetches market trends for specified coins with automatic exponential backoff."""
    params = {
        "vs_currency": VS_CURRENCY,
        "ids": ",".join(TARGET_COINS),
        "order": "market_cap_desc",
        "per_page": len(TARGET_COINS),
        "page": 1,
        "sparkline": "false"
    }
    
    headers = {"accept": "application/json"}
    response = requests.get(MARKETS_ENDPOINT, params=params, headers=headers, timeout=10)
    
    # Trigger retry on HTTP 429 (Rate Limit) or 5xx Server Errors
    if response.status_code in [429, 500, 502, 503, 504]:
        raise APIError(f"API Rate Limited or Unavailable. Status code: {response.status_code}")
    
    response.raise_for_status()
    return response.json()