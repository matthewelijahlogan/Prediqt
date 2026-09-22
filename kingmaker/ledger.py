"""Persist first-seen forecasts; settle only after their target bar has closed."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3

import pandas as pd


def connect():
    path = Path(os.environ.get("KINGMAKER_LEDGER_PATH", str(Path(__file__).resolve().parents[1] / "data" / "kingmaker.sqlite3")))
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute("""CREATE TABLE IF NOT EXISTS forecasts (
        id INTEGER PRIMARY KEY, ticker TEXT NOT NULL, horizon TEXT NOT NULL,
        model TEXT NOT NULL, origin TEXT NOT NULL, created_at TEXT NOT NULL,
        payload TEXT NOT NULL, actual_close REAL, actual_at TEXT,
        UNIQUE(ticker, horizon, model, origin))""")
    return db


def record(result):
    key = (result["ticker"], result["horizon"], result["model"], result["evidence"]["last_bar_at"])
    with connect() as db:
        db.execute("INSERT OR IGNORE INTO forecasts (ticker,horizon,model,origin,created_at,payload) VALUES (?,?,?,?,?,?)",
                   (*key, result["generated_at"], json.dumps(result, allow_nan=False)))
        row = db.execute("SELECT id FROM forecasts WHERE ticker=? AND horizon=? AND model=? AND origin=?", key).fetchone()
    db.close()
    return row["id"]


def recent(limit=100):
    with connect() as db:
        rows = db.execute("SELECT * FROM forecasts ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    db.close()
    return [dict(row, payload=json.loads(row["payload"])) for row in rows]


def settle(limit=100):
    from backend.market_data import get_history
    from trainers.trainer_1_yfinance import FORWARD_BARS
    with connect() as db:
        rows = db.execute("SELECT * FROM forecasts WHERE actual_close IS NULL ORDER BY id LIMIT ?", (limit,)).fetchall()
    db.close()
    settled, errors = 0, []
    for row in rows:
        try:
            frame, provider = get_history(row["ticker"], row["horizon"])
            if provider.endswith("_stale"):
                continue
            timestamps = pd.to_datetime(frame.index, utc=True)
            origin = pd.to_datetime(row["origin"], utc=True)
            if origin not in timestamps:
                continue
            future = frame.loc[timestamps > origin].copy()
            step = FORWARD_BARS[row["horizon"]]
            # The subsequent bar proves that the target bar has ended. This is
            # deliberately conservative across weekends and market holidays.
            if len(future) <= step:
                continue
            target_at = pd.to_datetime(future.index[step - 1], utc=True)
            closed_by = pd.to_datetime(future.index[step], utc=True)
            if target_at <= pd.to_datetime(row["created_at"], utc=True):
                continue
            if closed_by > pd.Timestamp.now(tz="UTC"):
                continue
            price = float(future.iloc[step - 1]["Close"])
            if not 0 < price < float("inf"):
                continue
            with connect() as db:
                changed = db.execute("UPDATE forecasts SET actual_close=?,actual_at=? WHERE id=? AND actual_close IS NULL",
                                     (price, target_at.isoformat(), row["id"])).rowcount
            db.close()
            settled += changed
        except Exception as error:
            errors.append({"id": row["id"], "error": str(error)})
    return {"settled": settled, "checked": len(rows), "errors": errors,
            "checked_at": datetime.now(timezone.utc).isoformat()}
