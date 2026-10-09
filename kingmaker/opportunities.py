"""Transparent watchlist rankings; movement potential is not profit probability."""
from datetime import datetime, timezone
import math

import numpy as np
import pandas as pd

from backend.market_data import get_history
from kingmaker.model import predict

DEFAULT_SYMBOLS = "AAPL,MSFT,NVDA,AMZN,GOOGL,META,TSLA,AMD,AVGO,PLTR,COIN,HOOD,SOFI,RKLB,IONQ,SMCI,MU,INTC,UBER,SHOP,SPY,QQQ,IWM,GLD,XLE"


def finite(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Non-finite market evidence")
    return number


def candidate(symbol, horizon, cost_bps):
    forecast = predict(symbol, horizon)
    if not forecast["data_quality"]["usable"]:
        raise ValueError("Market history is stale or unverifiable")
    frame, provider = get_history(symbol, horizon)
    if provider.endswith("_stale"):
        raise ValueError("History fallback is stale")
    closes = pd.to_numeric(frame["Close"], errors="coerce")
    if len(closes) < 21 or not np.isfinite(closes.to_numpy()).all() or (closes <= 0).any():
        raise ValueError("Insufficient valid price history")
    # The graphic and ranking must use the same origin as the model forecast.
    if pd.to_datetime(frame.index[-1], utc=True) != pd.to_datetime(forecast["evidence"]["last_bar_at"], utc=True):
        raise ValueError("History changed during scan; rerun to align the forecast")
    price = finite(forecast["current_price"])
    if price <= 0:
        raise ValueError("Invalid forecast origin price")
    move = finite(forecast["signal"]["expected_move_percent"])
    volatility = finite(np.log(closes).diff().tail(20).std(ddof=1) * 100)
    momentum = finite((closes.iloc[-1] / closes.iloc[-6] - 1) * 100)
    daily_change = finite((closes.iloc[-1] / closes.iloc[-2] - 1) * 100)
    relative_volume = None
    if "Volume" in frame:
        volume = pd.to_numeric(frame["Volume"], errors="coerce")
        reference = volume.iloc[-21:-1].mean()
        if reference > 0 and pd.notna(volume.iloc[-1]) and volume.iloc[-1] >= 0:
            relative_volume = finite(volume.iloc[-1] / reference)
    components = {
        "volatility": round(min(volatility / 5, 1) * 35, 2),
        "volume": round(min((relative_volume or 0) / 3, 1) * 25, 2),
        "momentum": round(min(abs(momentum) / 10, 1) * 25, 2),
        "forecast": round(min(abs(move) / 3, 1) * 15, 2),
    }
    rmse = finite(math.sqrt(finite(forecast["model_mse"])))
    target = finite(forecast["predicted_next_close"])
    if target <= 0:
        raise ValueError("Invalid forecast target")
    net_move = move - cost_bps / 100
    history = [{"at": pd.to_datetime(at, utc=True).isoformat(), "close": finite(close)}
               for at, close in closes.tail(30).items()]
    qualified = forecast["signal"]["action"] == "BUY" and forecast["signal"]["qualified"] and net_move > 0
    return {"ticker": symbol, "forecast": forecast, "last_price": price,
            "forecast_move_percent": move, "estimated_net_move_percent": round(net_move, 4),
            "change_percent": round(daily_change, 4), "momentum_5_bars_percent": round(momentum, 4),
            "volatility_20_bars_percent": round(volatility, 4), "relative_volume": relative_volume,
            "movement_score": round(sum(components.values()), 2), "score_components": components,
            "qualified_driver": qualified, "driver_status": "QUALIFIED BUY" if qualified else "WATCH ONLY",
            "history": history, "target": target,
            "error_band": {"low": max(0, target-rmse), "high": target+rmse,
                           "label": "Forecast +/- historical validation RMSE; not a calibrated confidence interval"}}


def build_board(symbols, horizon="day", cost_bps=20, progress=None):
    items, errors = [], []
    for index, symbol in enumerate(symbols):
        try:
            items.append(candidate(symbol, horizon, cost_bps))
        except Exception:
            # Provider exceptions may embed signed URLs or credentials.
            errors.append({"ticker": symbol, "error": "No usable aligned forecast/history; check provider status."})
        if progress:
            progress(index+1, len(symbols))
    movers = sorted(items, key=lambda x: (-x["movement_score"], x["ticker"]))[:5]
    drivers = sorted(items,
                     key=lambda x: (not x["qualified_driver"], -x["estimated_net_move_percent"],
                                    -x["forecast"]["validation_confidence"], x["ticker"]))[:10]
    return {"generated_at": datetime.now(timezone.utc).isoformat(), "horizon": horizon,
            "universe": symbols, "evaluated": len(items), "errors": errors,
            "big_movers": movers, "daily_drivers": drivers,
            "round_trip_cost_bps": cost_bps, "profitability": "unproven",
            "methodology": "Watchlist only. Movement score = volatility/5% capped *35 + relative volume/3 capped *25 + abs(5-bar momentum)/10% capped *25 + abs(forecast move)/3% capped *15. Daily drivers prefer qualified BUYs, then estimated long return after assumed costs. No padding with failed/stale symbols. Missing volume contributes zero. Costs are assumptions, not broker quotes."}
