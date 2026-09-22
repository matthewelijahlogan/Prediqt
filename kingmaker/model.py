from datetime import datetime, timezone
import re

import pandas as pd

from backend.signals import classify_signal
from trainers.trainer_1_yfinance import FORWARD_BARS, predict as base_predict

MODEL_VERSION = "kingmaker-v1"


def predict(ticker: str, horizon: str = "day") -> dict:
    symbol = ticker.strip().upper()
    if not re.fullmatch(r"[A-Z][A-Z0-9.-]{0,9}", symbol):
        raise ValueError("Invalid stock symbol")
    if horizon not in FORWARD_BARS:
        raise ValueError("Horizon must be hour, day, week, or month")
    base = base_predict(symbol, horizon)
    if base.get("error"):
        raise RuntimeError(base["error"])
    evidence = base["meta"]
    confidence = base["validation_confidence"]
    provider = evidence["market_data_provider"]
    last_bar = pd.to_datetime(evidence["last_bar_at"], utc=True, errors="coerce")
    age = (pd.Timestamp.now(tz="UTC") - last_bar).total_seconds() if pd.notna(last_bar) else None
    data_usable = age is not None and 0 <= age <= 4 * 86400 and not provider.endswith("_stale")
    if not data_usable:
        confidence = 0.0
    result = {
        "ticker": symbol, "horizon": horizon, "model": MODEL_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "current_price": evidence["current_price"],
        "predicted_next_close": base["predicted_next_close"],
        "model_mse": base["model_mse"], "validation_confidence": confidence,
        "used_models": ["purged_ridge"], "weights_used": {"purged_ridge": 1.0},
        "evidence": evidence,
        "data_quality": {"usable": data_usable, "provider": provider, "bar_age_seconds": age},
        "confidence_description": "Validation quality score; not a probability of profit.",
    }
    result["signal"] = classify_signal(result["current_price"], result["predicted_next_close"],
                                       result["model_mse"], horizon, confidence)
    if not data_usable:
        result["signal"]["rationale"] = "HOLD: market history is stale or its timestamp cannot be verified."
    if data_usable:
        from kingmaker.ledger import record
        result["forecast_id"] = record(result)
    return result
