from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
from threading import Lock
import time

import pandas as pd
import requests


FRESH_TTL_SECONDS = 300
STALE_TTL_SECONDS = 86400
_cache: dict[str, tuple[float, pd.DataFrame, str]] = {}
_lock = Lock()
_health: dict[str, dict] = {
    provider: {"configured": provider == "yahoo", "healthy": None, "last_error": None}
    for provider in ("alpaca", "alpha_vantage", "yahoo")
}


def _record(provider: str, healthy: bool, error: str | None = None) -> None:
    _health[provider].update({
        "healthy": healthy,
        "last_error": error,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    })


def _alpaca_history(symbol: str, horizon: str = "day") -> pd.DataFrame:
    key = os.environ.get("ALPACA_PAPER_API_KEY", "").strip()
    secret = os.environ.get("ALPACA_PAPER_SECRET_KEY", "").strip()
    _health["alpaca"]["configured"] = bool(key and secret)
    if not key or not secret:
        raise RuntimeError("not configured")
    intraday = horizon == "hour"
    start = (
        datetime.now(timezone.utc) - timedelta(days=120 if intraday else 1100)
    ).isoformat()
    response = requests.get(
        f"https://data.alpaca.markets/v2/stocks/{symbol}/bars",
        params={
            "timeframe": "1Hour" if intraday else "1Day",
            "start": start,
            "limit": 1000,
            "sort": "desc",
            "adjustment": "all",
            "feed": "iex",
        },
        headers={"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret},
        timeout=15,
    )
    response.raise_for_status()
    bars = response.json().get("bars") or []
    if len(bars) < 30:
        raise RuntimeError("insufficient Alpaca history")
    frame = pd.DataFrame([{
        "Date": bar["t"], "Open": bar["o"], "High": bar["h"],
        "Low": bar["l"], "Close": bar["c"], "Volume": bar["v"],
    } for bar in bars])
    return frame.set_index(pd.to_datetime(frame.pop("Date"))).sort_index()


def _alpha_vantage_history(symbol: str, horizon: str = "day") -> pd.DataFrame:
    key = os.environ.get("ALPHA_VANTAGE_API_KEY", "").strip()
    _health["alpha_vantage"]["configured"] = bool(key)
    if not key:
        raise RuntimeError("not configured")
    intraday = horizon == "hour"
    params = {
        "function": "TIME_SERIES_INTRADAY" if intraday else "TIME_SERIES_DAILY",
        "symbol": symbol,
        "outputsize": "full" if intraday else "compact",
        "apikey": key,
    }
    if intraday:
        params["interval"] = "60min"
    response = requests.get(
        "https://www.alphavantage.co/query",
        params=params,
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    series = payload.get("Time Series (60min)" if intraday else "Time Series (Daily)")
    if not series:
        raise RuntimeError(payload.get("Note") or payload.get("Information") or payload.get("Error Message") or "no daily series")
    rows = [{
        "Date": date, "Open": float(values["1. open"]), "High": float(values["2. high"]),
        "Low": float(values["3. low"]), "Close": float(values["4. close"]),
        "Volume": float(values["5. volume"]),
    } for date, values in series.items()]
    frame = pd.DataFrame(rows)
    return frame.set_index(pd.to_datetime(frame.pop("Date"))).sort_index()


def _yahoo_history(symbol: str, horizon: str = "day") -> pd.DataFrame:
    import yfinance as yf

    intraday = horizon == "hour"
    frame = yf.download(
        symbol,
        period="6mo" if intraday else "3y",
        interval="1h" if intraday else "1d",
        progress=False,
        auto_adjust=True, threads=False,
    )
    if frame.empty:
        raise RuntimeError("no Yahoo history")
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)
    return frame


def get_history(symbol: str, horizon: str = "day") -> tuple[pd.DataFrame, str]:
    normalized = symbol.strip().upper()
    normalized_horizon = horizon if horizon in {"hour", "day", "week", "month"} else "day"
    cache_key = f"{normalized}:{normalized_horizon}"
    now = time.time()
    with _lock:
        cached = _cache.get(cache_key)
        if cached and now - cached[0] < FRESH_TTL_SECONDS:
            return cached[1].copy(), cached[2]

        for provider, fetcher in (
            ("alpaca", _alpaca_history),
            ("alpha_vantage", _alpha_vantage_history),
            ("yahoo", _yahoo_history),
        ):
            try:
                frame = fetcher(normalized, normalized_horizon)
                if frame.empty or len(frame) < 30:
                    raise RuntimeError("insufficient history")
                _record(provider, True)
                frame.attrs["bar_interval"] = "1h" if normalized_horizon == "hour" else "1d"
                _cache[cache_key] = (now, frame.copy(), provider)
                return frame, provider
            except Exception as error:
                if str(error) != "not configured":
                    _record(provider, False, str(error)[:300])

        if cached and now - cached[0] < STALE_TTL_SECONDS:
            return cached[1].copy(), f"{cached[2]}_stale"
        raise RuntimeError(f"No market-data provider returned history for {normalized}")


def get_daily_history(symbol: str) -> tuple[pd.DataFrame, str]:
    """Backward-compatible daily history interface used by quote endpoints."""
    return get_history(symbol, "day")


def provider_status() -> dict:
    return {
        "providers": _health,
        "fresh_cache_seconds": FRESH_TTL_SECONDS,
        "stale_cache_seconds": STALE_TTL_SECONDS,
    }
