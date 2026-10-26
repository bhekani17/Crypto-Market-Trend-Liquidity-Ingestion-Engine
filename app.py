from pathlib import Path

from flask import Flask, jsonify, render_template, request

from src.db import get_connection, initialize_database
from src.pipeline import run_pipeline

app = Flask(__name__, template_folder=str(Path(__file__).parent / "templates"))


def serialize_row(row, columns):
    return dict(zip(columns, row))


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/market")
def market():
    initialize_database()
    conn = get_connection()
    try:
        latest = conn.execute("""
            SELECT coin_id, symbol, name, price_usd, market_cap_usd,
                   total_volume_usd, price_change_24h, last_updated_at, ingested_at
            FROM fact_crypto_market_ticks
            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY coin_id ORDER BY last_updated_at DESC
            ) = 1
            ORDER BY market_cap_usd DESC NULLS LAST
        """).fetchall()
        latest_columns = [
            "coin_id", "symbol", "name", "price_usd", "market_cap_usd",
            "total_volume_usd", "price_change_24h", "last_updated_at", "ingested_at",
        ]

        summary = conn.execute("""
            SELECT COUNT(DISTINCT coin_id), COALESCE(SUM(market_cap_usd), 0),
                   COALESCE(SUM(total_volume_usd), 0), MAX(last_updated_at)
            FROM (
                SELECT *, ROW_NUMBER() OVER (
                    PARTITION BY coin_id ORDER BY last_updated_at DESC
                ) AS rn
                FROM fact_crypto_market_ticks
            ) WHERE rn = 1
        """).fetchone()

        coin_id = request.args.get("coin_id")
        if coin_id:
            history = conn.execute("""
                SELECT price_usd, last_updated_at
                FROM fact_crypto_market_ticks
                WHERE coin_id = ?
                ORDER BY last_updated_at ASC
                LIMIT 100
            """, [coin_id]).fetchall()
        else:
            history = []

        return jsonify({
            "coins": [serialize_row(row, latest_columns) for row in latest],
            "summary": {
                "coin_count": summary[0] if summary else 0,
                "market_cap": summary[1] if summary else 0,
                "volume_24h": summary[2] if summary else 0,
                "last_updated": summary[3].isoformat() if summary and summary[3] else None,
            },
            "history": [
                {"price": row[0], "timestamp": row[1].isoformat()}
                for row in history
            ],
        })
    finally:
        conn.close()


@app.route("/api/refresh", methods=["POST"])
def refresh():
    try:
        run_pipeline()
        return jsonify({"ok": True, "message": "Market data refreshed successfully."})
    except Exception as exc:
        return jsonify({"ok": False, "message": str(exc)}), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
