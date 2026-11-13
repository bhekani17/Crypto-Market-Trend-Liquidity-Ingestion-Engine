import json
import pytest
import duckdb
from pydantic import ValidationError
from src.pipeline import validate_data, run_pipeline
from src.transform_silver import process_bronze_to_silver
from src.load_gold import load_silver_to_gold
from app import app


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


def test_database_initialization_creates_table(tmp_path, monkeypatch):
    from src import db

    test_db = tmp_path / "crypto.db"
    monkeypatch.setattr(db, "DB_FILEPATH", test_db)

    db.initialize_database()
    conn = db.get_connection()
    tables = conn.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_name = 'fact_crypto_market_ticks'"
    ).fetchall()
    conn.close()

    assert tables == [("fact_crypto_market_ticks",)]


def test_pipeline_upsert_idempotency(tmp_path, monkeypatch):
    from src import db, pipeline

    test_db = tmp_path / "crypto.db"
    monkeypatch.setattr(db, "DB_FILEPATH", test_db)

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
    monkeypatch.setattr(pipeline, "fetch_market_data", lambda: sample_raw)

    # Run twice with identical (coin_id, last_updated) to verify idempotent MERGE
    run_pipeline()
    run_pipeline()

    conn = db.get_connection()
    count = conn.execute("SELECT COUNT(*) FROM fact_crypto_market_ticks").fetchone()[0]
    conn.close()
    assert count == 1


def test_medallion_silver_to_gold_pipeline(tmp_path, monkeypatch):
    from src import transform_silver

    monkeypatch.setattr(transform_silver, "DATA_DIR", tmp_path)

    bronze_file = tmp_path / "issues_sample.json"
    bronze_payload = [
        {
            "id": 101,
            "number": 1,
            "title": "Fix bug in ingestion",
            "state": "closed",
            "user": {"login": "alice"},
            "comments": 3,
            "created_at": "2026-10-01T10:00:00Z",
            "closed_at": "2026-10-01T12:00:00Z",
        },
        {
            "id": 102,
            "number": 2,
            "title": "Add PR feature",
            "state": "open",
            "user": {"login": "bob"},
            "comments": 1,
            "created_at": "2026-10-02T10:00:00Z",
            "closed_at": None,
            "pull_request": {"url": "https://api.github.com/repos/x/y/pulls/2"},
        },
    ]
    bronze_file.write_text(json.dumps(bronze_payload))

    silver_path = process_bronze_to_silver(str(bronze_file))
    assert silver_path is not None

    gold_db = tmp_path / "gold_warehouse.db"
    load_silver_to_gold(silver_filepath=silver_path, db_filepath=str(gold_db))

    conn = duckdb.connect(str(gold_db))
    rows = conn.execute(
        "SELECT author, total_issues, closed_issues, total_comments, avg_resolution_hours "
        "FROM gold_author_metrics"
    ).fetchall()
    conn.close()

    assert rows == [("alice", 1, 1, 3, 2.0)]


def test_flask_market_endpoint(tmp_path, monkeypatch):
    from src import db

    test_db = tmp_path / "crypto.db"
    monkeypatch.setattr(db, "DB_FILEPATH", test_db)

    client = app.test_client()
    response = client.get("/api/market")
    assert response.status_code == 200
    payload = response.get_json()
    assert "coins" in payload
    assert "summary" in payload
    assert payload["summary"]["coin_count"] == 0
