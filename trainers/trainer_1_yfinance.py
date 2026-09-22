import numpy as np
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from backend.market_data import get_history


FORWARD_BARS = {"hour": 1, "day": 1, "week": 5, "month": 21}

# Guardrails against turning an unstable fit into an actionable signal.
MAX_BASE_RETURN = {"hour": 0.015, "day": 0.03, "week": 0.08, "month": 0.15}


def fetch_market_data(ticker: str, horizon: str = "day"):
    try:
        data, source = get_history(ticker, horizon)
        data.attrs["provider"] = source
        return data
    except Exception as error:
        print(f"[trainer_1_yfinance] Error fetching data for {ticker}: {error}")
        return None


# Preserve the former helper for external callers while honoring the interval.
def fetch_yfinance_data(ticker: str, period="6mo", interval="1d", horizon=None):
    selected_horizon = horizon or ("hour" if interval == "1h" else "day")
    return fetch_market_data(ticker, selected_horizon)


def _feature_vector(close_prices: np.ndarray, index: int) -> np.ndarray:
    window = close_prices[index - 20:index + 1]
    returns = np.diff(np.log(window))
    current = close_prices[index]
    return np.array([
        returns[-1], returns[-2], returns[-3],
        returns[-5:].mean(), returns[-10:].mean(), returns.mean(),
        returns[-5:].std(), returns[-10:].std(), returns.std(),
        current / window[-6:-1].mean() - 1,
        current / window[-11:-1].mean() - 1,
        current / window[:-1].mean() - 1,
    ], dtype=float)


def _training_set(close_prices: np.ndarray, forward_bars: int):
    features = []
    targets = []
    for index in range(20, len(close_prices) - forward_bars):
        features.append(_feature_vector(close_prices, index))
        targets.append(np.log(close_prices[index + forward_bars] / close_prices[index]))
    return np.asarray(features), np.asarray(targets)


def predict(ticker: str, horizon="day"):
    normalized_horizon = horizon if horizon in FORWARD_BARS else "day"
    print(f"[trainer_1_yfinance] Starting prediction for {ticker} horizon={normalized_horizon}")
    df = fetch_market_data(ticker, normalized_horizon)
    forward_bars = FORWARD_BARS[normalized_horizon]
    minimum_rows = max(70, 20 + forward_bars + 30)
    if df is None or len(df) < minimum_rows:
        return {
            "trainer": "base", "error": "Insufficient horizon-matched market data",
            "confidence": 0.0, "predicted_next_close": 0.0,
            "meta": {"horizon": normalized_horizon},
        }

    close_prices = np.asarray(df["Close"], dtype=float).reshape(-1)
    close_prices = close_prices[np.isfinite(close_prices) & (close_prices > 0)]
    if len(close_prices) < minimum_rows:
        return {
            "trainer": "base", "error": "Insufficient valid close prices",
            "confidence": 0.0, "predicted_next_close": 0.0,
            "meta": {"horizon": normalized_horizon},
        }

    features, targets = _training_set(close_prices, forward_bars)
    split = max(30, int(len(features) * 0.8))
    if len(features) - split < 10:
        split = len(features) - 10
    # Purge labels that reach the first validation feature timestamp. Each
    # expanding fold only sees outcomes already known before that fold starts.
    validation_predictions = []
    fold_details = []
    for indices in np.array_split(np.arange(split, len(features)), 3):
        if not len(indices):
            continue
        start = int(indices[0])
        train_end = start - forward_bars
        model = make_pipeline(StandardScaler(), Ridge(alpha=8.0))
        model.fit(features[:train_end], targets[:train_end])
        validation_predictions.extend(model.predict(features[indices]).tolist())
        fold_details.append({"train_samples": train_end, "validation_start": start,
                             "validation_samples": len(indices), "purge_bars": forward_bars})
    validation_predictions = np.asarray(validation_predictions)
    y_validation = targets[split:]
    validation_errors = validation_predictions - y_validation
    return_mse = float(np.mean(validation_errors ** 2))
    baseline_mse = float(np.mean(y_validation ** 2))
    direction_accuracy = float(
        np.mean(np.sign(validation_predictions) == np.sign(y_validation))
    )

    latest = _feature_vector(close_prices, len(close_prices) - 1).reshape(1, -1)
    # Refit for the prospective forecast only after recording holdout errors.
    model = make_pipeline(StandardScaler(), Ridge(alpha=8.0))
    model.fit(features, targets)
    raw_return = float(model.predict(latest)[0])

    # If the fit cannot beat a no-change baseline out of sample, shrink to zero.
    relative_skill = 0.0 if baseline_mse <= 0 else float(
        np.clip(1.0 - (return_mse / baseline_mse), 0.0, 1.0)
    )
    shrunk_return = raw_return * relative_skill
    predicted_return = float(np.clip(
        shrunk_return, -MAX_BASE_RETURN[normalized_horizon], MAX_BASE_RETURN[normalized_horizon]
    ))

    current_price = float(close_prices[-1])
    predicted_next_close = current_price * np.exp(predicted_return)
    price_rmse = current_price * np.sqrt(return_mse)
    model_mse = float(price_rmse ** 2)
    error_confidence = 1.0 / (1.0 + (price_rmse / current_price) * 10.0)
    validation_quality = (0.5 * direction_accuracy) + (0.5 * error_confidence)
    validation_confidence = float(np.clip(
        validation_quality * (0.25 + 0.75 * relative_skill), 0.0, 1.0
    ))

    meta = {
        "current_price": round(current_price, 2),
        "bar_interval": df.attrs.get("bar_interval", "1h" if normalized_horizon == "hour" else "1d"),
        "forward_bars": forward_bars,
        "raw_return_percent": round(float((np.exp(raw_return) - 1) * 100), 4),
        "predicted_return_percent": round(float((np.exp(predicted_return) - 1) * 100), 4),
        "relative_skill": round(relative_skill, 4),
        "direction_accuracy": round(direction_accuracy, 4),
        "validation_samples": int(len(y_validation)),
        "validation_method": "purged_expanding_window",
        "validation_folds": fold_details,
        "return_mse": return_mse,
        "baseline_return_mse": baseline_mse,
        "last_bar_at": str(df.index[-1]),
        "market_data_provider": df.attrs.get("provider", "unknown"),
    }
    print(
        f"[trainer_1_yfinance] Prediction complete: {predicted_next_close:.2f} "
        f"(skill={relative_skill:.3f}, direction={direction_accuracy:.3f})"
    )
    return {
        "trainer": "base",
        "prediction": round(float(np.exp(predicted_return) - 1), 6),
        "confidence": round(validation_confidence, 3),
        "validation_confidence": round(validation_confidence * 100, 1),
        "model_mse": round(model_mse, 6),
        "predicted_next_close": round(float(predicted_next_close), 2),
        "meta": meta,
    }


if __name__ == "__main__":
    import json
    import sys
    symbol = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    selected_horizon = sys.argv[2] if len(sys.argv) > 2 else "day"
    print(json.dumps(predict(symbol, selected_horizon), indent=2))
