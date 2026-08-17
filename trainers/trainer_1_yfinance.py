import yfinance as yf
import numpy as np
import threading
import time


DATA_CACHE_TTL_SECONDS = 300
_DATA_CACHE = {}
_DATA_CACHE_LOCK = threading.Lock()

def fetch_yfinance_data(ticker: str, period="6mo", interval="1d"):
    key = (ticker.upper(), period, interval)
    now = time.time()
    with _DATA_CACHE_LOCK:
        cached = _DATA_CACHE.get(key)
        if cached and now - cached[0] < DATA_CACHE_TTL_SECONDS:
            return cached[1].copy()

        try:
            data = yf.download(
                ticker,
                period=period,
                interval=interval,
                progress=False,
                auto_adjust=True,
                threads=False,
            )
            if data.empty:
                raise RuntimeError(f"No market history returned for {ticker}")
            _DATA_CACHE[key] = (now, data.copy())
            return data
        except Exception as e:
            if cached:
                print(f"[trainer_1_yfinance] Using stale cache for {ticker}: {e}")
                return cached[1].copy()
            print(f"[trainer_1_yfinance] Error fetching data for {ticker}: {e}")
            return None

def calculate_features_numpy(close_prices):
    # close_prices is a numpy array (1D)
    returns = np.diff(close_prices) / close_prices[:-1]
    ma5 = np.convolve(close_prices, np.ones(5)/5, mode='valid')
    ma10 = np.convolve(close_prices, np.ones(10)/10, mode='valid')
    
    # Volatility: rolling std of returns (window 10)
    vol = np.array([np.std(returns[i:i+10]) for i in range(len(returns)-9)])
    
    # Momentum: difference of close price - close price 5 steps ago
    momentum = close_prices[5:] - close_prices[:-5]
    
    # Align lengths (shortest length to use for prediction)
    min_len = min(len(ma10), len(vol), len(momentum))
    
    # Truncate all to min_len
    ma10 = ma10[-min_len:]
    vol = vol[-min_len:]
    momentum = momentum[-min_len:]
    ma5 = ma5[-min_len:]
    
    return {
        "returns": returns[-min_len:],
        "ma5": ma5,
        "ma10": ma10,
        "volatility": vol,
        "momentum": momentum
    }

def exponential_smoothing(values, alpha=0.5):
    if len(values) == 0:
        return 0.0
    smoothed = values[0]
    for v in values[1:]:
        smoothed = alpha * v + (1 - alpha) * smoothed
    return smoothed

def predict(ticker: str, horizon="day"):
    print(f"[trainer_1_yfinance] Starting prediction for {ticker} horizon={horizon}")
    df = fetch_yfinance_data(ticker)
    if df is None or len(df) < 20:
        return {
            "trainer": "base",
            "error": "Insufficient data",
            "confidence": 0.0,
            "predicted_next_close": 0.0,
            "meta": {}
        }

    close_prices = df['Close'].to_numpy().flatten()  # <-- Flatten here

    features = calculate_features_numpy(close_prices)

    if len(features['ma10']) < 5:
        return {
            "trainer": "base",
            "error": "Not enough data after feature calculation",
            "confidence": 0.0,
            "predicted_next_close": float(close_prices[-1]),
            "meta": {}
        }

    current_price = close_prices[-1]

    # Backtest a trailing-ten-close baseline so downstream signal confidence
    # is evidence-based instead of permanently zero due to a missing MSE.
    baseline_predictions = np.array([
        np.mean(close_prices[index - 10:index])
        for index in range(10, len(close_prices))
    ])
    baseline_actuals = close_prices[10:]
    model_mse = float(np.mean((baseline_actuals - baseline_predictions) ** 2))
    
    # Simple trend: smooth ma10[-5:]
    smoothed_trend = exponential_smoothing(features['ma10'][-5:])

    predicted_pct_change = (smoothed_trend - current_price) / current_price
    predicted_pct_change = np.clip(predicted_pct_change, -0.1, 0.1)

    recent_vol = features['volatility'][-1]
    confidence = float(np.clip(1.0 - recent_vol * 5, 0.1, 1.0))

    predicted_next_close = current_price * (1 + predicted_pct_change)

    meta = {
        "current_price": round(float(current_price), 2),
        "smoothed_trend": round(float(smoothed_trend), 2),
        "volatility": round(float(recent_vol), 4),
        "predicted_pct_change": round(float(predicted_pct_change), 5)
    }

    print(f"[trainer_1_yfinance] Prediction complete: {predicted_next_close:.2f} (conf={confidence:.3f})")

    return {
        "trainer": "base",
        "prediction": round(float(predicted_pct_change), 5),
        "confidence": round(confidence, 3),
        "model_mse": round(model_mse, 6),
        "predicted_next_close": round(float(predicted_next_close), 2),
        "meta": meta
    }

# Local test
if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    result = predict(ticker)
    print(result)
