import pytest
from pydantic import ValidationError
from src.pipeline import validate_data

def test_valid_payload_validation():
    sample_raw = [{
        "id": "bitcoin",
        "symbol": "btc",
        "name": "Bitcoin",
        "current_price": 65000.50,
        "market_cap": 1200000000000.0,
        "total_volume": 30000000000.0,
        "price_change_24h": 1200.5,
        "last_updated": "2026-10-20T00:00:00.000Z"
    }]
    
    result = validate_data(sample_raw)
    assert len(result) == 1
    assert result[0]["id"] == "bitcoin"
    assert result[0]["current_price"] == 65000.50

def test_invalid_price_fails_validation():
    sample_invalid_raw = [{
        "id": "bitcoin",
        "symbol": "btc",
        "name": "Bitcoin",
        "current_price": -500.0,  # Invalid negative price!
        "market_cap": 1000.0,
        "total_volume": 500.0,
        "last_updated": "2026-10-20T00:00:00.000Z"
    }]
    
    with pytest.raises(ValidationError):
        validate_data(sample_invalid_raw)